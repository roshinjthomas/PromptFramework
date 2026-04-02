# Rule: SLM Prompting Standards

## System Prompt Requirements
Every system prompt sent to the SLM MUST include ALL of the following:

1. **Role declaration**: "You are a helpful, professional customer service assistant for {company_name}."
2. **Context-only instruction**: "Answer questions using ONLY the information provided in the context below."
3. **Fallback instruction**: "If the answer is not in the context, say: 'I don't have that information — please contact our support team.'"
4. **Citation instruction**: "Always be polite, concise, and cite the document section you're referencing."
5. **Context block**: The retrieved chunks, formatted with source labels.
6. **Query**: The customer's question, clearly labeled.

## Tone Guidelines
- Always professional and polite.
- Never condescending, dismissive, or informal.
- Use "I" (first person) to speak as the assistant, not "the system" or "the chatbot".
- Avoid filler phrases: "Certainly!", "Absolutely!", "Of course!" — respond directly.

## Temperature
- Temperature MUST be ≤ 0.3 for factual customer service responses.
- Higher temperatures increase creativity but also hallucination risk.
- Default: 0.1.

## Context Window Management
- The prompt (system + context + query) must fit within the model's context window (4096 tokens for Phi-3 Mini 4k).
- If retrieved context would exceed 3000 tokens, truncate the least-relevant chunks (lowest similarity score).

## Do Not
- Do not allow the SLM to browse the internet, run code, or call external APIs.
- Do not include conversation history beyond the current turn (stateless by default).
- Do not allow the SLM to make up policies, prices, or contact details not in the retrieved context.
