import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0'
  },
  optimizeDeps: {
    include: ['naive-ui', 'vueuc', 'date-fns', 'treemate']
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'naive-ui': ['naive-ui', 'vueuc', 'date-fns', 'treemate']
        }
      }
    }
  }
})
