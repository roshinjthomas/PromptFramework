import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { EvalRun } from '../../types/evaluation'
import { METRIC_LABELS } from '../../types/evaluation'

interface TrendChartProps {
  runs: EvalRun[]
}

const METRIC_COLORS: Record<string, string> = {
  faithfulness: '#3b82f6',
  answer_relevancy: '#10b981',
  context_precision: '#f59e0b',
  context_recall: '#8b5cf6',
  answer_correctness: '#ef4444',
}

export default function TrendChart({ runs }: TrendChartProps) {
  if (runs.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center text-gray-400 text-sm">
        No evaluation runs to display yet. Run your first evaluation to see trends.
      </div>
    )
  }

  // Prepare chart data — oldest first
  const chartData = [...runs]
    .reverse()
    .map((run) => ({
      name: new Date(run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      run_id: run.run_id,
      ...Object.fromEntries(
        Object.entries(run.metrics).map(([key, score]) => [key, score])
      ),
    }))

  // Determine which metrics are present
  const metricKeys = Object.keys(runs[0]?.metrics ?? {})

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Score Trends Across Runs</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v) => v.toFixed(1)}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              value.toFixed(3),
              METRIC_LABELS[name] ?? name,
            ]}
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              fontSize: '12px',
            }}
          />
          <Legend
            formatter={(value) => METRIC_LABELS[value] ?? value}
            wrapperStyle={{ fontSize: '11px' }}
          />
          {/* Threshold guideline at 0.75 */}
          <ReferenceLine y={0.75} stroke="#d1d5db" strokeDasharray="4 4" label="" />

          {metricKeys.map((key) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={METRIC_COLORS[key] ?? '#9ca3af'}
              strokeWidth={2}
              dot={{ r: 4, strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
