import type { Message } from '../../types/chat'

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold mr-2">
          AI
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? 'order-first' : ''}`}>
        {/* Bubble */}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-sm'
              : 'bg-white text-gray-800 border border-gray-200 rounded-bl-sm shadow-sm'
          }`}
        >
          {message.content || (
            <span className="inline-flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]" />
            </span>
          )}
        </div>

        {/* Citation badges */}
        {!isUser && message.citations && message.citations.length > 0 && !message.isStreaming && (
          <div className="flex flex-wrap gap-1 mt-1.5 ml-1">
            {message.citations.map((citation) => (
              <span
                key={citation.id}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 text-xs rounded-full"
                title={citation.text_excerpt}
              >
                <span className="font-medium">[{citation.id}]</span>
                <span className="truncate max-w-[120px]">{citation.label}</span>
                <span className="text-blue-400">p.{citation.page_number}</span>
              </span>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left ml-1'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-xs font-bold ml-2">
          You
        </div>
      )}
    </div>
  )
}
