import { useEffect, useMemo } from 'react'
import Header from './components/layout/Header'
import Sidebar from './components/layout/Sidebar'
import MainContent from './components/layout/MainContent'
import AiChatPanel from './components/ai/AiChatPanel'
import PetalAnimation from './components/ui/PetalAnimation'
import ShortcutsHelpModal from './components/ui/ShortcutsHelpModal'
import ErrorBoundary from './components/ui/ErrorBoundary'
import { useWebSocket } from './components/hooks/useWebSocket'
import { useKeyboardShortcuts } from './components/hooks/useKeyboardShortcuts'
import { useChatStore } from './store/chatStore'
import { getAiStatus } from './utils/api'

function App() {
  const clientId = useMemo(() => crypto.randomUUID(), [])
  const setClientId = useChatStore((s) => s.setClientId)
  useWebSocket(clientId)
  const { showHelp, closeHelp } = useKeyboardShortcuts()
  const setAiAvailable = useChatStore((s) => s.setAiAvailable)
  const isOpen = useChatStore((s) => s.isOpen)

  useEffect(() => {
    setClientId(clientId)
  }, [clientId, setClientId])

  useEffect(() => {
    getAiStatus().then(({ available }) => setAiAvailable(available))
  }, [setAiAvailable])

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-pink-50 to-yellow-50 font-round relative">
        <PetalAnimation />
        <div className="relative z-10 flex flex-col h-screen">
          <Header />
          <div className="flex-1 flex overflow-hidden">
            <Sidebar />
            <ErrorBoundary fallback={
              <div className="flex-1 flex items-center justify-center text-gray-400">
                Graph visualization error. Try refreshing.
              </div>
            }>
              <MainContent />
            </ErrorBoundary>
            {isOpen && <AiChatPanel />}
          </div>
        </div>
        <ShortcutsHelpModal open={showHelp} onClose={closeHelp} />
      </div>
    </ErrorBoundary>
  )
}

export default App
