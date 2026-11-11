export const ROLES = ['admin', 'owner', 'analyst'] as const
export type RoleKey = (typeof ROLES)[number]
export const ROLE_LABELS: Record<RoleKey, string> = {
  admin: '治理委员会管理员',
  owner: '指标负责人',
  analyst: '分析员（只读）',
}
