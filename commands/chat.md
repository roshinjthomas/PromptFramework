# /chat

Start an interactive customer chat session against the knowledge base.

## Usage
```
/chat
/chat --company "Acme Corp"
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `--company` | string | no | Company name injected into the system prompt (default: "our company") |

## What Happens
1. Opens an interactive REPL-style session.
2. Each query is embedded and top-5 chunks retrieved from ChromaDB.
3. Phi-3 Mini generates a response grounded in the retrieved context.
4. Response is returned with inline citations (`[Source: filename, p.N]`).
5. Conversation is saved to `data/feedback/` for later export.

## Example Session
```
/chat --company "Acme Corp"

You: What is your return policy for electronics?

Bot: Electronics can be returned within 30 days of purchase with the
original receipt and in original packaging. [Source: Returns Policy, p.4]

Sources:
  [1] returns-policy.pdf, p.4 — "Electronics Return Conditions"
  [2] returns-policy.pdf, p.2 — "General Return Policy"

You: What about software?

Bot: Software purchases are non-refundable once the license key has been
activated. [Source: Returns Policy, p.6]
```

## Fallback
If no relevant chunks are found:
```
I don't have specific information about that in my knowledge base.
Please contact our support team at support@example.com or call 1-800-XXX-XXXX.
```

## Agent
`agents/slm-inference.md`, `agents/retriever.md`, `agents/response-postprocessor.md`

## Web UI
For a full web interface, use `/eval-ui` and navigate to the Chat tab.
