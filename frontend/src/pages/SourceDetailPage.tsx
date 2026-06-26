import { ArrowLeftOutlined } from '@ant-design/icons'
import { Button, Col, Row, Spin, Switch, Tabs, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
  if (!source) return <div>{t('source.not_found')}</div>

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
            label: t('source.tab_player'),
            children: (
              <div>
                <Row gutter={8} style={{ marginBottom: 12 }}>
                  <Col>
                    <Switch
                      checked={source.show_overlay}
                      onChange={handleToggleOverlay}
                      checkedChildren={t('source.show_overlay')}
                      unCheckedChildren={t('source.hide_overlay')}
                    />
                  </Col>
                  <Col>
                    <Switch
                      checked={source.face_recognition_enabled}
                      onChange={handleToggleFaceRecognition}
                      checkedChildren={t('source.face_on')}
                      unCheckedChildren={t('source.face_off')}
                    />
                  </Col>
                  <Col>
                    <Switch
                      checked={source.face_check_front}
                      onChange={handleToggleFaceCheckFront}
                      checkedChildren={t('source.front_on')}
                      unCheckedChildren={t('source.front_off')}
                    />
                  </Col>
                  <Col>
                    <Switch
                      checked={source.show_skeleton}
                      onChange={handleToggleSkeleton}
                      checkedChildren={t('source.skeleton_on')}
                      unCheckedChildren={t('source.skeleton_off')}
                    />
                  </Col>
                </Row>
                {source.is_active ? (
                  <HlsPlayer sourceId={sourceId} zones={zones} showOverlay={source.show_overlay} />
                ) : (
                  <div style={{ background: '#222', color: '#888', padding: 40, textAlign: 'center' }}>
                    {t('source.not_started')}
                  </div>
                )}
              </div>
            ),
          },
          {
            key: 'zones',
            label: t('source.tab_zones'),
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
            label: t('source.tab_roi'),
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
            label: t('source.tab_reports'),
            children: <ReportConfigPanel sourceId={sourceId} zones={zones} />,
          },
        ]}
      />
    </div>
  )
}
