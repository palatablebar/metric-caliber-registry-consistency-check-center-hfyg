export const CONFLICT_TYPES = ['agg', 'measure', 'filter', 'window', 'grain', 'multi'] as const
export const CONFLICT_LABELS: Record<string, string> = {
  agg: '聚合函数',
  measure: '度量字段',
  filter: '过滤集合',
  window: '时间窗口',
  grain: '时间粒度',
  multi: '多维差异',
}
// policy mirrors backend/app/constants/conflict_type.py
export const DIMENSION_SEVERITY: Record<string, 'high' | 'medium' | 'low'> = {
  grain: 'high',
  filter: 'high',
  agg: 'high',
  window: 'medium',
  measure: 'low',
}
