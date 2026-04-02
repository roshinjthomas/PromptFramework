# /kb-list

List all documents currently in the knowledge base.

## Usage
```
/kb-list
```

## What Happens
Queries ChromaDB for all unique `source_file` metadata values and their chunk counts.

## Example Output
```
Knowledge Base — 3 documents (215 total chunks)

1. product-manual.pdf       | 142 chunks | ingested 2026-04-01
2. returns-policy.pdf       |  28 chunks | ingested 2026-04-01
3. shipping-faq.pdf         |  45 chunks | ingested 2026-03-28
```

## Empty KB
```
Knowledge Base is empty.
Use /ingest to add your first document.
```

## Agent
`agents/kb-manager.md`

## Implementation
`scripts/lib/vector_store.py:VectorStore.list_sources()`
`backend/routers/knowledge_base.py` GET `/api/kb`
