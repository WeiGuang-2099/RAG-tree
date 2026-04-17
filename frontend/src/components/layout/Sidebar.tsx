import ProjectSelector from '../ui/ProjectSelector'
import FileUpload from '../ui/FileUpload'

export default function Sidebar() {
  return (
    <aside className="w-72 shrink-0 p-4 flex flex-col gap-4 overflow-y-auto">
      <ProjectSelector />
      <FileUpload />
    </aside>
  )
}
