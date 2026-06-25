import client from './client'
import type { Face } from './types'

export const listFaces = () => client.get<Face[]>('/faces')
export const uploadFace = (personName: string, file: File) => {
  const form = new FormData()
  form.append('person_name', personName)
  form.append('file', file)
  return client.post<Face>('/faces', form)
}
export const updateFace = (id: number, personName: string) =>
  client.patch<Face>(`/faces/${id}`, { person_name: personName })
export const deleteFace = (id: number) => client.delete(`/faces/${id}`)
