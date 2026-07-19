import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Proxy /api to the FastAPI backend so the frontend can use same-origin calls
// in dev (no CORS juggling).
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
