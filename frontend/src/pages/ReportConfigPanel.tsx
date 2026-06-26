import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import {
  Button, Card, Checkbox, Form, Input, InputNumber, Popconfirm,
  Radio, Space, Tag, Tooltip, Typography, message
} from 'antd'
import type { TextAreaRef } from 'antd/es/input/TextArea'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  addTriggerRule, createReportConfig, deleteReportConfig,
  listReportConfigs, removeTriggerRule, updateReportConfig
} from '../api/reportConfigs'
import { listRules } from '../api/rules'
import type { ReportConfig, Rule, Zone } from '../api/types'

const { Text } = Typography

interface VarButtonsProps {
  textAreaRef: React.RefObject<TextAreaRef>
  formInstance: ReturnType<typeof Form.useForm>[0]
  fieldName: string
}

function VarButtons({ textAreaRef, formInstance, fieldName }: VarButtonsProps) {
  const { t } = useTranslation()

  const TEMPLATE_VARS = [
    { key: '{{person_name}}', label: t('report.var_person') },
    { key: '{{source_id}}', label: t('report.var_source') },
    { key: '{{zone_id}}', label: t('report.var_zone') },
    { key: '{{rule_id}}', label: t('report.var_rule') },
    { key: '{{triggered_at}}', label: t('report.var_time') },
    { key: '{{details}}', label: t('report.var_details') },
  ]

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
      <Text type="secondary" style={{ fontSize: 12 }}>{t('report.insert_var')}</Text>
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
  const { t } = useTranslation()
  const subjectRef = useRef<TextAreaRef>(null)
  const bodyRef = useRef<TextAreaRef>(null)

  return (
    <>
      <Form.Item label={t('report.subject_tmpl')}>
        <VarButtons textAreaRef={subjectRef} formInstance={formInstance} fieldName="subject_template" />
        <Form.Item name="subject_template" noStyle>
          <Input.TextArea ref={subjectRef} rows={2} placeholder="[RanVision] #{{rule_id}}" />
        </Form.Item>
      </Form.Item>
      <Form.Item label={t('report.body_tmpl')}>
        <VarButtons textAreaRef={bodyRef} formInstance={formInstance} fieldName="body_template" />
        <Form.Item name="body_template" noStyle>
          <Input.TextArea
            ref={bodyRef}
            rows={5}
            placeholder={`Source: {{source_id}}\nZone: {{zone_id}}\nRule: {{rule_id}}\nPerson: {{person_name}}\nDetails: {{details}}`}
          />
        </Form.Item>
      </Form.Item>
    </>
  )
}

interface Props {
  sourceId: number
  zones: Zone[]
}

export default function ReportConfigPanel({ sourceId, zones }: Props) {
  const { t } = useTranslation()
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

  const handleCreate = async (values: Record<string, unknown>) => {
    try {
      const data = { ...values, source_id: sourceId, photo_count: (values.photo_count as number) ?? 0 }
      const res = await createReportConfig(data)
      setConfigs((prev) => [...prev, res.data])
      setShowForm(false)
      form.resetFields()
      message.success(t('report.created'))
    } catch {
      message.error(t('report.create_failed'))
    }
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

  const handleUpdate = async (values: Record<string, unknown>) => {
    if (editingId === null) return
    try {
      const data = { ...values, photo_count: (values.photo_count as number) ?? 0 }
      const res = await updateReportConfig(editingId, data)
      setConfigs((prev) => prev.map((c) => (c.id === editingId ? res.data : c)))
      setEditingId(null)
      editForm.resetFields()
      message.success(t('report.updated'))
    } catch {
      message.error(t('report.update_failed'))
    }
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
      <Form.Item name="name" label={t('report.name')} rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="delivery_method" label={t('report.method')}>
        <Radio.Group>
          <Radio value="email">{t('report.email')}</Radio>
          <Radio value="webhook">{t('report.webhook')}</Radio>
        </Radio.Group>
      </Form.Item>
      <Form.Item name="destination" label={t('report.destination')} rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="photo_count" label={t('report.photo_count')}>
        <InputNumber min={0} max={10} />
      </Form.Item>
      <Form.Item name="include_person_name" valuePropName="checked">
        <Checkbox>{t('report.include_name')}</Checkbox>
      </Form.Item>
      <Form.Item name="save_records" valuePropName="checked">
        <Checkbox>{t('report.save_records')}</Checkbox>
      </Form.Item>
      <TemplateFields formInstance={formInstance} />
    </>
  )

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<PlusOutlined />} type="primary" onClick={() => { setShowForm(!showForm); setEditingId(null) }}>
          {t('report.add')}
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
              <Button type="primary" htmlType="submit">{t('report.btn_create')}</Button>
              <Button onClick={() => { setShowForm(false); form.resetFields() }}>{t('report.btn_cancel')}</Button>
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
              <Popconfirm title={t('report.confirm_delete')} onConfirm={() => handleDelete(config.id)}>
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
                <Button type="primary" htmlType="submit">{t('report.btn_save')}</Button>
                <Button onClick={() => { setEditingId(null); editForm.resetFields() }}>{t('report.btn_cancel')}</Button>
              </Space>
            </Form>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Tag color={config.delivery_method === 'email' ? 'blue' : 'purple'}>
                  {config.delivery_method === 'email' ? t('report.email') : t('report.webhook')}
                </Tag>
                <Text type="secondary">{config.destination}</Text>
              </Space>
              <Text type="secondary">
                {t('report.photos_info', {
                  count: config.photo_count,
                  include: config.include_person_name ? t('report.name_include') : t('report.name_exclude'),
                })}
              </Text>
              {config.subject_template && (
                <Text type="secondary" style={{ fontSize: 12 }}>{t('report.subject_label')}{config.subject_template}</Text>
              )}
              {config.body_template && (
                <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                  {t('report.body_label')}{config.body_template.slice(0, 80)}{config.body_template.length > 80 ? '…' : ''}
                </Text>
              )}
              <div>
                <Text strong>{t('report.trigger_rules')}</Text>
                <div style={{ marginTop: 4 }}>
                  {allRules.length === 0 ? (
                    <Text type="secondary">{t('report.no_rules')}</Text>
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
