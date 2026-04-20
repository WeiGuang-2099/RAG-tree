import { useState, useRef, useEffect } from 'react'
import { useChatStore } from '../../store/chatStore'
import { useAiChat } from '../hooks/useAiChat'
import GlassCard from '../ui/GlassCard'
import MessageBubble from './MessageBubble'
import ArchitectureButton from './ArchitectureButton'

export default function AiChatPanel() {
  const messages = useChatStore((s) => s.messages)
  const isOpen = useChatStore((s) => s.isOpen)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { sendMessage, clearChat } = useAiChat()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!isOpen) return null

  const handleSend = () => {
    if (!input.trim() || isStreaming) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <aside className="w-96 shrink-0 flex flex-col p-4">
      <GlassCard className="p-4 flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-3 px-1">
          <h3 className="font-bold text-gray-800 text-sm">AI Assistant</h3>
          <div className="flex gap-2">
            <ArchitectureButton />
            <button
              onClick={clearChat}
              className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg hover:bg-white/30"
            >
              Clear
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto px-1 space-y-3 mb-3">
          {messages.length === 0 && (
            <p className="text-xs text-gray-400 text-center mt-8">
              Ask questions about the codebase...
            </p>
          )}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isStreaming && (
            <div className="flex gap-1 px-2">
              <span className="w-2 h-2 rounded-full bg-spring-pink animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-spring-green animate-bounce" style={{ animationDelay: '0.1s' }} />
              <span className="w-2 h-2 rounded-full bg-spring-yellow animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-2 px-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            disabled={isStreaming}
            className="flex-1 px-3 py-2 rounded-xl text-sm bg-white/30 border border-white/20 outline-none focus:border-spring-green disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-spring-green to-spring-pink text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            Send
          </button>
        </div>
      </GlassCard>
    </aside>
  )
}
