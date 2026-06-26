import { Button, Card, Checkbox, Form, Input, InputNumber, Spin, Typography, message } from 'antd'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getSmtpConfig, updateSmtpConfig } from '../api/smtpConfig'

const { Title } = Typography

export default function SettingsPage() {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getSmtpConfig()
      .then((r) => {
        form.setFieldsValue({
          host: r.data.host,
          port: r.data.port,
          username: r.data.username,
          from_addr: r.data.from_addr,
          use_tls: r.data.use_tls,
        })
      })
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async (values: {
    host: string
    port: number
    username: string
    password?: string
    from_addr: string
    use_tls: boolean
  }) => {
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        host: values.host,
        port: values.port,
        username: values.username,
        from_addr: values.from_addr,
        use_tls: values.use_tls,
      }
      if (values.password) {
        payload.password = values.password
      }
      await updateSmtpConfig(payload)
      message.success(t('settings.saved'))
      form.setFieldValue('password', '')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Spin style={{ padding: 40 }} />

  return (
    <div style={{ maxWidth: 560 }}>
      <Title level={4} style={{ marginBottom: 24 }}>{t('settings.title')}</Title>
      <Card title={t('settings.smtp_card')}>
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="host" label={t('settings.smtp_host')} rules={[{ required: true, message: t('settings.smtp_host') }]}>
            <Input placeholder="smtp.example.com" />
          </Form.Item>
          <Form.Item name="port" label={t('settings.port')}>
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="username" label={t('settings.username')}>
            <Input placeholder="your@email.com" />
          </Form.Item>
          <Form.Item name="password" label={t('settings.password')}>
            <Input.Password placeholder={t('settings.password_placeholder')} autoComplete="new-password" />
          </Form.Item>
          <Form.Item name="from_addr" label={t('settings.from_addr')}>
            <Input placeholder="RanVision <noreply@example.com>" />
          </Form.Item>
          <Form.Item name="use_tls" valuePropName="checked">
            <Checkbox>{t('settings.use_tls')}</Checkbox>
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>
            {t('settings.save')}
          </Button>
        </Form>
      </Card>
    </div>
  )
}
