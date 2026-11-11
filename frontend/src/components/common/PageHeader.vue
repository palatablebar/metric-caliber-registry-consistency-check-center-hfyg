<template>
  <header class="page-head">
    <div>
      <div class="eyebrow">{{ eyebrow }}</div>
      <h1 class="display mt-1">{{ title }}</h1>
      <p v-if="lede" class="lede mt-2">{{ lede }}</p>
    </div>
    <div v-if="$slots.actions" class="page-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ eyebrow: string; title: string; lede?: string }>()
</script>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--rule);
  margin-bottom: 22px;
}
.page-actions { display: flex; gap: 10px; flex-wrap: wrap; }
</style>
