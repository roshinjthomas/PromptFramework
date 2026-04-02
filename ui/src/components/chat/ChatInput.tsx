import { useState, useRef, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (query: string) => void
  onStop?: () => void
  isLoading: boolean
  placeholder?: string
}

export default function ChatInput({
  onSend,
  onStop,
  isLoading,
  placeholder = 'Type your question…',
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={isLoading ? 'Generating response…' : placeholder}
          disabled={isLoading}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed
            placeholder:text-gray-400 leading-relaxed max-h-40 overflow-y-auto"
        />

        {isLoading ? (
          /* Stop button — shown while streaming */
          <button
            onClick={onStop}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-red-500 text-white
              flex items-center justify-center
              hover:bg-red-600 active:bg-red-700 transition-colors"
            aria-label="Stop generation"
            title="Stop generation"
          >
            {/* Square stop icon */}
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="5" y="5" width="14" height="14" rx="2" />
            </svg>
          </button>
        ) : (
          /* Send button */
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-blue-600 text-white
              flex items-center justify-center
              hover:bg-blue-700 active:bg-blue-800 transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Send message"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        )}
      </div>

      <p className="text-xs text-gray-400 text-center mt-1.5">
        {isLoading ? 'Click the red button to stop · ' : ''}
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
