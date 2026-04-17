import { useGraphStore } from '../../store/graphStore'

export default function SearchBar() {
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const setSearchQuery = useGraphStore((s) => s.setSearchQuery)

  return (
    <input
      type="text"
      placeholder="Search nodes..."
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      className="w-full px-3 py-2 rounded-xl text-sm bg-white/30 border border-white/20 outline-none focus:border-spring-green"
    />
  )
}
