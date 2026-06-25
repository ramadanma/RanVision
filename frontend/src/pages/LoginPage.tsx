import { Button, Card, Form, Input, Tabs, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
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
      message.error('用户名或密码错误')
    }
  }

  const handleRegister = async (values: { username: string; email: string; password: string }) => {
    try {
      await register(values.username, values.email, values.password)
      message.success('注册成功，请登录')
      regForm.resetFields()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '注册失败'
      message.error(msg)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h2 style={{ margin: 0 }}>RanVision</h2>
          <p style={{ color: '#888', margin: '4px 0 0' }}>视频监控规则检测系统</p>
        </div>
        <Tabs
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form form={loginForm} layout="vertical" onFinish={handleLogin}>
                  <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="password" label="密码" rules={[{ required: true }]}>
                    <Input.Password />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block>登录</Button>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form form={regForm} layout="vertical" onFinish={handleRegister}>
                  <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
                    <Input.Password />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block>注册</Button>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}
