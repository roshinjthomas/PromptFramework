import MetricBar from './MetricBar'
import type { MetricScore } from '../../types/evaluation'
import { METRIC_DESCRIPTIONS, METRIC_LABELS } from '../../types/evaluation'

interface ScoreCardProps {
  metricName: string
  metricScore: MetricScore
}

function StatusBadge({ passed, score, threshold }: { passed: boolean; score: number; threshold: number }) {
  if (passed) {
    return <span className="badge-pass">PASS</span>
  }
  // Warn if within 10% of threshold
  if (score >= threshold * 0.9) {
    return <span className="badge-warn">WARN</span>
  }
  return <span className="badge-fail">FAIL</span>
}

export default function ScoreCard({ metricName, metricScore }: ScoreCardProps) {
  const { score, threshold, passed } = metricScore
  const label = METRIC_LABELS[metricName] ?? metricName
  const description = METRIC_DESCRIPTIONS[metricName] ?? ''

  return (
    <div
      className={`bg-white rounded-xl border p-4 shadow-sm flex flex-col gap-3 ${
        !passed ? 'border-red-200' : 'border-gray-200'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">{label}</h3>
          {description && (
            <p className="text-xs text-gray-400 mt-0.5 leading-tight">{description}</p>
          )}
        </div>
        <StatusBadge passed={passed} score={score} threshold={threshold} />
      </div>

      <div className="flex items-center gap-3">
        <span className="text-2xl font-bold text-gray-900 tabular-nums">
          {score.toFixed(2)}
        </span>
        <div className="flex-1">
          <MetricBar score={score} threshold={threshold} />
          <div className="flex justify-between text-xs text-gray-400 mt-0.5">
            <span>0</span>
            <span>Threshold: {threshold.toFixed(2)}</span>
            <span>1</span>
          </div>
        </div>
      </div>
    </div>
  )
}
