import client from './client'
import type { User } from './types'

export const login = (username: string, password: string) =>
  client.post<{ access_token: string }>('/auth/login', new URLSearchParams({ username, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

export const register = (username: string, email: string, password: string) =>
  client.post<User>('/auth/register', { username, email, password })

export const getMe = () => client.get<User>('/auth/me')
