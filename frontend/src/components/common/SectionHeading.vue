<template>
  <div class="section-head">
    <div>
      <div class="eyebrow">{{ eyebrow }}</div>
      <h2 class="section-title mt-1">{{ title }}</h2>
    </div>
    <slot name="actions" />
  </div>
</template>

<script setup lang="ts">
defineProps<{ eyebrow: string; title: string }>()
</script>

<style scoped>
.section-head {
  display: flex; justify-content: space-between; align-items: flex-end; gap: 14px;
  padding-bottom: 8px; border-bottom: 1px solid var(--rule); margin-bottom: 14px;
}
</style>
