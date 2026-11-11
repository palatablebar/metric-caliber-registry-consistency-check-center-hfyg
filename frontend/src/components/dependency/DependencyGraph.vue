<template>
  <div class="graph-wrap">
    <svg v-if="layout" :viewBox="`0 0 ${layout.width} ${layout.height}`" class="graph-svg" role="img" aria-label="指标依赖图">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink-soft)" />
        </marker>
        <marker id="arrow-cycle" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--vermilion)" />
        </marker>
      </defs>

      <g class="layer-labels">
        <text v-for="layer in layout.layerLabels" :key="layer" :x="layer.x" y="16" class="layer-text">
          L{{ layer.index }}
        </text>
      </g>

      <g class="edges">
        <path
          v-for="edge in layout.edges"
          :key="`${edge.from_id}-${edge.to_id}`"
          :d="edge.path"
          :class="['edge', { 'is-cycle': edge.in_cycle }]"
          :marker-end="edge.in_cycle ? 'url(#arrow-cycle)' : 'url(#arrow)'"
        />
      </g>

      <g
        v-for="node in layout.nodes"
        :key="node.id"
        class="node"
        :class="{ 'is-selected': selectedKey === node.key, 'is-cycle': node.in_cycle, 'is-orphan': node.is_orphan }"
        :transform="`translate(${node.x}, ${node.y})`"
        @click="$emit('select', node)"
      >
        <rect class="node-card" :width="nodeWidth" :height="nodeHeight" rx="2" />
        <rect class="node-bar" :width="4" :height="nodeHeight" :fill="domainColor(node.domain)" />
        <text class="node-key" x="12" y="20">{{ node.key }}</text>
        <text class="node-name" x="12" y="38">{{ node.name }}</text>
        <text v-if="node.in_cycle" class="node-flag" :x="nodeWidth - 26" y="20">环</text>
        <text v-else-if="node.is_orphan" class="node-flag orphan" :x="nodeWidth - 34" y="20">孤儿</text>
      </g>
    </svg>
    <div v-else class="hint">暂无依赖图数据。</div>

    <div v-if="layout" class="graph-legend">
      <span class="legend-item"><i class="dot normal"></i>普通依赖（箭头指向被依赖指标）</span>
      <span class="legend-item"><i class="dot cycle"></i>环依赖</span>
      <span class="legend-item"><i class="dot orphan"></i>孤儿指标（无下游消费）</span>
      <span class="legend-item faint">层号 L0 为最底层依赖</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { GraphNode, GraphPayload } from '../../types/dependency'
import { domainColor } from '../../utils/severityTone'

const props = defineProps<{ graph: GraphPayload | null; selectedKey: string | null }>()
defineEmits<{ select: [node: GraphNode] }>()

const nodeWidth = 172
const nodeHeight = 54
const colWidth = 214
const rowHeight = 78
const padX = 30
const padY = 28

const layout = computed(() => {
  const graph = props.graph
  if (!graph || !graph.nodes.length) return null
  const byLayer = new Map<number, GraphNode[]>()
  for (const node of graph.nodes) {
    if (!byLayer.has(node.layer)) byLayer.set(node.layer, [])
    byLayer.get(node.layer)!.push(node)
  }
  const positions = new Map<number, { x: number; y: number }>()
  let maxRows = 1
  for (const [, nodes] of [...byLayer.entries()].sort((a, b) => a[0] - b[0])) {
    nodes.sort((a, b) => a.key.localeCompare(b.key))
    maxRows = Math.max(maxRows, nodes.length)
    nodes.forEach((node, index) => {
      positions.set(node.id, { x: padX + node.layer * colWidth, y: padY + index * rowHeight })
    })
  }
  const maxLayer = Math.max(...byLayer.keys())
  const width = padX * 2 + maxLayer * colWidth + nodeWidth
  const height = padY * 2 + maxRows * rowHeight

  const edges = graph.edges.map((edge) => {
    const source = positions.get(edge.from_id)!
    const target = positions.get(edge.to_id)!
    const sx = source.x
    const sy = source.y + nodeHeight / 2
    const tx = target.x + nodeWidth
    const ty = target.y + nodeHeight / 2
    return {
      ...edge,
      path: `M ${sx} ${sy} C ${sx - 70} ${sy}, ${tx + 70} ${ty}, ${tx} ${ty}`,
    }
  })

  const nodes = graph.nodes.map((node) => ({ ...node, ...positions.get(node.id)! }))
  const layerLabels = [...byLayer.keys()].sort((a, b) => a - b).map((index) => ({ index, x: padX + index * colWidth }))
  return { nodes, edges, width: Math.max(width, 640), height: Math.max(height, 300), layerLabels }
})
</script>

<style scoped>
.graph-wrap { border: 1px solid var(--rule); background: var(--paper-raised); padding: 10px 12px 8px; overflow: auto; }
.graph-svg { width: 100%; min-width: 620px; display: block; }
.layer-text { font-size: 9px; letter-spacing: 0.16em; fill: var(--ink-faint); text-transform: uppercase; }
.edge { fill: none; stroke: var(--ink-faint); stroke-width: 1.1; opacity: 0.85; }
.edge.is-cycle { stroke: var(--vermilion); stroke-width: 1.6; stroke-dasharray: 5 4; }
.node { cursor: pointer; }
.node-card { fill: var(--paper-raised); stroke: var(--rule); stroke-width: 1; transition: stroke 0.2s var(--ease); }
.node-bar { opacity: 0.9; }
.node-key { font-family: var(--font-body); font-size: 11px; fill: var(--ink-strong); font-weight: 500; }
.node-name { font-family: var(--font-body); font-size: 10px; fill: var(--ink-soft); }
.node-flag { font-size: 9px; fill: var(--vermilion-deep); text-anchor: end; }
.node-flag.orphan { fill: var(--ink-faint); }
.node:hover .node-card, .node.is-selected .node-card { stroke: var(--ink); stroke-width: 1.6; }
.node.is-cycle .node-card { stroke: var(--vermilion); stroke-dasharray: 4 3; }
.node.is-orphan .node-card { stroke-dasharray: 2 3; }
.graph-legend { display: flex; gap: 18px; flex-wrap: wrap; margin-top: 8px; font-size: 10.5px; color: var(--ink-soft); }
.legend-item { display: inline-flex; align-items: center; gap: 5px; }
.dot { width: 12px; height: 2px; display: inline-block; background: var(--ink-faint); }
.dot.cycle { background: var(--vermilion); }
.dot.orphan { background: repeating-linear-gradient(90deg, var(--ink-faint) 0 3px, transparent 3px 5px); }
</style>
