# Sample Chat Session Walkthrough

This example demonstrates a typical customer service chat session using the RAG chatbot.

---

## Setup

```bash
# Ensure the backend is running
uvicorn backend.main:app --reload --port 8000

# In another terminal, start the UI
cd ui && npm run dev
# Open http://localhost:3000
```

Or via CLI:
```bash
/chat --company "Acme Corp"
```

---

## Session Transcript

**Bot:** Hello! How can I help you today? Ask me anything about our products or services.

---

**User:** What is your return policy for electronics?

**Bot:** Electronics can be returned within 30 days of purchase with the original receipt and in original packaging. Items must be in their original, undamaged condition. Software licenses that have been activated are non-refundable.

**Sources:**
- [1] Returns Policy Guide, p.4 — "Electronics Return Conditions"
- [2] Returns Policy Guide, p.2 — "General Return Policy Overview"

---

**User:** What about software I bought online?

**Bot:** Software purchases made online are non-refundable once the license key has been activated or the product has been downloaded. If you have not yet activated your license, please contact our support team within 7 days of purchase for assistance.

**Sources:**
- [1] Returns Policy Guide, p.6 — "Digital Products and Software"

---

**User:** Do you offer free shipping?

**Bot:** Yes! Free standard shipping is available on all orders over $50. Orders under $50 are charged a flat shipping fee of $5.99.

**Sources:**
- [1] Shipping FAQ, p.2 — "Shipping Rates and Free Shipping"

---

**User:** How long does shipping take?

**Bot:** Standard shipping typically takes 5–7 business days from the date of dispatch. Expedited shipping (2–3 business days) is available for an additional $12.99. Next-day delivery is available in select areas for $24.99.

**Sources:**
- [1] Shipping FAQ, p.3 — "Delivery Timeframes"
- [2] Shipping FAQ, p.5 — "Expedited Shipping Options"

---

**User:** What's the capital of France?

**Bot:** I don't have specific information about that in my knowledge base.
Please contact our support team at support@example.com or call 1-800-XXX-XXXX.

*(Fallback triggered — no relevant chunks found for this off-topic question)*

---

## What Happened Behind the Scenes

For each query, the pipeline executed:

1. **Embed** — The query was embedded using `all-MiniLM-L6-v2`.
2. **Retrieve** — ChromaDB returned the top-5 chunks with similarity ≥ 0.60.
3. **Generate** — Phi-3 Mini assembled a response from the system prompt + context.
4. **Post-process** — Citations were injected; tone was verified; fallback applied when needed.
5. **Stream** — Tokens were streamed to the UI via Server-Sent Events.

For the last query, no chunks passed the 0.60 threshold, so the fallback response was returned instead of calling the SLM — avoiding any hallucination risk.
