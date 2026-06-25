import client from './client'
import type { ReportConfig } from './types'

export const listReportConfigs = (sourceId: number) =>
  client.get<ReportConfig[]>('/report-configs', { params: { source_id: sourceId } })
export const createReportConfig = (data: object) => client.post<ReportConfig>('/report-configs', data)
export const updateReportConfig = (id: number, data: object) => client.patch<ReportConfig>(`/report-configs/${id}`, data)
export const deleteReportConfig = (id: number) => client.delete(`/report-configs/${id}`)
export const addTriggerRule = (configId: number, ruleId: number) =>
  client.post(`/report-configs/${configId}/trigger-rules/${ruleId}`)
export const removeTriggerRule = (configId: number, ruleId: number) =>
  client.delete(`/report-configs/${configId}/trigger-rules/${ruleId}`)
