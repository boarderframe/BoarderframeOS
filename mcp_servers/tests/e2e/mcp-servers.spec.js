/**
 * End-to-end tests for MCP server management
 */
import { test, expect } from '@playwright/test';

test.describe('MCP Server Management', () => {
  test.beforeEach(async ({ page }) => {
    // Use saved authentication state
    await page.goto('/mcp-servers');
    
    // Verify we're on the servers page and authenticated
    await expect(page).toHaveURL(/.*\/mcp-servers/);
    await expect(page.locator('[data-testid="servers-page"]')).toBeVisible();
  });

  test('should display servers list page', async ({ page }) => {
    // Check page title and main elements
    await expect(page.locator('h1')).toContainText('MCP Servers');
    await expect(page.locator('[data-testid="servers-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="add-server-button"]')).toBeVisible();
    
    // Check if refresh button exists
    await expect(page.locator('[data-testid="refresh-button"]')).toBeVisible();
  });

  test('should load and display servers from API', async ({ page }) => {
    // Wait for servers to load
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Check that servers are displayed
    const serverItems = page.locator('[data-testid="server-item"]');
    await expect(serverItems).toHaveCount(3); // Based on our mock data
    
    // Check first server details
    const firstServer = serverItems.first();
    await expect(firstServer.locator('[data-testid="server-name"]')).toContainText('test-server-1');
    await expect(firstServer.locator('[data-testid="server-status"]')).toContainText('active');
    await expect(firstServer.locator('[data-testid="server-port"]')).toContainText('8080');
  });

  test('should show loading state while fetching servers', async ({ page }) => {
    // Intercept API call to add delay
    await page.route('**/api/v1/mcp-servers/', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });
    
    // Reload page to trigger loading
    await page.reload();
    
    // Check loading state
    await expect(page.locator('[data-testid="servers-loading"]')).toBeVisible();
    
    // Wait for servers to load
    await expect(page.locator('[data-testid="servers-loading"]')).toBeHidden();
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(3);
  });

  test('should handle API error gracefully', async ({ page }) => {
    // Intercept API call to return error
    await page.route('**/api/v1/mcp-servers/', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });
    
    // Reload page to trigger error
    await page.reload();
    
    // Check error state
    await expect(page.locator('[data-testid="servers-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="servers-error"]')).toContainText('Failed to load servers');
    
    // Check retry button exists
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should refresh servers list', async ({ page }) => {
    // Wait for initial load
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Click refresh button
    await page.click('[data-testid="refresh-button"]');
    
    // Should show loading state briefly
    await expect(page.locator('[data-testid="servers-loading"]')).toBeVisible();
    
    // Wait for refresh to complete
    await expect(page.locator('[data-testid="servers-loading"]')).toBeHidden();
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(3);
  });

  test('should navigate to server details', async ({ page }) => {
    // Wait for servers to load
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Click on first server
    const firstServer = page.locator('[data-testid="server-item"]').first();
    await firstServer.click();
    
    // Should navigate to server details page
    await page.waitForURL('**/mcp-servers/1');
    await expect(page).toHaveURL(/.*\/mcp-servers\/1/);
    
    // Check server details page elements
    await expect(page.locator('[data-testid="server-details"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-name"]')).toContainText('test-server-1');
  });

  test('should show different status indicators', async ({ page }) => {
    await page.waitForSelector('[data-testid="server-item"]');
    
    const serverItems = page.locator('[data-testid="server-item"]');
    
    // Check active server (green)
    const activeServer = serverItems.nth(0);
    await expect(activeServer.locator('[data-testid="status-indicator"]')).toHaveClass(/active|success|green/);
    
    // Check inactive server (yellow/orange)
    const inactiveServer = serverItems.nth(1);
    await expect(inactiveServer.locator('[data-testid="status-indicator"]')).toHaveClass(/inactive|warning|yellow/);
    
    // Check error server (red)
    const errorServer = serverItems.nth(2);
    await expect(errorServer.locator('[data-testid="status-indicator"]')).toHaveClass(/error|danger|red/);
  });

  test('should show server actions menu', async ({ page }) => {
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Click on server actions menu
    const firstServer = page.locator('[data-testid="server-item"]').first();
    await firstServer.locator('[data-testid="server-actions"]').click();
    
    // Check action menu items
    await expect(page.locator('[data-testid="action-view"]')).toBeVisible();
    await expect(page.locator('[data-testid="action-edit"]')).toBeVisible();
    await expect(page.locator('[data-testid="action-delete"]')).toBeVisible();
    await expect(page.locator('[data-testid="action-restart"]')).toBeVisible();
  });

  test('should filter servers by status', async ({ page }) => {
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Check initial count
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(3);
    
    // Apply active filter
    await page.click('[data-testid="status-filter"]');
    await page.click('[data-testid="filter-active"]');
    
    // Should show only active servers
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="server-item"] [data-testid="server-status"]')).toContainText('active');
    
    // Clear filter
    await page.click('[data-testid="clear-filters"]');
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(3);
  });

  test('should search servers by name', async ({ page }) => {
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Enter search term
    await page.fill('[data-testid="search-input"]', 'test-server-1');
    
    // Should show filtered results
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="server-name"]')).toContainText('test-server-1');
    
    // Clear search
    await page.fill('[data-testid="search-input"]', '');
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(3);
  });

  test('should handle pagination', async ({ page }) => {
    // Mock API to return more servers for pagination testing
    await page.route('**/api/v1/mcp-servers/*', async route => {
      const url = new URL(route.request().url());
      const skip = parseInt(url.searchParams.get('skip') || '0');
      const limit = parseInt(url.searchParams.get('limit') || '10');
      
      // Generate mock servers for pagination
      const allServers = Array.from({ length: 25 }, (_, i) => ({
        id: i + 1,
        name: `server-${i + 1}`,
        status: 'active',
        host: 'localhost',
        port: 8080 + i,
        protocol: 'stdio',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }));
      
      const paginatedServers = allServers.slice(skip, skip + limit);
      
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify(paginatedServers)
      });
    });
    
    await page.reload();
    await page.waitForSelector('[data-testid="server-item"]');
    
    // Check pagination controls
    await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
    await expect(page.locator('[data-testid="next-page"]')).toBeVisible();
    
    // Go to next page
    await page.click('[data-testid="next-page"]');
    
    // Check that different servers are shown
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(10);
  });
});

