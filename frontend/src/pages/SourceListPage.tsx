import { PlusOutlined } from '@ant-design/icons'
import { Button, Col, Empty, Row, Spin, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { listSources } from '../api/sources'
import AddSourceModal from '../components/source/AddSourceModal'
import SourceCard from '../components/source/SourceCard'
import { useSourceStore } from '../store/sourceStore'

const { Title } = Typography

export default function SourceListPage() {
  const { sources, setSources } = useSourceStore()
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)

  useEffect(() => {
    listSources()
      .then((res) => setSources(res.data))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>视频源列表</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowAdd(true)}>添加视频源</Button>
      </div>
      {loading ? (
        <Spin />
      ) : sources.length === 0 ? (
        <Empty description="暂无视频源，点击右上角添加" />
      ) : (
        <Row gutter={[16, 16]}>
          {sources.map((s) => (
            <Col key={s.id} xs={24} sm={12} md={8} lg={6}>
              <SourceCard source={s} />
            </Col>
          ))}
        </Row>
      )}
      {showAdd && <AddSourceModal onClose={() => setShowAdd(false)} />}
    </div>
  )
}
