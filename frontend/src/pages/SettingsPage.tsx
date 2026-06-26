import { Button, Card, Checkbox, Form, Input, InputNumber, Spin, Typography, message } from 'antd'
import { useEffect, useState } from 'react'
import { getSmtpConfig, updateSmtpConfig } from '../api/smtpConfig'

const { Title } = Typography

export default function SettingsPage() {
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
      message.success('SMTP 配置已保存')
      form.setFieldValue('password', '')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Spin style={{ padding: 40 }} />

  return (
    <div style={{ maxWidth: 560 }}>
      <Title level={4} style={{ marginBottom: 24 }}>系统设置</Title>
      <Card title="邮件服务器（SMTP）配置">
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="host" label="SMTP 服务器地址" rules={[{ required: true, message: '请填写 SMTP 服务器地址' }]}>
            <Input placeholder="smtp.example.com" />
          </Form.Item>
          <Form.Item name="port" label="端口">
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="username" label="用户名（邮箱账号）">
            <Input placeholder="your@email.com" />
          </Form.Item>
          <Form.Item name="password" label="授权码 / 密码（留空则不修改）">
            <Input.Password placeholder="填写则更新，留空保持原值" autoComplete="new-password" />
          </Form.Item>
          <Form.Item name="from_addr" label="发件人地址（From，留空则使用用户名）">
            <Input placeholder="RanVision <noreply@example.com>" />
          </Form.Item>
          <Form.Item name="use_tls" valuePropName="checked">
            <Checkbox>启用 STARTTLS 加密</Checkbox>
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>
            保存配置
          </Button>
        </Form>
      </Card>
    </div>
  )
}
