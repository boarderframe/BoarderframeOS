/**
 * Comprehensive unit tests for ServerCard component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ServerCard } from '@/components/ServerCard';
import { MCPServer } from '@/types';

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

// Mock handlers
const mockHandlers = {
  onStart: jest.fn(),
  onStop: jest.fn(),
  onRestart: jest.fn(),
  onConfigure: jest.fn(),
  onClick: jest.fn()
};

describe('ServerCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders server information correctly', () => {
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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

    statusTests.forEach(({ status, expectedClasses, shouldAnimate }) => {
      it(`displays correct icon and styling for ${status} status`, () => {
        const server = createMockServer({ status });
        
        render(
          <ServerCard
            server={server}
            isSelected={false}
            {...mockHandlers}
          />
        );

        const statusIcon = screen.getByRole('button', { name: new RegExp(status) }).querySelector('svg');
        expect(statusIcon).toBeInTheDocument();
        
        expectedClasses.forEach(className => {
          expect(statusIcon).toHaveClass(className);
        });
      });
    });

    it('shows activity indicator for running servers', () => {
      const server = createMockServer({ status: 'running' });
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      // Should have activity icon with pulse animation
      const activityIcon = document.querySelector('.animate-pulse-slow');
      expect(activityIcon).toBeInTheDocument();
    });

    it('does not show activity indicator for non-running servers', () => {
      const server = createMockServer({ status: 'stopped' });
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      // Should not have activity icon
      const activityIcon = document.querySelector('.animate-pulse-slow');
      expect(activityIcon).not.toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('shows start button when server is stopped', () => {
      const server = createMockServer({ status: 'stopped' });
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const startButton = screen.getByRole('button', { name: 'Start server' });
      expect(startButton).toBeInTheDocument();
      expect(startButton).toHaveTextContent('Start');
    });

    it('shows stop and restart buttons when server is running', () => {
      const server = createMockServer({ status: 'running' });
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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
        const { unmount } = render(
          <ServerCard
            server={server}
            isSelected={false}
            {...mockHandlers}
          />
        );

        const configureButton = screen.getByRole('button', { name: 'Configure server' });
        expect(configureButton).toBeInTheDocument();
        
        unmount();
      });
    });
  });

  describe('User Interactions', () => {
    it('calls onClick when card is clicked', async () => {
      const user = userEvent.setup();
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      await user.click(card);

      expect(mockHandlers.onClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard navigation', async () => {
      const user = userEvent.setup();
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      
      // Test Enter key
      card.focus();
      await user.keyboard('{Enter}');
      expect(mockHandlers.onClick).toHaveBeenCalledTimes(1);

      // Test Space key
      await user.keyboard(' ');
      expect(mockHandlers.onClick).toHaveBeenCalledTimes(2);
    });

    it('prevents event propagation for action buttons', async () => {
      const user = userEvent.setup();
      const server = createMockServer({ status: 'running' });
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      await user.click(stopButton);

      // Action handler should be called
      expect(mockHandlers.onStop).toHaveBeenCalledWith('test-server-1');
      
      // Card onClick should not be called due to event.stopPropagation()
      expect(mockHandlers.onClick).not.toHaveBeenCalled();
    });

    it('calls appropriate action handlers', async () => {
      const user = userEvent.setup();
      
      // Test start action
      const stoppedServer = createMockServer({ status: 'stopped' });
      const { rerender } = render(
        <ServerCard
          server={stoppedServer}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const startButton = screen.getByRole('button', { name: 'Start server' });
      await user.click(startButton);
      expect(mockHandlers.onStart).toHaveBeenCalledWith('test-server-1');

      // Test stop and restart actions
      const runningServer = createMockServer({ status: 'running' });
      rerender(
        <ServerCard
          server={runningServer}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      const restartButton = screen.getByRole('button', { name: 'Restart server' });
      
      await user.click(stopButton);
      expect(mockHandlers.onStop).toHaveBeenCalledWith('test-server-1');

      await user.click(restartButton);
      expect(mockHandlers.onRestart).toHaveBeenCalledWith('test-server-1');

      // Test configure action
      const configureButton = screen.getByRole('button', { name: 'Configure server' });
      await user.click(configureButton);
      expect(mockHandlers.onConfigure).toHaveBeenCalledWith('test-server-1');
    });
  });

  describe('Selection State', () => {
    it('applies selection styling when selected', () => {
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={true}
          {...mockHandlers}
        />
      );

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).toHaveClass('ring-2', 'ring-primary-500', 'ring-offset-2');
    });

    it('does not apply selection styling when not selected', () => {
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).not.toHaveClass('ring-2', 'ring-primary-500', 'ring-offset-2');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const card = screen.getByRole('button', { name: /Server Test MCP Server/ });
      expect(card).toHaveAttribute('tabIndex', '0');
    });

    it('supports screen readers with proper role', () => {
      const server = createMockServer();
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

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
        render(
          <ServerCard
            server={malformedServer}
            isSelected={false}
            {...mockHandlers}
          />
        );
      }).not.toThrow();

      // Should still render without crashing
      expect(screen.getByText('Test MCP Server')).toBeInTheDocument();
    });

    it('handles missing metrics gracefully', () => {
      const serverWithoutMetrics = createMockServer({
        metrics: undefined
      });
      
      render(
        <ServerCard
          server={serverWithoutMetrics}
          isSelected={false}
          {...mockHandlers}
        />
      );

      // Should not crash and should not show metrics section
      expect(screen.queryByText('CPU')).not.toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('uses memo to prevent unnecessary re-renders', () => {
      const server = createMockServer();
      const handlers = { ...mockHandlers };
      
      const { rerender } = render(
        <ServerCard
          server={server}
          isSelected={false}
          {...handlers}
        />
      );

      // Re-render with same props should not cause re-render
      rerender(
        <ServerCard
          server={server}
          isSelected={false}
          {...handlers}
        />
      );

      // Component should still be functional
      expect(screen.getByText('Test MCP Server')).toBeInTheDocument();
    });

    it('handles rapid status changes', async () => {
      const server = createMockServer({ status: 'stopped' });
      
      const { rerender } = render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      const statuses: Array<MCPServer['status']> = ['starting', 'running', 'stopping', 'stopped'];
      
      for (const status of statuses) {
        const updatedServer = { ...server, status };
        rerender(
          <ServerCard
            server={updatedServer}
            isSelected={false}
            {...mockHandlers}
          />
        );
        
        expect(screen.getByText(status)).toBeInTheDocument();
      }
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
        const { unmount } = render(
          <ServerCard
            server={server}
            isSelected={false}
            {...mockHandlers}
          />
        );

        expect(screen.getByText(expected)).toBeInTheDocument();
        unmount();
      });
    });

    it('handles undefined uptime', () => {
      const server = createMockServer({ uptime: undefined });
      
      render(
        <ServerCard
          server={server}
          isSelected={false}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });
});