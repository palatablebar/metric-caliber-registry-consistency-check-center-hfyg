<template>
  <span :class="severityClass(severity)">{{ SEVERITY_LABELS[severity] ?? severity }}</span>
</template>

<script setup lang="ts">
import { SEVERITY_LABELS } from '../../constants/severity'
import { severityClass } from '../../utils/severityTone'

defineProps<{ severity: string | null }>()
</script>
