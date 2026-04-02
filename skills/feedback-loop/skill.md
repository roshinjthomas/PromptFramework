# Skill: Feedback Loop

## Using Thumbs Feedback for Fine-Tuning

### Collection Strategy
Collect feedback at the response level (per query-response pair), not at the conversation level. This allows fine-grained filtering.

Store with:
- `rating`: thumbs_up or thumbs_down
- `query`: exact user question
- `response`: full chatbot response (with citations)
- `session_id`: for conversation-level analysis
- `timestamp`: for temporal drift analysis
- `citations`: which sources were used (for retrieval quality analysis)

### What to Export for Fine-Tuning

**Export thumbs-up only** for supervised fine-tuning. Thumbs-down examples can be used for:
- Direct Preference Optimization (DPO) training (requires thumbs-up as chosen, thumbs-down as rejected).
- Identifying systematic failures in the RAG pipeline.

### OpenAI Chat Format (preferred for most SLMs)
```jsonl
{"messages": [{"role": "user", "content": "What is your return policy?"}, {"role": "assistant", "content": "You can return items within 30 days..."}]}
{"messages": [{"role": "user", "content": "Do you offer free shipping?"}, {"role": "assistant", "content": "Free shipping is available on orders over $50..."}]}
```

### Quality Filtering Before Export
1. Minimum rating: thumbs_up only.
2. Minimum response length: discard responses < 50 characters.
3. No fallback responses: exclude responses where `used_fallback: true`.
4. Deduplication: remove near-duplicate query-response pairs.

### Dataset Size for Fine-Tuning
- Phi-3 Mini LoRA fine-tuning: minimum 100–500 high-quality examples for noticeable improvement.
- Full fine-tuning: 1000+ examples recommended.
- Collect feedback actively before attempting fine-tuning.

### Fine-Tuning Tools
- **Hugging Face TRL**: `trl SFTTrainer` for supervised fine-tuning on chat format.
- **Axolotl**: easier YAML-based fine-tuning config for Phi-3 and Llama.
- **LM Studio**: for quick LoRA fine-tuning without code.
