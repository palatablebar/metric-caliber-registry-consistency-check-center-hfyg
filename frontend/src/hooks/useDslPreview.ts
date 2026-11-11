import { onBeforeUnmount, ref, watch } from 'vue'
import type { Ref } from 'vue'
import { parseDsl } from '../api/metric'
import type { DslParseResult } from '../types/metric'

/** Debounced live DSL parse against the backend parser (never parsed in the browser). */
export function useDslPreview(source: Ref<string>) {
  const parsed = ref<DslParseResult | null>(null)
  const loading = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let sequence = 0

  async function parseNow(text: string) {
    if (!text.trim()) {
      parsed.value = null
      return
    }
    const current = ++sequence
    loading.value = true
    try {
      const result = await parseDsl(text)
      if (current === sequence) parsed.value = result
    } catch {
      if (current === sequence) parsed.value = null
    } finally {
      if (current === sequence) loading.value = false
    }
  }

  watch(
    source,
    (value) => {
      if (timer) clearTimeout(timer)
      loading.value = true
      timer = setTimeout(() => void parseNow(value), 380)
    },
    { immediate: true },
  )

  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer)
  })

  return { parsed, loading, reparse: () => void parseNow(source.value) }
}
