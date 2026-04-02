/**
 * TypeScript types for chat messages, citations, and API responses.
 */

export interface Citation {
  id: number
  source_file: string
  page_number: number
  section_header: string
  label: string
  score: number
  text_excerpt: string
}

export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  id: string
  role: MessageRole
  content: string
  citations?: Citation[]
  used_fallback?: boolean
  timestamp: Date
  isStreaming?: boolean
}

export interface ChatRequest {
  query: string
  session_id?: string
  company_name?: string
  top_k?: number
  score_threshold?: number
  stream?: boolean
}

export interface ChatResponse {
  response: string
  citations: Citation[]
  used_fallback: boolean
  session_id?: string
  generation_time_s: number
  model_id: string
}

export interface FeedbackRequest {
  session_id?: string
  query: string
  response: string
  rating: 'thumbs_up' | 'thumbs_down'
  comment?: string
  citations?: Citation[]
}

export interface FeedbackResponse {
  feedback_id: string
  message: string
}

export interface SSEChunkEvent {
  type: 'chunk'
  data: string
}

export interface SSESourcesEvent {
  type: 'sources'
  data: {
    citations: Citation[]
    used_fallback: boolean
  }
}

export interface SSEDoneEvent {
  type: 'done'
  data: {
    session_id: string
  }
}

export interface SSEErrorEvent {
  type: 'error'
  data: {
    error: string
  }
}

export type SSEEvent = SSEChunkEvent | SSESourcesEvent | SSEDoneEvent | SSEErrorEvent
