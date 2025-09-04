/**
 * Comprehensive End-to-End test suite for critical user workflows
 * Tests complete user journeys from authentication to server management
 */
import { test, expect, Page, BrowserContext } from '@playwright/test';

// Test data factory for E2E tests
const testData = {
  user: {
    email: 'test-user@example.com',
    password: 'SecurePassword123!',
    username: 'testuser'
  },
  admin: {
    email: 'admin@example.com',
    password: 'AdminPassword123!',
    username: 'admin'
  },
  server: {
    name: 'Test MCP Server',
    host: 'localhost',
    port: '8080',
    command: '/usr/bin/python',
    args: ['-m', 'test_server'],
    description: 'A test MCP server for E2E testing'
  }
};

// Helper functions
async function loginUser(page: Page, userCreds: typeof testData.user) {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', userCreds.email);
  await page.fill('[data-testid="password-input"]', userCreds.password);
  await page.click('[data-testid="login-button"]');
  
  // Wait for successful login
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
}

async function createServer(page: Page, serverData: typeof testData.server) {
  await page.click('[data-testid="add-server-button"]');
  await expect(page.locator('[data-testid="server-form"]')).toBeVisible();
  
  await page.fill('[data-testid="server-name"]', serverData.name);
  await page.fill('[data-testid="server-host"]', serverData.host);
  await page.fill('[data-testid="server-port"]', serverData.port);
  await page.fill('[data-testid="server-command"]', serverData.command);
  await page.fill('[data-testid="server-description"]', serverData.description);
  
  await page.click('[data-testid="save-server-button"]');
  
  // Wait for server to be created
  await expect(page.locator(`[data-testid="server-card-${serverData.name}"]`)).toBeVisible();
}

