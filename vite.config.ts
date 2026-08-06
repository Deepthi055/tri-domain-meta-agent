import path from 'path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = (env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/auth': backendTarget,
        '/profile': backendTarget,
        '/memory': backendTarget,
        '/chat': backendTarget,
        '/reports': backendTarget,
        '/query': backendTarget,
        '/query-langchain': backendTarget,
        '/domains': backendTarget,
        '/health-check': backendTarget,
        '/api-status': backendTarget,
      },
    },
  }
})
