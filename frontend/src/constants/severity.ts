export const SEVERITIES = ['high', 'medium', 'low'] as const
export type SeverityValue = (typeof SEVERITIES)[number]
export const SEVERITY_LABELS: Record<string, string> = { high: '高', medium: '中', low: '低' }
export const SEVERITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 }
