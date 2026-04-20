import { useEffect, useState } from 'react'
import { getDashboard } from '../../utils/api'
import { useGraphStore } from '../../store/graphStore'
import type { DashboardData } from '../../types'

interface Props {
  projectId: number
}

export default function ProjectDashboard({ projectId }: Props) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)
  const setFocusNodeId = useGraphStore((s) => s.setFocusNodeId)
  const graphData = useGraphStore((s) => s.graphData)

  useEffect(() => {
    setLoading(true)
    getDashboard(projectId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [projectId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400 text-sm">Loading dashboard...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-400 text-sm">{error || 'Failed to load dashboard'}</div>
      </div>
    )
  }

  const handleHubClick = (hubId: string) => {
    const node = graphData.nodes.find((n) => n.id === hubId)
    if (node) {
      setSelectedNode(node)
      setFocusNodeId(node.id)
    }
  }

  const metrics = [
    { label: 'Nodes', value: data.node_count, color: 'bg-spring-green/30' },
    { label: 'Edges', value: data.edge_count, color: 'bg-blue-100/50' },
    { label: 'Cycles', value: data.cycle_count, color: data.cycle_count > 0 ? 'bg-red-100/60' : 'bg-green-100/50' },
    { label: 'Avg Degree', value: data.avg_degree.toFixed(2), color: 'bg-purple-100/50' },
    { label: 'Density', value: data.density.toFixed(4), color: 'bg-yellow-100/50' },
  ]

  const langEntries = Object.entries(data.language_distribution).sort((a, b) => b[1] - a[1])
  const maxLangCount = langEntries.length > 0 ? langEntries[0][1] : 1

  return (
    <div className="p-4 space-y-4 overflow-y-auto h-full">
      {/* Metric cards */}
      <div className="grid grid-cols-5 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className={`${m.color} rounded-xl px-3 py-2 text-center`}>
            <div className="text-xs text-gray-500">{m.label}</div>
            <div className="text-lg font-bold text-gray-800">{m.value}</div>
          </div>
        ))}
      </div>

      {/* Language distribution */}
      {langEntries.length > 0 && (
        <div className="glass-card p-3 rounded-xl">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Language Distribution</h3>
          <div className="space-y-1.5">
            {langEntries.map(([ext, count]) => (
              <div key={ext} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-12 text-right">{ext}</span>
                <div className="flex-1 h-4 bg-white/30 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-spring-green to-blue-300 rounded-full transition-all"
                    style={{ width: `${(count / maxLangCount) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-600 w-8">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top hubs */}
      {data.top_hubs.length > 0 && (
        <div className="glass-card p-3 rounded-xl">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Top Hubs</h3>
          <div className="space-y-1">
            {data.top_hubs.map((hub, i) => (
              <button
                key={hub.id}
                onClick={() => handleHubClick(hub.id)}
                className="w-full flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-white/40 transition-colors text-left cursor-pointer"
              >
                <span className="text-xs text-gray-400 w-5">{i + 1}.</span>
                <span className="text-xs font-mono text-gray-700 flex-1">{hub.name}</span>
                <span className="text-xs text-gray-500">{hub.type}</span>
                <span className="text-xs text-blue-500">{hub.centrality.toFixed(3)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
