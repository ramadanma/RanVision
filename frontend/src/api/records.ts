import client from './client'
import type { PaginatedRecords } from './types'

export const listRecords = (sourceId: number, page = 1, size = 20) =>
  client.get<PaginatedRecords>('/records', { params: { source_id: sourceId, page, size } })
export const deleteRecord = (id: number) => client.delete(`/records/${id}`)
