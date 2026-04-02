import type { Citation } from '../../types/chat'

interface SourcePanelProps {
  citations: Citation[]
}

export default function SourcePanel({ citations }: SourcePanelProps) {
  if (citations.length === 0) {
    return (
      <aside className="w-72 border-l border-gray-200 bg-gray-50 flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200 bg-white">
          <h2 className="text-sm font-semibold text-gray-700">Sources</h2>
        </div>
        <div className="flex-1 flex items-center justify-center text-gray-400 text-sm p-4 text-center">
          Sources will appear here after your first message.
        </div>
      </aside>
    )
  }

  return (
    <aside className="w-72 border-l border-gray-200 bg-gray-50 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">Sources</h2>
        <span className="text-xs text-gray-400">{citations.length} document{citations.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-gray-200">
        {citations.map((citation) => (
          <div key={citation.id} className="p-3 hover:bg-white transition-colors">
            {/* Citation number + label */}
            <div className="flex items-start gap-2 mb-1">
              <span className="flex-shrink-0 w-5 h-5 rounded bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mt-0.5">
                {citation.id}
              </span>
              <div>
                <p className="text-xs font-semibold text-gray-800 leading-tight">{citation.label}</p>
                <p className="text-xs text-gray-500">Page {citation.page_number}</p>
              </div>
            </div>

            {/* Section header */}
            {citation.section_header && (
              <p className="text-xs text-blue-600 font-medium ml-7 mb-1 truncate" title={citation.section_header}>
                {citation.section_header}
              </p>
            )}

            {/* Excerpt */}
            {citation.text_excerpt && (
              <p className="text-xs text-gray-500 ml-7 leading-relaxed line-clamp-3 italic">
                "{citation.text_excerpt.slice(0, 180)}{citation.text_excerpt.length > 180 ? '…' : ''}"
              </p>
            )}

            {/* Score badge */}
            <div className="ml-7 mt-1.5">
              <span className="inline-flex items-center text-xs text-gray-400">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 mr-1" />
                {(citation.score * 100).toFixed(0)}% match
              </span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
