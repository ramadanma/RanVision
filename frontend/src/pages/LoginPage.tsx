import { Button, Card, Form, Input, Tabs, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { setToken } = useAuthStore()
  const [loginForm] = Form.useForm()
  const [regForm] = Form.useForm()

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      const res = await login(values.username, values.password)
      setToken(res.data.access_token)
      navigate('/sources')
    } catch {
      message.error(t('login.err_login'))
    }
  }

  const handleRegister = async (values: { username: string; email: string; password: string }) => {
    try {
      await register(values.username, values.email, values.password)
      message.success(t('login.ok_register'))
      regForm.resetFields()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('login.err_register')
      message.error(msg)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h2 style={{ margin: 0 }}>RanVision</h2>
          <p style={{ color: '#888', margin: '4px 0 0' }}>{t('login.subtitle')}</p>
        </div>
        <Tabs
          items={[
            {
              key: 'login',
              label: t('login.tab_login'),
              children: (
                <Form form={loginForm} layout="vertical" onFinish={handleLogin}>
                  <Form.Item name="username" label={t('login.username')} rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="password" label={t('login.password')} rules={[{ required: true }]}>
                    <Input.Password />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block>{t('login.btn_login')}</Button>
                </Form>
              ),
            },
            {
              key: 'register',
              label: t('login.tab_register'),
              children: (
                <Form form={regForm} layout="vertical" onFinish={handleRegister}>
                  <Form.Item name="username" label={t('login.username')} rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="email" label={t('login.email')} rules={[{ required: true, type: 'email' }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="password" label={t('login.password')} rules={[{ required: true, min: 6 }]}>
                    <Input.Password />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block>{t('login.btn_register')}</Button>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}
