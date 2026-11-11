export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 16)
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('zh-CN').format(value)
}

export function shortKey(key: string | null | undefined): string {
  return (key ?? '').replace(/_/g, ' ')
}

export function trimFilters(filters: string[]): string {
  if (!filters.length) return '无过滤'
  return filters.join(' · ')
}
