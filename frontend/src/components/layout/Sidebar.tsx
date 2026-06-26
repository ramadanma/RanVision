import {
  AlertOutlined,
  CameraOutlined,
  LogoutOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Menu, Segmented, Typography } from 'antd'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useLangStore, type Lang } from '../../store/langStore'

const { Title } = Typography

export default function Sidebar() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)
  const { lang, setLang } = useLangStore()

  const items = [
    { key: '/sources', icon: <CameraOutlined />, label: t('nav.sources') },
    { key: '/faces', icon: <UserOutlined />, label: t('nav.faces') },
    { key: '/records', icon: <AlertOutlined />, label: t('nav.records') },
    { key: '/settings', icon: <SettingOutlined />, label: t('nav.settings') },
  ]

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
      <div style={{ padding: '8px 12px', borderTop: '1px solid #303030' }}>
        <Segmented
          block
          size="small"
          options={[
            { label: '中文', value: 'zh' },
            { label: 'EN', value: 'en' },
          ]}
          value={lang}
          onChange={(v) => setLang(v as Lang)}
        />
      </div>
      <Menu
        theme="dark"
        mode="inline"
        items={[{ key: 'logout', icon: <LogoutOutlined />, label: t('nav.logout') }]}
        onClick={() => { logout(); navigate('/login') }}
        style={{ borderRight: 0 }}
      />
    </div>
  )
}
