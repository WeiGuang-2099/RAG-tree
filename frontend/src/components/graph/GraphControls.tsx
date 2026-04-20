import { useGraphStore } from '../../store/graphStore'
import { useChatStore } from '../../store/chatStore'

const LEVELS = ['all', 'module', 'class', 'function'] as const

const LEVEL_LABELS: Record<string, string> = {
  all: 'All',
  module: 'Module',
  class: 'Class',
  function: 'Function',
}

export default function GraphControls() {
  const viewLevel = useGraphStore((s) => s.viewLevel)
  const setViewLevel = useGraphStore((s) => s.setViewLevel)
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const setSearchQuery = useGraphStore((s) => s.setSearchQuery)
  const filterFilePath = useGraphStore((s) => s.filterFilePath)
  const setFilterFilePath = useGraphStore((s) => s.setFilterFilePath)
  const showCycles = useGraphStore((s) => s.showCycles)
  const toggleShowCycles = useGraphStore((s) => s.toggleShowCycles)
  const fetchCycles = useGraphStore((s) => s.fetchCycles)
  const currentProjectId = useChatStore((s) => s.currentProjectId)

  const handleToggleCycles = () => {
    toggleShowCycles()
    // Fetch cycles when enabling (if we have a project)
    if (!showCycles && currentProjectId) {
      fetchCycles(currentProjectId)
    }
  }

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
            {LEVEL_LABELS[level]}
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

      <button
        onClick={handleToggleCycles}
        className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
          showCycles
            ? 'bg-red-400 text-white'
            : 'bg-white/30 text-gray-600 hover:bg-white/50'
        }`}
      >
        Show Cycles
      </button>
    </div>
  )
}
