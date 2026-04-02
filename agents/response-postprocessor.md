# Agent: Response Post-Processor

## Purpose
Applies three post-processing steps to the SLM-generated response before returning it to the user:
1. **Fallback guard** — Replaces the response with a support contact message if no chunks were retrieved.
2. **Citation injection** — Appends formatted source references.
3. **Tone check** — Flags hallucination signals and unprofessional language.

## Trigger
Called after SLM Inference, before returning the API response.

## Inputs
- `response` (string): Raw text from the SLM.
- `chunks` (list): Retrieved chunks used to generate the response.
- `inject_sources` (bool, default true): Whether to append citation list.
- `tone_check` (bool, default true): Whether to run tone analysis.

## Processing Steps

### 1. Fallback Guard
If `chunks` is empty, replace `response` with:
```
I don't have specific information about that in my knowledge base.
Please contact our support team at support@example.com or call 1-800-XXX-XXXX.
```

### 2. Citation Injection
Append a de-duplicated source list to the response:
```
Sources:
[1] Returns Policy Guide, p.4 — "Return Conditions"
[2] Shipping FAQ, p.2 — "Delivery Times"
```

### 3. Tone Check
Pattern-match for:
- Hallucination signals: "I believe", "I think", "probably", "might be"
- Tone violations: "obviously", "frankly", "stupid"

Log warnings; do not auto-modify (leave that for future fine-tuning feedback).

## Outputs
```json
{
  "response": "Full response text with citations appended...",
  "citations": [
    {"id": 1, "source_file": "returns-policy.pdf", "page_number": 4, "label": "Returns Policy Guide", "score": 0.87}
  ],
  "tone": {"is_acceptable": true, "warnings": []},
  "used_fallback": false
}
```

## Implementation
`scripts/pipeline/postprocess.py:postprocess()`
