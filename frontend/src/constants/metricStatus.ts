export const METRIC_STATUSES = ['draft', 'active', 'deprecated'] as const
export type MetricStatusValue = (typeof METRIC_STATUSES)[number]
export const METRIC_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  active: '生效',
  deprecated: '已下线',
}
