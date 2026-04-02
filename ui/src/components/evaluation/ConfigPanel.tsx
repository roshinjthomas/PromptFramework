import type { ConfigSnapshot } from '../../types/evaluation'

interface ConfigPanelProps {
  config?: ConfigSnapshot
}

function ConfigRow({ label, value }: { label: string; value?: string | number | null }) {
  if (value == null) return null
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-xs font-mono font-medium text-gray-800">{String(value)}</span>
    </div>
  )
}

export default function ConfigPanel({ config }: ConfigPanelProps) {
  if (!config) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 text-center text-gray-400 text-sm">
        No configuration snapshot available for this run.
      </div>
    )
  }

  const { rag, slm } = config

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* RAG Config */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">RAG Configuration</h4>
        <ConfigRow label="Chunk Size" value={rag?.chunk_size ? `${rag.chunk_size} tokens` : null} />
        <ConfigRow label="Chunk Overlap" value={rag?.chunk_overlap ? `${rag.chunk_overlap} tokens` : null} />
        <ConfigRow label="Top-K" value={rag?.top_k} />
        <ConfigRow label="Score Threshold" value={rag?.score_threshold} />
        <ConfigRow label="Embedding Model" value={rag?.embedding_model} />
      </div>

      {/* SLM Config */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">SLM Configuration</h4>
        <ConfigRow label="Model ID" value={slm?.model_id} />
        <ConfigRow label="Quantization" value={slm?.quantization} />
        <ConfigRow label="Temperature" value={slm?.temperature} />
        <ConfigRow label="Max New Tokens" value={slm?.max_new_tokens} />
      </div>
    </div>
  )
}