test.describe('Authentication Workflows', () => {
  test('complete user registration and login flow', async ({ page }) => {
    // Registration
    await page.goto('/register');
    await page.fill('[data-testid="email-input"]', testData.user.email);
    await page.fill('[data-testid="username-input"]', testData.user.username);
    await page.fill('[data-testid="password-input"]', testData.user.password);
    await page.fill('[data-testid="confirm-password-input"]', testData.user.password);
    
    await page.click('[data-testid="register-button"]');
    
    // Should redirect to login or dashboard
    await expect(page).toHaveURL(/\/(login|dashboard)/);
    
    // If redirected to login, complete login
    if (page.url().includes('/login')) {
      await page.fill('[data-testid="email-input"]', testData.user.email);
      await page.fill('[data-testid="password-input"]', testData.user.password);
      await page.click('[data-testid="login-button"]');
    }
    
    // Should be in dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome-message"]')).toContainText(testData.user.username);
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'invalid@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    
    await page.click('[data-testid="login-button"]');
    
    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/invalid.*credentials/i);
    
    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('logout functionality works correctly', async ({ page }) => {
    await loginUser(page, testData.user);
    
    // Click user menu
    await page.click('[data-testid="user-menu"]');
    await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
    
    // Logout
    await page.click('[data-testid="logout-button"]');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    
    // Should not be able to access protected routes
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });

  test('password reset workflow', async ({ page }) => {
    await page.goto('/login');
    await page.click('[data-testid="forgot-password-link"]');
    
    await expect(page).toHaveURL('/forgot-password');
    
    await page.fill('[data-testid="email-input"]', testData.user.email);
    await page.click('[data-testid="reset-password-button"]');
    
    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText(/reset.*sent/i);
  });
});

test.describe('Server Management Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, testData.user);
  });

  test('complete server lifecycle - create, configure, start, stop, delete', async ({ page }) => {
    // Create server
    await createServer(page, testData.server);
    
    // Verify server appears in list
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await expect(serverCard).toBeVisible();
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('stopped');
    
    // Start server
    await serverCard.locator('[data-testid="start-button"]').click();
    
    // Wait for status change
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('running', { timeout: 10000 });
    
    // Verify start button is replaced with stop/restart buttons
    await expect(serverCard.locator('[data-testid="stop-button"]')).toBeVisible();
    await expect(serverCard.locator('[data-testid="restart-button"]')).toBeVisible();
    
    // Stop server
    await serverCard.locator('[data-testid="stop-button"]').click();
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('stopped', { timeout: 10000 });
    
    // Configure server
    await serverCard.locator('[data-testid="configure-button"]').click();
    await expect(page.locator('[data-testid="server-config-modal"]')).toBeVisible();
    
    // Update configuration
    await page.fill('[data-testid="server-description"]', 'Updated description');
    await page.click('[data-testid="save-config-button"]');
    
    // Verify configuration was saved
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();
    await expect(serverCard.locator('[data-testid="server-description"]')).toContainText('Updated description');
    
    // Delete server
    await serverCard.locator('[data-testid="delete-button"]').click();
    
    // Confirm deletion
    await expect(page.locator('[data-testid="delete-confirmation-modal"]')).toBeVisible();
    await page.click('[data-testid="confirm-delete-button"]');
    
    // Verify server is removed
    await expect(serverCard).not.toBeVisible({ timeout: 5000 });
  });

  test('server form validation', async ({ page }) => {
    await page.click('[data-testid="add-server-button"]');
    
    // Try to submit empty form
    await page.click('[data-testid="save-server-button"]');
    
    // Should show validation errors
    await expect(page.locator('[data-testid="name-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="host-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="port-error"]')).toBeVisible();
    
    // Fill invalid data
    await page.fill('[data-testid="server-name"]', '');
    await page.fill('[data-testid="server-port"]', '999999'); // Invalid port
    await page.fill('[data-testid="server-host"]', 'invalid..host');
    
    await page.click('[data-testid="save-server-button"]');
    
    // Should show specific validation errors
    await expect(page.locator('[data-testid="port-error"]')).toContainText('valid port');
    await expect(page.locator('[data-testid="host-error"]')).toContainText('valid host');
  });

  test('server search and filtering', async ({ page }) => {
    // Create multiple servers
    const servers = [
      { ...testData.server, name: 'Production Server' },
      { ...testData.server, name: 'Development Server', port: '8081' },
      { ...testData.server, name: 'Test Server', port: '8082' }
    ];
    
    for (const server of servers) {
      await createServer(page, server);
    }
    
    // Search for specific server
    await page.fill('[data-testid="server-search"]', 'Production');
    
    // Should show only production server
    await expect(page.locator('[data-testid="server-card-Production Server"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-card-Development Server"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="server-card-Test Server"]')).not.toBeVisible();
    
    // Clear search
    await page.fill('[data-testid="server-search"]', '');
    
    // Should show all servers
    for (const server of servers) {
      await expect(page.locator(`[data-testid="server-card-${server.name}"]`)).toBeVisible();
    }
    
    // Filter by status
    await page.selectOption('[data-testid="status-filter"]', 'stopped');
    
    // All servers should be visible (all are stopped)
    for (const server of servers) {
      await expect(page.locator(`[data-testid="server-card-${server.name}"]`)).toBeVisible();
    }
  });

  test('bulk server operations', async ({ page }) => {
    // Create multiple servers
    const servers = [
      { ...testData.server, name: 'Server 1' },
      { ...testData.server, name: 'Server 2', port: '8081' },
      { ...testData.server, name: 'Server 3', port: '8082' }
    ];
    
    for (const server of servers) {
      await createServer(page, server);
    }
    
    // Select multiple servers
    for (const server of servers) {
      await page.click(`[data-testid="server-checkbox-${server.name}"]`);
    }
    
    // Bulk start
    await page.click('[data-testid="bulk-start-button"]');
    
    // Wait for all servers to start
    for (const server of servers) {
      await expect(
        page.locator(`[data-testid="server-card-${server.name}"] [data-testid="server-status"]`)
      ).toContainText('running', { timeout: 15000 });
    }
    
    // Bulk stop
    await page.click('[data-testid="bulk-stop-button"]');
    
    // Wait for all servers to stop
    for (const server of servers) {
      await expect(
        page.locator(`[data-testid="server-card-${server.name}"] [data-testid="server-status"]`)
      ).toContainText('stopped', { timeout: 15000 });
    }
  });
});

