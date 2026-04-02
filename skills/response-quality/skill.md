# Skill: Response Quality

## Citation Format Standards

### Inline Citations
Include source references inline at the end of relevant sentences:
```
You can return electronics within 30 days of purchase. [Returns Policy, p.4]
```

### Citation Block (appended)
Append a numbered citation block at the end of the response:
```
Sources:
[1] Returns Policy Guide, p.4 — "Electronics Return Conditions"
[2] Shipping FAQ, p.2 — "Delivery Timeframes"
```

### Citation Deduplication
If multiple chunks from the same page are used, cite the page only once.
Use a `set` of `(source_file, page_number)` tuples to deduplicate.

## Fallback Phrasing

The fallback message MUST:
1. Acknowledge that the information isn't available in the knowledge base.
2. Provide a concrete next step (contact info or escalation path).
3. Be polite and not dismissive.

Standard fallback:
```
I don't have specific information about that in my knowledge base.
Please contact our support team at support@example.com or call 1-800-XXX-XXXX.
```

Customize contact details via environment variables:
```
SUPPORT_EMAIL=support@yourcompany.com
SUPPORT_PHONE=1-800-555-0100
```

## Tone Guardrails

### Required Tone: Professional + Empathetic
- Address the customer's actual need, not just the literal question.
- If the answer is "no" or restrictive, soften with alternatives.
- Example: "Unfortunately, we can't process returns after 30 days, but you may be eligible for an exchange or store credit. Please contact our team to explore options."

### Prohibited Patterns
- Filler openers: "Certainly!", "Absolutely!", "Great question!"
- Condescending: "As I mentioned...", "Obviously...", "You should know..."
- Uncertainty without fallback: "I think...", "I'm not sure but..."

## Streaming Quality
When streaming, the quality of the response is the same as non-streaming. The difference is delivery mechanism only (SSE tokens vs. complete response). Always post-process the full streamed response before displaying to the user.
