export const DOMAINS = [
  { value: 'growth', label: '增长' },
  { value: 'trade', label: '交易' },
  { value: 'content', label: '内容' },
  { value: 'experience', label: '体验' },
] as const
export type DomainValue = (typeof DOMAINS)[number]['value']
export const DOMAIN_LABELS: Record<string, string> = Object.fromEntries(DOMAINS.map((d) => [d.value, d.label]))
