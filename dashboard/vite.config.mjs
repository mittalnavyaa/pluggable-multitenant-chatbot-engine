import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

const dashboardRoot = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  root: dashboardRoot,
  cacheDir: 'node_modules/.vite-dashboard',
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    hmr: {
      protocol: 'ws',
      host: '127.0.0.1',
      port: 5173
    },
    proxy: {
      '/api/v1/documents': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/v1/products': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/v1/bots': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/v1/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/v1/analytics': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/v1/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  preview: {
    host: '127.0.0.1',
    port: 4173
  }
});
