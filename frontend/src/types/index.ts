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
  type: 'imports' | 'calls' | 'inherits' | 'uses_data'
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
