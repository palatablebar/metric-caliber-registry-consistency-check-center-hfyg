<template>
  <div class="loading-hint">
    <span class="spin-dot"></span>
    <span>{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ text?: string }>(), { text: '读取索引卡…' })
</script>

<style scoped>
.loading-hint { display: flex; align-items: center; gap: 9px; color: var(--ink-soft); font-size: 12px; padding: 16px 2px; }
.spin-dot { width: 9px; height: 9px; border: 1px solid var(--vermilion); border-top-color: transparent; border-radius: 50%; animation: rotate 0.8s linear infinite; }
</style>
