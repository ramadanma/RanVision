import { DeleteOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import { Badge, Button, Card, Popconfirm, Space, Tag, Typography, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { deleteSource, startSource, stopSource } from '../../api/sources'
import { useSourceStore } from '../../store/sourceStore'
import type { Source } from '../../api/types'

const { Text } = Typography

interface Props {
  source: Source
}

export default function SourceCard({ source }: Props) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { updateSource, removeSource } = useSourceStore()

  const handleStart = async () => {
    try {
      const res = await startSource(source.id)
      updateSource(res.data)
      message.success(t('source.started'))
    } catch {
      message.error(t('source.start_failed'))
    }
  }

  const handleStop = async () => {
    try {
      const res = await stopSource(source.id)
      updateSource(res.data)
      message.success(t('source.stopped'))
    } catch {
      message.error(t('source.stop_failed'))
    }
  }

  const handleDelete = async () => {
    await deleteSource(source.id)
    removeSource(source.id)
    message.success(t('source.deleted'))
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
        <Popconfirm title={t('common.confirm_delete')} onConfirm={handleDelete}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      }
      actions={[
        source.is_active ? (
          <Button type="text" icon={<StopOutlined />} onClick={handleStop} danger>{t('source.btn_stop')}</Button>
        ) : (
          <Button type="text" icon={<PlayCircleOutlined />} onClick={handleStart}>{t('source.btn_start')}</Button>
        ),
        <Button type="link" onClick={() => navigate(`/sources/${source.id}`)}>{t('source.btn_config')}</Button>,
      ]}
    >
      <Tag color={source.source_type === 'file' ? 'blue' : 'green'}>
        {source.source_type === 'file' ? t('source.type_file') : t('source.type_camera')}
      </Tag>
      {source.source_type === 'ip_camera' && (
        <Text type="secondary" style={{ fontSize: 12 }}>{source.ip}:{source.port}</Text>
      )}
    </Card>
  )
}
