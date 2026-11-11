import type { User } from '../types/user'
import http from './http'

export interface LoginResult {
  token: string
  user: User
}

export function login(email: string, password: string) {
  return http.post<LoginResult>('/auth/login', { email, password })
}

export function fetchMe() {
  return http.get<{ user: User }>('/auth/me')
}

export function fetchQuota() {
  return http.get<Record<string, number | string | null>>('/quota')
}
