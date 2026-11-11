import type { DslParseResult, MetricDetail, MetricListResponse, MetricVersion } from '../types/metric'
import http from './http'

export interface MetricQuery {
  q?: string
  domain?: string
  status?: string
  team_id?: number
  page?: number
  page_size?: number
}

export function fetchMetrics(query: MetricQuery = {}) {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  })
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return http.get<MetricListResponse>(`/metrics${suffix}`)
}

export function fetchMetric(metricId: number) {
  return http.get<MetricDetail>(`/metrics/${metricId}`)
}

export function parseDsl(dsl_text: string) {
  return http.post<DslParseResult>('/dsl/parse', { dsl_text })
}

export function createVersion(
  metricId: number,
  payload: { dsl_text: string; team_id?: number; effective_from?: string; set_current?: boolean },
) {
  return http.post<MetricVersion>(`/metrics/${metricId}/versions`, payload)
}

export function compareVersions(metricId: number, versionA: number, versionB: number) {
  return http.get<Record<string, unknown>>(`/metrics/${metricId}/compare?version_a=${versionA}&version_b=${versionB}`)
}

export function fetchTeams() {
  return http.get<{ items: import('../types/user').OwnerTeam[] }>('/teams')
}
