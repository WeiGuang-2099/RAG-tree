export interface GraphNode {
  id: string
  name: string
  type: 'Module' | 'Class' | 'Function' | 'Variable'
  file_path: string
  start_line: number
  end_line: number
  source_code: string
}

export interface GraphEdge {
  source: string
  target: string
  type: 'imports' | 'calls' | 'inherits' | 'uses_data' | 'instantiates'
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface WsMessage {
  type: 'progress' | 'graph_update' | 'complete' | 'error' | 'ai_stream' | 'ping'
  data: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  context_node_id?: string
  referenced_node_ids?: number[]
}

export interface UploadResponse {
  task_id: string
  project_id: number
  file_count: number
  files: string[]
  status: string
}

export interface ProjectInfo {
  id: number
  name: string
  status: string
  created_at: string
  file_count: number
  node_count: number
  edge_count: number
}

export interface DashboardData {
  node_count: number
  edge_count: number
  cycle_count: number
  avg_degree: number
  density: number
  language_distribution: Record<string, number>
  top_hubs: Array<{
    id: string
    name: string
    type: string
    centrality: number
  }>
}

export interface CycleData {
  cycles: string[][]
  count: number
}
