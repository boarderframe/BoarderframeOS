/**
 * Comprehensive unit tests for ServerCard Svelte component
 */
import { render, screen, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import ServerCard from '$lib/components/ServerCard.svelte';
import type { MCPServer } from '$lib/types';

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

    it('does not render metrics when server is stopped', () => {
      const server = createMockServer({ 
        status: 'stopped',
        metrics: undefined 
      });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Metrics should not be visible
      expect(screen.queryByText('CPU')).not.toBeInTheDocument();
      expect(screen.queryByText('Memory')).not.toBeInTheDocument();
      expect(screen.queryByText('Connections')).not.toBeInTheDocument();
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

  describe('Status Indicators', () => {
    const statusTests = [
      { status: 'running' as const, expectedClasses: ['text-green-500'], shouldAnimate: false },
      { status: 'stopped' as const, expectedClasses: ['text-gray-400'], shouldAnimate: false },
      { status: 'error' as const, expectedClasses: ['text-red-500'], shouldAnimate: false },
      { status: 'starting' as const, expectedClasses: ['text-blue-500', 'animate-spin'], shouldAnimate: true },
      { status: 'stopping' as const, expectedClasses: ['text-orange-500', 'animate-spin'], shouldAnimate: true }
    ];

    statusTests.forEach(({ status, expectedClasses }) => {
      it(`displays correct icon and styling for ${status} status`, () => {
        const server = createMockServer({ status });
        
        render(ServerCard, {
          props: {
            server,
            isSelected: false
          }
        });

        const statusIcon = screen.getByRole('button', { name: new RegExp(status) }).querySelector('svg');
        expect(statusIcon).toBeInTheDocument();
        
        expectedClasses.forEach(className => {
          expect(statusIcon).toHaveClass(className);
        });
      });
    });

    it('shows activity indicator for running servers', () => {
      const server = createMockServer({ status: 'running' });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Should have activity icon with pulse animation
      const activityIcon = document.querySelector('.animate-pulse-slow');
      expect(activityIcon).toBeInTheDocument();
    });

    it('does not show activity indicator for non-running servers', () => {
      const server = createMockServer({ status: 'stopped' });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Should not have activity icon
      const activityIcon = document.querySelector('.animate-pulse-slow');
      expect(activityIcon).not.toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('shows start button when server is stopped', () => {
      const server = createMockServer({ status: 'stopped' });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const startButton = screen.getByRole('button', { name: 'Start server' });
      expect(startButton).toBeInTheDocument();
      expect(startButton).toHaveTextContent('Start');
    });

    it('shows stop and restart buttons when server is running', () => {
      const server = createMockServer({ status: 'running' });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      const restartButton = screen.getByRole('button', { name: 'Restart server' });
      
      expect(stopButton).toBeInTheDocument();
      expect(restartButton).toBeInTheDocument();
      
      expect(stopButton).toHaveTextContent('Stop');
      expect(restartButton).toHaveTextContent('Restart');
    });

    it('always shows configure button', () => {
      const statuses: Array<MCPServer['status']> = ['running', 'stopped', 'error', 'starting', 'stopping'];
      
      statuses.forEach(status => {
        const server = createMockServer({ status });
        const { unmount } = render(ServerCard, {
          props: {
            server,
            isSelected: false
          }
        });

        const configureButton = screen.getByRole('button', { name: 'Configure server' });
        expect(configureButton).toBeInTheDocument();
        
        unmount();
      });
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

    it('handles keyboard navigation', async () => {
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
      
      // Test Enter key
      card.focus();
      await user.keyboard('{Enter}');
      expect(clickHandler).toHaveBeenCalledTimes(1);

      // Test Space key
      await user.keyboard(' ');
      expect(clickHandler).toHaveBeenCalledTimes(2);
    });

    it('prevents event propagation for action buttons', async () => {
      const user = userEvent.setup();
      const server = createMockServer({ status: 'running' });
      
      const { component } = render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const clickHandler = vi.fn();
      const stopHandler = vi.fn();
      component.$on('click', clickHandler);
      component.$on('stop', stopHandler);

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      await user.click(stopButton);

      // Action handler should be called
      expect(stopHandler).toHaveBeenCalledTimes(1);
      
      // Card click should not be called due to event.stopPropagation()
      expect(clickHandler).not.toHaveBeenCalled();
    });

    it('dispatches appropriate action events', async () => {
      const user = userEvent.setup();
      
      // Test start action
      const stoppedServer = createMockServer({ status: 'stopped' });
      const { component, rerender } = render(ServerCard, {
        props: {
          server: stoppedServer,
          isSelected: false
        }
      });

      const startHandler = vi.fn();
      component.$on('start', startHandler);

      const startButton = screen.getByRole('button', { name: 'Start server' });
      await user.click(startButton);
      expect(startHandler).toHaveBeenCalledTimes(1);

      // Test stop and restart actions
      const runningServer = createMockServer({ status: 'running' });
      await rerender({ 
        server: runningServer,
        isSelected: false
      });

      const stopHandler = vi.fn();
      const restartHandler = vi.fn();
      const configureHandler = vi.fn();
      
      component.$on('stop', stopHandler);
      component.$on('restart', restartHandler);
      component.$on('configure', configureHandler);

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      const restartButton = screen.getByRole('button', { name: 'Restart server' });
      const configureButton = screen.getByRole('button', { name: 'Configure server' });
      
      await user.click(stopButton);
      expect(stopHandler).toHaveBeenCalledTimes(1);

      await user.click(restartButton);
      expect(restartHandler).toHaveBeenCalledTimes(1);

      await user.click(configureButton);
      expect(configureHandler).toHaveBeenCalledTimes(1);
    });
  });

  describe('Selection State', () => {
    it('applies selection styling when selected', () => {
      const server = createMockServer();
      
      render(ServerCard, {
        props: {
          server,
          isSelected: true
        }
      });

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).toHaveClass('ring-2', 'ring-primary-500', 'ring-offset-2');
    });

    it('does not apply selection styling when not selected', () => {
      const server = createMockServer();
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).not.toHaveClass('ring-2', 'ring-primary-500', 'ring-offset-2');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      const server = createMockServer();
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      // Main card should have aria-label
      const card = screen.getByRole('button', { name: 'Server Test MCP Server - running' });
      expect(card).toBeInTheDocument();

      // Action buttons should have aria-labels
      expect(screen.getByRole('button', { name: 'Stop server' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Restart server' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Configure server' })).toBeInTheDocument();
    });

    it('has proper tabIndex for keyboard navigation', () => {
      const server = createMockServer();
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).toHaveAttribute('tabindex', '0');
    });

    it('supports screen readers with proper role', () => {
      const server = createMockServer();
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).toHaveAttribute('role', 'button');
    });
  });

  describe('Error Handling', () => {
    it('handles malformed server data gracefully', () => {
      const malformedServer = {
        ...createMockServer(),
        config: {
          host: '',
          port: NaN
        },
        metrics: {
          cpuUsage: NaN,
          memoryUsage: NaN,
          connections: NaN
        }
      } as any;
      
      expect(() => {
        render(ServerCard, {
          props: {
            server: malformedServer,
            isSelected: false
          }
        });
      }).not.toThrow();

      // Should still render without crashing
      expect(screen.getByText('Test MCP Server')).toBeInTheDocument();
    });

    it('handles missing metrics gracefully', () => {
      const serverWithoutMetrics = createMockServer({
        metrics: undefined
      });
      
      render(ServerCard, {
        props: {
          server: serverWithoutMetrics,
          isSelected: false
        }
      });

      // Should not crash and should not show metrics section
      expect(screen.queryByText('CPU')).not.toBeInTheDocument();
    });
  });

  describe('Utility Functions', () => {
    it('formats uptime correctly', () => {
      const testCases = [
        { uptime: 0, expected: '0h 0m' },
        { uptime: 60, expected: '0h 1m' },
        { uptime: 3600, expected: '1h 0m' },
        { uptime: 3661, expected: '1h 1m' },
        { uptime: 7200, expected: '2h 0m' },
        { uptime: 90061, expected: '25h 1m' }
      ];

      testCases.forEach(({ uptime, expected }) => {
        const server = createMockServer({ uptime });
        const { unmount } = render(ServerCard, {
          props: {
            server,
            isSelected: false
          }
        });

        expect(screen.getByText(expected)).toBeInTheDocument();
        unmount();
      });
    });

    it('handles undefined uptime', () => {
      const server = createMockServer({ uptime: undefined });
      
      render(ServerCard, {
        props: {
          server,
          isSelected: false
        }
      });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });
});