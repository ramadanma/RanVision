import { DeleteOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import { Badge, Button, Card, Popconfirm, Space, Tag, Typography, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { deleteSource, startSource, stopSource } from '../../api/sources'
import { useSourceStore } from '../../store/sourceStore'
import type { Source } from '../../api/types'

const { Text } = Typography

interface Props {
  source: Source
}

export default function SourceCard({ source }: Props) {
  const navigate = useNavigate()
  const { updateSource, removeSource } = useSourceStore()

  const handleStart = async () => {
    try {
      const res = await startSource(source.id)
      updateSource(res.data)
      message.success('已启动')
    } catch {
      message.error('启动失败')
    }
  }

  const handleStop = async () => {
    try {
      const res = await stopSource(source.id)
      updateSource(res.data)
      message.success('已停止')
    } catch {
      message.error('停止失败')
    }
  }

  const handleDelete = async () => {
    await deleteSource(source.id)
    removeSource(source.id)
    message.success('已删除')
  }

  return (
    <Card
      hoverable
      title={
        <Space>
          <Badge status={source.is_active ? 'processing' : 'default'} />
          <Text strong>{source.name}</Text>
        </Space>
      }
      extra={
        <Popconfirm title="确认删除？" onConfirm={handleDelete}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      }
      actions={[
        source.is_active ? (
          <Button type="text" icon={<StopOutlined />} onClick={handleStop} danger>停止</Button>
        ) : (
          <Button type="text" icon={<PlayCircleOutlined />} onClick={handleStart}>启动</Button>
        ),
        <Button type="link" onClick={() => navigate(`/sources/${source.id}`)}>配置</Button>,
      ]}
    >
      <Tag color={source.source_type === 'file' ? 'blue' : 'green'}>
        {source.source_type === 'file' ? '视频文件' : 'IP摄像头'}
      </Tag>
      {source.source_type === 'ip_camera' && (
        <Text type="secondary" style={{ fontSize: 12 }}>{source.ip}:{source.port}</Text>
      )}
    </Card>
  )
}
