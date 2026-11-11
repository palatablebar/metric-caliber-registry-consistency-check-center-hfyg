<template>
  <div class="shell">
    <aside class="rail">
      <router-link to="/catalog" class="brand">
        <div class="eyebrow">微光课堂 · 数据治理委员会</div>
        <div class="brand-name">metricd</div>
        <div class="brand-sub">指标口径注册与一致性检查中心<br />Metric Caliber Registry</div>
      </router-link>

      <nav class="rail-nav">
        <router-link to="/catalog">
          <span>指标目录</span><span class="idx">01</span>
        </router-link>
        <router-link to="/graph">
          <span>依赖图</span><span class="idx">02</span>
        </router-link>
        <router-link to="/checks">
          <span>一致性检查</span><span class="idx">03</span>
        </router-link>
      </nav>

      <div class="rail-foot">
        <div class="user-line">
          <span class="user-name">{{ auth.displayName || '—' }}</span>
          <span class="role-tag">{{ auth.user?.role }}</span>
        </div>
        <div class="small mt-1">{{ auth.teamName }}</div>
        <div class="small faint mt-1">今日检查配额 {{ auth.user?.quota_used ?? 0 }}/{{ auth.user?.daily_check_quota ?? 0 }}</div>
        <button class="logout" @click="logout">退出登录</button>
      </div>
    </aside>

    <main class="main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/authStore'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
