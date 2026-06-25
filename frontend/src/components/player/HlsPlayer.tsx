import Hls from 'hls.js'
import { useEffect, useRef } from 'react'
import type { Zone } from '../../api/types'

interface Props {
  src: string
  zones: Zone[]
  showOverlay: boolean
}

const ZONE_COLORS = ['#ff4d4f', '#52c41a', '#1677ff', '#faad14', '#722ed1']

export default function HlsPlayer({ src, zones, showOverlay }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const token = localStorage.getItem('token')

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        xhrSetup: (xhr) => {
          if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        },
      })
      hlsRef.current = hls
      hls.loadSource(src)
      hls.attachMedia(video)
      hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}))
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.play().catch(() => {})
    }

    return () => {
      hlsRef.current?.destroy()
      hlsRef.current = null
    }
  }, [src])

  useEffect(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!canvas || !video) return

    const draw = () => {
      canvas.width = video.videoWidth || video.clientWidth
      canvas.height = video.videoHeight || video.clientHeight
      const ctx = canvas.getContext('2d')!
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (showOverlay && zones.length > 0) {
        zones.forEach((zone, i) => {
          const polygon: number[][] = JSON.parse(zone.polygon_json)
          const color = ZONE_COLORS[i % ZONE_COLORS.length]
          ctx.beginPath()
          polygon.forEach(([x, y], idx) => {
            const px = x * canvas.width
            const py = y * canvas.height
            idx === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py)
          })
          ctx.closePath()
          ctx.fillStyle = color + '33'
          ctx.fill()
          ctx.strokeStyle = color
          ctx.lineWidth = 2
          ctx.stroke()

          // Label
          if (polygon.length > 0) {
            ctx.fillStyle = color
            ctx.font = '14px sans-serif'
            ctx.fillText(zone.name, polygon[0][0] * canvas.width + 4, polygon[0][1] * canvas.height - 4)
          }
        })
      }

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(rafRef.current)
  }, [zones, showOverlay])

  return (
    <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
      <video
        ref={videoRef}
        style={{ width: '100%', display: 'block' }}
        muted
        playsInline
      />
      <canvas
        ref={canvasRef}
        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
      />
    </div>
  )
}
