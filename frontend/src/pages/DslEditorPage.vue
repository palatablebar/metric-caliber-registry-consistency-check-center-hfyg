<template>
  <div class="rise">
    <div class="row-between mt-1">
      <router-link class="back-link" :to="metric ? `/metrics/${metric.id}` : '/catalog'">← 返回指标详情</router-link>
      <div class="eyebrow" v-if="metric">{{ metric.key }} · v{{ nextVersionNo }}</div>
    </div>

    <LoadingHint v-if="loading" />
    <ErrorNotice :error="error" class="mt-2" />

    <template v-if="metric">
      <header class="mt-2">
        <div class="eyebrow">dsl workbench</div>
        <h1 class="display mt-1">口径 DSL 编辑器</h1>
        <p class="lede mt-2">
          编辑 DSL 后由后端实时解析成五元组并预览依赖；保存时同样走后端解析，语法错误会被拒绝落库。
        </p>
      </header>

      <div class="dsl-grid mt-3">
        <section class="editor-pane">
          <div class="row-between">
            <span class="label">metric DSL</span>
            <span class="faint small">{{ source.length }} / 4000</span>
          </div>
          <textarea v-model="source" class="textarea dsl-input" spellcheck="false" rows="9" />
          <div class="hint mt-1">
            语法示例：<code>metric active_users = count(distinct user_id) from fact_visit where date >= today-7 filter platform in ('ios','android') grain day</code>
          </div>

          <div class="mt-3">
            <SectionHeading eyebrow="live parse" title="解析预览（后端 dsl_parser）">
              <template #actions>
                <span class="badge" :class="parsed?.ok ? 'active' : parsed ? 'deprecated' : 'draft'">
                  {{ preview.loading.value ? '解析中' : parsed?.ok ? '解析通过' : parsed?.error ? '解析失败' : '待输入' }}
                </span>
              </template>
            </SectionHeading>
            <template v-if="parsed?.ok">
              <div class="parsed-grid">
                <div><div class="label">agg</div><div class="mono">{{ parsed.agg }}</div></div>
                <div><div class="label">measure</div><div class="mono">{{ parsed.measure }}</div></div>
                <div><div class="label">source</div><div class="mono">{{ parsed.source_table }}</div></div>
                <div><div class="label">grain</div><div class="mono">{{ parsed.grain }}</div></div>
                <div><div class="label">window</div><div class="mono">{{ parsed.window }}</div></div>
              </div>
              <div class="mt-2">
                <div class="label">filter 集合</div>
                <div class="row mt-1" style="flex-wrap: wrap; gap: 6px">
                  <span v-for="filter in parsed.filters" :key="filter" class="chip">{{ filter }}</span>
                  <span v-if="!parsed.filters.length" class="chip">无</span>
                </div>
              </div>
              <div class="mt-3">
                <div class="label">源码高亮</div>
                <DslPreview :source="source" :tokens="parsed.tokens" />
              </div>
              <div class="mt-3">
                <div class="label">依赖预览（using 子句）</div>
                <div class="row mt-1" style="flex-wrap: wrap; gap: 6px">
                  <router-link
                    v-for="dep in parsed.dependencies"
                    :key="dep"
                    class="chip"
                    :to="`/graph`"
                  >→ {{ dep }}</router-link>
                  <span v-if="!parsed.dependencies.length" class="hint">未声明 using 依赖</span>
                </div>
              </div>
              <p v-for="warning in parsed.warnings" :key="warning" class="hint mt-1">⚠ {{ warning }}</p>
            </template>
            <div v-else-if="parsed?.error" class="error-notice mt-2">
              {{ parsed.error }}
              <span class="faint small">（第 {{ parsed.error_offset + 1 }} 个字符，{{ parsed.error_kind }}）</span>
            </div>
            <p v-else class="hint mt-2">输入 DSL 后自动解析；解析在 backend/app/algorithms/dsl_parser.py 中完成。</p>
          </div>
        </section>

        <aside class="stack">
          <section class="index-card is-flat">
            <div class="eyebrow">save version</div>
            <h3 class="card-title mt-1">保存为新版本</h3>
            <p class="hint mt-1">
              指标归属：{{ metric.owner_team.name }}；当前角色：{{ auth.role }}。
              <span v-if="!auth.canWrite">只读角色只能预览，不能保存。</span>
            </p>
            <div class="stack mt-2" style="gap: 10px">
              <label class="field">
                <span class="label">提交团队</span>
                <select v-model.number="teamId" class="select" :disabled="!auth.canWrite">
                  <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}（{{ team.domain_label }}）</option>
                </select>
              </label>
              <label class="field">
                <span class="label">生效日期</span>
                <input v-model="effectiveFrom" type="date" class="input" :disabled="!auth.canWrite" />
              </label>
              <label class="row small" style="gap: 6px">
                <input v-model="setCurrent" type="checkbox" :disabled="!auth.canWrite" /> 设为当前版本
              </label>
              <button class="btn btn-solid" :disabled="!auth.canWrite || saving" @click="save">
                {{ saving ? '保存中…' : `保存为 v${nextVersionNo}` }}
              </button>
            </div>
            <p v-if="message" class="hint mt-2">{{ message }}</p>
            <ErrorNotice :error="saveError" class="mt-2" />
          </section>

          <section class="index-card is-flat">
            <div class="eyebrow">dsl keywords</div>
            <h3 class="card-title mt-1">语法速查</h3>
            <ul class="keyword-list mt-2">
              <li><code>metric &lt;key&gt; =</code> 声明指标</li>
              <li><code>agg(measure)</code> count/sum/avg/min/max，count 可接 distinct</li>
              <li><code>from &lt;table&gt;</code> 单个物理表</li>
              <li><code>where … [and …]</code> 过滤条件，date &gt;= today-N 推导窗口</li>
              <li><code>filter &lt;field&gt; in (…)</code> 过滤集合</li>
              <li><code>grain hour|day|week|month</code> 时间粒度</li>
              <li><code>window &lt;n&gt;d</code> 时间窗口，可省略</li>
              <li><code>using (a,b)</code> 声明依赖指标</li>
            </ul>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import SectionHeading from '../components/common/SectionHeading.vue'
