interface MetricBarProps {
  score: number       // 0–1
  threshold?: number  // optional threshold marker
  color?: string      // Tailwind color class override
}

export default function MetricBar({ score, threshold, color }: MetricBarProps) {
  const pct = Math.max(0, Math.min(100, score * 100))
  const thresholdPct = threshold != null ? Math.max(0, Math.min(100, threshold * 100)) : null

  const barColor =
    color ??
    (threshold != null
      ? score >= threshold
        ? 'bg-green-500'
        : score >= threshold * 0.9
        ? 'bg-yellow-400'
        : 'bg-red-500'
      : 'bg-blue-500')

  return (
    <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-visible">
      {/* Fill bar */}
      <div
        className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${barColor}`}
        style={{ width: `${pct}%` }}
      />
      {/* Threshold marker */}
      {thresholdPct != null && (
        <div
          className="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-gray-500 rounded"
          style={{ left: `${thresholdPct}%` }}
          title={`Threshold: ${(threshold! * 100).toFixed(0)}%`}
        />
      )}
    </div>
  )
}
