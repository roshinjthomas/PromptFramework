import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // SSE requires no request buffering
        configure: (proxy) => {
          proxy.on('proxyReq', (_proxyReq, req) => {
            if (req.headers.accept?.includes('text/event-stream')) {
              _proxyReq.setHeader('Connection', 'keep-alive')
            }
          })
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
