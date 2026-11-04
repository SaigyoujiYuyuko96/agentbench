import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 后端默认跑在 127.0.0.1:8090（见根目录 README 的快速开始）。
// 前端统一请求 /api/*，由这里的 proxy 转发，避免硬编码 host 和跨域。
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true,
      },
    },
  },
})
