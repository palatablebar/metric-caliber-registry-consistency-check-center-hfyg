import type { DomainKey, MetricStatus } from './metric'

export interface GraphNode {
  id: number
  key: string
  name: string
  domain: DomainKey
  status: MetricStatus
  consumers: string[]
  layer: number
  in_cycle: boolean
  is_orphan: boolean
  dependency_count: number
  dependent_count: number
  team_code: string | null
  team_name: string | null
}

export interface GraphEdge {
  from_id: number
  to_id: number
  from_key: string
  to_key: string
  relation: string
  note: string | null
  in_cycle: boolean
}

export interface CycleInfo {
  members: number[]
  member_keys: string[]
  path: number[]
  path_keys: string[]
  size: number
}

export interface GraphPayload {
  nodes: GraphNode[]
  edges: GraphEdge[]
  cycles: CycleInfo[]
  orphans: string[]
  orphan_nodes: { id: number; key: string; name: string }[]
  topological_order: string[]
  unresolved_cycle_keys: string[]
  layers: Record<string, number>
  stats: {
    node_count: number
    edge_count: number
    cycle_count: number
    orphan_count: number
    max_layer: number
    cyclic_metric_count: number
  }
  table_edges: { from_id: number; to_table: string; relation: string; note: string | null }[]
}

export interface ImpactPayload {
  metric_id: number
  metric_key: string
  metric_name?: string
  domain?: string
  affected_metric_count: number
  affected_metrics: { id: number; key: string; name: string; domain: string }[]
  boards: string[]
  board_count: number
}