import LoadingHint from '../components/common/LoadingHint.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import DslPreview from '../components/metric/DslPreview.vue'
import { fetchMetric, fetchTeams, createVersion } from '../api/metric'
import { useDslPreview } from '../hooks/useDslPreview'
import { useAuthStore } from '../stores/authStore'
import type { MetricDetail } from '../types/metric'
import type { OwnerTeam } from '../types/user'
import type { ApiError } from '../types/api'

const route = useRoute()
const auth = useAuthStore()
const metric = ref<MetricDetail | null>(null)
const teams = ref<OwnerTeam[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)
const message = ref('')
const saveError = ref<ApiError | null>(null)
const saving = ref(false)
const teamId = ref(0)
const effectiveFrom = ref(new Date().toISOString().slice(0, 10))
const setCurrent = ref(true)

const source = ref('')
const preview = useDslPreview(source)
const parsed = computed(() => preview.parsed.value)

const nextVersionNo = computed(() => {
  const versions = metric.value?.versions ?? []
  return (versions.length ? Math.max(...versions.map((version) => version.version_no)) : 0) + 1
})

onMounted(async () => {
  loading.value = true
  try {
    metric.value = await fetchMetric(Number(route.params.id))
    const teamResult = await fetchTeams()
    teams.value = teamResult.items
    teamId.value = metric.value.owner_team.id
    const requested = Number(route.query.version ?? 0)
    const version =
      metric.value.versions.find((row) => row.id === requested) ??
      metric.value.versions.find((row) => row.is_current) ??
      metric.value.versions[metric.value.versions.length - 1]
    source.value = version?.dsl_text ?? ''
  } catch (err) {
    error.value = err as ApiError
  } finally {
    loading.value = false
  }
})

async function save() {
  if (!metric.value) return
  saving.value = true
  message.value = ''
  saveError.value = null
  try {
    const created = await createVersion(metric.value.id, {
      dsl_text: source.value,
      team_id: teamId.value || undefined,
      effective_from: effectiveFrom.value || undefined,
      set_current: setCurrent.value,
    })
    message.value = `已保存为 v${created.version_no}，重新打开详情页可看到新版本。`
    metric.value = await fetchMetric(metric.value.id)
  } catch (err) {
    saveError.value = err as ApiError
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.back-link { font-size: 11.5px; color: var(--ink-soft); text-decoration: underline; text-underline-offset: 3px; }
.dsl-grid { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(270px, 1fr); gap: 26px; align-items: start; }
.dsl-input { min-height: 190px; }
.parsed-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; border: 1px solid var(--rule); padding: 10px 12px; background: var(--paper-raised); }
.parsed-grid .mono { font-size: 12.5px; color: var(--ink-strong); }
.keyword-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 5px; font-size: 11.5px; color: var(--ink-soft); }
.keyword-list code { font-family: 'IBM Plex Mono', ui-monospace, monospace; color: var(--vermilion-deep); font-size: 11px; }
@media (max-width: 1000px) { .dsl-grid { grid-template-columns: 1fr; } }
</style>
