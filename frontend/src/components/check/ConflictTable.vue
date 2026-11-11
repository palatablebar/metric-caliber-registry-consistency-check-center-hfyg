<template>
  <div class="table-wrap">
    <table class="data conflict-table">
      <thead>
        <tr>
          <th>严重度</th>
          <th>指标 / 版本</th>
          <th>冲突类型</th>
          <th>差异维度</th>
          <th>影响面</th>
          <th>状态</th>
          <th v-if="canTriage" class="text-right">处理</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="finding in findings" :key="finding.id">
          <tr>
            <td><SeverityBadge :severity="finding.severity" /></td>
            <td>
              <router-link class="metric-link mono" :to="`/metrics/${finding.metric_id}`">{{ finding.metric_key }}</router-link>
              <div class="faint small">v{{ finding.version_a_no ?? '?' }} vs v{{ finding.version_b_no ?? '?' }}</div>
            </td>
            <td>{{ finding.conflict_label }}</td>
            <td>
              <div class="row" style="gap: 4px; flex-wrap: wrap">
                <span v-for="dimension in finding.dimensions" :key="dimension" class="chip is-hot">{{ dimension }}</span>
              </div>
            </td>
            <td>
              <button class="link-button" @click="expanded = expanded === finding.id ? null : finding.id">
                {{ finding.impact.affected_metric_count }} 个指标 / {{ finding.impact.board_count }} 个看板
              </button>
              <div v-if="expanded === finding.id" class="impact-pop">
                <div class="label">受影响指标</div>
                <div class="small">{{ finding.impact.affected_metrics.map((m) => m.key).join('、') || '无' }}</div>
                <div class="label mt-1">受影响看板</div>
                <div class="small">{{ finding.impact.boards.join('、') || '无' }}</div>
                <div class="label mt-1">冲突说明</div>
                <div class="small">{{ finding.detail }}</div>
              </div>
            </td>
            <td><span class="badge" :class="finding.status === 'open' ? 'pending' : 'active'">{{ finding.status_label }}</span></td>
            <td v-if="canTriage" class="text-right">
              <div class="row" style="justify-content: flex-end; gap: 6px">
                <button class="btn btn-sm" :disabled="finding.status !== 'open'" @click="$emit('triage', finding.id, 'acknowledged')">确认</button>
                <button class="btn btn-sm btn-accent" :disabled="finding.status === 'resolved'" @click="$emit('triage', finding.id, 'resolved')">解决</button>
              </div>
            </td>
          </tr>
        </template>
        <tr v-if="!findings.length">
          <td :colspan="canTriage ? 7 : 6">
            <EmptyState title="本批次没有冲突" hint="同名指标的多版本五元组完全一致，可以放心下发。" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Finding } from '../../types/check'
import SeverityBadge from '../common/SeverityBadge.vue'
import EmptyState from '../common/EmptyState.vue'

defineProps<{ findings: Finding[]; canTriage: boolean }>()
defineEmits<{ triage: [findingId: number, status: string] }>()

const expanded = ref<number | null>(null)
</script>

<style scoped>
.conflict-table td { font-size: 12px; }
.metric-link { color: var(--vermilion-deep); text-decoration: underline; text-underline-offset: 3px; }
.link-button { background: none; border: 0; padding: 0; color: var(--ink); cursor: pointer; font-size: 11.5px; text-decoration: underline; text-underline-offset: 3px; }
.impact-pop { margin-top: 6px; border-left: 2px solid var(--vermilion); padding-left: 8px; }
</style>
