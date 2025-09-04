/**
 * End-to-end tests for authentication flows
 */
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Start each test from the login page
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    // Check that login form elements are present
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="username-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();
    
    // Check form labels and placeholders
    await expect(page.locator('label[for="username"]')).toContainText('Username');
    await expect(page.locator('label[for="password"]')).toContainText('Password');
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    // Try to submit form with empty fields
    await page.click('[data-testid="login-button"]');
    
    // Check for validation errors
    await expect(page.locator('[data-testid="username-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-error"]')).toBeVisible();
    
    // Should not navigate away from login page
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.fill('[data-testid="username-input"]', 'invaliduser');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="login-button"]');
    
    // Check for error message
    await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-error"]')).toContainText('Invalid credentials');
    
    // Should remain on login page
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Fill in valid credentials
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    
    // Click login button
    await page.click('[data-testid="login-button"]');
    
    // Should redirect to dashboard
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Check that user is logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
  });

  test('should handle login form keyboard navigation', async ({ page }) => {
    // Navigate through form using Tab key
    await page.press('[data-testid="username-input"]', 'Tab');
    await expect(page.locator('[data-testid="password-input"]')).toBeFocused();
    
    await page.press('[data-testid="password-input"]', 'Tab');
    await expect(page.locator('[data-testid="login-button"]')).toBeFocused();
    
    // Submit form using Enter key
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.press('[data-testid="login-button"]', 'Enter');
    
    // Should redirect to dashboard
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('should show loading state during login', async ({ page }) => {
    // Slow down the network to see loading state
    await page.route('**/api/v1/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });
    
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    // Check loading state
    await expect(page.locator('[data-testid="login-loading"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeDisabled();
    
    // Wait for login to complete
    await page.waitForURL('**/dashboard');
  });

  test('should persist login state after page refresh', async ({ page }) => {
    // Login first
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('**/dashboard');
    
    // Refresh the page
    await page.reload();
    
    // Should still be logged in and on dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('**/dashboard');
    
    // Open user menu and logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    
    // Should redirect to login page
    await page.waitForURL('**/login');
    await expect(page).toHaveURL(/.*\/login/);
    
    // Should not be able to access protected pages
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should redirect to intended page after login', async ({ page }) => {
    // Try to access protected page while not logged in
    await page.goto('/mcp-servers');
    
    // Should redirect to login page
    await expect(page).toHaveURL(/.*\/login/);
    
    // Login
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    // Should redirect to originally intended page
    await page.waitForURL('**/mcp-servers');
    await expect(page).toHaveURL(/.*\/mcp-servers/);
  });

  test('should handle session expiration', async ({ page }) => {
    // Login first
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('**/dashboard');
    
    // Simulate expired token by intercepting API calls
    await page.route('**/api/v1/**', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Token expired' })
      });
    });
    
    // Try to make an API call (e.g., navigate to servers page)
    await page.goto('/mcp-servers');
    
    // Should redirect to login page due to expired session
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator('[data-testid="session-expired-message"]')).toBeVisible();
  });
});

test.describe('Authentication - Password Security', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should mask password input', async ({ page }) => {
    await page.fill('[data-testid="password-input"]', 'password123');
    
    // Password should be masked
    await expect(page.locator('[data-testid="password-input"]')).toHaveAttribute('type', 'password');
    
    // Check if show/hide password toggle exists
    const toggleButton = page.locator('[data-testid="password-toggle"]');
    if (await toggleButton.isVisible()) {
      // Click to show password
      await toggleButton.click();
      await expect(page.locator('[data-testid="password-input"]')).toHaveAttribute('type', 'text');
      
      // Click to hide password again
      await toggleButton.click();
      await expect(page.locator('[data-testid="password-input"]')).toHaveAttribute('type', 'password');
    }
  });

  test('should not submit form with Enter on password field if validation fails', async ({ page }) => {
    // Fill only username
    await page.fill('[data-testid="username-input"]', 'testuser');
    
    // Press Enter on password field (which is empty)
    await page.press('[data-testid="password-input"]', 'Enter');
    
    // Should show validation error instead of submitting
    await expect(page.locator('[data-testid="password-error"]')).toBeVisible();
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should clear form data on navigation away', async ({ page }) => {
    // Fill in credentials
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    
    // Navigate away (e.g., to registration page if it exists)
    await page.goto('/register');
    
    // Navigate back to login
    await page.goto('/login');
    
    // Form should be cleared
    await expect(page.locator('[data-testid="username-input"]')).toHaveValue('');
    await expect(page.locator('[data-testid="password-input"]')).toHaveValue('');
  });
});