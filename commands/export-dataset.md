# /export-dataset

Export Q&A pairs (with feedback ratings) as a JSONL fine-tuning dataset.

## Usage
```
/export-dataset
/export-dataset --min-rating thumbs-up
/export-dataset --format jsonl --output data/finetune-dataset.jsonl
/export-dataset --format instruction --output alpaca-dataset.jsonl
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `--min-rating` | string | no | Filter by rating: `thumbs-up` or `thumbs-down` (default: `thumbs-up`) |
| `--format` | string | no | Output format: `chat` (OpenAI) or `instruction` (Alpaca) (default: `chat`) |
| `--output` | string | no | Output file path (default: `data/finetune-dataset.jsonl`) |
| `--limit` | int | no | Maximum number of examples to export |

## Chat Format (OpenAI)
```json
{"messages": [
  {"role": "user", "content": "What is your return policy?"},
  {"role": "assistant", "content": "You can return items within 30 days..."}
]}
```

## Instruction Format (Alpaca)
```json
{"instruction": "What is your return policy?", "input": "", "output": "You can return items within 30 days..."}
```

## What Happens
1. Loads `data/feedback/feedback_store.json`.
2. Filters by rating (thumbs-up recommended for quality data).
3. Converts to chosen format.
4. Writes one JSON object per line to the output JSONL file.
5. Reports count exported.

## Example Output
```
Exported 47 examples (thumbs-up, chat format)
Output: data/finetune-dataset.jsonl
```

## Agent
`agents/feedback-collector.md`

## Implementation
`scripts/feedback/exporter.py:export_dataset()`
