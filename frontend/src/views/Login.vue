<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { store } from '../store.js'

const router = useRouter()
const email = ref('admin@booksy.com')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await store.login(email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="wrap">
    <div class="card login">
      <div class="brand">🖥️ Hardware Hub</div>
      <p class="muted sub">Sign in to manage company equipment</p>

      <form @submit.prevent="submit">
        <label>Email</label>
        <input v-model="email" type="email" autocomplete="username" />

        <label>Password</label>
        <input v-model="password" type="password" autocomplete="current-password" />

        <button class="primary full" type="submit" :disabled="loading">
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p v-if="error" class="err">{{ error }}</p>
      <p class="muted hint">
        Accounts are created by an admin — there's no public sign-up.
        <br />
        Demo admin: <strong>admin@booksy.com</strong> /
        <strong>HwHub-Admin-daff4046</strong>
      </p>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 20px;
}
.login {
  width: 340px;
}
.brand {
  font-size: 18px;
  font-weight: 700;
}
.sub {
  margin: 6px 0 20px;
}
label {
  display: block;
  margin: 12px 0 5px;
  font-size: 12px;
  color: var(--muted);
}
input {
  width: 100%;
}
.full {
  width: 100%;
  margin-top: 18px;
  padding: 10px;
}
.err {
  color: var(--danger);
  font-size: 13px;
  margin-top: 12px;
}
.hint {
  font-size: 12px;
  margin-top: 18px;
  line-height: 1.5;
}
</style>
