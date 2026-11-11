<template>
  <div class="tuple-chips">
    <span class="chip" :class="{ 'is-hot': hot.includes('agg') }"><b>agg</b>{{ tuple.agg ?? '—' }}</span>
    <span class="chip" :class="{ 'is-hot': hot.includes('measure') }"><b>measure</b>{{ tuple.measure ?? '—' }}</span>
    <span class="chip" :class="{ 'is-hot': hot.includes('grain') }"><b>grain</b>{{ tuple.grain ?? '—' }}</span>
    <span class="chip" :class="{ 'is-hot': hot.includes('window') }"><b>window</b>{{ tuple.window ?? 'all' }}</span>
    <span
      v-for="filter in tuple.filters"
      :key="filter"
      class="chip"
      :class="{ 'is-hot': hot.includes('filter') }"
    ><b>filter</b>{{ filter }}</span>
    <span v-if="!tuple.filters.length" class="chip" :class="{ 'is-hot': hot.includes('filter') }"><b>filter</b>无</span>
  </div>
</template>

<script setup lang="ts">
import type { Tuple } from '../../types/metric'

withDefaults(defineProps<{ tuple: Tuple; hot?: string[] }>(), { hot: () => [] })
</script>

<style scoped>
.tuple-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip.is-hot { border-color: var(--vermilion); color: var(--vermilion-deep); background: var(--vermilion-wash); }
</style>
