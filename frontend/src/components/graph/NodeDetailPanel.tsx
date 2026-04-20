import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import GlassCard from '../ui/GlassCard'
import { useGraphStore } from '../../store/graphStore'
import { useAiChat } from '../hooks/useAiChat'
import { useChatStore } from '../../store/chatStore'

function getLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() || ''
  const map: Record<string, string> = {
    py: 'python',
    js: 'javascript',
    jsx: 'jsx',
    ts: 'typescript',
    tsx: 'tsx',
    vue: 'markup',
    html: 'markup',
    css: 'css',
    json: 'json',
  }
  return map[ext] || 'text'
}

export default function NodeDetailPanel() {
  const selectedNode = useGraphStore((s) => s.selectedNode)
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)
  const graphData = useGraphStore((s) => s.graphData)
  const aiAvailable = useChatStore((s) => s.aiAvailable)
  const { requestExplain } = useAiChat()
  const [activeTab, setActiveTab] = useState<'details' | 'code'>('details')

  if (!selectedNode) return null

  const relatedEdges = graphData.edges.filter(
    (e) => e.source === selectedNode.id || e.target === selectedNode.id,
  )

  const language = getLanguage(selectedNode.file_path)
  const lineCount = selectedNode.source_code ? selectedNode.source_code.split('\n').length : 0
  const highlightStart = selectedNode.start_line
  const highlightEnd = selectedNode.end_line

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
          x
        </button>
      </div>

      <p className="text-xs text-gray-500 mb-2">
        {selectedNode.file_path} : {selectedNode.start_line}-{selectedNode.end_line}
      </p>

      {/* Tab bar */}
      <div className="flex gap-1 mb-2">
        <button
          onClick={() => setActiveTab('details')}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'details'
              ? 'bg-spring-green text-gray-800'
              : 'bg-white/30 text-gray-600 hover:bg-white/50'
          }`}
        >
          Details
        </button>
        <button
          onClick={() => setActiveTab('code')}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'code'
              ? 'bg-spring-green text-gray-800'
              : 'bg-white/30 text-gray-600 hover:bg-white/50'
          }`}
        >
          Code
        </button>
      </div>

      {activeTab === 'details' ? (
        <>
          <div className="text-xs text-gray-600 mb-2">
            <p className="font-semibold mb-1">Relationships ({relatedEdges.length})</p>
            {relatedEdges.slice(0, 10).map((e, i) => (
              <div key={i} className="flex gap-1">
                <span className="text-gray-400">{e.source === selectedNode.id ? '->' : '<-'}</span>
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
              AI Explain
            </button>
          )}
        </>
      ) : (
        <>
          {selectedNode.source_code ? (
            <div className="relative text-xs rounded-lg overflow-auto max-h-56">
              <SyntaxHighlighter
                language={language}
                style={oneLight}
                showLineNumbers
                startingLineNumber={highlightStart}
                wrapLines
                lineProps={(lineNumber: number) => {
                  const inRange = lineNumber >= highlightStart && lineNumber <= highlightEnd
                  return {
                    style: inRange
                      ? { backgroundColor: 'rgba(250, 204, 21, 0.3)', display: 'block' }
                      : {},
                  }
                }}
                customStyle={{ margin: 0, fontSize: '0.7rem' }}
              >
                {selectedNode.source_code}
              </SyntaxHighlighter>
            </div>
          ) : (
            <div className="text-xs text-gray-400 text-center py-4">
              No source code available
            </div>
          )}
        </>
      )}
    </GlassCard>
  )
}
