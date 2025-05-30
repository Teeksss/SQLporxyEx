// Complete Vite Configuration
// Created: 2025-05-29 13:44:06 UTC by Teeksss

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [react()],
    
    // Development server configuration
    server: {
      host: '0.0.0.0',
      port: 3000,
      open: false,
      cors: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        },
        '/ws': {
          target: env.VITE_WS_URL || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true
        }
      }
    },
    
    // Build configuration
    build: {
      outDir: 'dist',
      sourcemap: mode === 'development',
      minify: mode === 'production' ? 'esbuild' : false,
      target: 'es2020',
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html')
        },
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'antd-vendor': ['antd', '@ant-design/icons'],
            'chart-vendor': ['recharts'],
            'utility-vendor': ['lodash', 'dayjs', 'axios']
          }
        }
      },
      chunkSizeWarningLimit: 1000
    },
    
    // Path resolution
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
        '@components': resolve(__dirname, './src/components'),
        '@pages': resolve(__dirname, './src/pages'),
        '@services': resolve(__dirname, './src/services'),
        '@utils': resolve(__dirname, './src/utils'),
        '@hooks': resolve(__dirname, './src/hooks'),
        '@types': resolve(__dirname, './src/types'),
        '@contexts': resolve(__dirname, './src/contexts'),
        '@assets': resolve(__dirname, './src/assets'),
        '@config': resolve(__dirname, './src/config')
      }
    },
    
    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(env.npm_package_version || '2.0.0'),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
      __GIT_COMMIT__: JSON.stringify(env.GIT_COMMIT || 'unknown')
    },
    
    // CSS configuration
    css: {
      preprocessorOptions: {
        less: {
          javascriptEnabled: true,
          additionalData: '@import "@/styles/variables.less";'
        }
      },
      modules: {
        localsConvention: 'camelCase'
      }
    },
    
    // Test configuration
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/tests/setup.ts'],
      include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
      exclude: ['node_modules', 'dist', 'e2e'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        include: ['src/**/*.{js,ts,jsx,tsx}'],
        exclude: [
          'src/**/*.{test,spec}.{js,ts,jsx,tsx}',
          'src/**/*.stories.{js,ts,jsx,tsx}',
          'src/tests/**/*',
          'src/types/**/*'
        ]
      }
    }
  }
})