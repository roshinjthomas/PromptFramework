import type { EvalRun } from '../../types/evaluation'

interface RunSelectorProps {
  runs: EvalRun[]
  selectedRunId: string | null
  onSelect: (runId: string) => void
  onStartNew?: () => void
  isStarting?: boolean
}

export default function RunSelector({
  runs,
  selectedRunId,
  onSelect,
  onStartNew,
  isStarting = false,
}: RunSelectorProps) {
  return (
    <div className="flex items-center gap-3">
      <label htmlFor="run-selector" className="text-sm font-medium text-gray-700 whitespace-nowrap">
        Evaluation Run:
      </label>

      <select
        id="run-selector"
        value={selectedRunId ?? ''}
        onChange={(e) => onSelect(e.target.value)}
        disabled={runs.length === 0}
        className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-1.5
          focus:outline-none focus:ring-2 focus:ring-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed bg-white"
      >
        {runs.length === 0 ? (
          <option value="">No runs available</option>
        ) : (
          runs.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {new Date(run.timestamp).toLocaleString()} —{' '}
              {run.status === 'passed' ? 'PASSED' : 'FAILED'} ({run.question_count} questions)
            </option>
          ))
        )}
      </select>

      {/* Status badge for selected run */}
      {selectedRunId && runs.find((r) => r.run_id === selectedRunId) && (
        <span
          className={
            runs.find((r) => r.run_id === selectedRunId)?.status === 'passed'
              ? 'badge-pass'
              : 'badge-fail'
          }
        >
          {runs.find((r) => r.run_id === selectedRunId)?.status?.toUpperCase()}
        </span>
      )}

      {/* Start new evaluation button */}
      {onStartNew && (
        <button
          onClick={onStartNew}
          disabled={isStarting}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg
            hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
            flex items-center gap-1.5 whitespace-nowrap"
        >
          {isStarting ? (
            <>
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Running…
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 3l14 9-14 9V3z" />
              </svg>
              Run Evaluation
            </>
          )}
        </button>
      )}
    </div>
  )
}
