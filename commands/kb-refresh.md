# /kb-refresh

Re-ingest an updated version of an existing document.

## Usage
```
/kb-refresh returns-policy-v2.pdf --replace returns-policy.pdf
/kb-refresh updated-manual.pdf --replace product-manual.pdf --label "Product Manual v2"
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `new-file` | string | yes | Path to the updated PDF file |
| `--replace` | string | yes | Filename of the existing document to replace |
| `--label` | string | no | New human-readable label |

## What Happens
1. Deletes all chunks for the old document (`delete_by_source(replace)`).
2. Ingests the new PDF using the full Document Ingestion pipeline.
3. Reports old chunk count removed and new chunk count added.

## Example Output
```
Refreshed: product-manual.pdf → product-manual-v2.pdf
  Old chunks removed: 142
  New chunks created: 156
  Net change: +14 chunks
  Total chunks in store: 229
```

## Use Case
Run this whenever a policy document is updated to ensure the KB reflects the latest version without manual cleanup.

## Agent
`agents/kb-manager.md`

## Implementation
`backend/routers/knowledge_base.py` POST `/api/kb/refresh`
