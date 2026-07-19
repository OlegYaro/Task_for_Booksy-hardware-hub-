import { reactive } from 'vue'

import { api, clearToken, hasToken } from './api.js'

// Minimal global auth state. Enough for this app; a larger one would use Pinia.
export const store = reactive({
  user: null,
  aiEnabled: false,

  async loadSession() {
    if (!hasToken()) return
    try {
      this.user = await api.me()
      const status = await api.aiStatus()
      this.aiEnabled = status.llm_enabled
    } catch {
      this.logout()
    }
  },

  async login(email, password) {
    await api.login(email, password)
    await this.loadSession()
  },

  logout() {
    clearToken()
    this.user = null
  },
})
