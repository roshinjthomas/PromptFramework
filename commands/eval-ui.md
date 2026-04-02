# /eval-ui

Launch the React web app — starts both the FastAPI backend and Vite dev server.

## Usage
```
/eval-ui
/eval-ui --port 3000
/eval-ui --backend-port 8000
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `--port` | int | no | Vite dev server port (default: 3000) |
| `--backend-port` | int | no | FastAPI server port (default: 8000) |

## What Happens
1. Starts FastAPI backend: `uvicorn backend.main:app --reload --port 8000`
2. Starts Vite dev server: `cd ui && npm run dev`
3. Opens browser to `http://localhost:3000`

## App Layout
- **Chat tab** (`/`): Customer chatbot with streaming responses and sources sidebar.
- **Evaluation tab** (`/evaluation`): Full RAGAS dashboard with ScoreCard, TrendChart, QuestionTable, FailureExplorer, ConfigPanel, and RunSelector.

## Manual Start
```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd ui && npm run dev
```

## Production Build
```bash
cd ui && npm run build
# Then the FastAPI app serves the built files from ui/dist/
```

## Agent
`agents/eval-reporter.md`
