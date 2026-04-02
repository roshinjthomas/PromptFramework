/**
 * TypeScript types for RAGAS evaluation results and runs.
 */

export interface MetricScore {
  score: number
  threshold: number
  passed: boolean
}

export type MetricName =
  | 'faithfulness'
  | 'answer_relevancy'
  | 'context_precision'
  | 'context_recall'
  | 'answer_correctness'

export interface RAGConfig {
  chunk_size?: number
  chunk_overlap?: number
  top_k?: number
  score_threshold?: number
  embedding_model?: string
}

export interface SLMConfig {
  model_id?: string
  quantization?: string
  temperature?: number
  max_new_tokens?: number
}

export interface ConfigSnapshot {
  rag?: RAGConfig
  slm?: SLMConfig
}

export interface PerQuestionResult {
  question: string
  answer: string
  ground_truth: string
  contexts: string[]
  source_document?: string
  scores?: Record<string, number>
  // flat fields for backwards compat
  faithfulness?: number
  answer_relevancy?: number
  context_precision?: number
  context_recall?: number
  answer_correctness?: number
}

export interface RAGASResult {
  run_id: string
  timestamp: string
  duration_s: number
  question_count: number
  status: 'passed' | 'failed'
  metrics: Record<MetricName, MetricScore>
  per_question: PerQuestionResult[]
  config_snapshot?: ConfigSnapshot
  fail_on_threshold_breach?: boolean
}

export interface EvalRun {
  run_id: string
  timestamp: string
  status: 'passed' | 'failed' | 'running' | 'queued' | 'failed'
  question_count: number
  duration_s: number
  metrics: Record<string, number>
}

export interface StartEvalRequest {
  dataset_path?: string
  metrics?: string[]
  run_id?: string
}

export interface StartEvalResponse {
  run_id: string
  message: string
}

// Metric display metadata
export const METRIC_LABELS: Record<string, string> = {
  faithfulness: 'Faithfulness',
  answer_relevancy: 'Answer Relevancy',
  context_precision: 'Context Precision',
  context_recall: 'Context Recall',
  answer_correctness: 'Answer Correctness',
}

export const METRIC_DESCRIPTIONS: Record<string, string> = {
  faithfulness: 'Is the answer grounded in the retrieved context? (no hallucination)',
  answer_relevancy: 'Does the answer address what the user actually asked?',
  context_precision: 'Are the retrieved chunks actually relevant to the question?',
  context_recall: 'Did retrieval surface all the chunks needed to answer correctly?',
  answer_correctness: 'Does the answer match the ground truth?',
}
