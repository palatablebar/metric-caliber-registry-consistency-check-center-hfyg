<template>
  <div v-if="message" class="error-notice">
    <div>{{ message }}</div>
    <div v-if="hint" class="small mt-1">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ERROR_HINTS } from '../../constants/errorCodes'

const props = defineProps<{ error: { code?: string; message: string } | null }>()
const message = computed(() => props.error?.message ?? '')
const hint = computed(() => (props.error?.code ? ERROR_HINTS[props.error.code] : '') ?? '')
</script>
