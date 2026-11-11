<template>
  <div class="compare">
    <div class="field-row">
      <label class="field" style="min-width: 160px">
        <span class="label">版本 A</span>
        <select class="select" :value="versionA" @change="$emit('update:versionA', Number(($event.target as HTMLSelectElement).value))">
          <option v-for="version in versions" :key="version.id" :value="version.id">
            v{{ version.version_no }} · {{ version.team_name ?? '—' }}
          </option>
        </select>
      </label>
      <label class="field" style="min-width: 160px">
        <span class="label">版本 B</span>
        <select class="select" :value="versionB" @change="$emit('update:versionB', Number(($event.target as HTMLSelectElement).value))">
          <option v-for="version in versions" :key="version.id" :value="version.id">
            v{{ version.version_no }} · {{ version.team_name ?? '—' }}
          </option>
        </select>
      </label>
      <button class="btn btn-sm" :disabled="loading || !versionA || !versionB" @click="$emit('compare')">
        {{ loading ? '比对中…' : '后端比对五元组' }}
      </button>
    </div>

    <div v-if="compare" class="mt-3">
      <div class="row-between">
        <span class="label">差异判定</span>
        <SeverityBadge v-if="compare.severity" :severity="compare.severity" />
        <span v-else class="badge active">口径一致</span>
      </div>
      <p class="hint mt-1">{{ compare.summary }}</p>
      <div class="table-wrap mt-2">
        <table class="data">
          <thead>
            <tr><th>维度</th><th>版本 A</th><th>版本 B</th><th>是否冲突</th></tr>
          </thead>
          <tbody>
            <tr v-for="field in compareFields" :key="field.key">
              <td>{{ field.label }}</td>
              <td class="mono">{{ format(field.key, compare.tuple_a) }}</td>
              <td class="mono">{{ format(field.key, compare.tuple_b) }}</td>
              <td>
                <span :class="compare.dimensions.includes(field.dim) ? 'badge high' : 'badge active'">
                  {{ compare.dimensions.includes(field.dim) ? '不一致' : '一致' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-else class="hint mt-3">选择两个版本后由后端计算差异维度与严重度（不在浏览器里硬编码）。</div>
  </div>
</template>

<script setup lang="ts">
import type { MetricVersion, Tuple, VersionCompare } from '../../types/metric'
import SeverityBadge from '../common/SeverityBadge.vue'

defineProps<{
  versions: MetricVersion[]
  versionA: number
  versionB: number
  compare: VersionCompare | null
  loading: boolean
}>()

defineEmits<{
  'update:versionA': [value: number]
  'update:versionB': [value: number]
  compare: []
}>()

const compareFields = [
  { key: 'agg', dim: 'agg', label: '聚合函数 agg' },
  { key: 'measure', dim: 'measure', label: '度量字段 measure' },
  { key: 'filters', dim: 'filter', label: '过滤集合 filter' },
  { key: 'window', dim: 'window', label: '时间窗口 window' },
  { key: 'grain', dim: 'grain', label: '时间粒度 grain' },
] as const

function format(field: string, tuple: Tuple): string {
  const value = tuple[field as keyof Tuple]
  return Array.isArray(value) ? value.join(' / ') || '无' : String(value ?? '—')
}
</script>
