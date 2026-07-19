<script setup>
import { useRouter, useRoute } from 'vue-router'

import { store } from './store.js'
import { toast } from './toast.js'

const router = useRouter()
const route = useRoute()

function logout() {
  store.logout()
  router.push('/login')
}
</script>

<template>
  <header v-if="store.user" class="topbar">
    <div class="container topbar-inner">
      <div class="row">
        <span class="logo">🖥️ Hardware Hub</span>
        <nav class="row nav">
          <router-link to="/" :class="{ active: route.path === '/' }">Dashboard</router-link>
          <router-link
            v-if="store.user.is_admin"
            to="/admin"
            :class="{ active: route.path === '/admin' }"
            >Admin</router-link
          >
        </nav>
      </div>
      <div class="row">
        <span class="muted">{{ store.user.email }}</span>
        <span v-if="store.user.is_admin" class="badge inuse">admin</span>
        <button class="ghost" @click="logout">Log out</button>
      </div>
    </div>
  </header>

  <router-view />

  <div v-if="toast.message" class="toast" :class="toast.kind === 'err' ? 'err' : 'ok'">
    {{ toast.message }}
  </div>
</template>

<style scoped>
.topbar {
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.topbar-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  padding-bottom: 14px;
}
.logo {
  font-weight: 700;
  font-size: 15px;
  margin-right: 8px;
}
.nav {
  gap: 4px;
  margin-left: 8px;
}
.nav a {
  color: var(--muted);
  padding: 6px 10px;
  border-radius: 8px;
}
.nav a.active {
  color: var(--text);
  background: var(--surface-2);
}
</style>
