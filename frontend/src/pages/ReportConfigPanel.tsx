import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import {
  Button, Card, Checkbox, Form, Input, InputNumber, Popconfirm,
  Radio, Select, Space, Switch, Tag, Typography, message
} from 'antd'
import { useEffect, useState } from 'react'
import {
  addTriggerRule, createReportConfig, deleteReportConfig,
  listReportConfigs, removeTriggerRule
} from '../api/reportConfigs'
import { listRules } from '../api/rules'
import type { ReportConfig, Rule, Zone } from '../api/types'

const { Text } = Typography

interface Props {
  sourceId: number
  zones: Zone[]
}

export default function ReportConfigPanel({ sourceId, zones }: Props) {
  const [configs, setConfigs] = useState<ReportConfig[]>([])
  const [allRules, setAllRules] = useState<Rule[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    listReportConfigs(sourceId).then((r) => setConfigs(r.data))
    // Load all rules for all zones
    Promise.all(zones.map((z) => listRules(z.id))).then((results) => {
      setAllRules(results.flatMap((r) => r.data))
    })
  }, [sourceId, zones.length])

  const handleCreate = async (values: {
    name: string
    delivery_method: string
    destination: string
    photo_count: number
    include_person_name: boolean
    save_records: boolean
  }) => {
    const res = await createReportConfig({ ...values, source_id: sourceId })
    setConfigs((prev) => [...prev, res.data])
    setShowForm(false)
    form.resetFields()
    message.success('报告配置已创建')
  }

  const handleDelete = async (id: number) => {
    await deleteReportConfig(id)
    setConfigs((prev) => prev.filter((c) => c.id !== id))
  }

  const handleToggleRule = async (config: ReportConfig, ruleId: number, checked: boolean) => {
    if (checked) {
      await addTriggerRule(config.id, ruleId)
      setConfigs((prev) =>
        prev.map((c) =>
          c.id === config.id ? { ...c, trigger_rule_ids: [...c.trigger_rule_ids, ruleId] } : c
        )
      )
    } else {
      await removeTriggerRule(config.id, ruleId)
      setConfigs((prev) =>
        prev.map((c) =>
          c.id === config.id ? { ...c, trigger_rule_ids: c.trigger_rule_ids.filter((id) => id !== ruleId) } : c
        )
      )
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<PlusOutlined />} type="primary" onClick={() => setShowForm(!showForm)}>
          新增报告配置
        </Button>
      </Space>

      {showForm && (
        <Card style={{ marginBottom: 16 }}>
          <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ delivery_method: 'email', photo_count: 0, include_person_name: false, save_records: true }}>
            <Form.Item name="name" label="配置名称" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="delivery_method" label="发送方式">
              <Radio.Group>
                <Radio value="email">邮件</Radio>
                <Radio value="webhook">HTTP Webhook</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="destination" label="目标地址（邮箱或URL）" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="photo_count" label="附带照片数量（0=不附带）">
              <InputNumber min={0} max={10} />
            </Form.Item>
            <Form.Item name="include_person_name" valuePropName="checked">
              <Checkbox>包含人员姓名（需开启人脸识别）</Checkbox>
            </Form.Item>
            <Form.Item name="save_records" valuePropName="checked">
              <Checkbox>保存触发记录</Checkbox>
            </Form.Item>
            <Button type="primary" htmlType="submit">创建</Button>
          </Form>
        </Card>
      )}

      {configs.map((config) => (
        <Card
          key={config.id}
          title={config.name}
          extra={
            <Popconfirm title="确认删除？" onConfirm={() => handleDelete(config.id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          }
          style={{ marginBottom: 12 }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space>
              <Tag color={config.delivery_method === 'email' ? 'blue' : 'purple'}>
                {config.delivery_method === 'email' ? '邮件' : 'Webhook'}
              </Tag>
              <Text type="secondary">{config.destination}</Text>
            </Space>
            <Text type="secondary">附带 {config.photo_count} 张照片，{config.include_person_name ? '含' : '不含'}姓名</Text>
            <div>
              <Text strong>触发规则：</Text>
              <div style={{ marginTop: 4 }}>
                {allRules.length === 0 ? (
                  <Text type="secondary">暂无规则（请先在「检测区域」中创建规则）</Text>
                ) : (
                  allRules.map((rule) => (
                    <Checkbox
                      key={rule.id}
                      checked={config.trigger_rule_ids.includes(rule.id)}
                      onChange={(e) => handleToggleRule(config, rule.id, e.target.checked)}
                      style={{ marginRight: 8 }}
                    >
                      {rule.name}
                    </Checkbox>
                  ))
                )}
              </div>
            </div>
          </Space>
        </Card>
      ))}
    </div>
  )
}
