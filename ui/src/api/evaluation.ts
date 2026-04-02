/**
 * Evaluation API.
 * GET  /api/evaluation/runs
 * GET  /api/evaluation/runs/:id
 * POST /api/evaluation/start
 */

import type { EvalRun, RAGASResult, StartEvalRequest, StartEvalResponse } from '../types/evaluation'

const BASE_URL = '/api/evaluation'

export async function fetchEvaluationRuns(): Promise<EvalRun[]> {
  const response = await fetch(`${BASE_URL}/runs`)
  if (!response.ok) {
    throw new Error(`Failed to fetch evaluation runs (${response.status})`)
  }
  return response.json()
}

export async function fetchEvaluationRun(runId: string): Promise<RAGASResult> {
  const response = await fetch(`${BASE_URL}/runs/${encodeURIComponent(runId)}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch run '${runId}' (${response.status})`)
  }
  return response.json()
}

export async function startEvaluation(request: StartEvalRequest = {}): Promise<StartEvalResponse> {
  const response = await fetch(`${BASE_URL}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Failed to start evaluation (${response.status}): ${err}`)
  }
  return response.json()
}

export async function fetchRunStatus(runId: string): Promise<{ run_id: string; status: string }> {
  const response = await fetch(`${BASE_URL}/runs/${encodeURIComponent(runId)}/status`)
  if (!response.ok) {
    throw new Error(`Failed to fetch run status (${response.status})`)
  }
  return response.json()
}
