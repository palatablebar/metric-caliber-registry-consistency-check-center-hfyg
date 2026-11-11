export type UserRole = 'admin' | 'owner' | 'analyst'

export interface User {
  id: number
  email: string
  display_name: string
  role: UserRole
  role_label: string
  team_id: number | null
  team_code: string | null
  team_name: string | null
  daily_check_quota: number
  quota_used: number
}

export interface OwnerTeam {
  id: number
  code: string
  name: string
  domain: string
  domain_label: string
  lead_name: string
  member_count: number
  sla_hours: number
  metric_count: number
}
