/**
 * MSW (Mock Service Worker) server setup for API mocking in tests
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup MSW server with request handlers
export const server = setupServer(...handlers);