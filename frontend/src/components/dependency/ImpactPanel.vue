<template>
  <section class="impact">
    <div class="row-between">
      <div class="eyebrow">impact closure</div>
      <span v-if="impact" class="faint small">{{ impact.affected_metric_count }} 个下游指标 · {{ impact.board_count }} 个看板</span>
    </div>
    <h3 class="section-title mt-1" style="font-size: 16px">{{ title }}</h3>
    <p v-if="loading" class="hint mt-2">计算依赖闭包中…</p>
    <template v-else-if="impact">
      <div class="impact-grid mt-2">
        <div>
          <div class="label">受影响指标</div>
          <ul v-if="impact.affected_metrics.length" class="clean-list mt-1">
            <li v-for="metric in impact.affected_metrics" :key="metric.id">
              <span class="mono small">{{ metric.key }}</span>
              <span class="faint small"> · {{ metric.name }}</span>
            </li>
          </ul>
          <p v-else class="hint mt-1">没有指标依赖它（可能是孤儿指标）。</p>
        </div>
        <div>
          <div class="label">受影响看板</div>
          <ul v-if="impact.boards.length" class="clean-list mt-1">
            <li v-for="board in impact.boards" :key="board" class="small">{{ board }}</li>
          </ul>
          <p v-else class="hint mt-1">暂无登记消费看板。</p>
        </div>
      </div>
    </template>
    <p v-else class="hint mt-2">选择指标后展示依赖闭包影响面。</p>
  </section>
</template>

<script setup lang="ts">
import type { ImpactPayload } from '../../types/dependency'

defineProps<{ impact: ImpactPayload | null; loading: boolean; title: string }>()
</script>

<style scoped>
.impact { border: 1px solid var(--rule); background: var(--paper-raised); padding: 16px 18px; }
.impact-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 18px; }
.clean-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 3px; }
@media (max-width: 700px) { .impact-grid { grid-template-columns: 1fr; } }
</style>
