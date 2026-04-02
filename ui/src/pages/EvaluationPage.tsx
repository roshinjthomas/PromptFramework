import ScoreCard from '../components/evaluation/ScoreCard'
import TrendChart from '../components/evaluation/TrendChart'
import QuestionTable from '../components/evaluation/QuestionTable'
import FailureExplorer from '../components/evaluation/FailureExplorer'
import ConfigPanel from '../components/evaluation/ConfigPanel'
import RunSelector from '../components/evaluation/RunSelector'
import { useEvaluation } from '../hooks/useEvaluation'
import type { MetricName, PerQuestionResult } from '../types/evaluation'

export default function EvaluationPage() {
  const {
    runs,
    selectedRunId,
    selectedRun,
    isLoadingRuns,
    isLoadingRun,
    isStarting,
    startError,
    selectRun,
    triggerEvaluation,
  } = useEvaluation()

  const thresholds = selectedRun
    ? Object.fromEntries(
        Object.entries(selectedRun.metrics).map(([k, v]) => [k, v.threshold])
      )
    : {}

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">

        {/* Page header */}
        <div>
          <h1 className="text-xl font-bold text-gray-900">RAGAS Evaluation Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Monitor Faithfulness, Answer Relevancy, Context Precision, Context Recall, and Answer Correctness.
          </p>
        </div>

        {/* Run Selector */}
        <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm">
          {isLoadingRuns ? (
            <p className="text-sm text-gray-400">Loading runs…</p>
          ) : (
            <RunSelector
              runs={runs}
              selectedRunId={selectedRunId}
              onSelect={selectRun}
              onStartNew={() => triggerEvaluation()}
              isStarting={isStarting}
            />
          )}
          {startError && (
            <p className="text-xs text-red-600 mt-2">{startError}</p>
          )}
        </div>

        {isLoadingRun ? (
          <div className="text-center py-16 text-gray-400 text-sm">Loading evaluation results…</div>
        ) : !selectedRun ? (
          <div className="text-center py-16 text-gray-400 text-sm">
            {runs.length === 0
              ? 'No evaluation runs yet. Click "Run Evaluation" to get started.'
              : 'Select an evaluation run above.'}
          </div>
        ) : (
          <>
            {/* Section 1 — Scorecard */}
            <section>
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Summary Scorecard
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {Object.entries(selectedRun.metrics).map(([metricName, metricScore]) => (
                  <ScoreCard
                    key={metricName}
                    metricName={metricName as MetricName}
                    metricScore={metricScore}
                  />
                ))}
              </div>
            </section>

            {/* Section 2 — Trend Chart */}
            <section>
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Score Trends
              </h2>
              <TrendChart runs={runs} />
            </section>

            {/* Section 3 — Failure Explorer */}
            <section>
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Failure Explorer
              </h2>
              <FailureExplorer
                questions={selectedRun.per_question as PerQuestionResult[]}
                metrics={selectedRun.metrics}
              />
            </section>

            {/* Section 4 — Per-Question Drill-Down */}
            <section>
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Per-Question Drill-Down
                <span className="ml-2 text-gray-400 font-normal normal-case text-xs">
                  Click a row to expand
                </span>
              </h2>
              <QuestionTable
                questions={selectedRun.per_question as PerQuestionResult[]}
                thresholds={thresholds}
              />
            </section>

            {/* Section 5 — Config Panel */}
            <section>
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
                Configuration (this run)
              </h2>
              <ConfigPanel config={selectedRun.config_snapshot} />
            </section>

            {/* Run metadata footer */}
            <div className="text-xs text-gray-400 pb-2">
              Run ID: {selectedRun.run_id} · {selectedRun.question_count} questions ·{' '}
              {selectedRun.duration_s}s · {new Date(selectedRun.timestamp).toLocaleString()}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
