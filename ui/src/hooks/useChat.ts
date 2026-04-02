/**
 * useChat hook — non-streaming JSON mode for reliability.
 */

import { useCallback, useRef, useState } from 'react'
import { sendChatMessage } from '../api/chat'
import type { Citation, Message } from '../types/chat'

function generateId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  currentCitations: Citation[]
  sessionId: string
  sendMessage: (query: string) => void
  stopGeneration: () => void
  clearChat: () => void
  error: string | null
}

export function useChat(companyName = 'our company'): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: generateId(),
      role: 'assistant',
      content: 'Hello! How can I help you today? Ask me anything about our products or services.',
      timestamp: new Date(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [currentCitations, setCurrentCitations] = useState<Citation[]>([])
  const [error, setError] = useState<string | null>(null)
  const sessionId = useRef<string>(generateId())
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    (query: string) => {
      if (!query.trim() || isLoading) return

      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      setError(null)
      setCurrentCitations([])

      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: query,
        timestamp: new Date(),
      }
      const assistantMsgId = generateId()
      const assistantMsg: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsLoading(true)

      sendChatMessage(
        { query, session_id: sessionId.current, company_name: companyName, stream: false },
      )
        .then((result) => {
          if (controller.signal.aborted) return
          setCurrentCitations(result.citations ?? [])
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: result.response, citations: result.citations, isStreaming: false }
                : m,
            ),
          )
          if (result.session_id) sessionId.current = result.session_id
        })
        .catch((err) => {
          if (controller.signal.aborted) return
          const msg = err?.message ?? String(err)
          setError(msg)
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: 'Sorry, I encountered an error. Please try again.', isStreaming: false }
                : m,
            ),
          )
        })
        .finally(() => {
          if (!controller.signal.aborted) setIsLoading(false)
        })
    },
    [isLoading, companyName],
  )

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m)),
    )
    setIsLoading(false)
  }, [])

  const clearChat = useCallback(() => {
    abortRef.current?.abort()
    sessionId.current = generateId()
    setMessages([
      {
        id: generateId(),
        role: 'assistant',
        content: 'Hello! How can I help you today? Ask me anything about our products or services.',
        timestamp: new Date(),
      },
    ])
    setCurrentCitations([])
    setIsLoading(false)
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    currentCitations,
    sessionId: sessionId.current,
    sendMessage,
    stopGeneration,
    clearChat,
    error,
  }
}
