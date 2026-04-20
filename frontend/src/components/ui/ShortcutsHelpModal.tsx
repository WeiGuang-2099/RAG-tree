import { useEffect } from 'react'

interface Props {
  open: boolean
  onClose: () => void
}

const SHORTCUTS = [
  { keys: 'Ctrl+K', description: 'Focus search' },
  { keys: 'Ctrl+1', description: 'Show all nodes' },
  { keys: 'Ctrl+2', description: 'Show modules' },
  { keys: 'Ctrl+3', description: 'Show classes' },
  { keys: 'Ctrl+4', description: 'Show functions' },
  { keys: 'Ctrl+Shift+A', description: 'Toggle AI panel' },
  { keys: 'Escape', description: 'Deselect / close panel' },
  { keys: 'F', description: 'Fit graph to viewport' },
  { keys: '?', description: 'Show this help' },
]

export default function ShortcutsHelpModal({ open, onClose }: Props) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      onClick={onClose}
    >
      <div
        className="glass-card p-6 rounded-2xl w-96 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-bold text-gray-800 mb-4">Keyboard Shortcuts</h2>
        <div className="space-y-2">
          {SHORTCUTS.map((s) => (
            <div key={s.keys} className="flex items-center justify-between">
              <span className="text-sm text-gray-600">{s.description}</span>
              <kbd className="px-2 py-0.5 rounded bg-gray-100 text-xs font-mono text-gray-700 border border-gray-200">
                {s.keys}
              </kbd>
            </div>
          ))}
        </div>
        <button
          onClick={onClose}
          className="mt-4 w-full px-3 py-2 rounded-xl text-sm font-semibold bg-white/40 hover:bg-white/60 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  )
}
