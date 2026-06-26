import { Button, Input, message, Space } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { createZone } from '../../api/zones'
import type { Zone } from '../../api/types'

interface Props {
  sourceId: number
  zones: Zone[]
  onZoneCreated: (zone: Zone) => void
}

const COLORS = ['#ff4d4f', '#52c41a', '#1677ff', '#faad14', '#722ed1']

export default function ZoneCanvas({ sourceId, zones, onZoneCreated }: Props) {
  const { t } = useTranslation()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [drawing, setDrawing] = useState(false)
  const [points, setPoints] = useState<[number, number][]>([])
  const [zoneName, setZoneName] = useState('')
  const [canvasSize, setCanvasSize] = useState({ w: 640, h: 360 })
  const [bgImage, setBgImage] = useState<HTMLImageElement | null>(null)
  const [snapshotLoading, setSnapshotLoading] = useState(false)

  useEffect(() => {
    const obs = new ResizeObserver((entries) => {
      const w = entries[0].contentRect.width
      if (w > 0) setCanvasSize({ w, h: Math.round(w * 9 / 16) })
    })
    if (containerRef.current) obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  const loadSnapshot = () => {
    const token = localStorage.getItem('token')
    setSnapshotLoading(true)
    fetch(`/api/v1/stream/${sourceId}/snapshot?t=${Date.now()}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => (r.ok ? r.blob() : null))
      .then((blob) => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        const img = new Image()
        img.onload = () => setBgImage(img)
        img.src = url
      })
      .catch(() => {})
      .finally(() => setSnapshotLoading(false))
  }

  useEffect(() => { loadSnapshot() }, [sourceId])

  useEffect(() => {
    redraw()
  }, [zones, points, canvasSize, bgImage, t])

  const redraw = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (bgImage) {
      ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height)
    } else {
      ctx.fillStyle = '#222'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = '#555'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(t('canvas.start_hint'), canvas.width / 2, canvas.height / 2)
      ctx.textAlign = 'left'
    }

    zones.forEach((zone, i) => {
      const poly: number[][] = JSON.parse(zone.polygon_json)
      const color = COLORS[i % COLORS.length]
      ctx.beginPath()
      poly.forEach(([x, y], idx) => {
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
      ctx.fillStyle = color
      ctx.font = '14px sans-serif'
      if (poly.length > 0) {
        ctx.fillText(zone.name, poly[0][0] * canvas.width + 4, poly[0][1] * canvas.height - 4)
      }
    })

    if (points.length > 0) {
      ctx.beginPath()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 3])
      points.forEach(([x, y], idx) => {
        idx === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      })
      ctx.stroke()
      ctx.setLineDash([])
      points.forEach(([x, y]) => {
        ctx.beginPath()
        ctx.arc(x, y, 5, 0, Math.PI * 2)
        ctx.fillStyle = '#fff'
        ctx.fill()
      })
    }
  }

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing) return
    const rect = canvasRef.current!.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    setPoints((prev) => [...prev, [x, y]])
  }

  const handleDblClick = () => {
    if (points.length >= 4) handleSave()
  }

  const handleSave = async () => {
    if (points.length < 4) {
      message.warning(t('canvas.min_points'))
      return
    }
    if (!zoneName.trim()) {
      message.warning(t('canvas.name_required'))
      return
    }
    const canvas = canvasRef.current!
    const normalized = points.map(([x, y]) => [
      parseFloat((x / canvas.width).toFixed(4)),
      parseFloat((y / canvas.height).toFixed(4)),
    ])
    try {
      const res = await createZone({ source_id: sourceId, name: zoneName, polygon: normalized })
      onZoneCreated(res.data)
      setPoints([])
      setDrawing(false)
      setZoneName('')
      message.success(t('canvas.saved'))
    } catch {
      message.error(t('canvas.save_failed'))
    }
  }

  const handleCancel = () => {
    setPoints([])
    setDrawing(false)
  }

  return (
    <div>
      <Space style={{ marginBottom: 8 }}>
        {!drawing ? (
          <>
            <Button type="primary" onClick={() => setDrawing(true)}>{t('canvas.draw_zone')}</Button>
            <Button onClick={loadSnapshot} loading={snapshotLoading}>{t('canvas.refresh')}</Button>
          </>
        ) : (
          <>
            <Input
              placeholder={t('canvas.zone_name_placeholder')}
              value={zoneName}
              onChange={(e) => setZoneName(e.target.value)}
              style={{ width: 160 }}
            />
            <Button onClick={handleSave} disabled={points.length < 4}>
              {t('canvas.save_points', { n: points.length })}
            </Button>
            <Button onClick={handleCancel}>{t('canvas.cancel')}</Button>
            <span style={{ color: '#888', fontSize: 12 }}>{t('canvas.draw_hint')}</span>
          </>
        )}
      </Space>
      <div ref={containerRef} style={{ lineHeight: 0, width: '100%', minHeight: 360 }}>
        <canvas
          ref={canvasRef}
          width={canvasSize.w}
          height={canvasSize.h}
          style={{ width: '100%', cursor: drawing ? 'crosshair' : 'default', display: 'block' }}
          onClick={handleClick}
          onDoubleClick={handleDblClick}
        />
      </div>
    </div>
  )
}
