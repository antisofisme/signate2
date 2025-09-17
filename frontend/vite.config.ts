import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  define: {
    // Define environment variables
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
  },

  server: {
    port: 3000,
    host: true, // Allow external connections
    proxy: {
      // Proxy API calls to backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy WebSocket connections
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },

  build: {
    // Build configuration
    target: 'es2020',
    outDir: 'dist',
    sourcemap: true,

    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'state-vendor': ['zustand'],
          'ui-vendor': ['react-hot-toast', 'lucide-react'],
          'api-vendor': ['axios', 'socket.io-client'],
        },
      },
    },

    // Bundle size warnings
    chunkSizeWarningLimit: 600,
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'zustand',
      'axios',
      'socket.io-client',
      'react-hot-toast',
      'lucide-react',
      'zod',
      'react-hook-form',
      '@hookform/resolvers',
      'date-fns',
      'react-dropzone',
      'idb',
      'clsx',
      'tailwind-merge',
    ],
  },

  esbuild: {
    // Remove console.log in production
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
  },
});