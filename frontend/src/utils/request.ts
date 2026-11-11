import type { ApiError } from '../types/api'

export const TOKEN_KEY = 'metricd_token'
const BASE = '/api'

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const text = await response.text()
  const payload = text ? JSON.parse(text) : null
  if (!response.ok) {
    const error: ApiError = {
      code: payload?.code ?? `HTTP-${response.status}`,
      message: payload?.message ?? `请求失败（HTTP ${response.status}）`,
      detail: payload?.detail,
      request_id: payload?.request_id,
    }
    if (response.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
    }
    throw error
  }
  return payload as T
}

export const http = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
}

export async function downloadWithAuth(path: string, filename: string): Promise<void> {
  const response = await fetch(`${BASE}${path}`, { headers: authHeaders() })
  if (!response.ok) {
    let message = `下载失败（HTTP ${response.status}）`
    try {
      const payload = await response.json()
      message = payload?.message ?? message
    } catch {
      /* keep fallback */
    }
    throw { code: `HTTP-${response.status}`, message } as ApiError
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
