# RAG Chatbot Framework — Example CLAUDE.md

This is an example `CLAUDE.md` project config for the RAG Chatbot Framework. Place it in your project root as `CLAUDE.md` to configure Claude Code's behavior for this project.

---

## Project Overview

This is a RAG-based customer service chatbot for **Acme Corp**.

- **Knowledge base**: Product manual, returns policy, shipping FAQ, payment FAQ.
- **Model**: Phi-3 Mini 4-bit quantized.
- **Evaluation**: RAGAS with weekly scheduled runs.

---

## Commands Available

| Command | Description |
|---|---|
| `/ingest <pdf>` | Add a PDF to the knowledge base |
| `/chat` | Interactive chat session |
| `/evaluate` | Run RAGAS evaluation |
| `/eval-ui` | Launch the web app |
| `/kb-list` | List all ingested documents |
| `/kb-remove <file>` | Remove a document |
| `/kb-refresh <new> --replace <old>` | Update a document |
| `/tune-retriever` | Adjust retrieval config + re-evaluate |
| `/export-dataset` | Export fine-tuning JSONL |

---

## Important Rules

1. **Never change `config/rag.yaml` or `config/slm.yaml` without running `/evaluate` first.**
2. **faithfulness score must stay ≥ 0.80.** A drop indicates hallucination — investigate immediately.
3. **All PDFs must be text-based or have OCR applied.** Password-protected PDFs are rejected.
4. **PII must be stripped before ingestion.** Do not ingest customer records or HR files.
5. **The test dataset must have ≥ 20 questions** before any production deployment.

---

## Environment Setup

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt

cd ui && npm install && cd ..

# Copy example configs
cp config/rag.yaml.example config/rag.yaml    # (if examples exist)
```

---

## Backend Start

```bash
uvicorn backend.main:app --reload --port 8000
```

## Frontend Start

```bash
cd ui && npm run dev
```

---

## Directory Structure Notes

- `data/documents/` — Source PDFs (gitignored, do not commit)
- `data/vector-store/` — ChromaDB index (gitignored)
- `data/feedback/` — User feedback store (gitignored)
- `data/evaluation/results/` — RAGAS run results (committed for audit trail)
- `config/` — YAML config files (committed, no secrets)
