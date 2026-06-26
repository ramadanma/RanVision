import client from './client'

export interface SmtpConfig {
  host: string
  port: number
  username: string
  from_addr: string
  use_tls: boolean
}

export interface SmtpConfigUpdate extends Partial<SmtpConfig> {
  password?: string
}

export const getSmtpConfig = () => client.get<SmtpConfig>('/smtp-config')
export const updateSmtpConfig = (data: SmtpConfigUpdate) => client.patch<SmtpConfig>('/smtp-config', data)