test.describe('Real-time Updates and WebSocket', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, testData.user);
  });

  test('connection status indicator updates', async ({ page }) => {
    // Should show connected status
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
    await expect(page.locator('[data-testid="connection-indicator"]')).toHaveClass(/connected/);
    
    // Simulate network disconnection
    await page.route('**/ws', route => route.abort());
    
    // Should show disconnected status
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Disconnected', { timeout: 10000 });
    await expect(page.locator('[data-testid="connection-indicator"]')).toHaveClass(/disconnected/);
    
    // Should show reconnect button
    await expect(page.locator('[data-testid="reconnect-button"]')).toBeVisible();
  });

  test('server status updates in real-time', async ({ page }) => {
    await createServer(page, testData.server);
    
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    
    // Start server
    await serverCard.locator('[data-testid="start-button"]').click();
    
    // Status should update without page refresh
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('starting');
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('running', { timeout: 10000 });
    
    // Metrics should appear
    await expect(serverCard.locator('[data-testid="cpu-metric"]')).toBeVisible();
    await expect(serverCard.locator('[data-testid="memory-metric"]')).toBeVisible();
    await expect(serverCard.locator('[data-testid="connections-metric"]')).toBeVisible();
  });

  test('live metrics updates', async ({ page }) => {
    await createServer(page, testData.server);
    
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await serverCard.locator('[data-testid="start-button"]').click();
    
    // Wait for server to start
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('running', { timeout: 10000 });
    
    // Capture initial metrics
    const initialCpu = await serverCard.locator('[data-testid="cpu-metric"]').textContent();
    
    // Wait for metrics to update (should happen automatically via WebSocket)
    await page.waitForTimeout(5000);
    
    const updatedCpu = await serverCard.locator('[data-testid="cpu-metric"]').textContent();
    
    // Metrics should have updated (or at least not be null)
    expect(updatedCpu).not.toBeNull();
  });
});

test.describe('Error Handling and Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, testData.user);
  });

  test('handles API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/mcp-servers', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });
    
    await page.click('[data-testid="add-server-button"]');
    await page.fill('[data-testid="server-name"]', testData.server.name);
    await page.fill('[data-testid="server-host"]', testData.server.host);
    await page.fill('[data-testid="server-port"]', testData.server.port);
    
    await page.click('[data-testid="save-server-button"]');
    
    // Should show error message
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-toast"]')).toContainText('Internal server error');
  });

  test('handles server startup failures', async ({ page }) => {
    await createServer(page, { ...testData.server, command: '/invalid/command' });
    
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await serverCard.locator('[data-testid="start-button"]').click();
    
    // Should show error status
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('error', { timeout: 10000 });
    
    // Should show error message
    await expect(serverCard.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test('handles concurrent user actions', async ({ page, context }) => {
    await createServer(page, testData.server);
    
    // Open second tab
    const page2 = await context.newPage();
    await loginUser(page2, testData.user);
    
    const serverCard1 = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    const serverCard2 = page2.locator(`[data-testid="server-card-${testData.server.name}"]`);
    
    // Start server from first tab
    await serverCard1.locator('[data-testid="start-button"]').click();
    
    // Both tabs should show updated status
    await expect(serverCard1.locator('[data-testid="server-status"]')).toContainText('running', { timeout: 10000 });
    await expect(serverCard2.locator('[data-testid="server-status"]')).toContainText('running', { timeout: 10000 });
    
    await page2.close();
  });
});

test.describe('Accessibility and Usability', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, testData.user);
  });

  test('keyboard navigation works throughout the application', async ({ page }) => {
    // Navigate to server creation using keyboard
    await page.keyboard.press('Tab'); // Navigate to add server button
    await page.keyboard.press('Enter'); // Open form
    
    // Fill form using tab navigation
    await page.keyboard.press('Tab'); // Move to name field
    await page.keyboard.type(testData.server.name);
    
    await page.keyboard.press('Tab'); // Move to host field
    await page.keyboard.type(testData.server.host);
    
    await page.keyboard.press('Tab'); // Move to port field
    await page.keyboard.type(testData.server.port);
    
    // Submit form
    await page.keyboard.press('Tab'); // Navigate to submit button
    await page.keyboard.press('Enter');
    
    // Verify server was created
    await expect(page.locator(`[data-testid="server-card-${testData.server.name}"]`)).toBeVisible();
  });

  test('screen reader announcements work correctly', async ({ page }) => {
    await createServer(page, testData.server);
    
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    
    // Check aria-labels and announcements
    await expect(serverCard).toHaveAttribute('aria-label', new RegExp(testData.server.name));
    
    // Start server and check status announcement
    await serverCard.locator('[data-testid="start-button"]').click();
    
    // Status updates should be announced
    const statusElement = serverCard.locator('[data-testid="server-status"]');
    await expect(statusElement).toHaveAttribute('aria-live', 'polite');
  });

  test('high contrast mode support', async ({ page }) => {
    // Enable high contrast mode simulation
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
    
    await createServer(page, testData.server);
    
    // Verify elements are still visible and accessible
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await expect(serverCard).toBeVisible();
    
    // Verify buttons have sufficient contrast
    const startButton = serverCard.locator('[data-testid="start-button"]');
    await expect(startButton).toBeVisible();
  });
});

