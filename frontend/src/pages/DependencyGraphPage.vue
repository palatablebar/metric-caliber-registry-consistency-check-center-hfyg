<template>
  <div class="rise">
    <PageHeader
      eyebrow="dependency graph · 拓扑与环"
      title="指标依赖图"
      lede="后端用 Kahn 拓扑排序、Tarjan 强连通分量与孤儿检测计算出的依赖结构；前端手写 SVG 分层布局，不依赖图库。"
    >
      <template #actions>
        <button class="btn btn-sm" @click="load">重新计算</button>
        <router-link class="btn btn-sm btn-solid" to="/checks">去一致性检查 →</router-link>
      </template>
    </PageHeader>

    <LoadingHint v-if="loading" />
    <ErrorNotice :error="error" class="mt-2" />

    <template v-if="graph">
      <section class="graph-stats">
        <div class="stat"><span class="label">指标节点</span><span class="num">{{ graph.stats.node_count }}</span></div>
        <div class="stat"><span class="label">依赖边</span><span class="num">{{ graph.stats.edge_count }}</span></div>
        <div class="stat" :class="{ warn: graph.stats.cycle_count > 0 }">
          <span class="label">环依赖</span><span class="num">{{ graph.stats.cycle_count }}</span>
        </div>
        <div class="stat" :class="{ warn: graph.stats.orphan_count > 0 }">
          <span class="label">孤儿指标</span><span class="num">{{ graph.stats.orphan_count }}</span>
        </div>
        <div class="stat"><span class="label">最大层深</span><span class="num">{{ graph.stats.max_layer }}</span></div>
        <div class="stat"><span class="label">环内指标</span><span class="num">{{ graph.stats.cyclic_metric_count }}</span></div>
      </section>

      <div class="graph-grid mt-3">
        <section>
          <SectionHeading eyebrow="layered svg" title="依赖图（点击节点查看影响面）" />
          <DependencyGraph :graph="graph" :selected-key="selected?.key ?? null" @select="selectNode" />
          <div class="mt-2 hint">
            拓扑序（DAG 部分，依赖在前）：<span class="mono">{{ graph.topological_order.join(' → ') }}</span>
          </div>
        </section>

        <aside class="stack">
          <ImpactPanel :impact="impact" :loading="impactLoading" :title="selected ? `影响面 · ${selected.key}` : '影响面'" />

          <section class="index-card is-flat">
            <div class="eyebrow">cycles</div>
            <h3 class="card-title mt-1">环依赖（Tarjan SCC）</h3>
            <div v-for="cycle in graph.cycles" :key="cycle.member_keys.join('-')" class="cycle-row">
              <div class="row-between">
                <span class="badge high">{{ cycle.size }} 节点环</span>
                <span class="faint small mono">{{ cycle.member_keys.join(' / ') }}</span>
              </div>
              <div class="cycle-path mono mt-1">{{ cycle.path_keys.join(' → ') }}</div>
            </div>
            <p v-if="!graph.cycles.length" class="hint mt-1">没有检测到环依赖。</p>
          </section>

          <section class="index-card is-flat">
            <div class="eyebrow">orphans</div>
            <h3 class="card-title mt-1">孤儿指标（无下游消费）</h3>
            <ul class="clean-list mt-1">
              <li v-for="node in graph.orphan_nodes" :key="node.id">
                <router-link class="dep-link mono small" :to="`/metrics/${node.id}`">{{ node.key }}</router-link>
                <span class="faint small"> {{ node.name }}</span>
              </li>
              <li v-if="!graph.orphan_nodes.length" class="hint">没有孤儿指标。</li>
            </ul>
          </section>

          <section class="index-card is-flat">
            <div class="eyebrow">physical tables</div>
            <h3 class="card-title mt-1">物理表依赖</h3>
            <ul class="clean-list mt-1">
              <li v-for="edge in graph.table_edges" :key="`${edge.from_id}-${edge.to_table}`" class="small">
                <span class="mono">{{ metricKey(edge.from_id) }}</span> → {{ edge.to_table }}
              </li>
              <li v-if="!graph.table_edges.length" class="hint">暂未登记物理表依赖。</li>
            </ul>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '../components/common/PageHeader.vue'
import SectionHeading from '../components/common/SectionHeading.vue'
import LoadingHint from '../components/common/LoadingHint.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import DependencyGraph from '../components/dependency/DependencyGraph.vue'
import ImpactPanel from '../components/dependency/ImpactPanel.vue'
import { fetchGraph } from '../api/dependency'
import { fetchImpact } from '../api/dependency'
import type { GraphNode, GraphPayload } from '../types/dependency'
import type { ImpactPayload } from '../types/dependency'
import type { ApiError } from '../types/api'

const graph = ref<GraphPayload | null>(null)
const loading = ref(false)
const error = ref<ApiError | null>(null)
const selected = ref<GraphNode | null>(null)
const impact = ref<ImpactPayload | null>(null)
const impactLoading = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    graph.value = await fetchGraph()
    if (!selected.value && graph.value.nodes.length) {
      await selectNode(graph.value.nodes.find((node) => node.in_cycle) ?? graph.value.nodes[0])
    }
  } catch (err) {
    error.value = err as ApiError
  } finally {
    loading.value = false
  }
}

async function selectNode(node: GraphNode) {
  selected.value = node
  impactLoading.value = true
  try {
    impact.value = await fetchImpact(node.id)
  } catch (err) {
    error.value = err as ApiError
  } finally {
    impactLoading.value = false
  }
}

function metricKey(id: number): string {
  return graph.value?.nodes.find((node) => node.id === id)?.key ?? String(id)
}

onMounted(() => void load())
</script>

<style scoped>
.graph-stats { display: flex; flex-wrap: wrap; gap: 0; border: 1px solid var(--rule); background: var(--paper-raised); }
.stat { display: flex; flex-direction: column; gap: 2px; padding: 10px 18px; border-right: 1px solid var(--rule-soft); min-width: 104px; }
.stat:last-child { border-right: 0; }
.stat .num { font-family: var(--font-display); font-size: 22px; color: var(--ink-strong); }
.stat.warn .num { color: var(--vermilion-deep); }
.graph-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr); gap: 26px; align-items: start; }
.cycle-row { border-top: 1px dashed var(--rule); padding-top: 9px; margin-top: 9px; }
.cycle-row:first-of-type { border-top: 0; margin-top: 6px; padding-top: 0; }
.cycle-path { font-size: 11.5px; color: var(--vermilion-deep); }
.clean-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 3px; }
.dep-link { color: var(--vermilion-deep); text-decoration: underline; text-underline-offset: 3px; }
@media (max-width: 1080px) { .graph-grid { grid-template-columns: 1fr; } }
</style>
