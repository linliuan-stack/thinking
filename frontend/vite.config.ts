import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api/auth': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/modules': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/experiment': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
