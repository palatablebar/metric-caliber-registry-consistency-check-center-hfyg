<template>
  <div class="rise">
    <PageHeader
      eyebrow="consistency checks · 口径巡检"
      title="一致性检查与冲突"
      lede="检查批次由后端发起、Celery worker 重新解析全部 DSL 并落库；分数、环、孤儿与影响面都由 Python 算法计算。"
    >
      <template #actions>
        <button class="btn btn-sm btn-solid" :disabled="store.running" @click="runCheck">
          {{ store.running ? '检查中…' : '运行一致性检查' }}
        </button>
        <button class="btn btn-sm" :disabled="!store.detail" @click="downloadCsv">导出影响面 CSV</button>
      </template>
    </PageHeader>

    <ErrorNotice :error="store.error" class="mt-2" />

    <div v-if="store.loading && !store.batches.length"><LoadingHint text="读取检查批次…" /></div>

    <div class="checks-grid" v-if="store.detail">
      <aside class="batch-rail">
        <div class="eyebrow">batches</div>
        <button
          v-for="batch in store.batches"
          :key="batch.id"
          class="batch-item"
          :class="{ active: store.detail && store.detail.id === batch.id }"
          @click="selectBatch(batch.id)"
        >
          <div class="row-between">
            <span class="mono small">{{ batch.batch_no }}</span>
            <StatusBadge :status="batch.status" :label="batch.status_label" />
          </div>
          <div class="small faint mt-1">
            {{ batch.scope_label }} · 分数 {{ batch.consistency_score }} · {{ batch.conflict_count }} 条冲突
          </div>
        </button>
        <EmptyState v-if="!store.batches.length" title="还没有检查批次" hint="点击「运行一致性检查」发起第一轮巡检。" />
      </aside>

      <section class="stack">
        <div class="grid-summary">
          <ScoreGauge :score="store.detail.consistency_score" />
          <div class="index-card is-flat summary-card">
            <div class="eyebrow">batch summary</div>
            <div class="row-between mt-1">
              <h3 class="card-title">{{ store.detail.batch_no }}</h3>
              <StatusBadge :status="store.detail.status" :label="store.detail.status_label" />
            </div>
            <div class="card-rule"></div>
            <dl class="summary-facts">
              <div><dt>范围</dt><dd>{{ store.detail.scope_label }}</dd></div>
              <div><dt>触发人</dt><dd>{{ store.detail.triggered_by ?? '—' }}</dd></div>
              <div><dt>指标 / 版本</dt><dd class="num">{{ store.detail.metrics_checked }} / {{ store.detail.versions_checked }}</dd></div>
              <div><dt>冲突 / high</dt><dd class="num">{{ store.detail.conflict_count }} / {{ store.detail.high_count }}</dd></div>
              <div><dt>耗时</dt><dd class="num">{{ store.detail.duration_ms ?? '—' }} ms</dd></div>
              <div><dt>完成时间</dt><dd>{{ formatDateTime(store.detail.finished_at) }}</dd></div>
            </dl>
            <div class="card-rule"></div>
            <div class="row" style="flex-wrap: wrap; gap: 6px">
              <span class="label">finding 维度：</span>
              <span v-for="(count, dimension) in store.detail.summary.findings_by_dimension" :key="dimension" class="chip">
                {{ dimension }} × {{ count }}
              </span>
            </div>
          </div>
        </div>

        <section>
          <SectionHeading eyebrow="findings" title="冲突明细（五元组差异）">
            <template #actions>
              <span class="faint small">按严重度排序 · 点击影响面展开</span>
            </template>
          </SectionHeading>
          <ConflictTable
            :findings="store.detail.findings"
            :can-triage="auth.isAdmin"
            @triage="triage"
          />
        </section>

        <section class="grid-two-panels">
          <div class="index-card is-flat">
            <div class="eyebrow">cycles · orphans</div>
            <h3 class="card-title mt-1">同批次结构问题</h3>
            <div class="mt-2">
              <div class="label">环依赖</div>
              <ul class="clean-list mt-1">
                <li v-for="cycle in store.detail.summary.cycles" :key="cycle.member_keys.join('-')" class="small">
                  <span class="mono" style="color: var(--vermilion-deep)">{{ cycle.path_keys.join(' → ') }}</span>
                </li>
                <li v-if="!store.detail.summary.cycles?.length" class="hint">无</li>
              </ul>
            </div>
            <div class="mt-2">
              <div class="label">孤儿指标</div>
              <div class="row mt-1" style="gap: 6px; flex-wrap: wrap">
                <span v-for="orphan in store.detail.summary.orphans" :key="orphan" class="chip">{{ orphan }}</span>
                <span v-if="!store.detail.summary.orphans?.length" class="hint">无</span>
              </div>
            </div>
            <div class="mt-2" v-if="store.detail.summary.parse_failed?.length">
              <div class="label">解析失败版本</div>
              <ul class="clean-list mt-1">
                <li v-for="item in store.detail.summary.parse_failed" :key="`${item.metric_key}-${item.version_no}`" class="small">
                  {{ item.metric_key }} v{{ item.version_no }}：{{ item.error }}
                </li>
              </ul>
            </div>
          </div>

          <div class="index-card is-flat">
            <div class="eyebrow">metric scores</div>
            <h3 class="card-title mt-1">多版本指标分数</h3>
            <div class="table-wrap mt-2">
              <table class="data">
                <thead><tr><th>指标</th><th class="num">一致性</th></tr></thead>
                <tbody>
                  <tr v-for="(score, key) in store.detail.summary.metric_scores" :key="key">
                    <td class="mono">{{ key }}</td>
                    <td class="num">{{ score }}</td>
                  </tr>
                  <tr v-if="!Object.keys(store.detail.summary.metric_scores ?? {}).length">
                    <td colspan="2" class="hint">没有多版本指标</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="hint mt-2">
              分数 = 100 × (1 − Σ各对差异加权 / (对比对数 × 12))；grain/filter/agg 权重 3，window 2，measure 1。
            </p>
          </div>
        </section>
      </section>
    </div>

    <EmptyState v-else-if="!store.loading" title="还没有检查结果" hint="点击右上角发起一次一致性检查。" />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import PageHeader from '../components/common/PageHeader.vue'
