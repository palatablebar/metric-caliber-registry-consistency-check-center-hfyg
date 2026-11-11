<template>
  <div class="gauge">
    <div class="gauge-head">
      <span class="label">一致性分数</span>
      <span class="gauge-number num">{{ score }}<em>/100</em></span>
    </div>
    <div class="gauge-track">
      <div class="gauge-fill" :style="{ width: `${Math.max(0, Math.min(100, score))}%` }"></div>
    </div>
    <p class="hint mt-1">{{ verdict }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ score: number }>()

const verdict = computed(() => {
  if (props.score >= 90) return '口径整体稳定，保持巡检节奏即可。'
  if (props.score >= 75) return '存在需要治理的口径差异，优先处理 high 冲突。'
  if (props.score >= 60) return '多团队口径明显分叉，建议在本周治理会上收敛。'
  return '口径严重不一致，报表已不可直接对比，需要立即冻结版本。'
})
</script>

<style scoped>
.gauge { border: 1px solid var(--rule); background: var(--paper-raised); padding: 14px 16px; }
.gauge-head { display: flex; justify-content: space-between; align-items: baseline; }
.gauge-number { font-family: var(--font-display); font-size: 34px; line-height: 1; color: var(--ink-strong); }
.gauge-number em { font-style: normal; font-size: 12px; color: var(--ink-faint); margin-left: 2px; }
.gauge-track { height: 8px; background: var(--paper-deep); border: 1px solid var(--rule-soft); margin-top: 10px; }
.gauge-fill { height: 100%; background: var(--vermilion); transition: width 0.6s var(--ease); }
</style>
