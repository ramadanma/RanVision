import { ArrowLeftOutlined } from '@ant-design/icons'
import { Button, Col, Row, Spin, Switch, Tabs, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getSource, toggleFaceCheckFront, toggleFaceRecognition, toggleOverlay, toggleSkeleton } from '../api/sources'
import { listZones } from '../api/zones'
import HlsPlayer from '../components/player/HlsPlayer'
import RoiCanvas from '../components/zone/RoiCanvas'
import ZoneCanvas from '../components/zone/ZoneCanvas'
import ZoneList from '../components/zone/ZoneList'
import ReportConfigPanel from './ReportConfigPanel'
import type { Source, Zone } from '../api/types'

const { Title } = Typography

export default function SourceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const sourceId = Number(id)
  const navigate = useNavigate()

  const [source, setSource] = useState<Source | null>(null)
  const [zones, setZones] = useState<Zone[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getSource(sourceId),
      listZones(sourceId),
    ])
      .then(([sRes, zRes]) => {
        setSource(sRes.data)
        setZones(zRes.data)
      })
      .finally(() => setLoading(false))
  }, [sourceId])

  const handleToggleOverlay = async () => {
    const res = await toggleOverlay(sourceId)
    setSource(res.data)
  }

  const handleToggleFaceRecognition = async () => {
    const res = await toggleFaceRecognition(sourceId)
    setSource(res.data)
  }

  const handleToggleFaceCheckFront = async () => {
    const res = await toggleFaceCheckFront(sourceId)
    setSource(res.data)
  }

  const handleToggleSkeleton = async () => {
    const res = await toggleSkeleton(sourceId)
    setSource(res.data)
  }

  if (loading) return <Spin style={{ padding: 40 }} />
  if (!source) return <div>源不存在</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/sources')} />
        <Title level={4} style={{ margin: 0 }}>{source.name}</Title>
      </div>

      <Tabs
        items={[
          {
            key: 'player',
            label: '播放器',
            children: (
              <div>
                <Row gutter={8} style={{ marginBottom: 12 }}>
                  <Col>
                    <Switch
                      checked={source.show_overlay}
                      onChange={handleToggleOverlay}
                      checkedChildren="显示区域"
                      unCheckedChildren="隐藏区域"
                    />
                  </Col>
                  <Col>
                    <Switch
                      checked={source.face_recognition_enabled}
                      onChange={handleToggleFaceRecognition}
                      checkedChildren="人脸识别开"
                      unCheckedChildren="人脸识别关"
                    />
                  </Col>
                  <Col>
                    <Switch
                      checked={source.face_check_front}
                      onChange={handleToggleFaceCheckFront}
                      checkedChildren="仅正面识别"
                      unCheckedChildren="正面检测关"
                    />
                  </Col>
                  <Col>
                    <Switch
                      checked={source.show_skeleton}
                      onChange={handleToggleSkeleton}
                      checkedChildren="骨架显示"
                      unCheckedChildren="骨架隐藏"
                    />
                  </Col>
                </Row>
                {source.is_active ? (
                  <HlsPlayer sourceId={sourceId} zones={zones} showOverlay={source.show_overlay} />
                ) : (
                  <div style={{ background: '#222', color: '#888', padding: 40, textAlign: 'center' }}>
                    流未启动，请在列表页点击「启动」
                  </div>
                )}
              </div>
            ),
          },
          {
            key: 'zones',
            label: '检测区域',
            children: (
              <Row gutter={16}>
                <Col xs={24} md={16}>
                  <ZoneCanvas
                    sourceId={sourceId}
                    zones={zones}
                    onZoneCreated={(z) => setZones((prev) => [...prev, z])}
                  />
                </Col>
                <Col xs={24} md={8}>
                  <ZoneList
                    zones={zones}
                    onZoneDeleted={(id) => setZones((prev) => prev.filter((z) => z.id !== id))}
                  />
                </Col>
              </Row>
            ),
          },
          {
            key: 'roi',
            label: '侦测ROI',
            children: (
              <RoiCanvas
                sourceId={sourceId}
                roiJson={source.detection_roi_json}
                onRoiUpdated={(roi) => setSource((prev) => prev ? { ...prev, detection_roi_json: roi } : prev)}
              />
            ),
          },
          {
            key: 'reports',
            label: '报告配置',
            children: <ReportConfigPanel sourceId={sourceId} zones={zones} />,
          },
        ]}
      />
    </div>
  )
}
