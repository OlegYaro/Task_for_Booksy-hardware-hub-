import { createApp } from 'vue'

import App from './App.vue'
import router from './router.js'
import { store } from './store.js'
import './style.css'

// Restore the session (if a token is in localStorage) before mounting so the
// router guard has the user available on first navigation.
store.loadSession().finally(() => {
  createApp(App).use(router).mount('#app')
})
