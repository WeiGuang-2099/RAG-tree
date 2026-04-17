import { useGraphStore } from '../../store/graphStore'

const LEVELS = ['module', 'function', 'class'] as const

export default function GraphControls() {
  const viewLevel = useGraphStore((s) => s.viewLevel)
  const setViewLevel = useGraphStore((s) => s.setViewLevel)
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const setSearchQuery = useGraphStore((s) => s.setSearchQuery)
  const filterFilePath = useGraphStore((s) => s.filterFilePath)
  const setFilterFilePath = useGraphStore((s) => s.setFilterFilePath)

  return (
    <div className="glass-card px-4 py-2 flex items-center gap-4 flex-wrap">
      <div className="flex items-center gap-1">
        <span className="text-xs text-gray-500 mr-1">Level:</span>
        {LEVELS.map((level) => (
          <button
            key={level}
            onClick={() => setViewLevel(level)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              viewLevel === level
                ? 'bg-spring-green text-gray-800'
                : 'bg-white/30 text-gray-600 hover:bg-white/50'
            }`}
          >
            {level}
          </button>
        ))}
      </div>

      <div className="flex-1 flex items-center gap-2 min-w-[200px]">
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 px-3 py-1.5 rounded-lg text-sm bg-white/30 border border-white/20 outline-none focus:border-spring-green transition-colors"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="text"
          placeholder="Filter by file path..."
          value={filterFilePath}
          onChange={(e) => setFilterFilePath(e.target.value)}
          className="w-48 px-3 py-1.5 rounded-lg text-sm bg-white/30 border border-white/20 outline-none focus:border-spring-pink transition-colors"
        />
      </div>
    </div>
  )
}
