const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`

export function createWsUrl(clientId: string): string {
  return `${WS_BASE}/ws/${clientId}`
}
