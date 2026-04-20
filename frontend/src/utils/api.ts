import type { GraphData, UploadResponse, ProjectInfo, DashboardData, CycleData } from '../types'

const API_BASE = '/api'

export async function uploadFiles(
  files: File[],
  clientId?: string,
  projectId?: number,
): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f))
  if (clientId) formData.append('client_id', clientId)
  if (projectId) formData.append('project_id', String(projectId))
  const res = await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function getFullGraph(projectId: number): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/graph/full/${projectId}`)
  if (!res.ok) throw new Error('Failed to load graph')
  return res.json()
}

export async function getNodeNeighbors(
  projectId: number,
  nodeId: string,
  depth: number = 1,
): Promise<GraphData> {
  const res = await fetch(
    `${API_BASE}/graph/neighbors/${projectId}/${nodeId}?depth=${depth}`,
  )
  if (!res.ok) throw new Error('Failed to load neighbors')
  return res.json()
}

export async function sendAiChat(
  projectId: number,
  message: string,
  contextNodeId?: string,
  history?: Array<{ role: string; content: string }>,
): Promise<{ response: string; referenced_node_ids: number[] }> {
  const res = await fetch(`${API_BASE}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: projectId,
      message,
      context_node_id: contextNodeId ? parseInt(contextNodeId) : null,
      history,
    }),
  })
  if (!res.ok) {
    if (res.status === 503) throw new Error('AI service unavailable')
    throw new Error('AI chat failed')
  }
  return res.json()
}

export async function getArchitecture(
  projectId: number,
): Promise<{ architecture: string }> {
  const res = await fetch(`${API_BASE}/ai/architecture`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId }),
  })
  if (!res.ok) throw new Error('Architecture analysis failed')
  return res.json()
}

export async function getAiStatus(): Promise<{ available: boolean }> {
  const res = await fetch(`${API_BASE}/ai/status`)
  if (!res.ok) return { available: false }
  return res.json()
}

export async function listProjects(): Promise<ProjectInfo[]> {
  const res = await fetch(`${API_BASE}/projects/`)
  if (!res.ok) throw new Error('Failed to list projects')
  return res.json()
}

export async function createProject(name: string): Promise<ProjectInfo> {
  const res = await fetch(`${API_BASE}/projects/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to create project')
  return res.json()
}

export async function getProject(projectId: number): Promise<ProjectInfo> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`)
  if (!res.ok) throw new Error('Failed to get project')
  return res.json()
}

export async function renameProject(
  projectId: number,
  name: string,
): Promise<ProjectInfo> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to rename project')
  return res.json()
}

export async function deleteProject(projectId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Failed to delete project')
}

export async function getCycles(projectId: number): Promise<CycleData> {
  const res = await fetch(`${API_BASE}/graph/cycles/${projectId}`)
  if (!res.ok) throw new Error('Failed to get cycles')
  return res.json()
}

export async function getDashboard(projectId: number): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/dashboard`)
  if (!res.ok) throw new Error('Failed to get dashboard')
  return res.json()
}
