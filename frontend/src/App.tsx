import { useEffect, useMemo, useState } from 'react'
import Header from './components/layout/Header'
import Sidebar from './components/layout/Sidebar'
import MainContent from './components/layout/MainContent'
import AiChatPanel from './components/ai/AiChatPanel'
import PetalAnimation from './components/ui/PetalAnimation'
import ShortcutsHelpModal from './components/ui/ShortcutsHelpModal'
import { useWebSocket } from './components/hooks/useWebSocket'
import { useKeyboardShortcuts } from './components/hooks/useKeyboardShortcuts'
import { useChatStore } from './store/chatStore'
import { getAiStatus } from './utils/api'

function App() {
  const clientId = useMemo(() => crypto.randomUUID(), [])
  const setClientId = useChatStore((s) => s.setClientId)
  useWebSocket(clientId)
  useKeyboardShortcuts()
  const setAiAvailable = useChatStore((s) => s.setAiAvailable)
  const isOpen = useChatStore((s) => s.isOpen)
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    setClientId(clientId)
  }, [clientId, setClientId])

  useEffect(() => {
    getAiStatus().then(({ available }) => setAiAvailable(available))
  }, [setAiAvailable])

  // ? key to open help modal
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      if (e.key === '?' && !e.ctrlKey && !e.shiftKey) {
        // Shift+/ produces '?'
      }
      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        setShowHelp((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-pink-50 to-yellow-50 font-round relative">
      <PetalAnimation />
      <div className="relative z-10 flex flex-col h-screen">
        <Header />
        <div className="flex-1 flex overflow-hidden">
          <Sidebar />
          <MainContent />
          {isOpen && <AiChatPanel />}
        </div>
      </div>
      <ShortcutsHelpModal open={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  )
}

export default App
