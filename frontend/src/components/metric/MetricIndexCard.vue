<template>
  <button class="index-card" :class="{ 'is-warn': metric.status === 'deprecated' }" @click="$emit('select', metric)">
    <span class="card-tab">{{ metric.domain_label }}</span>
    <div class="card-key mono">{{ metric.key }}</div>
    <div class="card-title mt-1">{{ metric.name }}</div>
    <div class="card-rule"></div>
    <div class="card-meta">
      <span>负责团队 · {{ metric.owner_team.name ?? '未指定' }}</span>
      <span class="num">版本 {{ metric.version_count }}</span>
      <span v-if="metric.team_count > 1" class="faint">跨 {{ metric.team_count }} 个团队</span>
    </div>
    <div class="mt-2">
      <TupleChips v-if="metric.current_version" :tuple="metric.current_version.tuple" />
    </div>
    <div class="card-foot">
      <StatusBadge :status="metric.status" :label="metric.status_label" />
      <span class="faint small">{{ metric.consumers.length }} 个下游看板</span>
    </div>
  </button>
</template>

<script setup lang="ts">
import type { Metric } from '../../types/metric'
import StatusBadge from '../common/StatusBadge.vue'
import TupleChips from './TupleChips.vue'

defineProps<{ metric: Metric }>()
defineEmits<{ select: [metric: Metric] }>()
</script>

<style scoped>
.card-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }
.card-meta { line-height: 1.7; }
</style>
