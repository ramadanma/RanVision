import { Button, Input, message, Space } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { createZone } from '../../api/zones'
import type { Zone } from '../../api/types'

interface Props {
  sourceId: number
  zones: Zone[]
  onZoneCreated: (zone: Zone) => void
}

const COLORS = ['#ff4d4f', '#52c41a', '#1677ff', '#faad14', '#722ed1']

export default function ZoneCanvas({ sourceId, zones, onZoneCreated }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [drawing, setDrawing] = useState(false)
  const [points, setPoints] = useState<[number, number][]>([])
  const [zoneName, setZoneName] = useState('')
  const [canvasSize, setCanvasSize] = useState({ w: 640, h: 360 })

  useEffect(() => {
    const obs = new ResizeObserver((entries) => {
      const entry = entries[0]
      setCanvasSize({ w: entry.contentRect.width, h: entry.contentRect.height })
    })
    if (containerRef.current) obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    redraw()
  }, [zones, points, canvasSize])

  const redraw = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw saved zones
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

    // Draw in-progress polygon
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
      message.warning('至少需要 4 个点')
      return
    }
    if (!zoneName.trim()) {
      message.warning('请输入区域名称')
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
      message.success('区域已保存')
    } catch {
      message.error('保存失败')
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
          <Button type="primary" onClick={() => setDrawing(true)}>绘制新区域</Button>
        ) : (
          <>
            <Input
              placeholder="区域名称"
              value={zoneName}
              onChange={(e) => setZoneName(e.target.value)}
              style={{ width: 160 }}
            />
            <Button onClick={handleSave} disabled={points.length < 4}>保存（{points.length} 点）</Button>
            <Button onClick={handleCancel}>取消</Button>
            <span style={{ color: '#888', fontSize: 12 }}>点击添加顶点，双击完成（至少 4 点）</span>
          </>
        )}
      </Space>
      <div ref={containerRef} style={{ background: '#222', lineHeight: 0 }}>
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
