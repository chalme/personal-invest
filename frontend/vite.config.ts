import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendPort = process.env.BACKEND_PORT ?? '8000';
const backendTarget = process.env.VITE_PROXY_TARGET ?? `http://127.0.0.1:${backendPort}`;
const frontendHost = process.env.FRONTEND_HOST ?? '0.0.0.0';
const frontendPort = Number(process.env.FRONTEND_PORT ?? '5173');

export default defineConfig({
  plugins: [react()],
  build: {
    // ECharts is loaded as a lazy chart chunk; 700KB keeps the build signal focused on unexpected growth.
    chunkSizeWarningLimit: 700,
  },
  server: {
    host: frontendHost,
    port: frontendPort,
    strictPort: true,
    proxy: {
      '/api': backendTarget,
      '/health': backendTarget
    }
  }
});

