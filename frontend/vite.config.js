import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Em dev, proxy de /api para o backend FastAPI (porta 8080).
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
