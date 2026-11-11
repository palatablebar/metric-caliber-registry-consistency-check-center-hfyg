export const CHECK_STATUS_LABELS: Record<string, string> = {
  pending: '排队中',
  running: '检查中',
  completed: '已完成',
  incomplete: '不完整',
  failed: '失败',
}
export const FINDING_STATUS_LABELS: Record<string, string> = {
  open: '待处理',
  acknowledged: '已确认',
  resolved: '已解决',
}
export const TRUST_STATUS_LABELS: Record<string, string> = {
  trusted: '结果可信',
  untrusted: '结果不可信',
  pending: '结果未出',
}
export const TERMINAL_CHECK_STATUSES = ['completed', 'incomplete', 'failed'] as const
