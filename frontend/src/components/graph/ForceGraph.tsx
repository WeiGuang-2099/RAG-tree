import { useRef, useCallback, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useGraphStore } from '../../store/graphStore'
import { useGraphData } from '../hooks/useGraphData'

const NODE_COLORS: Record<string, string> = {
  Module: '#86efac',
  Class: '#fda4af',
  Function: '#fef3c7',
  Variable: '#c4b5fd',
}

const EDGE_COLORS: Record<string, string> = {
  imports: '#9ca3af',
  calls: '#86efac',
  inherits: '#fda4af',
  uses_data: '#fef3c7',
}

export default function ForceGraph() {
  const graphData = useGraphStore((s) => s.getFilteredGraph())
  const { selectNode } = useGraphData()
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const fgRef = useRef<any>(null)

  const graphDataFormatted = {
    nodes: graphData.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      file_path: n.file_path,
      val: graphData.edges.filter(
        (e) => e.source === n.id || e.target === n.id,
      ).length + 1,
      highlighted: (n as any).highlighted,
    })),
    links: graphData.edges.map((e) => ({
      source: e.source,
      target: e.target,
      type: e.type,
    })),
  }

  const handleNodeClick = useCallback(
    (node: any) => {
      selectNode(node.id)
    },
    [selectNode],
  )

  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge')?.strength(-200)
      fgRef.current.d3Force('link')?.distance(80)
    }
  }, [])

  return (
    <ForceGraph2D
      ref={fgRef}
      graphData={graphDataFormatted}
      onNodeClick={handleNodeClick}
      nodeColor={(node: any) =>
        searchQuery && !node.highlighted
          ? '#e5e7eb'
          : NODE_COLORS[node.type] || '#e5e7eb'
      }
      nodeVal={(node: any) => node.val}
      nodeLabel={(node: any) => `${node.name} (${node.type})`}
      nodeCanvasObjectMode={() => 'after'}
      nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
        const label = node.name
        const fontSize = 12 / globalScale
        ctx.font = `${fontSize}px Nunito, sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        ctx.fillStyle = '#374151'
        ctx.fillText(label, node.x, node.y + (node.val || 3) + 2)
      }}
      linkColor={(link: any) => EDGE_COLORS[link.type] || '#9ca3af'}
      linkWidth={1}
      linkDirectionalArrowLength={4}
      linkDirectionalArrowRelPos={1}
      backgroundColor="transparent"
      warmupTicks={50}
    />
  )
}
