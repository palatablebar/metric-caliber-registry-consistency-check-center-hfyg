<template>
  <div class="index-card is-flat integrity-card" :class="{ 'is-warn': !isTrusted && isFinished }">
    <div class="row-between">
      <div class="eyebrow">input integrity · 输入核对</div>
      <div class="row" style="gap: 6px">
        <span class="badge" :class="trustBadgeClass">{{ check.trust_label }}</span>
        <span v-if="isFinished" class="badge" :class="check.input_complete ? 'trusted' : 'untrusted'">
          {{ check.input_complete ? '输入完整' : '输入不完整' }}
        </span>
      </div>
    </div>

    <div v-if="isFinished && !check.input_complete" class="warn-banner mt-2">
      <strong>本批次结果不完整，不能当作正常完成发布。</strong>
      <span class="small">
        范围内有 {{ totalMissing }} 个所选版本无法解析、缺失或在检查期间被修改；当前分数与冲突仅基于其余版本计算，仅供参考。
      </span>
    </div>

    <dl class="integrity-facts mt-2">
      <div><dt>冻结时间</dt><dd>{{ inputInfo?.captured_at ?? snapshot.captured_at ?? '—' }}</dd></div>
      <div><dt>检查范围</dt><dd>{{ check.scope_label }}</dd></div>
      <div>
        <dt>所选指标 / 版本 / 依赖边</dt>
        <dd class="num">
          {{ inputInfo?.metric_count ?? snapshot.metric_count ?? check.metrics_checked }} /
          {{ inputInfo?.version_count ?? snapshot.version_count ?? check.versions_checked }} /
          {{ inputInfo?.edge_count ?? snapshot.edge_count ?? 0 }}
        </dd>
      </div>
      <div>
        <dt>输入指纹 SHA-256</dt>
        <dd class="mono fingerprint" :title="fingerprint">{{ fingerprint ? fingerprint.slice(0, 16) + '…' : '—' }}</dd>
      </div>
    </dl>

    <div v-if="missingGroups.length" class="mt-2">
      <div class="label">缺失 / 异常项（{{ totalMissing }}）</div>
      <ul class="clean-list mt-1">
        <li v-for="group in missingGroups" :key="group.title" class="missing-group">
          <span class="chip is-hot">{{ group.title }} × {{ group.items.length }}</span>
          <span v-for="label in group.items" :key="label" class="missing-label mono">{{ label }}</span>
        </li>
      </ul>
    </div>

    <button class="link-button mt-2" @click="showSnapshot = !showSnapshot">
      {{ showSnapshot ? '收起冻结版本清单' : `查看本轮冻结的 ${snapshot.versions?.length ?? 0} 个版本与哈希` }}
    </button>
    <div v-if="showSnapshot" class="snapshot-box mt-1">
      <div class="table-wrap">
        <table class="data snapshot-table">
          <thead>
            <tr><th>指标</th><th class="num">版本</th><th>DSL SHA-256</th><th class="num">字符</th></tr>
          </thead>
          <tbody>
            <tr v-for="version in snapshot.versions ?? []" :key="version.id">
              <td class="mono">{{ version.metric_key }}</td>
              <td class="num">v{{ version.version_no }}</td>
              <td class="mono hash-cell" :title="version.dsl_sha256">{{ version.dsl_sha256.slice(0, 18) }}…</td>
              <td class="num">{{ version.dsl_chars }}</td>
            </tr>
            <tr v-if="!(snapshot.versions?.length)">
              <td colspan="4" class="hint">该批次没有冻结输入（历史批次）。</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="hint mt-1">
        本轮检查只读取上表冻结的版本；检查期间新提交或修改的版本不会混入，需发起新一轮检查才会纳入。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CheckBatch, MissingInputs } from '../../types/check'

const props = defineProps<{ check: CheckBatch }>()

const showSnapshot = ref(false)

const isFinished = computed(() => props.check.status !== 'pending' && props.check.status !== 'running')
const isTrusted = computed(() => props.check.trust_status === 'trusted')
const snapshot = computed(() => props.check.input_snapshot ?? {})
const inputInfo = computed(() => props.check.summary.input)
const fingerprint = computed(
  () => inputInfo.value?.fingerprint ?? (snapshot.value as { fingerprint?: string }).fingerprint ?? '',
)
const trustBadgeClass = computed(() => {
  if (props.check.trust_status === 'trusted') return 'trusted'
  if (props.check.trust_status === 'untrusted') return 'untrusted'
  return 'trust-pending'
})

const missingGroups = computed<{ title: string; items: string[] }[]>(() => {
  const missing: MissingInputs | undefined = inputInfo.value?.missing
  if (!missing) return []
  const groups: { title: string; items: string[] }[] = []
  if (missing.unparseable_labels.length) groups.push({ title: '无法解析版本', items: missing.unparseable_labels })
  if (missing.missing_version_labels.length) groups.push({ title: '版本缺失', items: missing.missing_version_labels })
  if (missing.changed_version_labels.length) groups.push({ title: '期间被修改', items: missing.changed_version_labels })
  if (missing.missing_metric_keys.length) groups.push({ title: '指标缺失', items: missing.missing_metric_keys })
  return groups
})

const totalMissing = computed(() => missingGroups.value.reduce((sum, group) => sum + group.items.length, 0))
</script>

<style scoped>
.integrity-card { border-left-color: var(--gold); }
.integrity-card.is-warn { border-left-color: var(--vermilion); }
.warn-banner {
  display: flex; flex-direction: column; gap: 4px;
  border-left: 3px solid var(--vermilion); background: var(--vermilion-wash);
  padding: 9px 12px; color: var(--vermilion-deep);
}
.integrity-facts {
  margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 5px 18px; font-size: 11.5px;
}
.integrity-facts > div {
  display: flex; justify-content: space-between; gap: 8px;
  border-bottom: 1px dotted var(--rule-soft); padding-bottom: 3px;
}
.integrity-facts dt { color: var(--ink-faint); }
.integrity-facts dd { margin: 0; color: var(--ink); text-align: right; }
.fingerprint { max-width: 150px; overflow: hidden; text-overflow: ellipsis; }
.clean-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.missing-group { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.missing-label { font-size: 11px; color: var(--vermilion-deep); }
.link-button {
  background: none; border: 0; padding: 0; color: var(--ink); cursor: pointer;
  font-size: 11.5px; text-decoration: underline; text-underline-offset: 3px;
}
.snapshot-box { border: 1px solid var(--rule-soft); background: var(--paper-deep); padding: 8px; }
.snapshot-table td, .snapshot-table th { font-size: 11px; padding: 6px 8px; }
.hash-cell { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