import SectionHeading from '../components/common/SectionHeading.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import LoadingHint from '../components/common/LoadingHint.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ScoreGauge from '../components/check/ScoreGauge.vue'
import ConflictTable from '../components/check/ConflictTable.vue'
import { useCheckStore } from '../stores/checkStore'
import { useAuthStore } from '../stores/authStore'
import { downloadImpactCsv, triageFinding } from '../api/check'
import { formatDateTime } from '../utils/formatters'
import type { ApiError } from '../types/api'

const store = useCheckStore()
const auth = useAuthStore()

onMounted(() => void store.loadBatches())

async function runCheck() {
  await store.runCheck('all')
}

async function selectBatch(checkId: number) {
  await store.loadDetail(checkId)
}

async function triage(findingId: number, status: string) {
  try {
    await triageFinding(findingId, status)
    if (store.detail) await store.loadDetail(store.detail.id)
  } catch (error) {
    store.error = error as ApiError
  }
}

async function downloadCsv() {
  if (!store.detail) return
  try {
    await downloadImpactCsv(store.detail.id, store.detail.batch_no)
  } catch (error) {
    store.error = error as ApiError
  }
}
</script>

<style scoped>
.checks-grid { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 26px; align-items: start; }
.batch-rail { display: flex; flex-direction: column; gap: 4px; border-right: 1px solid var(--rule); padding-right: 16px; }
.batch-item {
  text-align: left; border: 1px solid transparent; border-left: 3px solid var(--rule);
  background: transparent; padding: 9px 10px; cursor: pointer;
  transition: all 0.2s var(--ease);
}
.batch-item:hover { background: var(--paper-raised); border-left-color: var(--sage); }
.batch-item.active { background: var(--paper-raised); border-left-color: var(--vermilion); border-color: var(--rule); }
.grid-summary { display: grid; grid-template-columns: minmax(200px, 0.7fr) minmax(0, 1.3fr); gap: 16px; }
.summary-facts { margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 5px 18px; font-size: 11.5px; }
.summary-facts > div { display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px dotted var(--rule-soft); padding-bottom: 3px; }
.summary-facts dt { color: var(--ink-faint); }
.summary-facts dd { margin: 0; color: var(--ink); text-align: right; }
.grid-two-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.clean-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
@media (max-width: 1000px) {
  .checks-grid { grid-template-columns: 1fr; }
  .batch-rail { border-right: 0; padding-right: 0; }
  .grid-summary, .grid-two-panels { grid-template-columns: 1fr; }
}
</style>
