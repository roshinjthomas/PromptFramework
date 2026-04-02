import ChatWindow from '../components/chat/ChatWindow'
import ChatInput from '../components/chat/ChatInput'
import SourcePanel from '../components/chat/SourcePanel'
import { useChat } from '../hooks/useChat'

export default function ChatPage() {
  const { messages, isLoading, currentCitations, sendMessage, stopGeneration, clearChat, error } = useChat()

  return (
    <div className="flex h-full">
      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-gray-800">Customer Support</h1>
            <p className="text-xs text-gray-400">Powered by RAG + Claude Haiku</p>
          </div>
          <button
            onClick={clearChat}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100 transition-colors"
          >
            New chat
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
            {error}
          </div>
        )}

        {/* Messages */}
        <ChatWindow messages={messages} isLoading={isLoading} />

        {/* Input */}
        <ChatInput onSend={sendMessage} onStop={stopGeneration} isLoading={isLoading} />
      </div>

      {/* Sources sidebar */}
      <SourcePanel citations={currentCitations} />
    </div>
  )
}
