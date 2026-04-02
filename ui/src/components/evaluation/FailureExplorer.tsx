import type { MetricScore, PerQuestionResult } from '../../types/evaluation'
import { METRIC_LABELS } from '../../types/evaluation'

interface FailureExplorerProps {
  questions: PerQuestionResult[]
  metrics: Record<string, MetricScore>
}

type FailureType = 'hallucination' | 'retrieval' | 'relevancy' | 'correctness'

const FAILURE_MAP: Record<string, FailureType> = {
  faithfulness: 'hallucination',
  context_precision: 'retrieval',
  context_recall: 'retrieval',
  answer_relevancy: 'relevancy',
  answer_correctness: 'correctness',
}

const FAILURE_LABELS: Record<FailureType, { label: string; description: string; color: string }> = {
  hallucination: {
    label: 'Hallucination Risk',
    description: 'Low Faithfulness — response not grounded in retrieved context.',
    color: 'border-l-red-500 bg-red-50',
  },
  retrieval: {
    label: 'Poor Retrieval',
    description: 'Low Context Precision or Recall — retrieved chunks may be irrelevant or incomplete.',
    color: 'border-l-amber-500 bg-amber-50',
  },
  relevancy: {
    label: 'Misunderstood Query',
    description: 'Low Answer Relevancy — the SLM did not address the question.',
    color: 'border-l-orange-500 bg-orange-50',
  },
  correctness: {
    label: 'Incorrect Answer',
    description: 'Low Answer Correctness — the answer diverges from ground truth.',
    color: 'border-l-purple-500 bg-purple-50',
  },
}

interface FailedQuestion {
  question: PerQuestionResult
  failures: Array<{ metric: string; score: number; failureType: FailureType }>
}

function getScore(q: PerQuestionResult, metric: string): number | undefined {
  if (q.scores && metric in q.scores) return q.scores[metric]
  return (q as Record<string, unknown>)[metric] as number | undefined
}

export default function FailureExplorer({ questions, metrics }: FailureExplorerProps) {
  const failedQuestions: FailedQuestion[] = questions
    .map((q) => {
      const failures = Object.entries(metrics)
        .filter(([_metric, result]) => !result.passed)
        .map(([metric, result]) => {
          const qScore = getScore(q, metric)
          return { metric, score: qScore ?? 0, threshold: result.threshold, failureType: FAILURE_MAP[metric] ?? 'correctness' }
        })
        .filter(({ score, threshold }) => score < threshold)

      return { question: q, failures }
    })
    .filter((item) => item.failures.length > 0)

  if (failedQuestions.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
        <p className="text-green-700 font-semibold text-sm">All questions passed!</p>
        <p className="text-green-600 text-xs mt-1">No failures detected in this evaluation run.</p>
      </div>
    )
  }

  // Group by failure type
  const groups: Record<FailureType, FailedQuestion[]> = {
    hallucination: [],
    retrieval: [],
    relevancy: [],
    correctness: [],
  }

  for (const item of failedQuestions) {
    const types = new Set(item.failures.map((f) => f.failureType))
    for (const t of types) {
      groups[t].push(item)
    }
  }

  return (
    <div className="space-y-4">
      {(Object.entries(groups) as [FailureType, FailedQuestion[]][]).map(([type, items]) => {
        if (items.length === 0) return null
        const meta = FAILURE_LABELS[type]

        return (
          <div key={type} className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <div className={`border-l-4 ${meta.color} px-4 py-3`}>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-gray-800">{meta.label}</h4>
                  <p className="text-xs text-gray-500 mt-0.5">{meta.description}</p>
                </div>
                <span className="badge-fail">{items.length} question{items.length !== 1 ? 's' : ''}</span>
              </div>
            </div>

            <div className="divide-y divide-gray-100">
              {items.map((item, idx) => (
                <div key={idx} className="px-4 py-3">
                  <p className="text-xs font-medium text-gray-700 mb-1">{item.question.question}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {item.failures.map((f) => (
                      <span key={f.metric} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                        {METRIC_LABELS[f.metric] ?? f.metric}: <strong>{f.score.toFixed(2)}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
