import client from './client'
import type { Zone } from './types'

export const listZones = (sourceId: number) => client.get<Zone[]>('/zones', { params: { source_id: sourceId } })
export const createZone = (data: { source_id: number; name: string; polygon: number[][] }) =>
  client.post<Zone>('/zones', data)
export const updateZone = (id: number, data: { name?: string; polygon?: number[][] }) =>
  client.patch<Zone>(`/zones/${id}`, data)
export const deleteZone = (id: number) => client.delete(`/zones/${id}`)
