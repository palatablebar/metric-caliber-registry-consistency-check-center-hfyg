<template>
  <div class="rise">
    <div class="row-between mt-1">
      <router-link class="back-link" to="/catalog">← 返回指标目录</router-link>
      <div class="row">
        <router-link v-if="metric" class="btn btn-sm" :to="`/metrics/${metric.id}/dsl`">打开 DSL 编辑器</router-link>
        <router-link class="btn btn-sm" to="/graph">依赖图</router-link>
      </div>
    </div>

    <LoadingHint v-if="loading" />
    <ErrorNotice :error="error" class="mt-2" />

    <template v-if="metric">
      <header class="detail-head mt-3">
        <div>
          <div class="eyebrow">{{ metric.domain_label }} · {{ metric.owner_team.name }}</div>
          <div class="row mt-1" style="align-items: baseline">
            <h1 class="display">{{ metric.name }}</h1>
            <span class="mono card-key">{{ metric.key }}</span>
            <StatusBadge :status="metric.status" :label="metric.status_label" />
          </div>
          <p class="lede mt-2">{{ metric.description }}</p>
        </div>
        <div class="detail-badges">
          <div class="chip"><b>versions</b>{{ metric.version_count }}</div>
          <div class="chip"><b>teams</b>{{ metric.team_count }}</div>
          <div class="chip"><b>boards</b>{{ metric.consumers.length }}</div>
        </div>
      </header>

      <div class="grid-2 mt-3">
        <section>
          <SectionHeading eyebrow="version history" title="版本历史与口径五元组" />
          <VersionTimeline :versions="metric.versions" />
        </section>

        <aside class="stack">
          <section class="index-card is-flat">
            <div class="eyebrow">current caliber</div>
            <h3 class="card-title mt-1">当前生效口径</h3>
            <div class="mt-2">
              <TupleChips v-if="metric.current_version" :tuple="metric.current_version.tuple" />
            </div>
            <div class="card-rule"></div>
            <div class="small muted">提交人 {{ metric.current_version?.created_by ?? '—' }} · {{ metric.current_version?.effective_from ?? '—' }}</div>
            <div class="card-rule"></div>
            <div class="label">下游看板</div>
            <div class="row mt-1" style="flex-wrap: wrap; gap: 6px">
              <span v-for="board in metric.consumers" :key="board" class="chip">{{ board }}</span>
              <span v-if="!metric.consumers.length" class="hint">暂无登记消费方</span>
            </div>
          </section>

          <section class="index-card is-flat">
            <div class="eyebrow">dependency</div>
            <h3 class="card-title mt-1">依赖关系</h3>
            <div class="dep-block mt-2">
              <div class="label">上游依赖（本指标依赖）</div>
              <ul class="clean-list mt-1">
                <li v-for="ref in metric.dependencies.upstream" :key="ref.edge_id">
                  <router-link class="dep-link mono small" :to="`/metrics/${ref.id}`">{{ ref.key }}</router-link>
                  <span class="faint small"> {{ ref.name }}</span>
                </li>
                <li v-for="table in metric.dependencies.tables" :key="table.edge_id" class="small faint">
                  物理表 {{ table.table }}
                </li>
                <li v-if="!metric.dependencies.upstream.length && !metric.dependencies.tables.length" class="hint">无上游依赖</li>
              </ul>
            </div>
            <div class="dep-block mt-2">
              <div class="label">下游消费（谁依赖本指标）</div>
              <ul class="clean-list mt-1">
                <li v-for="ref in metric.dependencies.downstream" :key="ref.edge_id">
                  <router-link class="dep-link mono small" :to="`/metrics/${ref.id}`">{{ ref.key }}</router-link>
                  <span class="faint small"> {{ ref.name }}</span>
                </li>
                <li v-if="!metric.dependencies.downstream.length" class="hint">没有指标依赖它（可能是孤儿指标）</li>
              </ul>
            </div>
          </section>

          <ImpactPanel :impact="impact" :loading="impactLoading" title="口径变更影响面" />
        </aside>
      </div>

      <section class="mt-4">
        <SectionHeading eyebrow="five-tuple compare" title="三版本口径对比（后端计算）">
          <template #actions>
            <button class="btn btn-sm" :disabled="impactLoading" @click="loadImpact">刷新影响面</button>
          </template>
        </SectionHeading>
        <VersionCompareTable
          :versions="metric.versions"
          v-model:versionA="versionA"
          v-model:versionB="versionB"
          :compare="compare"
          :loading="compareLoading"
          @compare="runCompare"
        />
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import SectionHeading from '../components/common/SectionHeading.vue'
import LoadingHint from '../components/common/LoadingHint.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import TupleChips from '../components/metric/TupleChips.vue'
import VersionTimeline from '../components/metric/VersionTimeline.vue'
import VersionCompareTable from '../components/metric/VersionCompareTable.vue'
import ImpactPanel from '../components/dependency/ImpactPanel.vue'
import { fetchMetric, compareVersions } from '../api/metric'
import { fetchImpact } from '../api/dependency'
import type { MetricDetail, VersionCompare } from '../types/metric'
import type { ImpactPayload } from '../types/dependency'
import type { ApiError } from '../types/api'

const route = useRoute()
const metric = ref<MetricDetail | null>(null)
const loading = ref(false)
const error = ref<ApiError | null>(null)

const versionA = ref(0)
const versionB = ref(0)
const compare = ref<VersionCompare | null>(null)
const compareLoading = ref(false)

const impact = ref<ImpactPayload | null>(null)
const impactLoading = ref(false)

const metricId = computed(() => Number(route.params.id))

async function loadMetric() {
  loading.value = true
  error.value = null
  try {
    metric.value = await fetchMetric(metricId.value)
    const versions = metric.value.versions
    if (versions.length >= 2) {
      versionA.value = versions[0].id
      versionB.value = versions[versions.length - 1].id
      await runCompare()
    }
  } catch (err) {
    error.value = err as ApiError
  } finally {
    loading.value = false
  }
}

async function runCompare() {
  if (!versionA.value || !versionB.value || !metric.value) return
  compareLoading.value = true
  try {
    compare.value = (await compareVersions(metric.value.id, versionA.value, versionB.value)) as unknown as VersionCompare
  } catch (err) {
    error.value = err as ApiError
  } finally {
    compareLoading.value = false
  }
}

async function loadImpact() {
  if (!metric.value) return
  impactLoading.value = true
  try {
    impact.value = await fetchImpact(metric.value.id)
  } catch (err) {
    error.value = err as ApiError
  } finally {
    impactLoading.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    if (route.name === 'metric-detail') void loadMetric()
  },
)

onMounted(async () => {
  await loadMetric()
  await loadImpact()
})
</script>

<style scoped>
.back-link { font-size: 11.5px; color: var(--ink-soft); text-decoration: underline; text-underline-offset: 3px; }
.detail-head { display: flex; justify-content: space-between; gap: 22px; align-items: flex-start; border-bottom: 1px solid var(--rule); padding-bottom: 18px; flex-wrap: wrap; }
.detail-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.dep-block + .dep-block { border-top: 1px dashed var(--rule); padding-top: 10px; }
.clean-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.dep-link { color: var(--vermilion-deep); text-decoration: underline; text-underline-offset: 3px; }
</style>
