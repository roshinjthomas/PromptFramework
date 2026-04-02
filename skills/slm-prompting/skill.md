# Skill: SLM Prompting

## System Prompt Design for Customer Service SLMs

### Core Structure
Every prompt must have these sections in order:
1. Role + company name
2. Instruction: answer ONLY from context
3. Fallback instruction: what to say when context is missing
4. Tone instruction: polite, cite sources
5. Context block (retrieved chunks, labeled)
6. Customer question (clearly labeled)

### Phi-3 Mini Chat Format
Phi-3 Mini uses a specific chat template. Use the tokenizer's `apply_chat_template()` method rather than raw string formatting for best results.

```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": query},
]
tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

### Tone Calibration
- Temperature 0.1: very factual, deterministic. Best for policy Q&A.
- Temperature 0.3: slightly more natural. Best for conversational queries.
- Temperature > 0.5: too creative for customer service — avoid.

### Hallucination Prevention in Prompts
- Explicitly say "ONLY use the information provided below".
- Include a specific fallback phrase the model should use.
- Keep context < 3000 tokens to avoid model attention drift on long contexts.

### Citation Instruction Patterns
Good: "Cite the document name and page number in brackets, like [Returns Policy, p.4]."
Better: Include an example citation in the system prompt so the model mimics the format.

### Multi-turn Conversation
Phi-3 Mini 4k has a 4096 token context window. For multi-turn:
- Include last 2–3 turns of history.
- Summarize earlier history if needed.
- Re-attach the retrieved context for each turn (retrieval is per-query).
