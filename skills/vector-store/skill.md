# Skill: Vector Store

## ChromaDB Setup and Usage

### Why ChromaDB
- Zero-config local persistence (no Docker required).
- Built-in cosine similarity search.
- Simple Python API.
- Supports metadata filtering.

### Collection Setup
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="data/vector-store",
    settings=Settings(anonymized_telemetry=False),
)
collection = client.get_or_create_collection(
    name="customer-kb",
    metadata={"hnsw:space": "cosine"},
)
```

### Adding Documents
```python
collection.add(
    ids=["chunk-001", "chunk-002"],
    documents=["text of chunk 1", "text of chunk 2"],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    metadatas=[{"source_file": "policy.pdf", "page_number": 4}, ...],
)
```

### Querying
```python
results = collection.query(
    query_embeddings=[[0.15, 0.25, ...]],
    n_results=5,
    include=["documents", "metadatas", "distances"],
    where={"source_file": "policy.pdf"},  # optional filter
)
```

### Distance to Similarity Conversion
ChromaDB returns cosine **distance** (0=identical, 2=opposite):
```python
similarity = 1.0 - (distance / 2.0)
```

## FAISS Alternative
FAISS is faster at scale but requires manual persistence (no built-in metadata filtering):
```python
import faiss
import numpy as np

dim = 384
index = faiss.IndexFlatIP(dim)  # Inner product (for normalized vectors = cosine)
index.add(np.array(embeddings, dtype=np.float32))
```

## Performance Tips
- For collections > 100k chunks, use `chromadb.EphemeralClient()` with an external Chroma server.
- Normalize embeddings before adding (`normalize_embeddings=True` in SentenceTransformer).
- For FAISS at scale: use `IndexIVFFlat` with `nlist=100` for approximate nearest neighbor search.
