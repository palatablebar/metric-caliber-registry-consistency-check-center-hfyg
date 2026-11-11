import type { CheckBatch, CheckDetail } from '../types/check'
import { downloadWithAuth } from '../utils/request'
import http from './http'

export function fetchChecks() {
  return http.get<{ items: CheckBatch[]; total: number }>('/checks?page_size=20')
}

export function fetchLatestCheck() {
  return http.get<{ check: CheckBatch | null; findings: unknown[] }>('/checks/latest')
}

export function fetchCheck(checkId: number) {
  return http.get<CheckDetail>(`/checks/${checkId}`)
}

export function createCheck(scope = 'all') {
  return http.post<CheckBatch>('/checks', { scope })
}

export function triageFinding(findingId: number, status: string) {
  return http.patch<{ status: string }>(`/findings/${findingId}`, { status })
}

export async function downloadImpactCsv(checkId: number, batchNo: string) {
  await downloadWithAuth(`/checks/${checkId}/impact.csv`, `impact-${batchNo}.csv`)
}
