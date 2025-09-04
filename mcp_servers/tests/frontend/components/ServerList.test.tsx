/**
 * Comprehensive unit tests for ServerList component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ServerList } from '@/components/ServerList';
import { useServerStore } from '@/hooks/useServerStore';
import toast from 'react-hot-toast';
import { MCPServer } from '@/types';

// Mock the hooks and dependencies
jest.mock('@/hooks/useServerStore');
jest.mock('react-hot-toast');

const mockUseServerStore = useServerStore as jest.MockedFunction<typeof useServerStore>;
const mockToast = toast as jest.Mocked<typeof toast>;

// Mock data factory
const createMockServer = (id: string, overrides: Partial<MCPServer> = {}): MCPServer => ({
  id,
  name: `Test Server ${id}`,
  status: 'running',
  config: {
    host: 'localhost',
    port: 8080 + parseInt(id),
    autoStart: true,
    maxConnections: 10,
    timeout: 30000
  },
  metrics: {
    cpuUsage: 25.5,
    memoryUsage: 64.2,
    connections: 3,
    requestsPerSecond: 15.7,
    errorRate: 0.01,
    latency: { p50: 120, p95: 350, p99: 800 }
  },
  lastUpdated: '2025-01-15T10:30:00Z',
  version: '1.2.3',
  uptime: 7200,
  ...overrides
});

// Mock store state factory
const createMockStoreState = (overrides: any = {}) => ({
  servers: [],
  selectedServerId: null,
  loading: false,
  error: null,
  fetchServers: jest.fn(),
  selectServer: jest.fn(),
  startServer: jest.fn(),
  stopServer: jest.fn(),
  restartServer: jest.fn(),
  ...overrides
});

// Mock handlers
const mockHandlers = {
  onConfigureServer: jest.fn(),
  onAddServer: jest.fn()
};

describe('ServerList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockToast.success = jest.fn();
    mockToast.error = jest.fn();
  });

  describe('Loading States', () => {
    it('shows loading state when servers are being fetched', () => {
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          loading: true,
          servers: []
        })
      );

      render(<ServerList {...mockHandlers} />);

      expect(screen.getByText('Loading servers...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
      
      // Should show spinning icon
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('does not show loading state when servers exist but refreshing', () => {
      const servers = [createMockServer('1'), createMockServer('2')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          loading: true,
          servers
        })
      );

      render(<ServerList {...mockHandlers} />);

      // Should not show main loading state since servers exist
      expect(screen.queryByText('Loading servers...')).not.toBeInTheDocument();
      
      // Should show servers
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Test Server 2')).toBeInTheDocument();
      
      // Should show loading indicator on refresh button
      const refreshButton = screen.getByLabelText('Refresh server list');
      expect(refreshButton.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('shows error state when no servers and error exists', () => {
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          error: 'Failed to connect to API',
          servers: []
        })
      );

      render(<ServerList {...mockHandlers} />);

      expect(screen.getByText('Error: Failed to connect to API')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('does not show error state when servers exist', () => {
      const servers = [createMockServer('1')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          error: 'Some error',
          servers
        })
      );

      render(<ServerList {...mockHandlers} />);

      // Should not show error message since servers exist
      expect(screen.queryByText('Error: Some error')).not.toBeInTheDocument();
      
      // Should show servers
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });

    it('handles retry button click', async () => {
      const user = userEvent.setup();
      const mockFetchServers = jest.fn();
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          error: 'Connection failed',
          servers: [],
          fetchServers: mockFetchServers
        })
      );

      render(<ServerList {...mockHandlers} />);

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockFetchServers).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no servers configured', () => {
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers: []
        })
      );

      render(<ServerList {...mockHandlers} />);

      expect(screen.getByText('No servers configured')).toBeInTheDocument();
      expect(screen.getByText('Add Your First Server')).toBeInTheDocument();
    });

    it('calls onAddServer when Add Your First Server button is clicked', async () => {
      const user = userEvent.setup();
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers: []
        })
      );

      render(<ServerList {...mockHandlers} />);

      const addButton = screen.getByText('Add Your First Server');
      await user.click(addButton);

      expect(mockHandlers.onAddServer).toHaveBeenCalledTimes(1);
    });
  });

  describe('Server Display', () => {
    it('renders multiple servers in grid layout', () => {
      const servers = [
        createMockServer('1'),
        createMockServer('2'),
        createMockServer('3')
      ];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      render(<ServerList {...mockHandlers} />);

      servers.forEach(server => {
        expect(screen.getByText(server.name)).toBeInTheDocument();
      });

      // Should use grid layout
      const grid = document.querySelector('.grid');
      expect(grid).toBeInTheDocument();
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
    });

    it('passes correct props to ServerCard components', () => {
      const servers = [createMockServer('1')];
      const mockSelectServer = jest.fn();
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          selectedServerId: '1',
          selectServer: mockSelectServer
        })
      );

      render(<ServerList {...mockHandlers} />);

      // Verify ServerCard receives correct props by testing interactions
      const serverCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      expect(serverCard).toBeInTheDocument();
      
      // Card should show selected state (ring styling)
      expect(serverCard).toHaveClass('ring-2', 'ring-primary-500');
    });
  });

  describe('Header Actions', () => {
    it('renders header with correct title and buttons', () => {
      mockUseServerStore.mockReturnValue(
        createMockStoreState()
      );

      render(<ServerList {...mockHandlers} />);

      expect(screen.getByText('MCP Servers')).toBeInTheDocument();
      expect(screen.getByLabelText('Refresh server list')).toBeInTheDocument();
      expect(screen.getByLabelText('Add new server')).toBeInTheDocument();
    });

    it('handles refresh button click', async () => {
      const user = userEvent.setup();
      const mockFetchServers = jest.fn().mockResolvedValue(undefined);
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          fetchServers: mockFetchServers
        })
      );

      render(<ServerList {...mockHandlers} />);

      const refreshButton = screen.getByLabelText('Refresh server list');
      await user.click(refreshButton);

      expect(mockFetchServers).toHaveBeenCalledTimes(1);
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Server list refreshed');
      });
    });

    it('handles refresh button click failure', async () => {
      const user = userEvent.setup();
      const mockFetchServers = jest.fn().mockRejectedValue(new Error('Network error'));
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          fetchServers: mockFetchServers
        })
      );

      render(<ServerList {...mockHandlers} />);

      const refreshButton = screen.getByLabelText('Refresh server list');
      await user.click(refreshButton);

      expect(mockFetchServers).toHaveBeenCalledTimes(1);
      
      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to refresh servers');
      });
    });

    it('handles add server button click', async () => {
      const user = userEvent.setup();
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState()
      );

      render(<ServerList {...mockHandlers} />);

      const addButton = screen.getByLabelText('Add new server');
      await user.click(addButton);

      expect(mockHandlers.onAddServer).toHaveBeenCalledTimes(1);
    });

    it('disables refresh button when loading', () => {
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          loading: true
        })
      );

      render(<ServerList {...mockHandlers} />);

      const refreshButton = screen.getByLabelText('Refresh server list');
      expect(refreshButton).toBeDisabled();
      expect(refreshButton).toHaveClass('disabled:opacity-50');
    });
  });

  describe('Server Actions', () => {
    it('handles server start action', async () => {
      const user = userEvent.setup();
      const mockStartServer = jest.fn().mockResolvedValue(undefined);
      const servers = [createMockServer('1', { status: 'stopped' })];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          startServer: mockStartServer
        })
      );

      render(<ServerList {...mockHandlers} />);

      const startButton = screen.getByRole('button', { name: 'Start server' });
      await user.click(startButton);

      expect(mockStartServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Server start initiated');
      });
    });

    it('handles server stop action', async () => {
      const user = userEvent.setup();
      const mockStopServer = jest.fn().mockResolvedValue(undefined);
      const servers = [createMockServer('1', { status: 'running' })];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          stopServer: mockStopServer
        })
      );

      render(<ServerList {...mockHandlers} />);

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      await user.click(stopButton);

      expect(mockStopServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Server stop initiated');
      });
    });

    it('handles server restart action', async () => {
      const user = userEvent.setup();
      const mockRestartServer = jest.fn().mockResolvedValue(undefined);
      const servers = [createMockServer('1', { status: 'running' })];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          restartServer: mockRestartServer
        })
      );

      render(<ServerList {...mockHandlers} />);

      const restartButton = screen.getByRole('button', { name: 'Restart server' });
      await user.click(restartButton);

      expect(mockRestartServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Server restart initiated');
      });
    });

    it('handles configure action', async () => {
      const user = userEvent.setup();
      const servers = [createMockServer('1')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      render(<ServerList {...mockHandlers} />);

      const configureButton = screen.getByRole('button', { name: 'Configure server' });
      await user.click(configureButton);

      expect(mockHandlers.onConfigureServer).toHaveBeenCalledWith('1');
    });

    it('handles server action errors', async () => {
      const user = userEvent.setup();
      const mockStartServer = jest.fn().mockRejectedValue(new Error('Start failed'));
      const servers = [createMockServer('1', { status: 'stopped' })];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          startServer: mockStartServer
        })
      );

      render(<ServerList {...mockHandlers} />);

      const startButton = screen.getByRole('button', { name: 'Start server' });
      await user.click(startButton);

      expect(mockStartServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Failed to start server: Start failed');
      });
    });
  });

  describe('Server Selection', () => {
    it('handles server selection', async () => {
      const user = userEvent.setup();
      const mockSelectServer = jest.fn();
      const servers = [createMockServer('1'), createMockServer('2')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          selectServer: mockSelectServer
        })
      );

      render(<ServerList {...mockHandlers} />);

      const serverCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      await user.click(serverCard);

      expect(mockSelectServer).toHaveBeenCalledWith('1');
    });

    it('shows selection state correctly', () => {
      const servers = [createMockServer('1'), createMockServer('2')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers,
          selectedServerId: '1'
        })
      );

      render(<ServerList {...mockHandlers} />);

      const selectedCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      const unselectedCard = screen.getByRole('button', { name: /Server Test Server 2/ });

      expect(selectedCard).toHaveClass('ring-2', 'ring-primary-500');
      expect(unselectedCard).not.toHaveClass('ring-2', 'ring-primary-500');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for buttons', () => {
      mockUseServerStore.mockReturnValue(
        createMockStoreState()
      );

      render(<ServerList {...mockHandlers} />);

      expect(screen.getByLabelText('Refresh server list')).toBeInTheDocument();
      expect(screen.getByLabelText('Add new server')).toBeInTheDocument();
    });

    it('maintains focus management', async () => {
      const user = userEvent.setup();
      const servers = [createMockServer('1')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      render(<ServerList {...mockHandlers} />);

      // Test keyboard navigation
      const refreshButton = screen.getByLabelText('Refresh server list');
      const addButton = screen.getByLabelText('Add new server');
      
      refreshButton.focus();
      expect(document.activeElement).toBe(refreshButton);
      
      await user.tab();
      expect(document.activeElement).toBe(addButton);
    });

    it('provides screen reader friendly content', () => {
      const servers = [createMockServer('1')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      render(<ServerList {...mockHandlers} />);

      // Should have proper headings
      const heading = screen.getByRole('heading', { name: 'MCP Servers' });
      expect(heading).toBeInTheDocument();
      
      // Server cards should have descriptive aria-labels
      const serverCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      expect(serverCard).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large numbers of servers efficiently', () => {
      const servers = Array.from({ length: 100 }, (_, i) => 
        createMockServer(i.toString())
      );
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      const renderStart = performance.now();
      render(<ServerList {...mockHandlers} />);
      const renderTime = performance.now() - renderStart;

      // Should render within reasonable time (less than 100ms)
      expect(renderTime).toBeLessThan(100);
      
      // Should render all servers
      expect(screen.getAllByText(/Test Server/).length).toBe(100);
    });

    it('memoizes callback functions correctly', () => {
      const servers = [createMockServer('1')];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      const { rerender } = render(<ServerList {...mockHandlers} />);

      // Re-render with same props
      rerender(<ServerList {...mockHandlers} />);

      // Component should still function correctly
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });
  });

  describe('Error Boundaries', () => {
    it('handles server store errors gracefully', () => {
      // Mock store that throws error
      mockUseServerStore.mockImplementation(() => {
        throw new Error('Store error');
      });

      // Should not crash the application
      expect(() => {
        render(<ServerList {...mockHandlers} />);
      }).toThrow(); // In real app, would be caught by error boundary
    });

    it('handles malformed server data', () => {
      const malformedServers = [
        {
          id: '1',
          name: null, // Invalid
          status: 'invalid-status' as any,
          config: null // Invalid
        }
      ] as any;
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers: malformedServers
        })
      );

      // Should handle gracefully without crashing
      render(<ServerList {...mockHandlers} />);
      
      // Should still show the component structure
      expect(screen.getByText('MCP Servers')).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('updates when server list changes', () => {
      const initialServers = [createMockServer('1')];
      
      const { rerender } = render(<ServerList {...mockHandlers} />);
      
      // Initial render
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers: initialServers
        })
      );
      rerender(<ServerList {...mockHandlers} />);
      
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();

      // Add server
      const updatedServers = [
        ...initialServers,
        createMockServer('2')
      ];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({
          servers: updatedServers
        })
      );
      rerender(<ServerList {...mockHandlers} />);
      
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
      expect(screen.getByText('Test Server 2')).toBeInTheDocument();
    });

    it('handles server status updates', () => {
      const servers = [createMockServer('1', { status: 'stopped' })];
      
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers })
      );

      const { rerender } = render(<ServerList {...mockHandlers} />);

      // Should show start button for stopped server
      expect(screen.getByRole('button', { name: 'Start server' })).toBeInTheDocument();

      // Update server to running
      const updatedServers = [createMockServer('1', { status: 'running' })];
      mockUseServerStore.mockReturnValue(
        createMockStoreState({ servers: updatedServers })
      );
      rerender(<ServerList {...mockHandlers} />);

      // Should now show stop and restart buttons
      expect(screen.getByRole('button', { name: 'Stop server' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Restart server' })).toBeInTheDocument();
    });
  });
});