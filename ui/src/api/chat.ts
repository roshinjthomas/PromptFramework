/**
 * Chat API — POST /api/chat with SSE streaming support.
 */

import type { ChatRequest, ChatResponse, Citation, FeedbackRequest, FeedbackResponse } from '../types/chat'

const BASE_URL = '/api'

// ---------------------------------------------------------------------------
// Non-streaming chat
// ---------------------------------------------------------------------------

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...request, stream: false }),
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Chat request failed (${response.status}): ${err}`)
  }

  return response.json()
}

// ---------------------------------------------------------------------------
// SSE streaming chat
// ---------------------------------------------------------------------------

export interface StreamCallbacks {
  onChunk: (token: string) => void
  onSources: (citations: Citation[], usedFallback: boolean) => void
  onDone: (sessionId: string) => void
  onError: (error: string) => void
}

export function streamChatMessage(request: ChatRequest, callbacks: StreamCallbacks): () => void {
  const controller = new AbortController()

  ;(async () => {
    try {
      const response = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify({ ...request, stream: true }),
        signal: controller.signal,
      })

      if (!response.ok) {
        const err = await response.text()
        callbacks.onError(`Server error (${response.status}): ${err}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        callbacks.onError('No response body from server.')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim()
            try {
              const data = JSON.parse(dataStr)
              if (eventType === 'chunk') {
                callbacks.onChunk(data as string)
              } else if (eventType === 'sources') {
                callbacks.onSources(data.citations, data.used_fallback)
              } else if (eventType === 'done') {
                callbacks.onDone(data.session_id)
              } else if (eventType === 'error') {
                callbacks.onError(data.error)
              }
            } catch {
              // Ignore malformed JSON
            }
            eventType = ''
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        callbacks.onError(String(err))
      }
    }
  })()

  // Return a cancel function
  return () => controller.abort()
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export async function submitFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
  const response = await fetch(`${BASE_URL}/chat/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Feedback submission failed (${response.status})`)
  }

  return response.json()
}
