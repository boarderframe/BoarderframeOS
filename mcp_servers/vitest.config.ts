import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [sveltekit()],
  
  test: {
    // Test environment
    environment: 'jsdom',
    
    // Test patterns
    include: [
      'frontend/src/**/*.{test,spec}.{js,ts}',
      'tests/frontend/**/*.{test,spec}.{js,ts}'
    ],
    
    // Setup files
    setupFiles: [
      './tests/frontend/setup/setupTests.ts'
    ],
    
    // Globals
    globals: true,
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      include: [
        'frontend/src/**/*.{js,ts,svelte}',
        '!frontend/src/**/*.d.ts',
        '!frontend/src/**/*.stories.{js,ts}',
        '!frontend/src/**/__tests__/**',
        '!frontend/src/**/node_modules/**'
      ],
      exclude: [
        'frontend/src/app.html',
        'frontend/src/app.d.ts',
        'frontend/src/lib/index.ts'
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
    
    // Mock configuration
    alias: {
      '$lib': './frontend/src/lib',
      '$app': './frontend/src/app',
      '$env': './frontend/src/env'
    }
  },
  
  // Resolve configuration for Svelte
  resolve: {
    alias: {
      '$lib': './frontend/src/lib',
      '$app': './frontend/src/app'
    }
  }
});