import { defineConfig } from 'vite';
import { resolve } from 'path';
import legacy from '@vitejs/plugin-legacy';

export default defineConfig({
  root: './static',
  base: '/static/',
  
  build: {
    outDir: '../staticfiles',
    emptyOutDir: false,
    manifest: true,
    
    rollupOptions: {
      input: {
        // Main entry point that Django Vite is looking for
        main: resolve(__dirname, 'static/js/main.js'),
        // CSS entry
        styles: resolve(__dirname, 'static/css/src/main.css')
      },
      
      output: {
        // Code splitting configuration
        manualChunks: {
          'vendor': [
            'alpinejs',
            'htmx.org'
          ],
          'charts': [
            'apexcharts'
          ]
        },
        
        // Output naming
        chunkFileNames: 'js/chunks/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name.split('.').at(-1);
          if (/css/i.test(extType)) {
            return 'css/[name]-[hash].[ext]';
          }
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            return 'img/[name]-[hash].[ext]';
          }
          return 'assets/[name]-[hash].[ext]';
        }
      }
    },
    
    // Optimization settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true
      }
    },
    
    // Source maps for development
    sourcemap: process.env.NODE_ENV === 'development',
    
    // CSS code splitting
    cssCodeSplit: true,
    
    // Asset size warnings
    chunkSizeWarningLimit: 500,
    
    // Target modern browsers
    target: 'es2015'
  },
  
  // Development server configuration
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to Django
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  
  // Dependency optimization
  optimizeDeps: {
    include: [
      'alpinejs',
      'htmx.org',
      'apexcharts'
    ],
    exclude: []
  },
  
  plugins: [
    // Legacy browser support
    legacy({
      targets: ['defaults', 'not IE 11'],
      additionalLegacyPolyfills: ['regenerator-runtime/runtime']
    })
  ],
  
  // CSS configuration
  css: {
    preprocessorOptions: {
      css: {
        // CSS options if needed
      }
    },
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer')
      ]
    }
  },
  
  // Environment variables
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
  }
});