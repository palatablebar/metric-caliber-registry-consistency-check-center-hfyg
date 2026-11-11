import { defineStore } from 'pinia'
import { fetchMetrics } from '../api/metric'
import type { Metric } from '../types/metric'
import type { ApiError } from '../types/api'

interface CatalogState {
  items: Metric[]
  domainCounts: Record<string, number>
  total: number
  loading: boolean
  error: ApiError | null
  q: string
  domain: string
  status: string
}

export const useCatalogStore = defineStore('catalog', {
  state: (): CatalogState => ({
    items: [],
    domainCounts: {},
    total: 0,
    loading: false,
    error: null,
    q: '',
    domain: '',
    status: '',
  }),
  getters: {
    groups: (state): { domain: string; label: string; items: Metric[] }[] => {
      const order = ['growth', 'trade', 'content', 'experience']
      const labels: Record<string, string> = { growth: '增长', trade: '交易', content: '内容', experience: '体验' }
      const byDomain: Record<string, Metric[]> = {}
      for (const metric of state.items) {
        ;(byDomain[metric.domain] ||= []).push(metric)
      }
      return order
        .filter((domain) => (byDomain[domain] ?? []).length > 0)
        .map((domain) => ({ domain, label: labels[domain], items: byDomain[domain] }))
    },
    multiVersionCount: (state): number => state.items.filter((metric) => metric.version_count > 1).length,
  },
  actions: {
    async load() {
      this.loading = true
      this.error = null
      try {
        const result = await fetchMetrics({
          q: this.q || undefined,
          domain: this.domain || undefined,
          status: this.status || undefined,
          page_size: 100,
        })
        this.items = result.items
        this.total = result.total
        this.domainCounts = result.domain_counts
      } catch (error) {
        this.error = error as ApiError
      } finally {
        this.loading = false
      }
    },
  },
})
