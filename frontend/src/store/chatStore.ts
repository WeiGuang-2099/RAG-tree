import { create } from 'zustand'
import type { ChatMessage } from '../types'

interface ChatStore {
  messages: ChatMessage[]
  isOpen: boolean
  isStreaming: boolean
  aiAvailable: boolean
  currentProjectId: number | null
  clientId: string

  addMessage: (message: ChatMessage) => void
  updateLastMessage: (content: string) => void
  clearMessages: () => void
  toggleOpen: () => void
  setIsStreaming: (streaming: boolean) => void
  setAiAvailable: (available: boolean) => void
  setCurrentProjectId: (id: number | null) => void
  setClientId: (id: string) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isOpen: false,
  isStreaming: false,
  aiAvailable: false,
  currentProjectId: null,
  clientId: '',

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  updateLastMessage: (content) =>
    set((state) => {
      const msgs = [...state.messages]
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant') {
        msgs[msgs.length - 1] = {
          ...msgs[msgs.length - 1],
          content: msgs[msgs.length - 1].content + content,
        }
      }
      return { messages: msgs }
    }),
  clearMessages: () => set({ messages: [] }),
  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setAiAvailable: (available) => set({ aiAvailable: available }),
  setCurrentProjectId: (id) => set({ currentProjectId: id }),
  setClientId: (id) => set({ clientId: id }),
}))
