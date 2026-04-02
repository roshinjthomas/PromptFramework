"""
Claude API inference pipeline (async-native).

Uses claude-haiku-4-5 via the Anthropic SDK.
Requires ANTHROPIC_API_KEY in the environment or .env file.
"""

from __future__ import annotations

import time
from typing import Any, AsyncGenerator, Generator, Optional

from scripts.lib.utils import get_logger, load_slm_config

logger = get_logger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a helpful, professional customer service assistant for {company_name}.
Answer questions using ONLY the information provided in the context below.
If the answer is not in the context, say: "I don't have that information — please contact our support team."
Always be polite, concise, and cite the document section you're referencing.

Context:
{retrieved_chunks}"""

# Lazy singletons
_sync_client = None
_async_client = None


def _get_sync_client():
    global _sync_client
    if _sync_client is None:
        import anthropic
        _sync_client = anthropic.Anthropic()
    return _sync_client


def _get_async_client():
    global _async_client
    if _async_client is None:
        import anthropic
        _async_client = anthropic.AsyncAnthropic()
    return _async_client


def _build_system(company_name: str, context: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        company_name=company_name,
        retrieved_chunks=context if context else "No relevant documents found.",
    )


def generate_response(
    query: str,
    context: str,
    *,
    company_name: str = "our company",
    config: Optional[dict] = None,
) -> dict[str, Any]:
    """Synchronous non-streaming response."""
    cfg = config or load_slm_config()
    model_id = cfg.get("model", {}).get("claude_id", "claude-haiku-4-5-20251001")
    max_tokens = cfg.get("model", {}).get("max_new_tokens", 512)
    temperature = cfg.get("model", {}).get("temperature", 0.1)

    system = _build_system(company_name, context)
    t0 = time.time()
    try:
        client = _get_sync_client()
        message = client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": query}],
        )
        generated = message.content[0].text.strip()
    except Exception as exc:
        logger.error("Claude API inference failed: %s", exc)
        generated = (
            "I'm sorry, I encountered an error generating a response. "
            "Please try again or contact our support team."
        )

    gen_time = time.time() - t0
    logger.info("Response generated in %.2fs", gen_time)

    return {
        "response": generated,
        "model_id": model_id,
        "generation_time_s": round(gen_time, 3),
        "prompt_chars": len(system) + len(query),
    }


async def astream_response(
    query: str,
    context: str,
    *,
    company_name: str = "our company",
    config: Optional[dict] = None,
) -> AsyncGenerator[str, None]:
    """
    Async streaming response — yields text tokens as they arrive.
    Use this from async FastAPI route handlers.
    """
    cfg = config or load_slm_config()
    model_id = cfg.get("model", {}).get("claude_id", "claude-haiku-4-5-20251001")
    max_tokens = cfg.get("model", {}).get("max_new_tokens", 512)
    temperature = cfg.get("model", {}).get("temperature", 0.1)

    system = _build_system(company_name, context)

    try:
        client = _get_async_client()
        async with client.messages.stream(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": query}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        logger.error("Async streaming inference failed: %s", exc)
        yield (
            "I'm sorry, I encountered an error generating a response. "
            "Please contact our support team."
        )


def stream_response(
    query: str,
    context: str,
    *,
    company_name: str = "our company",
    config: Optional[dict] = None,
) -> Generator[str, None, None]:
    """Sync streaming fallback (used for non-async contexts)."""
    cfg = config or load_slm_config()
    model_id = cfg.get("model", {}).get("claude_id", "claude-haiku-4-5-20251001")
    max_tokens = cfg.get("model", {}).get("max_new_tokens", 512)
    temperature = cfg.get("model", {}).get("temperature", 0.1)

    system = _build_system(company_name, context)

    try:
        client = _get_sync_client()
        with client.messages.stream(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": query}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as exc:
        logger.error("Streaming inference failed: %s", exc)
        yield (
            "I'm sorry, I encountered an error generating a response. "
            "Please contact our support team."
        )
