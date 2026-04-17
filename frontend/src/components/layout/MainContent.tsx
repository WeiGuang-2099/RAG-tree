import ForceGraph from '../graph/ForceGraph'
import NodeDetailPanel from '../graph/NodeDetailPanel'
import GraphControls from '../graph/GraphControls'
import { useGraphStore } from '../../store/graphStore'

export default function MainContent() {
  const selectedNode = useGraphStore((s) => s.selectedNode)
  const graphData = useGraphStore((s) => s.graphData)

  return (
    <div className="flex-1 flex flex-col p-4 gap-4 min-w-0">
      <GraphControls />
      <div className="flex-1 glass-card relative overflow-hidden">
        {graphData.nodes.length > 0 ? (
          <ForceGraph />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-4xl mb-2">🍃</p>
              <p className="text-lg">Upload code files to start analysis</p>
            </div>
          </div>
        )}
      </div>
      {selectedNode && <NodeDetailPanel />}
    </div>
  )
}
