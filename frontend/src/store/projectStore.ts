import { create } from 'zustand'
import type { ProjectInfo } from '../types'
import { listProjects, createProject, deleteProject, renameProject } from '../utils/api'
import { getFullGraph } from '../utils/api'
import { useGraphStore } from './graphStore'
import { useChatStore } from './chatStore'

interface ProjectStore {
  projects: ProjectInfo[]
  currentProjectId: number | null
  loading: boolean

  fetchProjects: () => Promise<void>
  selectProject: (id: number | null) => Promise<void>
  createNewProject: (name: string) => Promise<ProjectInfo | null>
  removeProject: (id: number) => Promise<void>
  renameProjectById: (id: number, name: string) => Promise<void>
  getCurrentProject: () => ProjectInfo | undefined
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projects: [],
  currentProjectId: null,
  loading: false,

  fetchProjects: async () => {
    set({ loading: true })
    try {
      const projects = await listProjects()
      set({ projects })
    } catch {
      // ignore
    } finally {
      set({ loading: false })
    }
  },

  selectProject: async (id: number | null) => {
    const graphStore = useGraphStore.getState()
    const chatStore = useChatStore.getState()

    set({ currentProjectId: id })
    graphStore.setGraphData({ nodes: [], edges: [] })
    graphStore.setSelectedNode(null)
    graphStore.setErrorMessage(null)
    chatStore.setCurrentProjectId(id)
    chatStore.clearMessages()

    if (id !== null) {
      graphStore.setIsLoading(true)
      try {
        const graphData = await getFullGraph(id)
        graphStore.setGraphData(graphData)
      } catch {
        graphStore.setErrorMessage('Failed to load graph for this project')
      } finally {
        graphStore.setIsLoading(false)
      }
    }
  },

  createNewProject: async (name: string) => {
    try {
      const project = await createProject(name)
      set((state) => ({
        projects: [project, ...state.projects],
      }))
      return project
    } catch {
      return null
    }
  },

  removeProject: async (id: number) => {
    try {
      await deleteProject(id)
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id),
        currentProjectId: state.currentProjectId === id ? null : state.currentProjectId,
      }))
      if (get().currentProjectId === null) {
        const graphStore = useGraphStore.getState()
        graphStore.setGraphData({ nodes: [], edges: [] })
        graphStore.setSelectedNode(null)
      }
    } catch {
      // ignore
    }
  },

  renameProjectById: async (id: number, name: string) => {
    try {
      await renameProject(id, name)
      set((state) => ({
        projects: state.projects.map((p) =>
          p.id === id ? { ...p, name } : p
        ),
      }))
    } catch {
      // ignore
    }
  },

  getCurrentProject: () => {
    const { projects, currentProjectId } = get()
    return projects.find((p) => p.id === currentProjectId)
  },
}))
