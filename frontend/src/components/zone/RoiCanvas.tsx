import { Button, Space, message } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { updateDetectionRoi } from '../../api/sources'

interface Props {
  sourceId: number
  roiJson: string | null
  onRoiUpdated: (roiJson: string | null) => void
}

export default function RoiCanvas({ sourceId, roiJson, onRoiUpdated }: Props) {
  const { t } = useTranslation()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [drawing, setDrawing] = useState(false)
  const [points, setPoints] = useState<[number, number][]>([])
  const [canvasSize, setCanvasSize] = useState({ w: 640, h: 360 })
  const [bgImage, setBgImage] = useState<HTMLImageElement | null>(null)
  const [snapshotLoading, setSnapshotLoading] = useState(false)
  const [saving, setSaving] = useState(false)

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

  useEffect(() => { redraw() }, [points, canvasSize, bgImage, roiJson, t])

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

    if (roiJson && points.length === 0) {
      try {
        const poly: number[][] = JSON.parse(roiJson)
        ctx.beginPath()
        poly.forEach(([x, y], idx) => {
          idx === 0 ? ctx.moveTo(x * canvas.width, y * canvas.height) : ctx.lineTo(x * canvas.width, y * canvas.height)
        })
        ctx.closePath()
        ctx.fillStyle = 'rgba(255, 165, 0, 0.15)'
        ctx.fill()
        ctx.strokeStyle = '#ffa500'
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.fillStyle = '#ffa500'
        ctx.font = '13px sans-serif'
        ctx.fillText(t('roi.label'), poly[0][0] * canvas.width + 4, poly[0][1] * canvas.height - 4)
      } catch { /* ignore bad JSON */ }
    }

    if (points.length > 0) {
      ctx.beginPath()
      ctx.strokeStyle = '#ffa500'
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
        ctx.fillStyle = '#ffa500'
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
    if (points.length >= 3) handleSave()
  }

  const handleSave = async () => {
    if (points.length < 3) {
      message.warning(t('roi.min_points'))
      return
    }
    const canvas = canvasRef.current!
    const normalized = points.map(([x, y]) => [
      parseFloat((x / canvas.width).toFixed(4)),
      parseFloat((y / canvas.height).toFixed(4)),
    ])
    setSaving(true)
    try {
      const roi_json = JSON.stringify(normalized)
      await updateDetectionRoi(sourceId, roi_json)
      onRoiUpdated(roi_json)
      setPoints([])
      setDrawing(false)
      message.success(t('roi.saved'))
    } catch {
      message.error(t('roi.save_failed'))
    } finally {
      setSaving(false)
    }
  }

  const handleClear = async () => {
    setSaving(true)
    try {
      await updateDetectionRoi(sourceId, null)
      onRoiUpdated(null)
      setPoints([])
      setDrawing(false)
      message.success(t('roi.cleared'))
    } catch {
      message.error(t('roi.clear_failed'))
    } finally {
      setSaving(false)
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
            <Button type="primary" onClick={() => setDrawing(true)}>{t('roi.draw')}</Button>
            {roiJson && (
              <Button danger onClick={handleClear} loading={saving}>{t('roi.clear')}</Button>
            )}
            <Button onClick={loadSnapshot} loading={snapshotLoading}>{t('roi.refresh')}</Button>
          </>
        ) : (
          <>
            <Button type="primary" onClick={handleSave} disabled={points.length < 3} loading={saving}>
              {t('roi.save_points', { n: points.length })}
            </Button>
            <Button onClick={handleCancel}>{t('roi.cancel')}</Button>
            <span style={{ color: '#888', fontSize: 12 }}>{t('roi.draw_hint')}</span>
          </>
        )}
      </Space>
      <div style={{ color: '#888', fontSize: 12, marginBottom: 6 }}>
        {t('roi.hint')}
      </div>
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
