import { createRouter, createWebHistory } from 'vue-router'

import { hasToken } from './api.js'
import { store } from './store.js'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Admin from './views/Admin.vue'

const routes = [
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/', component: Dashboard },
  { path: '/admin', component: Admin, meta: { admin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  if (!hasToken()) return '/login'
  if (!store.user) await store.loadSession()
  if (!store.user) return '/login'

  if (to.meta.admin && !store.user.is_admin) return '/'
  return true
})

export default router
