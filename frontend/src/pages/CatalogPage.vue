<template>
  <div class="rise">
    <PageHeader
      eyebrow="metric catalog · 口径索引"
      title="指标目录"
      lede="按业务域分组的指标索引卡；每张卡记录负责团队、当前版本的 DSL 五元组和下游看板。"
    >
      <template #actions>
        <router-link class="btn btn-sm" to="/graph">查看依赖图 →</router-link>
        <router-link class="btn btn-sm btn-solid" to="/checks">一致性检查 →</router-link>
      </template>
    </PageHeader>

    <section class="catalog-summary">
      <div class="summary-cell">
        <div class="label">指标总数</div>
        <div class="summary-number num">{{ store.total }}</div>
      </div>
      <div class="summary-cell">
        <div class="label">多版本指标</div>
        <div class="summary-number num">{{ store.multiVersionCount }}</div>
        <div class="hint">同名指标存在不止一版口径</div>
      </div>
      <div class="summary-cell" v-for="domain in domainSummary" :key="domain.value">
        <div class="label">{{ domain.label }}</div>
        <div class="summary-number num">{{ domain.count }}</div>
      </div>
      <div class="summary-note">
        <span class="eyebrow">read me</span>
        <p class="hint mt-1">同名指标三版本以卡片右上角团队区分；打开详情可做五元组比对与影响面导出。</p>
      </div>
    </section>

    <section class="filter-bar">
      <label class="field" style="min-width: 260px; flex: 1">
        <span class="label">搜索（key / 名称 / 描述）</span>
        <input v-model="q" class="input" placeholder="active_users、活跃、留存…" />
      </label>
      <div class="field">
        <span class="label">状态</span>
        <select class="select" :value="store.status" @change="setStatus(($event.target as HTMLSelectElement).value)">
          <option value="">全部状态</option>
          <option value="active">生效</option>
          <option value="draft">草稿</option>
          <option value="deprecated">已下线</option>
        </select>
      </div>
      <div class="domain-tabs">
        <button
          v-for="domain in domains"
          :key="domain.value"
          class="domain-tab"
          :class="{ active: store.domain === domain.value }"
          @click="setDomain(domain.value)"
        >
          {{ domain.label }}<span class="num">{{ store.domainCounts[domain.value] ?? 0 }}</span>
        </button>
      </div>
    </section>

    <LoadingHint v-if="store.loading && !store.items.length" />
    <ErrorNotice :error="store.error" class="mt-2" />

    <template v-if="!store.loading || store.items.length">
      <section v-for="group in store.groups" :key="group.domain" class="metric-group">
        <div class="group-head">
          <div class="row">
            <span class="group-tab">{{ group.label }}</span>
            <span class="faint small">{{ group.items.length }} 个指标</span>
          </div>
          <span class="faint small mono">{{ group.domain }}</span>
        </div>
        <div class="grid-cards">
          <MetricIndexCard v-for="metric in group.items" :key="metric.key" :metric="metric" @select="open" />
        </div>
      </section>
      <EmptyState
        v-if="!store.loading && !store.groups.length"
        title="没有匹配的指标"
        hint="换个关键词，或清空域筛选。索引卡只展示已注册的口径，不会自动发现未登记指标。"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '../components/common/PageHeader.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import EmptyState from '../components/common/EmptyState.vue'
import LoadingHint from '../components/common/LoadingHint.vue'
import MetricIndexCard from '../components/metric/MetricIndexCard.vue'
import { useCatalogFilter } from '../hooks/useCatalogFilter'
import { DOMAINS } from '../constants/domains'
import type { Metric } from '../types/metric'

const router = useRouter()
const { store, q, setDomain, setStatus } = useCatalogFilter()
const domains = DOMAINS

const domainSummary = computed(() =>
  domains.map((domain) => ({ ...domain, count: store.domainCounts[domain.value] ?? 0 })),
)

function open(metric: Metric) {
  router.push(`/metrics/${metric.id}`)
}

onMounted(() => {
  void store.load()
})
</script>

<style scoped>
.catalog-summary {
  display: grid; grid-template-columns: repeat(3, minmax(90px, 130px)) minmax(0, 1.6fr);
  gap: 18px; padding: 16px 18px; border: 1px solid var(--rule); background: var(--paper-raised); margin-bottom: 18px;
}
.summary-cell { border-right: 1px solid var(--rule-soft); padding-right: 14px; }
.summary-cell:last-of-type { border-right: 0; }
.summary-number { font-family: var(--font-display); font-size: 27px; color: var(--ink-strong); line-height: 1.1; }
.filter-bar { display: flex; gap: 14px; align-items: flex-end; flex-wrap: wrap; padding-bottom: 16px; border-bottom: 1px solid var(--rule); margin-bottom: 22px; }
.domain-tabs { display: flex; gap: 2px; flex-wrap: wrap; }
.domain-tab {
  border: 1px solid var(--rule); background: var(--paper-raised); padding: 7px 11px; font-size: 12px; cursor: pointer;
  display: inline-flex; gap: 8px; align-items: baseline; color: var(--ink-soft); border-radius: 1px;
  transition: all 0.2s var(--ease);
}
.domain-tab .num { font-size: 10px; color: var(--ink-faint); }
.domain-tab:hover { border-color: var(--sage); color: var(--ink); }
.domain-tab.active { background: var(--ink-strong); color: var(--paper-raised); border-color: var(--ink-strong); }
.domain-tab.active .num { color: var(--paper-deep); }
.metric-group { margin-bottom: 26px; }
.group-head { display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid var(--rule); margin-bottom: 14px; }
.group-tab { background: var(--vermilion); color: oklch(0.97 0.01 60); font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; padding: 3px 9px; }
@media (max-width: 960px) { .catalog-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } .summary-cell { border-right: 0; } }
</style>
