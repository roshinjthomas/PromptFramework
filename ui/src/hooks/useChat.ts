/**
 * useChat hook — manages chat state, SSE streaming, and session tracking.
 */

import { useCallback, useRef, useState } from 'react'
import { streamChatMessage } from '../api/chat'
import type { Citation, Message } from '../types/chat'

// Inline uuid v4 to avoid adding uuid dependency (use crypto.randomUUID in modern browsers)
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
  const cancelStreamRef = useRef<(() => void) | null>(null)

  const sendMessage = useCallback(
    (query: string) => {
      if (!query.trim() || isLoading) return

      // Cancel any active stream
      cancelStreamRef.current?.()

      setError(null)
      setCurrentCitations([])

      // Add user message
      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: query,
        timestamp: new Date(),
      }

      // Add placeholder assistant message (streaming)
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

      const cancel = streamChatMessage(
        {
          query,
          session_id: sessionId.current,
          company_name: companyName,
          stream: true,
        },
        {
          onChunk: (token) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, content: m.content + token } : m,
              ),
            )
          },
          onSources: (citations, usedFallback) => {
            setCurrentCitations(citations)
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, citations, used_fallback: usedFallback } : m,
              ),
            )
          },
          onDone: (newSessionId) => {
            if (newSessionId) sessionId.current = newSessionId
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, isStreaming: false } : m,
              ),
            )
            setIsLoading(false)
          },
          onError: (err) => {
            setError(err)
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content:
                        m.content ||
                        'Sorry, I encountered an error. Please try again.',
                      isStreaming: false,
                    }
                  : m,
              ),
            )
            setIsLoading(false)
          },
        },
      )

      cancelStreamRef.current = cancel
    },
    [isLoading, companyName],
  )

  const clearChat = useCallback(() => {
    cancelStreamRef.current?.()
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
    clearChat,
    error,
  }
}
