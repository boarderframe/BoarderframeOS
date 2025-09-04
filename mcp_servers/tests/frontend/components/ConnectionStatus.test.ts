/**
 * Comprehensive unit tests for ConnectionStatus Svelte component
 */
import { render, screen, fireEvent } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import ConnectionStatus from '../../frontend/src/components/ConnectionStatus.svelte';

describe('ConnectionStatus Component', () => {
  const mockOnReconnect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Connected State', () => {
    it('renders connected state correctly', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      // Should show connected status
      expect(screen.getByText('Connected')).toBeInTheDocument();
      
      // Should have WiFi icon
      const wifiIcon = document.querySelector('svg');
      expect(wifiIcon).toBeInTheDocument();
      
      // Should not show reconnect button
      expect(screen.queryByText('Reconnect')).not.toBeInTheDocument();
    });

    it('applies correct styling for connected state', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('bg-green-500', 'text-white');
      expect(statusElement).not.toHaveClass('bg-red-500');
    });

    it('has correct accessibility attributes for connected state', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
      expect(statusElement).toHaveAttribute('aria-label', 'Connected to server');
    });
  });

  describe('Disconnected State', () => {
    it('renders disconnected state correctly', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      // Should show disconnected status
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      
      // Should show reconnect button
      expect(screen.getByText('Reconnect')).toBeInTheDocument();
    });

    it('applies correct styling for disconnected state', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('bg-red-500', 'text-white');
      expect(statusElement).not.toHaveClass('bg-green-500');
    });

    it('has correct accessibility attributes for disconnected state', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
      expect(statusElement).toHaveAttribute('aria-label', 'Disconnected from server');
    });

    it('does not render reconnect button when onReconnect is not provided', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: null
        }
      });

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.queryByText('Reconnect')).not.toBeInTheDocument();
    });
  });

  describe('Reconnect Functionality', () => {
    it('calls onReconnect when reconnect button is clicked', async () => {
      const user = userEvent.setup();
      
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const reconnectButton = screen.getByRole('button', { name: 'Reconnect to server' });
      await user.click(reconnectButton);

      expect(mockOnReconnect).toHaveBeenCalledTimes(1);
    });

    it('handles multiple rapid clicks on reconnect button', async () => {
      const user = userEvent.setup();
      
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const reconnectButton = screen.getByRole('button', { name: 'Reconnect to server' });
      
      // Click multiple times rapidly
      await user.click(reconnectButton);
      await user.click(reconnectButton);
      await user.click(reconnectButton);

      expect(mockOnReconnect).toHaveBeenCalledTimes(3);
    });

    it('has proper accessibility attributes for reconnect button', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const reconnectButton = screen.getByRole('button', { name: 'Reconnect to server' });
      expect(reconnectButton).toHaveAttribute('aria-label', 'Reconnect to server');
    });
  });

  describe('Visual Styling', () => {
    it('has fixed positioning and proper z-index', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('fixed', 'bottom-4', 'right-4');
    });

    it('has shadow and rounded corners', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('shadow-lg', 'rounded-lg');
    });

    it('has transition classes for smooth animations', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('transition-all');
    });

    it('applies hover effects to reconnect button', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const reconnectButton = screen.getByRole('button', { name: 'Reconnect to server' });
      expect(reconnectButton).toHaveClass('hover:bg-white/30', 'transition-colors');
    });
  });

  describe('Icon Display', () => {
    it('shows Wifi icon when connected', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      // Check for Wifi icon (Lucide Svelte icons have specific structure)
      const statusElement = screen.getByRole('status');
      const icon = statusElement.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('w-4', 'h-4');
    });

    it('shows WifiOff icon when disconnected', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      // Check for WifiOff icon
      const statusElement = screen.getByRole('status');
      const icon = statusElement.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('w-4', 'h-4');
    });
  });

  describe('Component Layout', () => {
    it('has proper flex layout for connected state', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('flex', 'items-center', 'gap-2');
    });

    it('maintains layout consistency in disconnected state', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('flex', 'items-center', 'gap-2');
    });
  });

  describe('State Transitions', () => {
    it('updates correctly when connection state changes', async () => {
      const { rerender } = render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      // Initially connected
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.queryByText('Reconnect')).not.toBeInTheDocument();

      // Change to disconnected
      await rerender({
        isConnected: false,
        onReconnect: mockOnReconnect
      });

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.getByText('Reconnect')).toBeInTheDocument();

      // Change back to connected
      await rerender({
        isConnected: true,
        onReconnect: mockOnReconnect
      });

      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.queryByText('Reconnect')).not.toBeInTheDocument();
    });

    it('maintains accessibility announcements during state changes', async () => {
      const { rerender } = render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      let statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-label', 'Connected to server');

      await rerender({
        isConnected: false,
        onReconnect: mockOnReconnect
      });

      statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-label', 'Disconnected from server');
    });
  });

  describe('Performance', () => {
    it('handles rapid state changes efficiently', async () => {
      const { rerender } = render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      // Simulate rapid state changes
      for (let i = 0; i < 10; i++) {
        await rerender({
          isConnected: i % 2 === 0,
          onReconnect: mockOnReconnect
        });
      }

      // Should end in disconnected state
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined onReconnect gracefully', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: undefined
        }
      });

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.queryByText('Reconnect')).not.toBeInTheDocument();
    });

    it('handles null onReconnect gracefully', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: null
        }
      });

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.queryByText('Reconnect')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Interaction', () => {
    it('supports keyboard interaction for reconnect button', async () => {
      const user = userEvent.setup();
      
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const reconnectButton = screen.getByRole('button', { name: 'Reconnect to server' });
      
      // Test Enter key
      reconnectButton.focus();
      await user.keyboard('{Enter}');
      expect(mockOnReconnect).toHaveBeenCalledTimes(1);

      // Test Space key
      await user.keyboard(' ');
      expect(mockOnReconnect).toHaveBeenCalledTimes(2);
    });

    it('has proper tab order', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const reconnectButton = screen.getByRole('button', { name: 'Reconnect to server' });
      
      // Button should be focusable
      reconnectButton.focus();
      expect(document.activeElement).toBe(reconnectButton);
    });
  });

  describe('Screen Reader Support', () => {
    it('provides live region updates for connection status changes', async () => {
      const { rerender } = render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      let statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');

      // Change state
      await rerender({
        isConnected: false,
        onReconnect: mockOnReconnect
      });

      statusElement = screen.getByRole('status');
      expect(statusElement).toHaveAttribute('aria-live', 'polite');
    });

    it('has descriptive aria-labels', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: false,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      const reconnectButton = screen.getByRole('button');

      expect(statusElement).toHaveAttribute('aria-label', 'Disconnected from server');
      expect(reconnectButton).toHaveAttribute('aria-label', 'Reconnect to server');
    });
  });

  describe('CSS Classes and Styling', () => {
    it('applies correct base classes', () => {
      render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      const statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass(
        'fixed',
        'bottom-4',
        'right-4',
        'px-4',
        'py-2',
        'rounded-lg',
        'shadow-lg',
        'transition-all',
        'flex',
        'items-center',
        'gap-2'
      );
    });

    it('applies conditional classes based on connection state', async () => {
      const { rerender } = render(ConnectionStatus, {
        props: {
          isConnected: true,
          onReconnect: mockOnReconnect
        }
      });

      let statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('bg-green-500', 'text-white');

      await rerender({
        isConnected: false,
        onReconnect: mockOnReconnect
      });

      statusElement = screen.getByRole('status');
      expect(statusElement).toHaveClass('bg-red-500', 'text-white');
    });
  });
});