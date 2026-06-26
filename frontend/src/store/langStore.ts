import { create } from 'zustand'
import i18n from '../i18n'

export type Lang = 'zh' | 'en'

interface LangState {
  lang: Lang
  setLang: (lang: Lang) => void
}

function getInitialLang(): Lang {
  const saved = localStorage.getItem('lang')
  if (saved === 'en' || saved === 'zh') return saved
  return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

export const useLangStore = create<LangState>((set) => ({
  lang: getInitialLang(),
  setLang: (lang) => {
    localStorage.setItem('lang', lang)
    i18n.changeLanguage(lang)
    set({ lang })
  },
}))
