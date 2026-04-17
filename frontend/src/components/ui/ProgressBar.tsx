import { useGraphStore } from '../../store/graphStore'

export default function ProgressBar() {
  const progress = useGraphStore((s) => s.progress)
  const isLoading = useGraphStore((s) => s.isLoading)

  if (!isLoading || progress.total === 0) return null

  const percent = Math.round((progress.current / progress.total) * 100)

  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{progress.detail || 'Parsing...'}</span>
        <span>{percent}%</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{
            width: `${percent}%`,
            background: 'linear-gradient(90deg, #86efac, #fda4af)',
          }}
        />
      </div>
    </div>
  )
}
