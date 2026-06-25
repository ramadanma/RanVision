import client from './client'
import type { Rule } from './types'

export const listRules = (zoneId: number) => client.get<Rule[]>('/rules', { params: { zone_id: zoneId } })
export const createRule = (data: object) => client.post<Rule>('/rules', data)
export const updateRule = (id: number, data: object) => client.patch<Rule>(`/rules/${id}`, data)
export const toggleRule = (id: number) => client.patch<Rule>(`/rules/${id}/toggle`)
export const deleteRule = (id: number) => client.delete(`/rules/${id}`)
