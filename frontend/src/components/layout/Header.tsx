import GlassCard from '../ui/GlassCard'
import { useChatStore } from '../../store/chatStore'

export default function Header() {
  const aiAvailable = useChatStore((s) => s.aiAvailable)
  const toggleOpen = useChatStore((s) => s.toggleOpen)
  const isOpen = useChatStore((s) => s.isOpen)

  return (
    <header className="glass-card px-6 py-3 m-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-2xl">🌸</span>
        <h1 className="text-xl font-bold text-gray-800 font-round">
          Graph RAG 代码分析系统
        </h1>
      </div>
      <div className="flex items-center gap-3">
        {aiAvailable && (
          <button
            onClick={toggleOpen}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isOpen
                ? 'bg-spring-pink text-white'
                : 'bg-spring-green/50 text-gray-700 hover:bg-spring-green/70'
            }`}
          >
            {isOpen ? 'Close AI' : '💬 AI Assistant'}
          </button>
        )}
        <div className="flex items-center gap-1">
          <div
            className={`w-2 h-2 rounded-full ${
              aiAvailable ? 'bg-green-400' : 'bg-gray-300'
            }`}
          />
          <span className="text-xs text-gray-500">
            AI {aiAvailable ? 'Ready' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  )
}
