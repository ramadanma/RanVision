import { create } from 'zustand'
import type { Source } from '../api/types'

interface SourceState {
  sources: Source[]
  setSources: (sources: Source[]) => void
  updateSource: (source: Source) => void
  removeSource: (id: number) => void
}

export const useSourceStore = create<SourceState>((set) => ({
  sources: [],
  setSources: (sources) => set({ sources }),
  updateSource: (updated) =>
    set((state) => ({
      sources: state.sources.map((s) => (s.id === updated.id ? updated : s)),
    })),
  removeSource: (id) =>
    set((state) => ({ sources: state.sources.filter((s) => s.id !== id) })),
}))
