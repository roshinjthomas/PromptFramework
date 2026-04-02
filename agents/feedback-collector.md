# Agent: Feedback Collector

## Purpose
Captures user thumbs up/down ratings after each chat response and stores them with the full query-response pair for use in fine-tuning dataset construction.

## Trigger
- User clicks thumbs up/down in the chat UI.
- `on-chat-end` hook fires when a session ends (saves full conversation).

## Inputs
- `query` (string): The user's question.
- `response` (string): The chatbot's response.
- `rating` (string): `"thumbs_up"` or `"thumbs_down"`.
- `session_id` (string, optional): Chat session identifier.
- `citations` (list, optional): Source references from the response.
- `comment` (string, optional): Optional free-text comment.

## Storage Format
Feedback is appended to `data/feedback/feedback_store.json`:
```json
{
  "id": "uuid",
  "timestamp": "2026-04-01T12:00:00Z",
  "session_id": "abc123",
  "rating": "thumbs_up",
  "query": "What is your return policy?",
  "response": "You can return items within 30 days...",
  "citations": [{"source_file": "returns-policy.pdf", "page_number": 4}],
  "comment": null
}
```

## Export
The `exporter.py` script converts stored feedback to JSONL for fine-tuning:
- `--min-rating thumbs_up` — only export positive examples.
- `--format chat` — OpenAI chat format (messages array).
- `--format instruction` — Alpaca instruction format.

## Implementation
- `scripts/feedback/collector.py:store_feedback()`
- `scripts/feedback/exporter.py:export_dataset()`
- `backend/routers/chat.py` POST `/api/chat/feedback`
