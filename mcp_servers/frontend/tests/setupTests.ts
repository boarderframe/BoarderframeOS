/**
 * Vitest setup file for Svelte frontend testing
 */

// Import Jest DOM matchers for Vitest
import '@testing-library/jest-dom';

// Import MSW for API mocking
import { server } from './mocks/server';

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

beforeAll(() => {
  // Start MSW server
  server.listen({ onUnhandledRequest: 'error' });
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
});

// Test environment configuration
process.env.NODE_ENV = 'test';
process.env.VITE_API_URL = 'http://localhost:8000';
process.env.VITE_WS_URL = 'ws://localhost:8000';