import { useAiChat } from '../hooks/useAiChat'
import { useChatStore } from '../../store/chatStore'

export default function ArchitectureButton() {
  const { requestArchitecture } = useAiChat()
  const isStreaming = useChatStore((s) => s.isStreaming)

  return (
    <button
      onClick={requestArchitecture}
      disabled={isStreaming}
      className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded-lg hover:bg-white/30 disabled:opacity-50 flex items-center gap-1"
    >
      🏗️ Architecture
    </button>
  )
}
