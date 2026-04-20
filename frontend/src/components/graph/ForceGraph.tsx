import { useRef, useCallback, useEffect, useMemo } from 'react'
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
  instantiates: '#a78bfa',
}

export default function ForceGraph() {
  const graphData = useGraphStore((s) => s.graphData)
  const viewLevel = useGraphStore((s) => s.viewLevel)
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const filterFilePath = useGraphStore((s) => s.filterFilePath)
  const showCycles = useGraphStore((s) => s.showCycles)
  const cycleEdgeSet = useGraphStore((s) => s.cycleEdgeSet)
  const focusNodeId = useGraphStore((s) => s.focusNodeId)
  const setFocusNodeId = useGraphStore((s) => s.setFocusNodeId)
  const { selectNode } = useGraphData()
  const fgRef = useRef<any>(null)

  // Use store's getFilteredGraph with useMemo for reactivity
  const filteredGraph = useMemo(
    () => useGraphStore.getState().getFilteredGraph(),
    [graphData, viewLevel, searchQuery, filterFilePath],
  )

  const graphDataFormatted = {
    nodes: filteredGraph.nodes.map((n: any) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      file_path: n.file_path,
      val: filteredGraph.edges.filter(
        (e: any) => e.source === n.id || e.target === n.id,
      ).length + 1,
      highlighted: n.highlighted,
    })),
    links: filteredGraph.edges.map((e: any) => ({
      source: e.source,
      target: e.target,
      type: e.type,
      isCycleEdge: showCycles && cycleEdgeSet.has(`${e.source}->${e.target}`),
    })),
  }

  const handleNodeClick = useCallback(
    (node: any) => {
      selectNode(node.id)
    },
    [selectNode],
  )

  // Center camera on focus node (from chat navigation)
  useEffect(() => {
    if (focusNodeId && fgRef.current) {
      const node = graphDataFormatted.nodes.find((n: any) => n.id === focusNodeId)
      if (node && (node as any).x !== undefined) {
        fgRef.current.centerAt((node as any).x, (node as any).y, 600)
        fgRef.current.zoom(2, 600)
      }
      setFocusNodeId(null)
    }
  }, [focusNodeId])

  // Listen for graph:fit custom event (from keyboard shortcut F key)
  useEffect(() => {
    const handler = () => {
      if (fgRef.current) {
        fgRef.current.zoomToFit(400, 40, 600)
      }
    }
    window.addEventListener('graph:fit', handler)
    return () => window.removeEventListener('graph:fit', handler)
  }, [])

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
      linkColor={(link: any) =>
        link.isCycleEdge ? '#ef4444' : EDGE_COLORS[link.type] || '#9ca3af'
      }
      linkWidth={(link: any) => (link.isCycleEdge ? 2.5 : 1)}
      linkDirectionalArrowLength={4}
      linkDirectionalArrowRelPos={1}
      backgroundColor="transparent"
      warmupTicks={50}
    />
  )
}
