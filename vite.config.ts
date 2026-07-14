import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/profile': 'http://127.0.0.1:8000',
      '/memory': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/query': 'http://127.0.0.1:8000',
      '/query-langchain': 'http://127.0.0.1:8000',
      '/domains': 'http://127.0.0.1:8000',
      '/health-check': 'http://127.0.0.1:8000',
      '/api-status': 'http://127.0.0.1:8000',
    },
  },
})
