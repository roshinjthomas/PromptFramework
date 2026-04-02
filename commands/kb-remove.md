# /kb-remove

Remove a document and all its chunks from the knowledge base.

## Usage
```
/kb-remove returns-policy.pdf
/kb-remove "product manual v1.pdf"
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `filename` | string | yes | Exact filename of the document to remove (as shown in `/kb-list`) |

## What Happens
1. Calls `VectorStore.delete_by_source(filename)`.
2. Removes all ChromaDB chunks with `source_file == filename`.
3. Optionally deletes the source PDF from `data/documents/`.
4. Reports the number of chunks deleted.

## Example Output
```
Removed: returns-policy.pdf
  Chunks deleted: 28
  Total chunks remaining: 187
```

## Errors
- Document not found in KB: prints warning, does not error.
- Cannot remove file from disk (permissions): logs warning, KB chunks still deleted.

## Agent
`agents/kb-manager.md`

## Implementation
`scripts/lib/vector_store.py:VectorStore.delete_by_source()`
`backend/routers/knowledge_base.py` DELETE `/api/kb/{doc_id}`
