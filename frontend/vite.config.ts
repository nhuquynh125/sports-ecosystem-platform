import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [react()],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            if (!id.includes('node_modules')) return undefined
            if (/node_modules\/(react|react-dom|react-router|react-router-dom|scheduler)\//.test(id)) return 'vendor-react'
            if (/node_modules\/(@radix-ui|lucide-react|@floating-ui)\//.test(id)) return 'vendor-ui'
            return 'vendor-data'
          },
        },
      },
    },
    server: {
      port: 5173,
      // Same-origin calls in dev: the browser talks to :5173, Vite forwards /api (and WebSockets).
      proxy: {
        '/api': { target, changeOrigin: true, ws: true },
      },
    },
  }
})
