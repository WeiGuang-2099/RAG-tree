import { create } from 'zustand'
import type { GraphData, GraphNode } from '../types'

interface Progress {
  current: number
  total: number
  detail: string
}

interface GraphStore {
  graphData: GraphData
  selectedNode: GraphNode | null
  viewLevel: 'module' | 'function' | 'class'
  searchQuery: string
  filterFilePath: string
  isLoading: boolean
  progress: Progress
  errorMessage: string | null

  // Internal cache fields
  _cachedFilteredGraph: GraphData | null
  _cacheKey: string | null

  setGraphData: (data: GraphData) => void
  updateGraphData: (incremental: GraphData) => void
  setSelectedNode: (node: GraphNode | null) => void
  setViewLevel: (level: 'module' | 'function' | 'class') => void
  setSearchQuery: (query: string) => void
  setFilterFilePath: (path: string) => void
  setIsLoading: (loading: boolean) => void
  setProgress: (progress: Progress) => void
  setErrorMessage: (message: string | null) => void
  getFilteredGraph: () => GraphData
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  graphData: { nodes: [], edges: [] },
  selectedNode: null,
  viewLevel: 'module',
  searchQuery: '',
  filterFilePath: '',
  isLoading: false,
  progress: { current: 0, total: 0, detail: '' },
  errorMessage: null,

  // Internal cache fields
  _cachedFilteredGraph: null,
  _cacheKey: null,

  setGraphData: (data) => set({ graphData: data }),
  updateGraphData: (incremental) =>
    set((state) => ({
      graphData: {
        nodes: [...state.graphData.nodes, ...incremental.nodes],
        edges: [...state.graphData.edges, ...incremental.edges],
      },
    })),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setViewLevel: (level) => set({ viewLevel: level }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilterFilePath: (path) => set({ filterFilePath: path }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setProgress: (progress) => set({ progress }),
  setErrorMessage: (message) => set({ errorMessage: message }),

  getFilteredGraph: () => {
    const { graphData, searchQuery, filterFilePath, _cachedFilteredGraph, _cacheKey } = get()

    // Compute cache key from inputs
    const nodeCount = graphData.nodes.length
    const edgeCount = graphData.edges.length
    const cacheKey = `${nodeCount}:${edgeCount}:${searchQuery}:${filterFilePath}`

    // Return cached result if cache key matches
    if (_cacheKey === cacheKey && _cachedFilteredGraph) {
      return _cachedFilteredGraph
    }

    let nodes = graphData.nodes
    let edges = graphData.edges

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
      // Filter edges to only include those where BOTH source AND target are in the matched node set
      const filteredEdges = edges.filter(
        (e) => matchedIds.has(e.source) && matchedIds.has(e.target),
      )
      const result = {
        nodes: nodes.map((n) => ({
          ...n,
          highlighted: matchedIds.has(n.id),
        })),
        edges: filteredEdges,
      }
      set({ _cachedFilteredGraph: result, _cacheKey: cacheKey })
      return result
    }

    const result = { nodes, edges }
    set({ _cachedFilteredGraph: result, _cacheKey: cacheKey })
    return result
  },
}))