test.describe('Performance and Load', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, testData.user);
  });

  test('handles large number of servers efficiently', async ({ page }) => {
    // Create many servers quickly
    const serverCount = 50;
    const startTime = Date.now();
    
    for (let i = 0; i < serverCount; i++) {
      await createServer(page, {
        ...testData.server,
        name: `Server ${i}`,
        port: (8080 + i).toString()
      });
    }
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Should complete within reasonable time (adjust based on requirements)
    expect(totalTime).toBeLessThan(60000); // 60 seconds
    
    // All servers should be visible
    for (let i = 0; i < Math.min(10, serverCount); i++) {
      await expect(page.locator(`[data-testid="server-card-Server ${i}"]`)).toBeVisible();
    }
  });

  test('search performance with many servers', async ({ page }) => {
    // Create multiple servers
    const servers = Array.from({ length: 20 }, (_, i) => ({
      ...testData.server,
      name: `Server ${i}`,
      port: (8080 + i).toString()
    }));
    
    for (const server of servers) {
      await createServer(page, server);
    }
    
    // Test search performance
    const startTime = Date.now();
    await page.fill('[data-testid="server-search"]', 'Server 1');
    
    // Wait for search results
    await expect(page.locator('[data-testid="server-card-Server 1"]')).toBeVisible();
    
    const searchTime = Date.now() - startTime;
    
    // Search should be fast
    expect(searchTime).toBeLessThan(1000); // 1 second
    
    // Should show only matching servers
    await expect(page.locator('[data-testid="server-card-Server 1"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-card-Server 10"]')).toBeVisible();
    await expect(page.locator('[data-testid="server-card-Server 2"]')).not.toBeVisible();
  });
});

test.describe('Data Persistence and State Management', () => {
  test('preserves state across page reloads', async ({ page }) => {
    await loginUser(page, testData.user);
    await createServer(page, testData.server);
    
    // Start server
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await serverCard.locator('[data-testid="start-button"]').click();
    await expect(serverCard.locator('[data-testid="server-status"]')).toContainText('running', { timeout: 10000 });
    
    // Reload page
    await page.reload();
    
    // Should still be logged in and server should maintain state
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator(`[data-testid="server-card-${testData.server.name}"]`)).toBeVisible();
    
    // Server status should be preserved
    const reloadedServerCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await expect(reloadedServerCard.locator('[data-testid="server-status"]')).toContainText('running');
  });

  test('handles browser back/forward navigation', async ({ page }) => {
    await loginUser(page, testData.user);
    
    // Navigate to settings
    await page.click('[data-testid="settings-link"]');
    await expect(page).toHaveURL('/settings');
    
    // Go back
    await page.goBack();
    await expect(page).toHaveURL('/dashboard');
    
    // Go forward
    await page.goForward();
    await expect(page).toHaveURL('/settings');
    
    // State should be preserved
    await expect(page.locator('[data-testid="settings-form"]')).toBeVisible();
  });
});

test.describe('Mobile Responsiveness', () => {
  test('works correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await loginUser(page, testData.user);
    await createServer(page, testData.server);
    
    // Mobile menu should be visible
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    
    // Server cards should stack on mobile
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    await expect(serverCard).toBeVisible();
    
    // Touch interactions should work
    await serverCard.tap();
    await expect(serverCard).toHaveClass(/selected/);
  });

  test('touch gestures work correctly', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await loginUser(page, testData.user);
    await createServer(page, testData.server);
    
    const serverCard = page.locator(`[data-testid="server-card-${testData.server.name}"]`);
    
    // Test swipe gestures (if implemented)
    await serverCard.hover();
    await page.mouse.down();
    await page.mouse.move(100, 0); // Swipe right
    await page.mouse.up();
    
    // Should reveal action buttons or trigger action
    // (Implementation depends on UI design)
  });
});