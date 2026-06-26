import { DeleteOutlined } from '@ant-design/icons'
import { Button, Col, Popconfirm, Row, Select, Table, Tag, Tooltip, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { deleteRecord, listRecords } from '../api/records'
import { listSources } from '../api/sources'
import type { Source, TriggerRecord } from '../api/types'

const { Title } = Typography

export default function RecordsPage() {
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
    message.success('已删除')
  }

  const columns: ColumnsType<TriggerRecord> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '触发时间',
      dataIndex: 'triggered_at',
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
      width: 180,
    },
    { title: '规则ID', dataIndex: 'rule_id', width: 80 },
    { title: '区域ID', dataIndex: 'zone_id', width: 80 },
    { title: '人员', dataIndex: 'person_name', render: (v: string | null) => v || '-' },
    { title: '照片', dataIndex: 'photos_sent', width: 80 },
    {
      title: '报告',
      width: 120,
      render: (_: unknown, row: TriggerRecord) => {
        if (row.alert_delivered) return <Tag color="green">已发送</Tag>
        if (row.delivery_error) {
          return (
            <Tooltip title={row.delivery_error}>
              <Tag color="red" style={{ cursor: 'help' }}>失败（悬停查看）</Tag>
            </Tooltip>
          )
        }
        return <Tag color="default">未发送</Tag>
      },
    },
    {
      title: '操作',
      width: 80,
      render: (_, record) => (
        <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col><Title level={4} style={{ margin: 0 }}>触发记录</Title></Col>
        <Col>
          <Select
            style={{ width: 200 }}
            placeholder="选择视频源"
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
          showTotal: (t) => `共 ${t} 条`,
        }}
        scroll={{ x: 800 }}
      />
    </div>
  )
}
