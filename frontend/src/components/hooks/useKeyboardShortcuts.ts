import { useEffect, useCallback, useState } from 'react'
import { useGraphStore } from '../../store/graphStore'
import { useChatStore } from '../../store/chatStore'

export function useKeyboardShortcuts() {
  const setViewLevel = useGraphStore((s) => s.setViewLevel)
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)
  const toggleOpen = useChatStore((s) => s.toggleOpen)
  const isOpen = useChatStore((s) => s.isOpen)
  const [showHelp, setShowHelp] = useState(false)

  const toggleHelp = useCallback(() => setShowHelp((prev) => !prev), [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Skip when focus is in input/textarea/contenteditable
      const tag = (e.target as HTMLElement).tagName
      const isEditable =
        tag === 'INPUT' ||
        tag === 'TEXTAREA' ||
        (e.target as HTMLElement).isContentEditable
      if (isEditable) return

      // Ctrl+K: Focus search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault()
        const input = document.querySelector<HTMLInputElement>(
          'input[placeholder="Search nodes..."]',
        )
        if (input) input.focus()
        return
      }

      // Ctrl+1/2/3/4: Switch view level
      if (e.ctrlKey && e.key === '1') {
        e.preventDefault()
        setViewLevel('all')
        return
      }
      if (e.ctrlKey && e.key === '2') {
        e.preventDefault()
        setViewLevel('module')
        return
      }
      if (e.ctrlKey && e.key === '3') {
        e.preventDefault()
        setViewLevel('class')
        return
      }
      if (e.ctrlKey && e.key === '4') {
        e.preventDefault()
        setViewLevel('function')
        return
      }

      // Ctrl+Shift+A: Toggle AI panel
      if (e.ctrlKey && e.shiftKey && (e.key === 'a' || e.key === 'A')) {
        e.preventDefault()
        toggleOpen()
        return
      }

      // Escape: Deselect node or close panel
      if (e.key === 'Escape') {
        setSelectedNode(null)
        if (isOpen) toggleOpen()
        if (showHelp) toggleHelp()
        return
      }

      // F: Fit graph to viewport
      if (e.key === 'f' && !e.ctrlKey && !e.shiftKey) {
        e.preventDefault()
        window.dispatchEvent(new CustomEvent('graph:fit'))
        return
      }

      // ?: Toggle shortcuts help modal
      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault()
        toggleHelp()
        return
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [setViewLevel, setSelectedNode, toggleOpen, isOpen, showHelp, toggleHelp])

  return { showHelp, closeHelp: useCallback(() => setShowHelp(false), []) }
}
