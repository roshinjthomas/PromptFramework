# Agent: SLM Inference

## Purpose
Assembles the system prompt with retrieved context, submits it to the configured Small Language Model (default: Phi-3 Mini), and returns the generated response.

## Trigger
Called after the Retriever agent, with the retrieved context as input.

## Inputs
- `query` (string): The customer's question.
- `context` (string): Formatted retrieved chunks from the Retriever agent.
- `company_name` (string, optional): Injected into the system prompt (default: "our company").
- `stream` (bool): If true, stream tokens via generator.

## System Prompt Template
```
You are a helpful, professional customer service assistant for {company_name}.
Answer questions using ONLY the information provided in the context below.
If the answer is not in the context, say: "I don't have that information — please contact our support team."
Always be polite, concise, and cite the document section you're referencing.

Context:
{retrieved_chunks}

Customer Question:
{user_query}
```

## SLM Configuration (`config/slm.yaml`)
- Model: `microsoft/Phi-3-mini-4k-instruct`
- Quantization: 4-bit (bitsandbytes)
- max_new_tokens: 512
- temperature: 0.1
- top_p: 0.9
- repetition_penalty: 1.1
- device: auto (CPU/GPU)

## Outputs
```json
{
  "response": "You can return electronics within 30 days of purchase...",
  "model_id": "microsoft/Phi-3-mini-4k-instruct",
  "generation_time_s": 4.2,
  "prompt_chars": 1240
}
```

## Streaming
When `stream=True`, yields tokens via `stream_response()` generator for SSE delivery to the UI.

## Implementation
`scripts/pipeline/inference.py:generate_response()` / `stream_response()`
