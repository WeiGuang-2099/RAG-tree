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
    const { graphData, searchQuery, filterFilePath } = get()
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
      return {
        nodes: nodes.map((n) => ({
          ...n,
          highlighted: matchedIds.has(n.id),
        })),
        edges,
      }
    }

    return { nodes, edges }
  },
}))
