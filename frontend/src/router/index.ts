import { createRouter, createWebHistory } from 'vue-router'
import { setupGuards } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/catalog' },
    { path: '/login', name: 'login', component: () => import('../pages/LoginPage.vue'), meta: { public: true } },
    { path: '/catalog', name: 'catalog', component: () => import('../pages/CatalogPage.vue'), meta: { title: '指标目录' } },
    { path: '/metrics/:id', name: 'metric-detail', component: () => import('../pages/MetricDetailPage.vue'), meta: { title: '指标详情' } },
    { path: '/metrics/:id/dsl', name: 'dsl-editor', component: () => import('../pages/DslEditorPage.vue'), meta: { title: 'DSL 编辑器' } },
    { path: '/graph', name: 'graph', component: () => import('../pages/DependencyGraphPage.vue'), meta: { title: '依赖图' } },
    { path: '/checks', name: 'checks', component: () => import('../pages/ConflictsPage.vue'), meta: { title: '一致性检查' } },
    { path: '/:pathMatch(.*)*', redirect: '/catalog' },
  ],
})

setupGuards(router)

export default router
