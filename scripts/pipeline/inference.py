"""
SLM inference pipeline.

Assembles prompt + retrieved context, calls the Phi-3 Mini model via
transformers pipeline, and returns the generated response.
"""

from __future__ import annotations

import time
from typing import Any, Generator, Optional

from scripts.lib.utils import get_logger, load_slm_config

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are a helpful, professional customer service assistant for {company_name}.
Answer questions using ONLY the information provided in the context below.
If the answer is not in the context, say: "I don't have that information — please contact our support team."
Always be polite, concise, and cite the document section you're referencing.

Context:
{retrieved_chunks}

Customer Question:
{user_query}"""


# ---------------------------------------------------------------------------
# Model loader (lazy singleton)
# ---------------------------------------------------------------------------

_pipeline_cache: dict[str, Any] = {}


def _load_pipeline(config: dict) -> Any:
    """Load (or retrieve cached) transformers text-generation pipeline."""
    model_cfg = config.get("model", {})
    model_id: str = model_cfg.get("id", "microsoft/Phi-3-mini-4k-instruct")
    quantization: str = model_cfg.get("quantization", "none")
    device_str: str = config.get("inference", {}).get("device", "auto")

    cache_key = f"{model_id}::{quantization}::{device_str}"
    if cache_key in _pipeline_cache:
        return _pipeline_cache[cache_key]

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
    except ImportError as exc:
        raise ImportError(
            "transformers and torch are required. "
            "Run: pip install transformers torch"
        ) from exc

    logger.info("Loading model '%s' (quantization=%s)…", model_id, quantization)

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    # Quantization config
    bnb_config = None
    if quantization == "4bit":
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        except Exception as e:
            logger.warning("4-bit quantization not available (%s), loading in fp32.", e)
    elif quantization == "8bit":
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
        except Exception as e:
            logger.warning("8-bit quantization not available (%s), loading in fp32.", e)

    model_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if bnb_config:
        model_kwargs["quantization_config"] = bnb_config
        model_kwargs["device_map"] = device_str
    else:
        if device_str != "cpu":
            model_kwargs["device_map"] = device_str

    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        return_full_text=False,
    )

    _pipeline_cache[cache_key] = pipe
    logger.info("Model '%s' loaded and cached.", model_id)
    return pipe


# ---------------------------------------------------------------------------
# Inference function
# ---------------------------------------------------------------------------

def generate_response(
    query: str,
    context: str,
    *,
    company_name: str = "our company",
    config: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Generate a customer service response using the SLM.

    Args:
        query:        The customer's question.
        context:      Formatted retrieved context string.
        company_name: Company name inserted into the system prompt.
        config:       SLM config override (defaults to config/slm.yaml).

    Returns:
        Dict with keys: response (str), model_id, generation_time_s, prompt_tokens (approx).
    """
    cfg = config or load_slm_config()
    model_cfg = cfg.get("model", {})
    inference_cfg = cfg.get("inference", {})

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        company_name=company_name,
        retrieved_chunks=context if context else "No relevant documents found.",
        user_query=query,
    )

    pipe = _load_pipeline(cfg)

    gen_kwargs: dict[str, Any] = {
        "max_new_tokens": model_cfg.get("max_new_tokens", 512),
        "temperature": model_cfg.get("temperature", 0.1),
        "top_p": model_cfg.get("top_p", 0.9),
        "repetition_penalty": model_cfg.get("repetition_penalty", 1.1),
        "do_sample": model_cfg.get("temperature", 0.1) > 0,
    }

    timeout = inference_cfg.get("timeout_seconds", 30)

    t0 = time.time()
    try:
        outputs = pipe(prompt, **gen_kwargs)
        generated = outputs[0]["generated_text"].strip()
    except Exception as exc:
        logger.error("SLM inference failed: %s", exc)
        generated = (
            "I'm sorry, I encountered an error generating a response. "
            "Please try again or contact our support team."
        )

    gen_time = time.time() - t0
    logger.info("Response generated in %.2fs", gen_time)

    return {
        "response": generated,
        "model_id": model_cfg.get("id", "unknown"),
        "generation_time_s": round(gen_time, 3),
        "prompt_chars": len(prompt),
    }


def stream_response(
    query: str,
    context: str,
    *,
    company_name: str = "our company",
    config: Optional[dict] = None,
) -> Generator[str, None, None]:
    """
    Stream the SLM response token-by-token using transformers TextIteratorStreamer.

    Yields individual text tokens as they are generated.
    """
    cfg = config or load_slm_config()
    model_cfg = cfg.get("model", {})

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        company_name=company_name,
        retrieved_chunks=context if context else "No relevant documents found.",
        user_query=query,
    )

    try:
        import threading
        from transformers import TextIteratorStreamer

        pipe = _load_pipeline(cfg)
        tokenizer = pipe.tokenizer
        model = pipe.model

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

        gen_kwargs: dict[str, Any] = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": model_cfg.get("max_new_tokens", 512),
            "temperature": model_cfg.get("temperature", 0.1),
            "top_p": model_cfg.get("top_p", 0.9),
            "repetition_penalty": model_cfg.get("repetition_penalty", 1.1),
            "do_sample": model_cfg.get("temperature", 0.1) > 0,
        }

        thread = threading.Thread(target=model.generate, kwargs=gen_kwargs)
        thread.start()

        for token in streamer:
            yield token

        thread.join()

    except Exception as exc:
        logger.error("Streaming inference failed: %s", exc)
        yield (
            "I'm sorry, I encountered an error generating a response. "
            "Please contact our support team."
        )