test.describe('MCP Server Details', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/mcp-servers/1');
    await expect(page).toHaveURL(/.*\/mcp-servers\/1/);
  });

  test('should display server details', async ({ page }) => {
    await expect(page.locator('[data-testid="server-details"]')).toBeVisible();
    
    // Check server information
    await expect(page.locator('[data-testid="server-name"]')).toContainText('test-server-1');
    await expect(page.locator('[data-testid="server-host"]')).toContainText('localhost');
    await expect(page.locator('[data-testid="server-port"]')).toContainText('8080');
    await expect(page.locator('[data-testid="server-protocol"]')).toContainText('stdio');
    await expect(page.locator('[data-testid="server-status"]')).toContainText('active');
  });

  test('should show server configuration', async ({ page }) => {
    // Check configuration section
    await expect(page.locator('[data-testid="server-config"]')).toBeVisible();
    
    // Check command and args
    await expect(page.locator('[data-testid="server-command"]')).toContainText('/usr/bin/python');
    await expect(page.locator('[data-testid="server-args"]')).toContainText('-m test_server');
    
    // Check environment variables
    await expect(page.locator('[data-testid="server-env"]')).toBeVisible();
    
    // Check config options
    await expect(page.locator('[data-testid="server-config-json"]')).toBeVisible();
  });

  test('should display server health status', async ({ page }) => {
    await expect(page.locator('[data-testid="health-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="response-time"]')).toContainText('150.5 ms');
    await expect(page.locator('[data-testid="last-check"]')).toBeVisible();
  });

  test('should refresh health status', async ({ page }) => {
    // Click refresh health button
    await page.click('[data-testid="refresh-health"]');
    
    // Should show loading state
    await expect(page.locator('[data-testid="health-loading"]')).toBeVisible();
    
    // Wait for refresh to complete
    await expect(page.locator('[data-testid="health-loading"]')).toBeHidden();
    await expect(page.locator('[data-testid="health-status"]')).toBeVisible();
  });

  test('should show server tools', async ({ page }) => {
    // Navigate to tools tab
    await page.click('[data-testid="tools-tab"]');
    
    // Check tools list
    await expect(page.locator('[data-testid="tools-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="tool-item"]')).toHaveCount(2);
    
    // Check tool details
    const firstTool = page.locator('[data-testid="tool-item"]').first();
    await expect(firstTool.locator('[data-testid="tool-name"]')).toContainText('file_reader');
    await expect(firstTool.locator('[data-testid="tool-description"]')).toBeVisible();
  });

  test('should show server resources', async ({ page }) => {
    // Navigate to resources tab
    await page.click('[data-testid="resources-tab"]');
    
    // Check resources list
    await expect(page.locator('[data-testid="resources-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="resource-item"]')).toHaveCount(2);
    
    // Check resource details
    const firstResource = page.locator('[data-testid="resource-item"]').first();
    await expect(firstResource.locator('[data-testid="resource-name"]')).toContainText('config.json');
    await expect(firstResource.locator('[data-testid="resource-type"]')).toContainText('text/json');
  });

  test('should handle server not found', async ({ page }) => {
    await page.goto('/mcp-servers/999');
    
    // Should show not found error
    await expect(page.locator('[data-testid="server-not-found"]')).toBeVisible();
    await expect(page.locator('[data-testid="back-to-servers"]')).toBeVisible();
    
    // Click back to servers
    await page.click('[data-testid="back-to-servers"]');
    await expect(page).toHaveURL(/.*\/mcp-servers$/);
  });

  test('should navigate back to servers list', async ({ page }) => {
    // Click back button
    await page.click('[data-testid="back-button"]');
    
    // Should navigate to servers list
    await expect(page).toHaveURL(/.*\/mcp-servers$/);
    await expect(page.locator('[data-testid="servers-list"]')).toBeVisible();
  });
});

