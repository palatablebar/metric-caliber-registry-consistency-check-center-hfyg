<template>
  <span class="badge" :class="status">{{ label ?? status }}</span>
</template>

<script setup lang="ts">
defineProps<{ status: string; label?: string }>()
</script>
