/**
 * useEvaluation hook — fetches RAGAS results using react-query.
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchEvaluationRuns,
  fetchEvaluationRun,
  startEvaluation,
} from '../api/evaluation'
import type { EvalRun, RAGASResult, StartEvalRequest } from '../types/evaluation'

export interface UseEvaluationReturn {
  runs: EvalRun[]
  selectedRunId: string | null
  selectedRun: RAGASResult | undefined
  isLoadingRuns: boolean
  isLoadingRun: boolean
  isStarting: boolean
  startError: string | null
  selectRun: (runId: string) => void
  triggerEvaluation: (request?: StartEvalRequest) => void
}

export function useEvaluation(): UseEvaluationReturn {
  const queryClient = useQueryClient()
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [startError, setStartError] = useState<string | null>(null)

  // Fetch list of all runs
  const runsQuery = useQuery({
    queryKey: ['evaluation', 'runs'],
    queryFn: fetchEvaluationRuns,
    refetchInterval: 10_000, // Poll every 10s to pick up new completed runs
  })

  // Auto-select the most recent run when the list loads
  const runs = runsQuery.data ?? []
  const effectiveRunId = selectedRunId ?? runs[0]?.run_id ?? null

  // Fetch the selected run's full details
  const runDetailQuery = useQuery({
    queryKey: ['evaluation', 'run', effectiveRunId],
    queryFn: () => fetchEvaluationRun(effectiveRunId!),
    enabled: !!effectiveRunId,
    staleTime: 60_000,
  })

  // Start evaluation mutation
  const startMutation = useMutation({
    mutationFn: startEvaluation,
    onSuccess: (data) => {
      setStartError(null)
      // Optimistically add the new run to the list
      queryClient.invalidateQueries({ queryKey: ['evaluation', 'runs'] })
      setSelectedRunId(data.run_id)
    },
    onError: (err: Error) => {
      setStartError(err.message)
    },
  })

  return {
    runs,
    selectedRunId: effectiveRunId,
    selectedRun: runDetailQuery.data,
    isLoadingRuns: runsQuery.isLoading,
    isLoadingRun: runDetailQuery.isLoading,
    isStarting: startMutation.isPending,
    startError,
    selectRun: setSelectedRunId,
    triggerEvaluation: (request = {}) => startMutation.mutate(request),
  }
}
