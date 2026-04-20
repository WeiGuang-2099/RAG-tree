import { useState, useCallback, useRef } from 'react'
import { uploadFiles } from '../../utils/api'
import { useGraphStore } from '../../store/graphStore'
import { useChatStore } from '../../store/chatStore'
import { useProjectStore } from '../../store/projectStore'
import GlassCard from './GlassCard'
import ProgressBar from './ProgressBar'

const ACCEPTED_EXTENSIONS = ['.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.java', '.vue']

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const setIsLoading = useGraphStore((s) => s.setIsLoading)
  const setErrorMessage = useGraphStore((s) => s.setErrorMessage)
  const clientId = useChatStore((s) => s.clientId)
  const setCurrentProjectId = useChatStore((s) => s.setCurrentProjectId)
  const currentProjectId = useProjectStore((s) => s.currentProjectId)
  const selectProject = useProjectStore((s) => s.selectProject)
  const fetchProjects = useProjectStore((s) => s.fetchProjects)
  const wsErrorMessage = useGraphStore((s) => s.errorMessage)

  const displayError = wsErrorMessage || error

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files)
      const validFiles = fileArray.filter((f) => {
        const ext = '.' + f.name.split('.').pop()?.toLowerCase()
        return ACCEPTED_EXTENSIONS.includes(ext)
      })

      if (validFiles.length === 0) {
        setError('No supported files found. Supported: .py .js .ts .tsx .jsx .go .java .vue')
        return
      }

      setUploading(true)
      setError(null)
      setErrorMessage(null)
      setIsLoading(true)

      try {
        const result = await uploadFiles(
          validFiles,
          clientId || undefined,
          currentProjectId || undefined,
        )
        setCurrentProjectId(result.project_id)
        await selectProject(result.project_id)
        await fetchProjects()
        // Keep isLoading=true for background processing.
        // selectProject sets it false after fetching the (still empty) graph,
        // but the backend is still parsing — the WebSocket will clear it on complete.
        setIsLoading(true)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Upload failed'
        setError(msg)
        setErrorMessage(msg)
        setIsLoading(false)
      } finally {
        setUploading(false)
      }
    },
    [setIsLoading, setErrorMessage, clientId, currentProjectId, setCurrentProjectId, selectProject, fetchProjects],
  )

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      handleFiles(e.dataTransfer.files)
    },
    [handleFiles],
  )

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback(() => setIsDragging(false), [])

  return (
    <GlassCard className="p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        {currentProjectId ? 'Add Files to Project' : 'Upload Code Files'}
      </h3>
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
          isDragging
            ? 'border-spring-green bg-spring-green/10'
            : 'border-gray-300 hover:border-spring-pink'
        }`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(',')}
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        <p className="text-sm text-gray-500">
          {uploading ? 'Uploading...' : 'Drag & drop code files here, or click to select'}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          .py .js .ts .tsx .jsx .go .java .vue
        </p>
      </div>
      {displayError && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-xs text-red-600">{displayError}</p>
        </div>
      )}
      <ProgressBar />
    </GlassCard>
  )
}
