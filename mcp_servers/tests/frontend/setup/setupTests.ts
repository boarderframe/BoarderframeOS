/**
 * Vitest setup file for Svelte frontend testing
 */

// Import Jest DOM matchers for Vitest
import '@testing-library/jest-dom';

// Import MSW for API mocking
import { server } from '../mocks/server';

// Import testing utilities
import { beforeAll, afterEach, afterAll, vi, expect } from 'vitest';

// Polyfills for jsdom environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock window.matchMedia for components that use media queries
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  callback
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  callback
}));

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as any;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock as any;

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn().mockReturnValue('mock-object-url');
global.URL.revokeObjectURL = vi.fn();

// Mock fetch if not using MSW
if (!global.fetch) {
  global.fetch = vi.fn();
}

// Console warnings/errors configuration
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  // Start MSW server
  server.listen({ onUnhandledRequest: 'error' });
  
  // Suppress specific console warnings in tests
  console.error = (...args) => {
    const message = args[0];
    if (
      typeof message === 'string' &&
      (
        message.includes('Warning: SvelteComponent') ||
        message.includes('deprecated') ||
        message.includes('legacy')
      )
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
  
  console.warn = (...args) => {
    const message = args[0];
    if (
      typeof message === 'string' &&
      (
        message.includes('deprecated') ||
        message.includes('legacy')
      )
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterEach(() => {
  // Reset MSW handlers
  server.resetHandlers();
  
  // Clear all mocks
  vi.clearAllMocks();
  
  // Clear local/session storage
  localStorageMock.clear();
  sessionStorageMock.clear();
});

afterAll(() => {
  // Stop MSW server
  server.close();
  
  // Restore console methods
  console.error = originalError;
  console.warn = originalWarn;
});

// Custom matchers
expect.extend({
  toHaveValidationError(received: any, expectedError: string) {
    const pass = received && received.includes && received.includes(expectedError);
    if (pass) {
      return {
        message: () => `expected ${received} not to contain validation error ${expectedError}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to contain validation error ${expectedError}`,
        pass: false,
      };
    }
  },
  
  toBeAccessible(received: any) {
    // Basic accessibility checks
    const hasAriaLabel = received.getAttribute('aria-label');
    const hasRole = received.getAttribute('role');
    const hasTabIndex = received.getAttribute('tabindex');
    
    const pass = hasAriaLabel || hasRole || received.tagName?.toLowerCase() === 'button';
    
    if (pass) {
      return {
        message: () => `expected element not to be accessible`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected element to be accessible (have aria-label, role, or be a semantic element)`,
        pass: false,
      };
    }
  }
});

// Global test helpers
global.testHelpers = {
  // Helper to wait for async operations
  waitFor: async (callback: () => any, timeout = 5000) => {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      try {
        const result = await callback();
        if (result) return result;
      } catch (error) {
        // Continue waiting
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    throw new Error(`Timeout waiting for condition after ${timeout}ms`);
  },
  
  // Helper to create mock events
  createMockEvent: (type: string, properties = {}) => {
    const event = new Event(type, { bubbles: true, cancelable: true });
    Object.assign(event, properties);
    return event;
  },
  
  // Helper to mock API responses
  mockApiResponse: (data: any, status = 200) => ({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  }),
  
  // Helper to create test user
  createTestUser: (overrides = {}) => ({
    id: 'test-user-123',
    username: 'testuser',
    email: 'test@example.com',
    isActive: true,
    isAdmin: false,
    createdAt: new Date().toISOString(),
    ...overrides
  }),
  
  // Helper to create test MCP server
  createTestMCPServer: (overrides = {}) => ({
    id: 1,
    name: 'test-server',
    description: 'Test MCP server',
    host: 'localhost',
    port: 8080,
    protocol: 'stdio',
    status: 'active',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides
  })
};

// Test environment configuration
process.env.NODE_ENV = 'test';
process.env.VITE_API_URL = 'http://localhost:8000';
process.env.VITE_WS_URL = 'ws://localhost:8000';

// Silence specific warnings
const originalConsoleWarn = global.console.warn;
global.console.warn = (...args) => {
  const warningMessage = args[0];
  
  // Suppress known warnings that are not actionable in tests
  const suppressedWarnings = [
    'Warning: Svelte component',
    'deprecated',
    'legacy'
  ];
  
  if (suppressedWarnings.some(warning => warningMessage && warningMessage.includes(warning))) {
    return;
  }
  
  originalConsoleWarn.apply(console, args);
};