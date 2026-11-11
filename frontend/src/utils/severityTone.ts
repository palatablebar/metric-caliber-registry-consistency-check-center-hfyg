export function severityClass(severity: string | null | undefined): string {
  if (severity === 'high') return 'badge high'
  if (severity === 'medium') return 'badge medium'
  if (severity === 'low') return 'badge low'
  return 'badge'
}

export function domainColor(domain: string | null | undefined): string {
  switch (domain) {
    case 'growth':
      return 'var(--sage)'
    case 'trade':
      return 'var(--gold)'
    case 'content':
      return 'var(--vermilion)'
    case 'experience':
      return 'var(--ink-soft)'
    default:
      return 'var(--rule)'
  }
}
