<template>
  <div class="login-grid">
    <section class="login-brand">
      <div>
        <div class="eyebrow">微光课堂 · 数据治理委员会</div>
        <h1 class="login-title">metricd</h1>
        <p class="lede mt-2">
          指标口径注册与一致性检查中心。<br />
          把「活跃用户到底怎么算」从 Confluence 与 SQL 注释里收回来。
        </p>

        <div class="index-card catalog-card mt-4">
          <span class="card-tab">catalog card</span>
          <div class="card-key mono">METRIC CATALOG · 2026 Q4</div>
          <div class="card-title mt-1">口径索引卡</div>
          <div class="card-rule"></div>
          <dl class="login-facts">
            <div><dt>客户</dt><dd>在线教育「微光课堂」</dd></div>
            <div><dt>治理范围</dt><dd>14 个指标 / 4 个业务域 / 4 个团队</dd></div>
            <div><dt>已知议题</dt><dd>active_users 三团队三口径</dd></div>
            <div><dt>待治理</dt><dd>2 处环依赖 · 3 处 high 冲突</dd></div>
          </dl>
          <div class="card-rule"></div>
          <div class="card-meta">
            <span>DSL 五元组</span><span>DAG 环检测</span><span>影响面闭包</span>
          </div>
        </div>
      </div>
      <div class="login-foot">
        <span>口径 → 版本 → 依赖 → 一致性检查 → 影响面</span>
        <span class="faint">batch-20261110 · gb-550</span>
      </div>
    </section>

    <section class="login-form-wrap">
      <div class="login-form">
        <div class="eyebrow">sign in</div>
        <h2 class="display mt-1">进入索引室</h2>
        <p class="small muted mt-2">三角色账号：管理员 / 指标负责人 / 只读分析员。</p>

        <form class="stack mt-3" style="gap: 14px" @submit.prevent="submit">
          <label class="field">
            <span class="label">邮箱</span>
            <input v-model="email" class="input" type="email" autocomplete="username" placeholder="admin@metric.local" />
          </label>
          <label class="field">
            <span class="label">密码</span>
            <input v-model="password" class="input" type="password" autocomplete="current-password" placeholder="Demo@2026" />
          </label>
          <button class="btn btn-solid" type="submit" :disabled="auth.loading" style="justify-content: center">
            {{ auth.loading ? '核验中…' : '登录' }}
          </button>
        </form>

        <ErrorNotice :error="error" class="mt-2" />

        <div class="mt-3">
          <div class="label mb-1">演示账号（密码统一 Demo@2026）</div>
          <ul class="account-list">
            <li v-for="account in accounts" :key="account.email">
              <button type="button" class="account-button" @click="fill(account.email)">
                <span>{{ account.label }}</span>
                <span class="mono faint">{{ account.email }}</span>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import { useAuthStore } from '../stores/authStore'
import type { ApiError } from '../types/api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const email = ref('admin@metric.local')
const password = ref('Demo@2026')
const error = ref<ApiError | null>(null)

const accounts = [
  { label: '管理员 · 顾清和', email: 'admin@metric.local' },
  { label: '负责人 · 林知夏（增长）', email: 'owner@metric.local' },
  { label: '分析员 · 沈知微（只读）', email: 'analyst@metric.local' },
]

function fill(value: string) {
  email.value = value
  password.value = 'Demo@2026'
}

async function submit() {
  error.value = null
  try {
    await auth.login(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/catalog'
    router.push(redirect)
  } catch (err) {
    error.value = err as ApiError
  }
}
</script>

<style scoped>
.login-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); min-height: 100vh; }
.login-brand {
  padding: 54px clamp(28px, 5vw, 74px) 34px;
  border-right: 1px solid var(--rule);
  background: var(--paper-raised);
  display: flex; flex-direction: column; justify-content: space-between; gap: 36px;
}
.login-title { font-family: var(--font-display); font-size: clamp(44px, 5vw, 68px); line-height: 0.95; color: var(--ink-strong); margin-top: 10px; letter-spacing: -0.01em; }
.catalog-card { max-width: 400px; }
.login-facts { margin: 0; display: flex; flex-direction: column; gap: 7px; font-size: 12px; }
.login-facts > div { display: flex; gap: 12px; }
.login-facts dt { width: 70px; color: var(--ink-faint); font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase; padding-top: 2px; }
.login-facts dd { margin: 0; color: var(--ink); }
.login-foot { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-size: 11px; color: var(--ink-soft); }
.login-form-wrap { display: flex; align-items: center; justify-content: center; padding: 42px 30px; }
.login-form { width: 100%; max-width: 390px; }
.account-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
.account-button {
  width: 100%; display: flex; justify-content: space-between; gap: 12px; align-items: baseline;
  border: 0; border-bottom: 1px dashed var(--rule); background: none; padding: 6px 2px; cursor: pointer; font-size: 11.5px;
  color: var(--ink-soft); transition: color 0.2s var(--ease), border-color 0.2s var(--ease);
}
.account-button:hover { color: var(--vermilion-deep); border-bottom-color: var(--vermilion); }
@media (max-width: 900px) {
  .login-grid { grid-template-columns: 1fr; }
  .login-brand { border-right: 0; border-bottom: 1px solid var(--rule); }
}
</style>
