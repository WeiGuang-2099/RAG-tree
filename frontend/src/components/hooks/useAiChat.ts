import { useCallback } from 'react'
import { useChatStore } from '../../store/chatStore'
import { sendAiChat, getArchitecture } from '../../utils/api'

export function useAiChat() {
  const addMessage = useChatStore((s) => s.addMessage)
  const setIsStreaming = useChatStore((s) => s.setIsStreaming)
  const currentProjectId = useChatStore((s) => s.currentProjectId)
  const aiAvailable = useChatStore((s) => s.aiAvailable)

  const sendMessage = useCallback(
    async (text: string, contextNodeId?: string) => {
      if (!currentProjectId || !aiAvailable) return

      addMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: Date.now(),
        context_node_id: contextNodeId,
      })

      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      })

      setIsStreaming(true)
      try {
        const messages = useChatStore.getState().messages
        const history = messages
          .slice(-6)
          .map((m) => ({ role: m.role, content: m.content }))
        const result = await sendAiChat(currentProjectId, text, contextNodeId, history)
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: result.response,
          timestamp: Date.now(),
        })
      } catch {
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Sorry, an error occurred while processing your request.',
          timestamp: Date.now(),
        })
      } finally {
        setIsStreaming(false)
      }
    },
    [currentProjectId, aiAvailable, addMessage, setIsStreaming],
  )

  const requestExplain = useCallback(
    async (nodeId: string) => {
      await sendMessage(`Please explain this code node.`, nodeId)
    },
    [sendMessage],
  )

  const requestArchitecture = useCallback(async () => {
    if (!currentProjectId || !aiAvailable) return

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: 'Please analyze the project architecture.',
      timestamp: Date.now(),
    })

    setIsStreaming(true)
    try {
      const result = await getArchitecture(currentProjectId)
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.architecture,
        timestamp: Date.now(),
      })
    } catch {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Architecture analysis failed.',
        timestamp: Date.now(),
      })
    } finally {
      setIsStreaming(false)
    }
  }, [currentProjectId, aiAvailable, addMessage, setIsStreaming])

  const clearChat = useCallback(() => {
    useChatStore.getState().clearMessages()
  }, [])

  return { sendMessage, requestExplain, requestArchitecture, clearChat }
}
