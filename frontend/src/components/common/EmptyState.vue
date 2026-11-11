<template>
  <div class="empty-state">
    <div class="glyph">{{ glyph }}</div>
    <div class="section-title mt-2">{{ title }}</div>
    <p class="hint mt-1">{{ hint }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title: string; hint?: string; glyph?: string }>(), {
  hint: '',
  glyph: '¶',
})
</script>
