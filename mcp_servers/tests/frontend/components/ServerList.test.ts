/**
 * Comprehensive unit tests for ServerList Svelte component
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { get, writable } from 'svelte/store';
import ServerList from '$lib/components/ServerList.svelte';
import { serverStore } from '$lib/stores/serverStore';
import type { MCPServer } from '$lib/types';

// Mock the server store
vi.mock('$lib/stores/serverStore', () => {
  const mockStore = writable({
    servers: [],
    selectedServerId: null,
    loading: false,
    error: null,
    fetchServers: vi.fn(),
    selectServer: vi.fn(),
    startServer: vi.fn(),
    stopServer: vi.fn(),
    restartServer: vi.fn(),
  });
  
  return {
    serverStore: mockStore
  };
});

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
    latency: { p50: 120, p95: 350, p99: 800 }
  },
  lastUpdated: '2025-01-15T10:30:00Z',
  version: '1.2.3',
  uptime: 7200,
  ...overrides
});

// Helper to set store state
const setStoreState = (state: any) => {
  serverStore.set({
    servers: [],
    selectedServerId: null,
    loading: false,
    error: null,
    fetchServers: vi.fn(),
    selectServer: vi.fn(),
    startServer: vi.fn(),
    stopServer: vi.fn(),
    restartServer: vi.fn(),
    ...state
  });
};

// Mock console methods
const mockConsole = {
  log: vi.fn(),
  error: vi.fn()
};

describe('ServerList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.console.log = mockConsole.log;
    global.console.error = mockConsole.error;
    
    // Reset store to initial state
    setStoreState({});
  });

  describe('Loading States', () => {
    it('shows loading state when servers are being fetched', () => {
      setStoreState({
        loading: true,
        servers: []
      });

      render(ServerList);

      expect(screen.getByText('Loading servers...')).toBeInTheDocument();
      
      // Should show spinning icon
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('does not show loading state when servers exist but refreshing', () => {
      const servers = [createMockServer('1'), createMockServer('2')];
      
      setStoreState({
        loading: true,
        servers
      });

      render(ServerList);

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
      setStoreState({
        error: 'Failed to connect to API',
        servers: []
      });

      render(ServerList);

      expect(screen.getByText('Error: Failed to connect to API')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('does not show error state when servers exist', () => {
      const servers = [createMockServer('1')];
      
      setStoreState({
        error: 'Some error',
        servers
      });

      render(ServerList);

      // Should not show error message since servers exist
      expect(screen.queryByText('Error: Some error')).not.toBeInTheDocument();
      
      // Should show servers
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();
    });

    it('handles retry button click', async () => {
      const user = userEvent.setup();
      const mockFetchServers = vi.fn();
      
      setStoreState({
        error: 'Connection failed',
        servers: [],
        fetchServers: mockFetchServers
      });

      render(ServerList);

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockFetchServers).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no servers configured', () => {
      setStoreState({
        servers: []
      });

      render(ServerList);

      expect(screen.getByText('No servers configured')).toBeInTheDocument();
      expect(screen.getByText('Add Your First Server')).toBeInTheDocument();
    });

    it('dispatches addServer event when Add Your First Server button is clicked', async () => {
      const user = userEvent.setup();
      
      setStoreState({
        servers: []
      });

      const { component } = render(ServerList);
      const addServerHandler = vi.fn();
      component.$on('addServer', addServerHandler);

      const addButton = screen.getByText('Add Your First Server');
      await user.click(addButton);

      expect(addServerHandler).toHaveBeenCalledTimes(1);
    });
  });

  describe('Server Display', () => {
    it('renders multiple servers in grid layout', () => {
      const servers = [
        createMockServer('1'),
        createMockServer('2'),
        createMockServer('3')
      ];
      
      setStoreState({ servers });

      render(ServerList);

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
      
      setStoreState({
        servers,
        selectedServerId: '1'
      });

      render(ServerList);

      // Verify ServerCard receives correct props by testing interactions
      const serverCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      expect(serverCard).toBeInTheDocument();
      
      // Card should show selected state (ring styling)
      expect(serverCard).toHaveClass('ring-2', 'ring-primary-500');
    });
  });

  describe('Header Actions', () => {
    it('renders header with correct title and buttons', () => {
      setStoreState({});

      render(ServerList);

      expect(screen.getByText('MCP Servers')).toBeInTheDocument();
      expect(screen.getByLabelText('Refresh server list')).toBeInTheDocument();
      expect(screen.getByLabelText('Add new server')).toBeInTheDocument();
    });

    it('handles refresh button click', async () => {
      const user = userEvent.setup();
      const mockFetchServers = vi.fn().mockResolvedValue(undefined);
      
      setStoreState({
        fetchServers: mockFetchServers
      });

      render(ServerList);

      const refreshButton = screen.getByLabelText('Refresh server list');
      await user.click(refreshButton);

      expect(mockFetchServers).toHaveBeenCalledTimes(1);
      
      await waitFor(() => {
        expect(mockConsole.log).toHaveBeenCalledWith('Server list refreshed');
      });
    });

    it('handles refresh button click failure', async () => {
      const user = userEvent.setup();
      const mockFetchServers = vi.fn().mockRejectedValue(new Error('Network error'));
      
      setStoreState({
        fetchServers: mockFetchServers
      });

      render(ServerList);

      const refreshButton = screen.getByLabelText('Refresh server list');
      await user.click(refreshButton);

      expect(mockFetchServers).toHaveBeenCalledTimes(1);
      
      await waitFor(() => {
        expect(mockConsole.error).toHaveBeenCalledWith('Failed to refresh servers');
      });
    });

    it('dispatches addServer event when add server button is clicked', async () => {
      const user = userEvent.setup();
      
      setStoreState({});

      const { component } = render(ServerList);
      const addServerHandler = vi.fn();
      component.$on('addServer', addServerHandler);

      const addButton = screen.getByLabelText('Add new server');
      await user.click(addButton);

      expect(addServerHandler).toHaveBeenCalledTimes(1);
    });

    it('disables refresh button when loading', () => {
      setStoreState({
        loading: true
      });

      render(ServerList);

      const refreshButton = screen.getByLabelText('Refresh server list');
      expect(refreshButton).toBeDisabled();
      expect(refreshButton).toHaveClass('disabled:opacity-50');
    });
  });

  describe('Server Actions', () => {
    it('handles server start action', async () => {
      const user = userEvent.setup();
      const mockStartServer = vi.fn().mockResolvedValue(undefined);
      const servers = [createMockServer('1', { status: 'stopped' })];
      
      setStoreState({
        servers,
        startServer: mockStartServer
      });

      render(ServerList);

      const startButton = screen.getByRole('button', { name: 'Start server' });
      await user.click(startButton);

      expect(mockStartServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockConsole.log).toHaveBeenCalledWith('Server start initiated');
      });
    });

    it('handles server stop action', async () => {
      const user = userEvent.setup();
      const mockStopServer = vi.fn().mockResolvedValue(undefined);
      const servers = [createMockServer('1', { status: 'running' })];
      
      setStoreState({
        servers,
        stopServer: mockStopServer
      });

      render(ServerList);

      const stopButton = screen.getByRole('button', { name: 'Stop server' });
      await user.click(stopButton);

      expect(mockStopServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockConsole.log).toHaveBeenCalledWith('Server stop initiated');
      });
    });

    it('handles server restart action', async () => {
      const user = userEvent.setup();
      const mockRestartServer = vi.fn().mockResolvedValue(undefined);
      const servers = [createMockServer('1', { status: 'running' })];
      
      setStoreState({
        servers,
        restartServer: mockRestartServer
      });

      render(ServerList);

      const restartButton = screen.getByRole('button', { name: 'Restart server' });
      await user.click(restartButton);

      expect(mockRestartServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockConsole.log).toHaveBeenCalledWith('Server restart initiated');
      });
    });

    it('dispatches configureServer event', async () => {
      const user = userEvent.setup();
      const servers = [createMockServer('1')];
      
      setStoreState({ servers });

      const { component } = render(ServerList);
      const configureHandler = vi.fn();
      component.$on('configureServer', configureHandler);

      const configureButton = screen.getByRole('button', { name: 'Configure server' });
      await user.click(configureButton);

      expect(configureHandler).toHaveBeenCalledTimes(1);
    });

    it('handles server action errors', async () => {
      const user = userEvent.setup();
      const mockStartServer = vi.fn().mockRejectedValue(new Error('Start failed'));
      const servers = [createMockServer('1', { status: 'stopped' })];
      
      setStoreState({
        servers,
        startServer: mockStartServer
      });

      render(ServerList);

      const startButton = screen.getByRole('button', { name: 'Start server' });
      await user.click(startButton);

      expect(mockStartServer).toHaveBeenCalledWith('1');
      
      await waitFor(() => {
        expect(mockConsole.error).toHaveBeenCalledWith('Failed to start server:', expect.any(Error));
      });
    });
  });

  describe('Server Selection', () => {
    it('handles server selection', async () => {
      const user = userEvent.setup();
      const mockSelectServer = vi.fn();
      const servers = [createMockServer('1'), createMockServer('2')];
      
      setStoreState({
        servers,
        selectServer: mockSelectServer
      });

      render(ServerList);

      const serverCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      await user.click(serverCard);

      expect(mockSelectServer).toHaveBeenCalledWith('1');
    });

    it('shows selection state correctly', () => {
      const servers = [createMockServer('1'), createMockServer('2')];
      
      setStoreState({
        servers,
        selectedServerId: '1'
      });

      render(ServerList);

      const selectedCard = screen.getByRole('button', { name: /Server Test Server 1/ });
      const unselectedCard = screen.getByRole('button', { name: /Server Test Server 2/ });

      expect(selectedCard).toHaveClass('ring-2', 'ring-primary-500');
      expect(unselectedCard).not.toHaveClass('ring-2', 'ring-primary-500');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for buttons', () => {
      setStoreState({});

      render(ServerList);

      expect(screen.getByLabelText('Refresh server list')).toBeInTheDocument();
      expect(screen.getByLabelText('Add new server')).toBeInTheDocument();
    });

    it('maintains focus management', async () => {
      const user = userEvent.setup();
      const servers = [createMockServer('1')];
      
      setStoreState({ servers });

      render(ServerList);

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
      
      setStoreState({ servers });

      render(ServerList);

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
      
      setStoreState({ servers });

      const renderStart = performance.now();
      render(ServerList);
      const renderTime = performance.now() - renderStart;

      // Should render within reasonable time (less than 100ms)
      expect(renderTime).toBeLessThan(100);
      
      // Should render all servers
      expect(screen.getAllByText(/Test Server/).length).toBe(100);
    });
  });

  describe('Real-time Updates', () => {
    it('updates when server list changes', async () => {
      const initialServers = [createMockServer('1')];
      
      setStoreState({
        servers: initialServers
      });

      const { component } = render(ServerList);
      
      expect(screen.getByText('Test Server 1')).toBeInTheDocument();

      // Add server to store
      const updatedServers = [
        ...initialServers,
        createMockServer('2')
      ];
      
      setStoreState({
        servers: updatedServers
      });
      
      // Wait for reactive update
      await waitFor(() => {
        expect(screen.getByText('Test Server 1')).toBeInTheDocument();
        expect(screen.getByText('Test Server 2')).toBeInTheDocument();
      });
    });

    it('handles server status updates', async () => {
      const servers = [createMockServer('1', { status: 'stopped' })];
      
      setStoreState({ servers });

      render(ServerList);

      // Should show start button for stopped server
      expect(screen.getByRole('button', { name: 'Start server' })).toBeInTheDocument();

      // Update server to running
      const updatedServers = [createMockServer('1', { status: 'running' })];
      setStoreState({ servers: updatedServers });

      // Wait for reactive update
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Stop server' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Restart server' })).toBeInTheDocument();
      });
    });
  });
});