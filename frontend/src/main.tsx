import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import './i18n'
import App from './App'
import { useLangStore } from './store/langStore'

function Root() {
  const lang = useLangStore((s) => s.lang)
  return (
    <ConfigProvider locale={lang === 'zh' ? zhCN : enUS}>
      <App />
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
)