test.describe('MCP Server Actions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/mcp-servers');
    await page.waitForSelector('[data-testid="server-item"]');
  });

  test('should show create server modal', async ({ page }) => {
    // Click add server button
    await page.click('[data-testid="add-server-button"]');
    
    // Should show create modal
    await expect(page.locator('[data-testid="create-server-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-name-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-host-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-port-input"]')).toBeVisible();
  });

  test('should validate create server form', async ({ page }) => {
    await page.click('[data-testid="add-server-button"]');
    
    // Try to submit empty form
    await page.click('[data-testid="create-server-submit"]');
    
    // Should show validation errors
    await expect(page.locator('[data-testid="name-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="port-error"]')).toBeVisible();
    
    // Modal should remain open
    await expect(page.locator('[data-testid="create-server-modal"]')).toBeVisible();
  });

  test('should close create server modal', async ({ page }) => {
    await page.click('[data-testid="add-server-button"]');
    await expect(page.locator('[data-testid="create-server-modal"]')).toBeVisible();
    
    // Close modal with cancel button
    await page.click('[data-testid="cancel-button"]');
    await expect(page.locator('[data-testid="create-server-modal"]')).toBeHidden();
    
    // Open modal again
    await page.click('[data-testid="add-server-button"]');
    await expect(page.locator('[data-testid="create-server-modal"]')).toBeVisible();
    
    // Close modal with X button
    await page.click('[data-testid="close-modal"]');
    await expect(page.locator('[data-testid="create-server-modal"]')).toBeHidden();
  });

  test('should show delete confirmation', async ({ page }) => {
    // Open actions menu for first server
    const firstServer = page.locator('[data-testid="server-item"]').first();
    await firstServer.locator('[data-testid="server-actions"]').click();
    await page.click('[data-testid="action-delete"]');
    
    // Should show delete confirmation
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="confirm-delete"]')).toBeVisible();
    await expect(page.locator('[data-testid="cancel-delete"]')).toBeVisible();
  });

  test('should cancel delete operation', async ({ page }) => {
    const firstServer = page.locator('[data-testid="server-item"]').first();
    await firstServer.locator('[data-testid="server-actions"]').click();
    await page.click('[data-testid="action-delete"]');
    
    // Cancel delete
    await page.click('[data-testid="cancel-delete"]');
    
    // Confirmation should be hidden
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeHidden();
    
    // Server should still be in list
    await expect(page.locator('[data-testid="server-item"]')).toHaveCount(3);
  });
});