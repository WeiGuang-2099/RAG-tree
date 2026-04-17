import { useEffect, useRef, useCallback } from 'react'
import { createWsUrl } from '../../utils/ws'
import { useGraphStore } from '../../store/graphStore'
import { useChatStore } from '../../store/chatStore'
import type { WsMessage } from '../../types'

const MAX_RETRIES = 10
const BASE_DELAY = 1000
const MAX_DELAY = 30000

export function useWebSocket(clientId: string) {
  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)
  const connectingRef = useRef(false)
  const updateGraphData = useGraphStore((s) => s.updateGraphData)
  const setProgress = useGraphStore((s) => s.setProgress)
  const setIsLoading = useGraphStore((s) => s.setIsLoading)
  const setErrorMessage = useGraphStore((s) => s.setErrorMessage)
  const updateLastMessage = useChatStore((s) => s.updateLastMessage)
  const setIsStreaming = useChatStore((s) => s.setIsStreaming)
  const connectedRef = useRef(false)

  const clearRetryTimer = useCallback(() => {
    if (retryTimerRef.current !== null) {
      clearTimeout(retryTimerRef.current)
      retryTimerRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return
    if (connectingRef.current) return

    if (retryCountRef.current >= MAX_RETRIES) {
      setErrorMessage(`WebSocket: failed to connect after ${MAX_RETRIES} retries. Is the backend running?`)
      return
    }

    connectingRef.current = true
    const url = createWsUrl(clientId)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      connectedRef.current = true
      connectingRef.current = false
      retryCountRef.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        switch (msg.type) {
          case 'progress':
            setProgress(msg.data as { current: number; total: number; detail: string })
            break
          case 'graph_update':
            updateGraphData(msg.data as { nodes: never[]; edges: never[] })
            break
          case 'complete':
            setIsLoading(false)
            setErrorMessage(null)
            import('../../store/projectStore').then(({ useProjectStore }) => {
              useProjectStore.getState().fetchProjects()
            })
            break
          case 'error':
            setIsLoading(false)
            setErrorMessage((msg.data as { message?: string }).message || 'Unknown error from server')
            break
          case 'ai_stream':
            updateLastMessage((msg.data as { chunk: string }).chunk)
            break
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = (event) => {
      connectedRef.current = false
      connectingRef.current = false
      wsRef.current = null
      if (!mountedRef.current) return

      if (event.code !== 1000 && event.reason) {
        setErrorMessage(`WebSocket closed: ${event.reason}`)
      }

      retryCountRef.current += 1
      if (retryCountRef.current <= MAX_RETRIES) {
        const delay = Math.min(BASE_DELAY * Math.pow(2, retryCountRef.current - 1), MAX_DELAY)
        retryTimerRef.current = setTimeout(() => {
          if (mountedRef.current) connect()
        }, delay)
      }
    }

    ws.onerror = () => {
      connectingRef.current = false
      ws.close()
    }
  }, [clientId, updateGraphData, setProgress, setIsLoading, setErrorMessage, updateLastMessage, setIsStreaming])

  useEffect(() => {
    mountedRef.current = true
    retryCountRef.current = 0
    connectingRef.current = false
    connect()
    return () => {
      mountedRef.current = false
      connectingRef.current = false
      clearRetryTimer()
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.onerror = null
        wsRef.current.close(1000, 'Component unmounting')
        wsRef.current = null
      }
      connectedRef.current = false
    }
  }, [connect])

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const disconnect = useCallback(() => {
    clearRetryTimer()
    retryCountRef.current = MAX_RETRIES + 1
    wsRef.current?.close(1000, 'User disconnect')
    wsRef.current = null
    connectedRef.current = false
  }, [])

  return {
    isConnected: connectedRef.current,
    send,
    disconnect,
  }
}
