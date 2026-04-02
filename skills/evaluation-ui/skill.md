# Skill: Evaluation UI

## React Component Patterns for RAGAS Score Display

### ScoreCard Pattern
Display each metric as a card with score, progress bar, and status badge.
Key design choices:
- Use `bg-green-100 text-green-800` for PASS, `bg-yellow-100` for WARN, `bg-red-100` for FAIL.
- Show the threshold as a marker on the progress bar for context.
- Animate the bar on load with Tailwind `transition-all duration-500`.

### MetricBar Pattern
A simple reusable progress bar that accepts score (0–1) and threshold:
```tsx
<MetricBar score={0.84} threshold={0.80} />
```
Renders a colored fill with a threshold marker. Color changes based on pass/warn/fail.

### TrendChart with Recharts
Use `<LineChart>` from Recharts for the trend across runs:
- X-axis: run dates (from `run.timestamp`).
- Y-axis: 0–1 domain.
- One `<Line>` per metric with a distinct color.
- Add a `<ReferenceLine>` at y=0.75 as a visual threshold guide.
- Use `<Tooltip>` with custom formatter for clean display.

### QuestionTable with Expandable Rows
- Render a standard HTML table with `<tbody>`.
- Use `useState` to track which row is expanded.
- Expanded row spans all columns and shows answer, ground truth, contexts.
- Use `line-clamp-2` on context excerpts to keep rows compact.

### FailureExplorer Grouping
- Group failed questions by failure type (hallucination, retrieval, relevancy, correctness).
- Each group uses a colored left border (`border-l-4 border-l-red-500`) for visual differentiation.
- Show question text + per-metric scores in the group items.

### react-query Integration
Fetch evaluation data with proper caching:
```tsx
const { data: runs } = useQuery({
  queryKey: ['evaluation', 'runs'],
  queryFn: fetchEvaluationRuns,
  refetchInterval: 10_000,
})
```
Invalidate cache after triggering a new run so the list updates automatically.
