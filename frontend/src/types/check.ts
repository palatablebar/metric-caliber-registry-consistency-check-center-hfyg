export interface CheckSummary {
  score: number
  pairs_compared: number
  metric_scores: Record<string, number>
  metrics_with_multiple_versions: number
  cycles: { member_keys: string[]; path_keys: string[] }[]
  orphans: string[]
  topological_order: string[]
  graph_stats: {
    node_count: number
    edge_count: number
    cycle_count: number
    orphan_count: number
    max_layer: number
    cyclic_metric_count: number
  }
  parse_failed: { metric_key: string; version_no: number; error: string; offset: number }[]
  findings_by_dimension: Record<string, number>
}

export interface CheckBatch {
  id: number
  batch_no: string
  scope: string
  scope_label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  status_label: string
  triggered_by: string | null
  started_at: string | null
  finished_at: string | null
  metrics_checked: number
  versions_checked: number
  conflict_count: number
  high_count: number
  consistency_score: number
  duration_ms: number | null
  summary: CheckSummary
  error_message: string | null
  created_at: string | null
  task_id?: string | null
}

export interface FindingEvidence {
  left: {
    agg: string
    measure: string
    filters: string[]
    window: string
    grain: string
  }
  right: {
    agg: string
    measure: string
    filters: string[]
    window: string
    grain: string
  }
  diff: Record<string, { field: string; left: unknown; right: unknown }>
}

export interface Finding {
  id: number
  check_id: number
  metric_id: number
  metric_key: string
  metric_name: string | null
  conflict_type: string
  conflict_label: string
  severity: 'high' | 'medium' | 'low'
  severity_label: string
  version_a_id: number
  version_b_id: number
  version_a_no?: number
  version_b_no?: number
  dimensions: string[]
  evidence: FindingEvidence
  impact: {
    affected_metric_count: number
    affected_metrics: { id: number; key: string; name: string; domain: string }[]
    boards: string[]
    board_count: number
  }
  status: string
  status_label: string
  detail: string | null
  created_at: string | null
}

export interface CheckDetail extends CheckBatch {
  findings: Finding[]
}
