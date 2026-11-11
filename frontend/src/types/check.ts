export type CheckStatus = 'pending' | 'running' | 'completed' | 'incomplete' | 'failed'
export type TrustStatus = 'trusted' | 'untrusted' | 'pending'

export interface MissingInputs {
  metrics: { metric_id: number; metric_key: string; reason: string }[]
  versions_missing: {
    metric_id: number
    metric_key: string
    version_id: number
    version_no: number
    reason: string
  }[]
  versions_changed: {
    metric_id: number
    metric_key: string
    version_id: number
    version_no: number
    reason: string
    expected_sha256?: string
    actual_sha256?: string
  }[]
  unparseable_versions: {
    metric_key: string
    version_no: number
    error: string
    offset: number
    kind: string
  }[]
  missing_metric_keys: string[]
  missing_version_labels: string[]
  changed_version_labels: string[]
  unparseable_labels: string[]
}

export interface CheckInputInfo {
  complete: boolean
  trust_status: TrustStatus
  fingerprint: string
  captured_at: string | null
  scope: string
  metric_count: number
  version_count: number
  edge_count: number
  missing: MissingInputs
}

export interface InputSnapshotVersion {
  id: number
  metric_id: number
  metric_key: string
  version_no: number
  team_id: number
  dsl_sha256: string
  dsl_chars: number
  created_at: string | null
}

export interface InputSnapshot {
  snapshot_version: number
  scope: string
  captured_at: string | null
  metric_count: number
  version_count: number
  edge_count: number
  fingerprint: string
  metrics: {
    id: number
    key: string
    name: string
    domain: string
    status: string
    team_id: number
    consumers: string[]
    version_ids: number[]
  }[]
  versions: InputSnapshotVersion[]
  edges: { from_metric_id: number; to_metric_id: number; relation: string }[]
}

export interface CheckSummary {
  score: number
  score_partial?: boolean
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
  parse_failed: { metric_key: string; version_no: number; error: string; offset: number; kind?: string }[]
  findings_by_dimension: Record<string, number>
  input?: CheckInputInfo
}

export interface CheckBatch {
  id: number
  batch_no: string
  scope: string
  scope_label: string
  status: CheckStatus
  status_label: string
  trust_status: TrustStatus
  trust_label: string
  input_complete: boolean
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
  input_snapshot: InputSnapshot | Record<string, never>
  error_message: string | null
  created_at: string | null
  task_id?: string | null
}

export interface CheckListResponse {
  items: CheckBatch[]
  total: number
  latest_trusted: CheckBatch | null
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
  latest_trusted?: CheckBatch | null
}
