import { useEffect, useRef, useState } from 'react'
import type { Zone } from '../../api/types'

interface Props {
  sourceId: number
  zones: Zone[]
  showOverlay: boolean
}

const ZONE_COLORS = ['#ff4d4f', '#52c41a', '#1677ff', '#faad14', '#722ed1']

export default function HlsPlayer({ sourceId, zones, showOverlay }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const [status, setStatus] = useState<'connecting' | 'live' | 'error'>('connecting')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    // In dev, Vite proxy only handles HTTP. WebSocket needs to go directly to the backend.
    const host = window.location.hostname
    const wsUrl = `${protocol}://${host}:8000/api/v1/stream/${sourceId}/ws?token=${token}`

    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'blob'
    wsRef.current = ws

    ws.onopen = () => setStatus('live')
    ws.onerror = () => setStatus('error')
    ws.onclose = () => setStatus('error')

    ws.onmessage = (e: MessageEvent<Blob>) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')!
      const url = URL.createObjectURL(e.data)
      const img = new Image()
      img.onload = () => {
        // Resize canvas to match first frame
        if (canvas.width !== img.naturalWidth) canvas.width = img.naturalWidth
        if (canvas.height !== img.naturalHeight) canvas.height = img.naturalHeight
        ctx.drawImage(img, 0, 0)
        drawZones(ctx, canvas.width, canvas.height)
        URL.revokeObjectURL(url)
      }
      img.src = url
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [sourceId])

  const drawZones = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    if (!showOverlay || zones.length === 0) return
    zones.forEach((zone, i) => {
      const polygon: number[][] = JSON.parse(zone.polygon_json)
      const color = ZONE_COLORS[i % ZONE_COLORS.length]
      ctx.beginPath()
      polygon.forEach(([x, y], idx) => {
        idx === 0 ? ctx.moveTo(x * w, y * h) : ctx.lineTo(x * w, y * h)
      })
      ctx.closePath()
      ctx.fillStyle = color + '33'
      ctx.fill()
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.stroke()
      if (polygon.length > 0) {
        ctx.fillStyle = color
        ctx.font = '14px sans-serif'
        ctx.fillText(zone.name, polygon[0][0] * w + 4, polygon[0][1] * h - 4)
      }
    })
  }

  return (
    <div style={{ position: 'relative', width: '100%', background: '#111' }}>
      {status !== 'live' && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          color: status === 'error' ? '#ff4d4f' : '#888', fontSize: 14,
        }}>
          {status === 'connecting' ? '连接中…' : '连接失败，请检查视频源是否已启动'}
        </div>
      )}
      <canvas
        ref={canvasRef}
        style={{ width: '100%', display: 'block' }}
      />
    </div>
  )
}
