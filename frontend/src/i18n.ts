import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import zh from './locales/zh.json'

function getInitialLang(): string {
  const saved = localStorage.getItem('lang')
  if (saved === 'en' || saved === 'zh') return saved
  return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
    },
    lng: getInitialLang(),
    fallbackLng: 'zh',
    interpolation: { escapeValue: false },
  })

export default i18n
