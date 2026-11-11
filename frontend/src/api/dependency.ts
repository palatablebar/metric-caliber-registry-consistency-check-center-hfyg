import type { GraphPayload, ImpactPayload } from '../types/dependency'
import http from './http'

export function fetchGraph() {
  return http.get<GraphPayload>('/dependencies/graph')
}

export function fetchImpact(metricId: number) {
  return http.get<ImpactPayload>(`/metrics/${metricId}/impact`)
}
