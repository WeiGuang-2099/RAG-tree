import { useState, useEffect } from 'react'
import { useProjectStore } from '../../store/projectStore'
import GlassCard from './GlassCard'

export default function ProjectSelector() {
  const projects = useProjectStore((s) => s.projects)
  const currentProjectId = useProjectStore((s) => s.currentProjectId)
  const fetchProjects = useProjectStore((s) => s.fetchProjects)
  const selectProject = useProjectStore((s) => s.selectProject)
  const createNewProject = useProjectStore((s) => s.createNewProject)
  const removeProject = useProjectStore((s) => s.removeProject)
  const [newName, setNewName] = useState('')
  const [showNew, setShowNew] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleCreate = async () => {
    if (!newName.trim()) return
    const project = await createNewProject(newName.trim())
    if (project) {
      await selectProject(project.id)
    }
    setNewName('')
    setShowNew(false)
  }

  const handleDelete = async (id: number) => {
    await removeProject(id)
  }

  return (
    <GlassCard className="p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">Projects</h3>
        <button
          onClick={() => setShowNew(!showNew)}
          className="text-xs px-2 py-1 rounded-lg bg-spring-green/30 hover:bg-spring-green/50 text-green-700 transition-colors"
        >
          + New
        </button>
      </div>

      {showNew && (
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            placeholder="Project name..."
            className="flex-1 text-xs px-2 py-1.5 rounded-lg border border-gray-200 focus:border-spring-green focus:outline-none bg-white/60"
            autoFocus
          />
          <button
            onClick={handleCreate}
            className="text-xs px-2 py-1 rounded-lg bg-spring-green text-white hover:bg-green-500 transition-colors"
          >
            Create
          </button>
        </div>
      )}

      <div className="space-y-1 max-h-48 overflow-y-auto">
        {projects.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-2">
            No projects yet
          </p>
        )}
        {projects.map((p) => (
          <div
            key={p.id}
            className={`group flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
              currentProjectId === p.id
                ? 'bg-spring-green/20 border border-spring-green/40'
                : 'hover:bg-gray-100'
            }`}
            onClick={() => selectProject(p.id)}
          >
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">
                {p.name}
              </p>
              <p className="text-[10px] text-gray-400">
                {p.node_count} nodes · {p.edge_count} edges
              </p>
            </div>
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                p.status === 'completed'
                  ? 'bg-green-100 text-green-600'
                  : p.status === 'processing'
                  ? 'bg-yellow-100 text-yellow-600'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {p.status}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDelete(p.id)
              }}
              className="opacity-0 group-hover:opacity-100 text-xs text-red-400 hover:text-red-600 transition-all"
              title="Delete project"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </GlassCard>
  )
}
