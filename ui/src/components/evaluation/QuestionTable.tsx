import { useState } from 'react'
import type { PerQuestionResult } from '../../types/evaluation'
import { METRIC_LABELS } from '../../types/evaluation'

interface QuestionTableProps {
  questions: PerQuestionResult[]
  thresholds?: Record<string, number>
}

const METRICS = [
  'faithfulness',
  'answer_relevancy',
  'context_precision',
  'context_recall',
  'answer_correctness',
] as const

function ScorePill({ score, threshold }: { score?: number; threshold?: number }) {
  if (score == null) return <span className="text-gray-300 text-xs">—</span>
  const passed = threshold == null || score >= threshold
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-xs font-mono font-medium ${
        passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
      }`}
    >
      {score.toFixed(2)}
    </span>
  )
}

function getScore(q: PerQuestionResult, metric: string): number | undefined {
  // Backend returns scores nested under q.scores{}
  if (q.scores && metric in q.scores) return q.scores[metric]
  // Fallback: flat field
  return (q as Record<string, unknown>)[metric] as number | undefined
}

export default function QuestionTable({ questions, thresholds = {} }: QuestionTableProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  if (questions.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center text-gray-400 text-sm">
        No per-question data available.
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50">
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 w-8">#</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500">Question</th>
            {METRICS.map((m) => (
              <th key={m} className="text-center px-3 py-3 text-xs font-semibold text-gray-500 whitespace-nowrap">
                {METRIC_LABELS[m]?.split(' ')[0]}
              </th>
            ))}
            <th className="w-8" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {questions.map((q, idx) => (
            <>
              <tr
                key={idx}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
              >
                <td className="px-4 py-3 text-xs text-gray-400">{idx + 1}</td>
                <td className="px-4 py-3 text-gray-800 font-medium truncate max-w-xs" title={q.question}>
                  {q.question}
                </td>
                {METRICS.map((m) => (
                  <td key={m} className="px-3 py-3 text-center">
                    <ScorePill score={getScore(q, m)} threshold={thresholds[m]} />
                  </td>
                ))}
                <td className="px-3 py-3 text-gray-400 text-xs">
                  {expandedIdx === idx ? '▲' : '▼'}
                </td>
              </tr>

              {/* Expanded row */}
              {expandedIdx === idx && (
                <tr key={`${idx}-expanded`} className="bg-blue-50">
                  <td colSpan={METRICS.length + 3} className="px-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-semibold text-gray-500 mb-1">Generated Answer</p>
                        <p className="text-xs text-gray-700 leading-relaxed bg-white p-2 rounded border border-gray-200">
                          {q.answer}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-gray-500 mb-1">Ground Truth</p>
                        <p className="text-xs text-gray-700 leading-relaxed bg-white p-2 rounded border border-gray-200">
                          {q.ground_truth}
                        </p>
                      </div>
                    </div>

                    {q.contexts.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-semibold text-gray-500 mb-1">
                          Retrieved Contexts ({q.contexts.length})
                        </p>
                        <div className="space-y-1">
                          {q.contexts.map((ctx, ci) => (
                            <p
                              key={ci}
                              className="text-xs text-gray-600 bg-white p-2 rounded border border-gray-200 line-clamp-2"
                            >
                              [{ci + 1}] {ctx}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {q.source_document && (
                      <p className="text-xs text-gray-400 mt-2">Source: {q.source_document}</p>
                    )}
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  )
}
