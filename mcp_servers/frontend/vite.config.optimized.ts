import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { visualizer } from 'rollup-plugin-visualizer';
import viteCompression from 'vite-plugin-compression';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    sveltekit(),
    
    // Bundle analyzer
    visualizer({
      filename: './dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
    
    // Compression plugins for gzip and brotli
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 1024,
      deleteOriginFile: false,
    }),
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 1024,
      deleteOriginFile: false,
    }),
    
    // PWA for offline support and caching
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp,woff2}'],
        cleanupOutdatedCaches: true,
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 300, // 5 minutes
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            urlPattern: /\.(png|jpg|jpeg|svg|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 86400 * 30, // 30 days
              },
            },
          },
          {
            urlPattern: /\.(woff2?|ttf|eot)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'font-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 86400 * 365, // 1 year
              },
            },
          },
        ],
      },
      manifest: {
        name: 'MCP Server Manager',
        short_name: 'MCP Manager',
        theme_color: '#1e293b',
        background_color: '#0f172a',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
    }),
  ],
  
  build: {
    // Performance optimizations
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'],
        passes: 2,
      },
      mangle: {
        safari10: true,
      },
      format: {
        comments: false,
      },
    },
    
    // Code splitting configuration
    rollupOptions: {
      output: {
        // Manual chunks for vendor splitting
        manualChunks: (id) => {
          // Core framework chunk
          if (id.includes('svelte') || id.includes('@sveltejs')) {
            return 'vendor-svelte';
          }
          
          // UI libraries chunk
          if (id.includes('lucide') || id.includes('clsx')) {
            return 'vendor-ui';
          }
          
          // Utilities chunk
          if (id.includes('lodash') || id.includes('date-fns')) {
            return 'vendor-utils';
          }
          
          // Node modules chunk
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
        
        // Asset naming for better caching
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk';
          return `assets/js/${facadeModuleId}-[hash].js`;
        },
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name.split('.').pop();
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/woff|woff2|eot|ttf|otf/i.test(extType)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          if (/css/i.test(extType)) {
            return `assets/css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
      },
    },
    
    // Build performance settings
    sourcemap: false, // Disable in production for smaller builds
    reportCompressedSize: false, // Faster builds
    chunkSizeWarningLimit: 1000, // 1MB warning threshold
    
    // CSS code splitting
    cssCodeSplit: true,
    
    // Asset inlining threshold
    assetsInlineLimit: 4096, // 4KB
  },
  
  // Development server optimizations
  server: {
    hmr: {
      overlay: true,
      protocol: 'ws',
    },
    fs: {
      strict: true,
    },
  },
  
  // Dependency optimization
  optimizeDeps: {
    include: [
      'svelte',
      '@sveltejs/kit',
      'lucide-svelte',
      'clsx',
    ],
    exclude: ['@sveltejs/kit/node'],
    esbuildOptions: {
      target: 'es2020',
    },
  },
  
  // CSS optimization
  css: {
    devSourcemap: false,
    postcss: {
      plugins: [
        // Autoprefixer is included via svelte config
      ],
    },
  },
  
  // Performance hints
  resolve: {
    dedupe: ['svelte'],
    alias: {
      $lib: '/src/lib',
      $components: '/src/components',
      $stores: '/src/stores',
      $utils: '/src/utils',
    },
  },
  
  // Experimental features for better performance
  experimental: {
    renderBuiltUrl(filename, { hostType }) {
      if (hostType === 'js') {
        return {
          runtime: `window.__assetUrl(${JSON.stringify(filename)})`,
        };
      }
    },
  },
});