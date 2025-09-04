import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte({ hot: !process.env.VITEST })],
  
  test: {
    // Test environment
    environment: 'jsdom',
    
    // Test patterns
    include: [
      'src/**/*.{test,spec}.{js,ts}',
      '../tests/frontend/**/*.{test,spec}.{js,ts}'
    ],
    
    // Setup files
    setupFiles: [
      './tests/setupTests.ts'
    ],
    
    // Globals
    globals: true,
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      include: [
        'src/**/*.{js,ts,svelte}',
        '!src/**/*.d.ts',
        '!src/**/*.stories.{js,ts}',
        '!src/**/__tests__/**',
        '!src/**/node_modules/**'
      ],
      exclude: [
        'src/app.html',
        'src/app.d.ts'
      ],
      reporter: [
        'text',
        'lcov',
        'html',
        'json-summary'
      ],
      reportsDirectory: './coverage',
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    
    // Test timeout
    testTimeout: 10000,
    
    // Clear mocks between tests
    clearMocks: true,
    
    // Restore mocks after each test
    restoreMocks: true,
    
    // Resolve configuration for Svelte
    alias: {
      '$lib': './src/lib',
      '$app': './src/app'
    }
  },
  
  // Resolve configuration for Svelte
  resolve: {
    alias: {
      '$lib': './src/lib',
      '$app': './src/app'
    }
  }
});