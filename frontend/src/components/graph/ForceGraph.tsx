import { useRef, useCallback, useEffect, useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useGraphStore } from '../../store/graphStore'
import { useGraphData } from '../hooks/useGraphData'
import type { GraphNode } from '../../types'

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

  // Compute filtered graph with useMemo (no store mutation during render)
  const filteredGraph = useMemo(() => {
    let nodes = graphData.nodes
    let edges = graphData.edges

    const LEVEL_TYPES: Record<string, string[] | null> = {
      all: null,
      module: ['Module'],
      class: ['Class'],
      function: ['Function'],
    }
    const allowedTypes = LEVEL_TYPES[viewLevel]
    if (allowedTypes) {
      const levelNodeIds = new Set(
        nodes.filter((n) => allowedTypes.includes(n.type)).map((n) => n.id),
      )
      nodes = nodes.filter((n) => levelNodeIds.has(n.id))
      edges = edges.filter(
        (e) => levelNodeIds.has(e.source) && levelNodeIds.has(e.target),
      )
    }

    if (filterFilePath) {
      const nodeIds = new Set(
        nodes.filter((n) => n.file_path.includes(filterFilePath)).map((n) => n.id),
      )
      nodes = nodes.filter((n) => nodeIds.has(n.id))
      edges = edges.filter(
        (e) => nodeIds.has(e.source) && nodeIds.has(e.target),
      )
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      const matchedIds = new Set(
        nodes
          .filter((n) => n.name.toLowerCase().includes(q))
          .map((n) => n.id),
      )
      const filteredEdges = edges.filter(
        (e) => matchedIds.has(e.source) && matchedIds.has(e.target),
      )
      nodes = nodes.map((n) => ({
        ...n,
        highlighted: matchedIds.has(n.id),
      })) as GraphNode[]
      edges = filteredEdges
    }

    return { nodes, edges }
  }, [graphData, viewLevel, searchQuery, filterFilePath])

  const graphDataFormatted = {
    nodes: filteredGraph.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      file_path: n.file_path,
      val: filteredGraph.edges.filter(
        (e) => e.source === n.id || e.target === n.id,
      ).length + 1,
      highlighted: (n as any).highlighted,
    })),
    links: filteredGraph.edges.map((e) => ({
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
