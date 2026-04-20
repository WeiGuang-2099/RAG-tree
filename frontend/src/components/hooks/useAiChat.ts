import { useCallback } from 'react'
import { useChatStore } from '../../store/chatStore'
import { sendAiChat, streamAiChat, getArchitecture } from '../../utils/api'

export function useAiChat() {
  const addMessage = useChatStore((s) => s.addMessage)
  const setIsStreaming = useChatStore((s) => s.setIsStreaming)
  const currentProjectId = useChatStore((s) => s.currentProjectId)
  const aiAvailable = useChatStore((s) => s.aiAvailable)

  const sendMessage = useCallback(
    async (text: string, contextNodeId?: string) => {
      if (!currentProjectId || !aiAvailable) return

      // Capture history before adding the new user message
      const history = useChatStore.getState().messages
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }))

      addMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: Date.now(),
        context_node_id: contextNodeId,
      })

      setIsStreaming(true)

      // Create placeholder assistant message for streaming
      const assistantId = crypto.randomUUID()
      let fullContent = ''
      let referencedNodeIds: number[] = []

      try {
        await streamAiChat(
          currentProjectId,
          text,
          (chunk) => {
            fullContent += chunk
            // Update the message by replacing all messages
            const msgs = useChatStore.getState().messages
            const idx = msgs.findIndex((m) => m.id === assistantId)
            if (idx >= 0) {
              // Message already exists, update via replace
              const updated = [...msgs]
              updated[idx] = { ...updated[idx], content: fullContent }
              useChatStore.setState({ messages: updated })
            } else {
              // First chunk - add the message
              addMessage({
                id: assistantId,
                role: 'assistant',
                content: fullContent,
                timestamp: Date.now(),
              })
            }
          },
          (ids) => {
            referencedNodeIds = ids
          },
          contextNodeId,
          history,
        )

        // Final update with referenced_node_ids
        const msgs = useChatStore.getState().messages
        const idx = msgs.findIndex((m) => m.id === assistantId)
        if (idx >= 0) {
          const updated = [...msgs]
          updated[idx] = { ...updated[idx], referenced_node_ids: referencedNodeIds }
          useChatStore.setState({ messages: updated })
        }
      } catch {
        // Fallback to non-streaming
        try {
          const result = await sendAiChat(currentProjectId, text, contextNodeId, history)
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: result.response,
            timestamp: Date.now(),
            referenced_node_ids: result.referenced_node_ids,
          })
        } catch {
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'Sorry, an error occurred while processing your request.',
            timestamp: Date.now(),
          })
        }
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
