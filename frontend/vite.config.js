import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
      proxy: {
        // Any request whose path starts with /api is forwarded to the FastAPI
        // backend on :8000. So fetch('/api/banco/accounts') in our React code
        // actually hits http://localhost:8000/api/banco/accounts.
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  })

