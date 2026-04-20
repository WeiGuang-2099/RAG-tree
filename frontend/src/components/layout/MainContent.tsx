import { useState } from 'react'
import ForceGraph from '../graph/ForceGraph'
import NodeDetailPanel from '../graph/NodeDetailPanel'
import GraphControls from '../graph/GraphControls'
import ProjectDashboard from '../dashboard/ProjectDashboard'
import { useGraphStore } from '../../store/graphStore'
import { useChatStore } from '../../store/chatStore'

export default function MainContent() {
  const selectedNode = useGraphStore((s) => s.selectedNode)
  const graphData = useGraphStore((s) => s.graphData)
  const currentProjectId = useChatStore((s) => s.currentProjectId)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'graph'>('graph')

  const showTabs = currentProjectId !== null && graphData.nodes.length > 0

  return (
    <div className="flex-1 flex flex-col p-4 gap-4 min-w-0">
      {/* Tab bar */}
      {showTabs && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'dashboard'
                ? 'bg-spring-green text-gray-800'
                : 'bg-white/30 text-gray-600 hover:bg-white/50'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'graph'
                ? 'bg-spring-green text-gray-800'
                : 'bg-white/30 text-gray-600 hover:bg-white/50'
            }`}
          >
            Graph
          </button>
          {activeTab === 'graph' && <GraphControls />}
        </div>
      )}

      {!showTabs && <GraphControls />}

      <div className="flex-1 glass-card relative overflow-hidden">
        {activeTab === 'dashboard' && currentProjectId ? (
          <ProjectDashboard projectId={currentProjectId} />
        ) : graphData.nodes.length > 0 ? (
          <ForceGraph />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-lg">Upload code files to start analysis</p>
            </div>
          </div>
        )}
      </div>
      {selectedNode && <NodeDetailPanel />}
    </div>
  )
}
