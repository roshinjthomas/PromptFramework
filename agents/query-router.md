# Agent: Query Router

## Purpose
Classifies incoming queries and routes them to the appropriate handler:
- **RAG pipeline** — for questions requiring knowledge base retrieval.
- **FAQ shortcut** — for simple greetings, out-of-scope questions, or pre-cached answers.

## Trigger
Called at the start of every chat request, before the Retriever agent.

## Routing Logic

### FAQ Shortcut (no retrieval needed)
Conditions:
- Query length < 5 words AND matches a greeting pattern (e.g., "hi", "hello", "thanks").
- Query matches a hard-coded out-of-scope pattern (e.g., "what is the weather").
- Query matches a pre-cached FAQ (exact string match from a small FAQ dict).

Action: Return pre-built response immediately, skip retrieval + SLM.

### RAG Pipeline (default)
All other queries are routed through the full RAG pipeline:
Retrieve → Inference → Post-process.

## Pre-cached FAQ Examples
```python
FAQ_CACHE = {
    "hi": "Hello! How can I help you today?",
    "hello": "Hi there! What can I assist you with?",
    "thanks": "You're welcome! Is there anything else I can help with?",
    "thank you": "Happy to help! Feel free to ask if you have more questions.",
}
```

## Future Extensions
- Add intent classification using a lightweight classifier.
- Route complex multi-step queries to a multi-turn agent.
- Cache high-frequency queries for sub-100ms responses.

## Implementation
Inline logic in `backend/routers/chat.py` (check FAQ cache before calling retrieve()).
