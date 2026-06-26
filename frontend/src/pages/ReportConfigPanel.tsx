import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import {
  Button, Card, Checkbox, Form, Input, InputNumber, Popconfirm,
  Radio, Space, Tag, Tooltip, Typography, message
} from 'antd'
import type { TextAreaRef } from 'antd/es/input/TextArea'
import { useEffect, useRef, useState } from 'react'
import {
  addTriggerRule, createReportConfig, deleteReportConfig,
  listReportConfigs, removeTriggerRule, updateReportConfig
} from '../api/reportConfigs'
import { listRules } from '../api/rules'
import type { ReportConfig, Rule, Zone } from '../api/types'

const { Text } = Typography

// Variables that can be inserted into subject/body templates
const TEMPLATE_VARS = [
  { key: '{{person_name}}', label: '人员姓名' },
  { key: '{{source_id}}', label: '视频源ID' },
  { key: '{{zone_id}}', label: '区域ID' },
  { key: '{{rule_id}}', label: '规则ID' },
  { key: '{{triggered_at}}', label: '触发时间' },
  { key: '{{details}}', label: '规则详情' },
]

interface VarButtonsProps {
  textAreaRef: React.RefObject<TextAreaRef>
  formInstance: ReturnType<typeof Form.useForm>[0]
  fieldName: string
}

function VarButtons({ textAreaRef, formInstance, fieldName }: VarButtonsProps) {
  const insert = (variable: string) => {
    const el = textAreaRef.current?.resizableTextArea?.textArea
    const current: string = formInstance.getFieldValue(fieldName) || ''
    if (el) {
      const start = el.selectionStart ?? current.length
      const end = el.selectionEnd ?? current.length
      const newVal = current.slice(0, start) + variable + current.slice(end)
      formInstance.setFieldValue(fieldName, newVal)
      setTimeout(() => {
        el.selectionStart = el.selectionEnd = start + variable.length
        el.focus()
      }, 0)
    } else {
      formInstance.setFieldValue(fieldName, current + variable)
    }
  }

  return (
    <Space size={4} wrap style={{ marginBottom: 4 }}>
      <Text type="secondary" style={{ fontSize: 12 }}>插入变量：</Text>
      {TEMPLATE_VARS.map((v) => (
        <Tooltip key={v.key} title={v.key}>
          <Button size="small" onClick={() => insert(v.key)}>{v.label}</Button>
        </Tooltip>
      ))}
    </Space>
  )
}

interface TemplateFieldsProps {
  formInstance: ReturnType<typeof Form.useForm>[0]
}

function TemplateFields({ formInstance }: TemplateFieldsProps) {
  const subjectRef = useRef<TextAreaRef>(null)
  const bodyRef = useRef<TextAreaRef>(null)

  return (
    <>
      <Form.Item name="subject_template" label="邮件主题模板（留空使用默认）">
        <VarButtons textAreaRef={subjectRef} formInstance={formInstance} fieldName="subject_template" />
        <Input.TextArea ref={subjectRef} rows={2} placeholder="[RanVision] 规则触发: #{{rule_id}}" />
      </Form.Item>
      <Form.Item name="body_template" label="邮件正文模板（留空使用默认）">
        <VarButtons textAreaRef={bodyRef} formInstance={formInstance} fieldName="body_template" />
        <Input.TextArea
          ref={bodyRef}
          rows={5}
          placeholder={`Source: {{source_id}}\nZone: {{zone_id}}\nRule: {{rule_id}}\nPerson: {{person_name}}\nDetails: {{details}}`}
        />
      </Form.Item>
    </>
  )
}

interface Props {
  sourceId: number
  zones: Zone[]
}

export default function ReportConfigPanel({ sourceId, zones }: Props) {
  const [configs, setConfigs] = useState<ReportConfig[]>([])
  const [allRules, setAllRules] = useState<Rule[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    listReportConfigs(sourceId).then((r) => setConfigs(r.data))
    Promise.all(zones.map((z) => listRules(z.id))).then((results) => {
      setAllRules(results.flatMap((r) => r.data))
    })
  }, [sourceId, zones.length])

  const handleCreate = async (values: object) => {
    const res = await createReportConfig({ ...values, source_id: sourceId })
    setConfigs((prev) => [...prev, res.data])
    setShowForm(false)
    form.resetFields()
    message.success('报告配置已创建')
  }

  const handleEdit = (config: ReportConfig) => {
    setEditingId(config.id)
    editForm.setFieldsValue({
      name: config.name,
      delivery_method: config.delivery_method,
      destination: config.destination,
      photo_count: config.photo_count,
      include_person_name: config.include_person_name,
      save_records: config.save_records,
      subject_template: config.subject_template ?? '',
      body_template: config.body_template ?? '',
    })
  }

  const handleUpdate = async (values: object) => {
    if (editingId === null) return
    const res = await updateReportConfig(editingId, values)
    setConfigs((prev) => prev.map((c) => (c.id === editingId ? res.data : c)))
    setEditingId(null)
    editForm.resetFields()
    message.success('报告配置已更新')
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

  const commonFormFields = (formInstance: ReturnType<typeof Form.useForm>[0]) => (
    <>
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
      <TemplateFields formInstance={formInstance} />
    </>
  )

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<PlusOutlined />} type="primary" onClick={() => { setShowForm(!showForm); setEditingId(null) }}>
          新增报告配置
        </Button>
      </Space>

      {showForm && (
        <Card style={{ marginBottom: 16 }}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreate}
            initialValues={{ delivery_method: 'email', photo_count: 0, include_person_name: false, save_records: true }}
          >
            {commonFormFields(form)}
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => { setShowForm(false); form.resetFields() }}>取消</Button>
            </Space>
          </Form>
        </Card>
      )}

      {configs.map((config) => (
        <Card
          key={config.id}
          title={config.name}
          extra={
            <Space>
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={() => { setShowForm(false); handleEdit(config) }}
              />
              <Popconfirm title="确认删除？" onConfirm={() => handleDelete(config.id)}>
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          }
          style={{ marginBottom: 12 }}
        >
          {editingId === config.id ? (
            <Form form={editForm} layout="vertical" onFinish={handleUpdate} style={{ marginBottom: 8 }}>
              {commonFormFields(editForm)}
              <Space>
                <Button type="primary" htmlType="submit">保存</Button>
                <Button onClick={() => { setEditingId(null); editForm.resetFields() }}>取消</Button>
              </Space>
            </Form>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Tag color={config.delivery_method === 'email' ? 'blue' : 'purple'}>
                  {config.delivery_method === 'email' ? '邮件' : 'Webhook'}
                </Tag>
                <Text type="secondary">{config.destination}</Text>
              </Space>
              <Text type="secondary">
                附带 {config.photo_count} 张照片，{config.include_person_name ? '含' : '不含'}姓名
              </Text>
              {config.subject_template && (
                <Text type="secondary" style={{ fontSize: 12 }}>主题：{config.subject_template}</Text>
              )}
              {config.body_template && (
                <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                  正文：{config.body_template.slice(0, 80)}{config.body_template.length > 80 ? '…' : ''}
                </Text>
              )}
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
          )}
        </Card>
      ))}
    </div>
  )
}
