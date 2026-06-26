import { DeleteOutlined } from '@ant-design/icons'
import { Button, Col, Popconfirm, Row, Select, Table, Tag, Tooltip, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { deleteRecord, listRecords } from '../api/records'
import { listSources } from '../api/sources'
import type { Source, TriggerRecord } from '../api/types'

const { Title } = Typography

export default function RecordsPage() {
  const { t, i18n } = useTranslation()
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSource, setSelectedSource] = useState<number | null>(null)
  const [records, setRecords] = useState<TriggerRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    listSources().then((r) => {
      setSources(r.data)
      if (r.data.length > 0) setSelectedSource(r.data[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedSource) return
    setLoading(true)
    listRecords(selectedSource, page, 20)
      .then((r) => { setRecords(r.data.items); setTotal(r.data.total) })
      .finally(() => setLoading(false))
  }, [selectedSource, page])

  const handleDelete = async (id: number) => {
    await deleteRecord(id)
    setRecords((prev) => prev.filter((r) => r.id !== id))
    message.success(t('records.deleted'))
  }

  const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US'

  const columns: ColumnsType<TriggerRecord> = [
    { title: t('common.id'), dataIndex: 'id', width: 60 },
    {
      title: t('records.col_triggered'),
      dataIndex: 'triggered_at',
      render: (v: string) => new Date(v).toLocaleString(locale),
      width: 180,
    },
    { title: t('records.col_rule'), dataIndex: 'rule_id', width: 80 },
    { title: t('records.col_zone'), dataIndex: 'zone_id', width: 80 },
    { title: t('records.col_person'), dataIndex: 'person_name', render: (v: string | null) => v || '-' },
    { title: t('records.col_photos'), dataIndex: 'photos_sent', width: 80 },
    {
      title: t('records.col_alert'),
      width: 120,
      render: (_: unknown, row: TriggerRecord) => {
        if (row.alert_delivered) return <Tag color="green">{t('records.delivered')}</Tag>
        if (row.delivery_error) {
          return (
            <Tooltip title={row.delivery_error}>
              <Tag color="red" style={{ cursor: 'help' }}>{t('records.failed')}</Tag>
            </Tooltip>
          )
        }
        return <Tag color="default">{t('records.not_sent')}</Tag>
      },
    },
    {
      title: t('common.actions'),
      width: 80,
      render: (_, record) => (
        <Popconfirm title={t('records.confirm_delete')} onConfirm={() => handleDelete(record.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={4} style={{ margin: 0 }}>{t('records.title')}</Title></Col>
        <Col>
          <Select
            style={{ width: 200 }}
            placeholder={t('records.select_source')}
            value={selectedSource}
            onChange={setSelectedSource}
            options={sources.map((s) => ({ label: s.name, value: s.id }))}
          />
        </Col>
      </Row>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={records}
        loading={loading}
        pagination={{
          total,
          current: page,
          pageSize: 20,
          onChange: setPage,
          showTotal: (n) => t('records.total', { count: n }),
        }}
        scroll={{ x: 800 }}
      />
    </div>
  )
}
