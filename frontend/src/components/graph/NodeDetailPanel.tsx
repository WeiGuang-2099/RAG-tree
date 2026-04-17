import GlassCard from '../ui/GlassCard'
import { useGraphStore } from '../../store/graphStore'
import { useAiChat } from '../hooks/useAiChat'
import { useChatStore } from '../../store/chatStore'

export default function NodeDetailPanel() {
  const selectedNode = useGraphStore((s) => s.selectedNode)
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)
  const graphData = useGraphStore((s) => s.graphData)
  const aiAvailable = useChatStore((s) => s.aiAvailable)
  const { requestExplain } = useAiChat()

  if (!selectedNode) return null

  const relatedEdges = graphData.edges.filter(
    (e) => e.source === selectedNode.id || e.target === selectedNode.id,
  )

  return (
    <GlassCard className="absolute bottom-4 right-4 w-96 max-h-96 overflow-auto z-10">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-bold text-gray-800">{selectedNode.name}</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-spring-green/30 text-gray-600">
            {selectedNode.type}
          </span>
        </div>
        <button
          onClick={() => setSelectedNode(null)}
          className="text-gray-400 hover:text-gray-600 text-lg"
        >
          ×
        </button>
      </div>

      <p className="text-xs text-gray-500 mb-2">
        {selectedNode.file_path} : {selectedNode.start_line}-{selectedNode.end_line}
      </p>

      <pre className="text-xs bg-white/40 p-2 rounded-lg overflow-auto max-h-32 mb-2">
        <code>{selectedNode.source_code}</code>
      </pre>

      <div className="text-xs text-gray-600 mb-2">
        <p className="font-semibold mb-1">Relationships ({relatedEdges.length})</p>
        {relatedEdges.slice(0, 10).map((e, i) => (
          <div key={i} className="flex gap-1">
            <span className="text-gray-400">{e.source === selectedNode.id ? '→' : '←'}</span>
            <span>{e.source === selectedNode.id ? e.target : e.source}</span>
            <span className="text-gray-400">({e.type})</span>
          </div>
        ))}
      </div>

      {aiAvailable && (
        <button
          onClick={() => requestExplain(selectedNode.id)}
          className="w-full mt-2 px-3 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-spring-green to-spring-pink text-white hover:opacity-90 transition-opacity"
        >
          ✨ AI Explain
        </button>
      )}
    </GlassCard>
  )
}
