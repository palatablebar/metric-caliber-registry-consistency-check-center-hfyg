<template>
  <pre class="dsl-code dsl-preview"><template v-for="(segment, index) in segments" :key="index"><span :class="segment.kind ? `tok-${segment.kind}` : ''">{{ segment.text }}</span></template></pre>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DslToken } from '../../types/metric'

const props = defineProps<{ source: string; tokens: DslToken[] }>()

const segments = computed(() => {
  const spans = [...(props.tokens ?? [])].sort((a, b) => a.start - b.start)
  const output: { text: string; kind: string | null }[] = []
  let cursor = 0
  for (const span of spans) {
    if (span.start < cursor || span.end > props.source.length) continue
    if (span.start > cursor) output.push({ text: props.source.slice(cursor, span.start), kind: null })
    output.push({ text: props.source.slice(span.start, span.end), kind: span.kind })
    cursor = span.end
  }
  if (cursor < props.source.length) output.push({ text: props.source.slice(cursor), kind: null })
  return output
})
</script>

<style scoped>
.dsl-preview { background: var(--paper); border-style: dashed; margin: 0; }
</style>
