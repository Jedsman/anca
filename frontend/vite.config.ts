import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all addresses for Docker
    proxy: {
      '/api': {
        target: 'http://anca:8000', // Docker service name
        changeOrigin: true
      }
    },
    watch: {
        usePolling: true
    }
  }
})
