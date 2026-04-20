import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { ChatMessage } from '../../types'
import { useGraphStore } from '../../store/graphStore'

interface Props {
  message: ChatMessage
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const graphData = useGraphStore((s) => s.graphData)
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)
  const setFocusNodeId = useGraphStore((s) => s.setFocusNodeId)

  const handleNodeClick = (nodeId: number) => {
    const node = graphData.nodes.find((n) => n.id === String(nodeId))
    if (node) {
      setSelectedNode(node)
      setFocusNodeId(node.id)
    }
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] px-3 py-2 rounded-2xl text-sm ${
          isUser
            ? 'bg-spring-green/40 text-gray-800'
            : 'bg-white/40 text-gray-800'
        }`}
      >
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <ReactMarkdown
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                const inline = !match
                return !inline ? (
                  <SyntaxHighlighter
                    style={oneLight}
                    language={match[1]}
                    PreTag="div"
                    className="!text-xs !rounded-lg !my-1"
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="bg-white/50 px-1 rounded text-xs" {...props}>
                    {children}
                  </code>
                )
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
        {!isUser && message.referenced_node_ids && message.referenced_node_ids.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2 pt-1 border-t border-gray-200/50">
            {message.referenced_node_ids.map((nid) => {
              const node = graphData.nodes.find((n) => n.id === String(nid))
              return (
                <button
                  key={nid}
                  onClick={() => handleNodeClick(nid)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-100/60 hover:bg-blue-200/80 text-blue-700 transition-colors cursor-pointer"
                >
                  <span className="font-medium">{node ? node.type : 'Node'}</span>
                  <span>{node ? node.name : nid}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
