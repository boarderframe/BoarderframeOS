/**
 * Comprehensive unit tests for ServerCard Svelte component
 */
import { render, screen, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import ServerCard from '../lib/components/ServerCard.svelte';
import type { MCPServer } from '../lib/types';

// Mock data factory for ServerCard tests
const createMockServer = (overrides: Partial<MCPServer> = {}): MCPServer => ({
  id: 'test-server-1',
  name: 'Test MCP Server',
  status: 'running',
  config: {
    host: 'localhost',
    port: 8080,
    autoStart: true,
    maxConnections: 10,
    timeout: 30000,
    environment: { NODE_ENV: 'test' },
    command: '/usr/bin/node',
    args: ['-e', 'console.log("test")']
  },
  metrics: {
    cpuUsage: 25.5,
    memoryUsage: 64.2,
    connections: 3,
    requestsPerSecond: 15.7,
    errorRate: 0.01,
    latency: {
      p50: 120,
      p95: 350,
      p99: 800
    }
  },
  lastUpdated: '2025-01-15T10:30:00Z',
  version: '1.2.3',
  uptime: 7200, // 2 hours
  ...overrides
});

describe('ServerCard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders server information correctly', () => {
      const server = createMockServer();
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Check server name
      expect(screen.getByText('Test MCP Server')).toBeInTheDocument();
      
      // Check status
      expect(screen.getByText('running')).toBeInTheDocument();
      
      // Check host and port
      expect(screen.getByText('localhost:8080')).toBeInTheDocument();
      
      // Check version
      expect(screen.getByText('1.2.3')).toBeInTheDocument();
      
      // Check uptime formatting
      expect(screen.getByText('2h 0m')).toBeInTheDocument();
    });

    it('renders metrics when server is running', () => {
      const server = createMockServer({ status: 'running' });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Check CPU usage
      expect(screen.getByText('25.5%')).toBeInTheDocument();
      
      // Check memory usage
      expect(screen.getByText('64.2%')).toBeInTheDocument();
      
      // Check connections
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('handles missing optional fields gracefully', () => {
      const server = createMockServer({
        version: undefined,
        uptime: undefined,
        metrics: undefined
      });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Should not crash and should show N/A for missing uptime
      expect(screen.getByText('N/A')).toBeInTheDocument();
      
      // Version should not be displayed
      expect(screen.queryByText('Version:')).not.toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('dispatches click event when card is clicked', async () => {
      const user = userEvent.setup();
      const server = createMockServer();
      
      const { component } = render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const clickHandler = vi.fn();
      component.$on('click', clickHandler);

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      await user.click(card);

      expect(clickHandler).toHaveBeenCalledTimes(1);
    });
  });
});