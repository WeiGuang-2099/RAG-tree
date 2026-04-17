export default function PetalAnimation() {
  const petals = Array.from({ length: 18 }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    size: 8 + Math.random() * 16,
    delay: Math.random() * 8,
    duration: 6 + Math.random() * 6,
    opacity: 0.3 + Math.random() * 0.5,
  }))

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {petals.map((p) => (
        <div
          key={p.id}
          className="absolute"
          style={{
            left: p.left,
            top: '-20px',
            width: `${p.size}px`,
            height: `${p.size}px`,
            borderRadius: '50% 0 50% 50%',
            background: `linear-gradient(135deg, #fda4af, #86efac)`,
            opacity: p.opacity,
            animation: `petalFall ${p.duration}s ease-in-out ${p.delay}s infinite`,
          }}
        />
      ))}
    </div>
  )
}
