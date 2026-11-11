import { onBeforeUnmount, ref, watch } from 'vue'
import { useCatalogStore } from '../stores/catalogStore'

/** Search box debounce + filter state shared by the catalog page. */
export function useCatalogFilter() {
  const store = useCatalogStore()
  const q = ref(store.q)
  let timer: ReturnType<typeof setTimeout> | null = null

  watch(q, (value) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      store.q = value
      void store.load()
    }, 320)
  })

  function setDomain(domain: string) {
    store.domain = store.domain === domain ? '' : domain
    void store.load()
  }

  function setStatus(status: string) {
    store.status = status
    void store.load()
  }

  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer)
  })

  return { store, q, setDomain, setStatus }
}
