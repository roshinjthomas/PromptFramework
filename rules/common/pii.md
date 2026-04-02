# Rule: PII Handling

## Core Rule
**Strip personally identifiable information (PII) from all document text before embedding and storing in the vector store.**

PII in the knowledge base can be inadvertently surfaced in chatbot responses, creating privacy and compliance risks (GDPR, CCPA, HIPAA).

## What Counts as PII
- Full names (e.g., "John Smith")
- Email addresses (e.g., `john@example.com`)
- Phone numbers (e.g., `+1-800-555-0100`)
- Physical addresses (e.g., `123 Main St, Springfield, IL 62701`)
- National ID numbers (SSN, NI, etc.)
- Credit card / bank account numbers
- Date of birth

## Exceptions
The following are **not** PII and should **not** be stripped:
- Company names, brand names
- Generic support contact emails (e.g., `support@example.com` — acceptable if intentional)
- Geographic regions used for policy scope (e.g., "available in the US and Canada")

## Implementation
PII stripping SHOULD be applied in `scripts/lib/pdf_parser.py` during the parse step, before chunking and embedding. Use regex patterns or a dedicated library (e.g., `presidio-analyzer` from Microsoft).

### Recommended Patterns (minimum)
```python
import re
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
SSN_RE   = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
```

Replace matched PII with `[REDACTED]` before chunking.

## Audit
Log the count of PII redactions per document during ingestion so teams can review and confirm sensitive documents were handled correctly.

## Source Documents
Do NOT store sensitive source PDFs (e.g., HR files, customer records) in the knowledge base. The knowledge base is for product/policy/FAQ documents only.
