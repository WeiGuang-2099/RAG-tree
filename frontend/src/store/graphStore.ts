import { create } from 'zustand'
import type { GraphData, GraphNode } from '../types'
import { getCycles } from '../utils/api'

interface Progress {
  current: number
  total: number
  detail: string
}

interface GraphStore {
  graphData: GraphData
  selectedNode: GraphNode | null
  viewLevel: 'all' | 'module' | 'function' | 'class'
  searchQuery: string
  filterFilePath: string
  isLoading: boolean
  progress: Progress
  errorMessage: string | null
  showCycles: boolean
  cycleEdgeSet: Set<string>

  setGraphData: (data: GraphData) => void
  updateGraphData: (incremental: GraphData) => void
  setSelectedNode: (node: GraphNode | null) => void
  setViewLevel: (level: 'all' | 'module' | 'function' | 'class') => void
  setSearchQuery: (query: string) => void
  setFilterFilePath: (path: string) => void
  setIsLoading: (loading: boolean) => void
  setProgress: (progress: Progress) => void
  setErrorMessage: (message: string | null) => void
  getFilteredGraph: () => GraphData
  toggleShowCycles: () => void
  fetchCycles: (projectId: number) => Promise<void>
  focusNodeId: string | null
  setFocusNodeId: (id: string | null) => void
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  graphData: { nodes: [], edges: [] },
  selectedNode: null,
  viewLevel: 'all',
  searchQuery: '',
  filterFilePath: '',
  isLoading: false,
  progress: { current: 0, total: 0, detail: '' },
  errorMessage: null,
  showCycles: false,
  cycleEdgeSet: new Set(),
  focusNodeId: null,

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
    const { graphData, viewLevel, searchQuery, filterFilePath } = get()

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
      return {
        nodes: nodes.map((n) => ({
          ...n,
          highlighted: matchedIds.has(n.id),
        })),
        edges: filteredEdges,
      }
    }

    return { nodes, edges }
  },

  toggleShowCycles: () => {
    const { showCycles } = get()
    set({ showCycles: !showCycles, cycleEdgeSet: !showCycles ? get().cycleEdgeSet : new Set() })
  },

  fetchCycles: async (projectId: number) => {
    try {
      const data = await getCycles(projectId)
      const edgeSet = new Set<string>()
      const { graphData } = get()
      for (const cycle of data.cycles) {
        for (let i = 0; i < cycle.length; i++) {
          const src = cycle[i]
          const tgt = cycle[(i + 1) % cycle.length]
          // Find matching edge
          const edge = graphData.edges.find(
            (e) => e.source === src && e.target === tgt
          )
          if (edge) {
            edgeSet.add(`${edge.source}->${edge.target}`)
          }
        }
      }
      set({ cycleEdgeSet: edgeSet })
    } catch {
      set({ cycleEdgeSet: new Set() })
    }
  },

  setFocusNodeId: (id) => set({ focusNodeId: id }),
}))
