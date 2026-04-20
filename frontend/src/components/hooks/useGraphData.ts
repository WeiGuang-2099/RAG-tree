import { useCallback } from 'react'
import { useGraphStore } from '../../store/graphStore'
import { getFullGraph } from '../../utils/api'

export function useGraphData() {
  const setGraphData = useGraphStore((s) => s.setGraphData)
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)
  const setIsLoading = useGraphStore((s) => s.setIsLoading)
  const graphData = useGraphStore((s) => s.graphData)

  const loadGraph = useCallback(
    async (projectId: number) => {
      setIsLoading(true)
      try {
        const data = await getFullGraph(projectId)
        setGraphData(data)
      } catch {
        // error handling
      } finally {
        setIsLoading(false)
      }
    },
    [setGraphData, setIsLoading],
  )

  const selectNode = useCallback(
    (nodeId: string) => {
      const node = graphData.nodes.find((n) => n.id === nodeId) || null
      setSelectedNode(node)
    },
    [graphData.nodes, setSelectedNode],
  )

  const changeViewLevel = useCallback(
    (level: 'module' | 'function' | 'class') => {
      useGraphStore.getState().setViewLevel(level)
    },
    [],
  )

  return { loadGraph, selectNode, changeViewLevel }
}
