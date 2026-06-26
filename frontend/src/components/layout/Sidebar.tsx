import {
  AlertOutlined,
  CameraOutlined,
  LogoutOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Menu, Typography } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

const { Title } = Typography

const items = [
  { key: '/sources', icon: <CameraOutlined />, label: '视频源' },
  { key: '/faces', icon: <UserOutlined />, label: '人脸库' },
  { key: '/records', icon: <AlertOutlined />, label: '触发记录' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)

  const selectedKey = items.find((i) => location.pathname.startsWith(i.key))?.key || '/sources'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px 24px', borderBottom: '1px solid #303030' }}>
        <Title level={4} style={{ color: '#fff', margin: 0 }}>RanVision</Title>
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onClick={({ key }) => navigate(key)}
        style={{ flex: 1, borderRight: 0 }}
      />
      <Menu
        theme="dark"
        mode="inline"
        items={[{ key: 'logout', icon: <LogoutOutlined />, label: '退出登录' }]}
        onClick={() => { logout(); navigate('/login') }}
        style={{ borderRight: 0 }}
      />
    </div>
  )
}
