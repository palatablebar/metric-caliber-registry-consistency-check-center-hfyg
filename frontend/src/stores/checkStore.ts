import { defineStore } from 'pinia'
import { createCheck, fetchCheck, fetchChecks } from '../api/check'
import type { CheckBatch, CheckDetail } from '../types/check'
import type { ApiError } from '../types/api'

interface CheckState {
  batches: CheckBatch[]
  detail: CheckDetail | null
  loading: boolean
  running: boolean
  error: ApiError | null
}

export const useCheckStore = defineStore('check', {
  state: (): CheckState => ({
    batches: [],
    detail: null,
    loading: false,
    running: false,
    error: null,
  }),
  getters: {
    latest: (state): CheckBatch | null => state.batches[0] ?? null,
  },
  actions: {
    async loadBatches() {
      this.loading = true
      this.error = null
      try {
        const result = await fetchChecks()
        this.batches = result.items
        const latest = result.items[0]
        if (latest) await this.loadDetail(latest.id)
      } catch (error) {
        this.error = error as ApiError
      } finally {
        this.loading = false
      }
    },
    async loadDetail(checkId: number) {
      try {
        this.detail = await fetchCheck(checkId)
      } catch (error) {
        this.error = error as ApiError
      }
    },
    async runCheck(scope = 'all') {
      this.running = true
      this.error = null
      try {
        const created = await createCheck(scope)
        await this.waitFor(created.id)
        await this.loadBatches()
      } catch (error) {
        this.error = error as ApiError
      } finally {
        this.running = false
      }
    },
    async waitFor(checkId: number, attempts = 40) {
      for (let index = 0; index < attempts; index += 1) {
        const detail = await fetchCheck(checkId)
        this.detail = detail
        if (detail.status === 'completed' || detail.status === 'failed') return detail
        await new Promise((resolve) => setTimeout(resolve, 700))
      }
      return null
    },
  },
})
