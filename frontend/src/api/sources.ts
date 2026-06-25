import client from './client'
import type { Source } from './types'

export const listSources = () => client.get<Source[]>('/sources')
export const getSource = (id: number) => client.get<Source>(`/sources/${id}`)
export const createSource = (data: object) => client.post<Source>('/sources', data)
export const updateSource = (id: number, data: object) => client.patch<Source>(`/sources/${id}`, data)
export const deleteSource = (id: number) => client.delete(`/sources/${id}`)
export const startSource = (id: number) => client.post<Source>(`/sources/${id}/start`)
export const stopSource = (id: number) => client.post<Source>(`/sources/${id}/stop`)
export const toggleOverlay = (id: number) => client.patch<Source>(`/sources/${id}/overlay`)
export const toggleFaceRecognition = (id: number) => client.patch<Source>(`/sources/${id}/face-recognition`)
export const uploadVideo = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return client.post<{ file_path: string; filename: string }>('/stream/upload-video', form)
}
