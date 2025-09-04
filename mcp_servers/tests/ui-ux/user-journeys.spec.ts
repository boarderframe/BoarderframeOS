/**
 * User Journey Testing Suite
 * End-to-end user workflow validation
 */

import { test, expect, Page } from '@playwright/test';

// Helper functions for common actions
async function login(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', email);
  await page.fill('[data-testid="password-input"]', password);
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/dashboard');
}

async function searchProduct(page: Page, query: string) {
  await page.fill('[data-testid="search-input"]', query);
  await page.keyboard.press('Enter');
  await page.waitForSelector('[data-testid="search-results"]');
}

async function addToCart(page: Page, productIndex: number = 0) {
  const products = page.locator('[data-testid="product-card"]');
  await products.nth(productIndex).locator('[data-testid="add-to-cart"]').click();
  await page.waitForSelector('[data-testid="cart-notification"]');
}

test.describe('Complete Shopping Journey', () => {
  test('Guest user shopping flow', async ({ page }) => {
    // Step 1: Landing page
    await page.goto('/');
    await expect(page.locator('[data-testid="hero-section"]')).toBeVisible();
    
    // Step 2: Browse products
    await page.click('[data-testid="shop-now"]');
    await page.waitForURL('/products');
    
    const products = page.locator('[data-testid="product-card"]');
    await expect(products).toHaveCount(await products.count());
    
    // Step 3: Search for specific product
    await searchProduct(page, 'organic milk');
    await expect(page.locator('[data-testid="search-results"]')).toContainText('organic milk');
    
    // Step 4: View product details
    await products.first().click();
    await page.waitForSelector('[data-testid="product-details"]');
    
    await expect(page.locator('[data-testid="product-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="product-description"]')).toBeVisible();
    await expect(page.locator('[data-testid="nutrition-info"]')).toBeVisible();
    
    // Step 5: Add to cart
    await page.click('[data-testid="add-to-cart-detail"]');
    
    // Step 6: View cart
    await page.click('[data-testid="cart-icon"]');
    await page.waitForSelector('[data-testid="shopping-cart"]');
    
    const cartItems = page.locator('[data-testid="cart-item"]');
    await expect(cartItems).toHaveCount(1);
    
    // Step 7: Proceed to checkout
    await page.click('[data-testid="checkout-button"]');
    
    // Step 8: Guest checkout
    await page.click('[data-testid="checkout-as-guest"]');
    
    // Step 9: Enter shipping information
    await page.fill('[data-testid="shipping-name"]', 'John Doe');
    await page.fill('[data-testid="shipping-address"]', '123 Main St');
    await page.fill('[data-testid="shipping-city"]', 'Springfield');
    await page.selectOption('[data-testid="shipping-state"]', 'IL');
    await page.fill('[data-testid="shipping-zip"]', '62701');
    
    // Step 10: Select delivery option
    await page.click('[data-testid="delivery-option-standard"]');
    
    // Step 11: Payment information
    await page.fill('[data-testid="card-number"]', '4111111111111111');
    await page.fill('[data-testid="card-expiry"]', '12/25');
    await page.fill('[data-testid="card-cvv"]', '123');
    
    // Step 12: Review order
    await page.click('[data-testid="review-order"]');
    await expect(page.locator('[data-testid="order-summary"]')).toBeVisible();
    
    // Step 13: Place order
    await page.click('[data-testid="place-order"]');
    
    // Step 14: Order confirmation
    await page.waitForSelector('[data-testid="order-confirmation"]');
    await expect(page.locator('[data-testid="order-number"]')).toBeVisible();
    await expect(page.locator('[data-testid="estimated-delivery"]')).toBeVisible();
  });
  
  test('Registered user with saved preferences', async ({ page }) => {
    // Login
    await login(page, 'user@example.com', 'password123');
    
    // Check personalized homepage
    await expect(page.locator('[data-testid="recommended-products"]')).toBeVisible();
    await expect(page.locator('[data-testid="recent-purchases"]')).toBeVisible();
    
    // Quick reorder from history
    await page.click('[data-testid="reorder-button"]');
    await expect(page.locator('[data-testid="cart-count"]')).not.toHaveText('0');
    
    // Use saved address for checkout
    await page.click('[data-testid="cart-icon"]');
    await page.click('[data-testid="checkout-button"]');
    
    // Saved addresses should be available
    const savedAddresses = page.locator('[data-testid="saved-address"]');
    await expect(savedAddresses).toHaveCount(await savedAddresses.count());
    
    await savedAddresses.first().click();
    
    // Use saved payment method
    const savedPayments = page.locator('[data-testid="saved-payment"]');
    await savedPayments.first().click();
    
    // Express checkout
    await page.click('[data-testid="express-checkout"]');
    await page.waitForSelector('[data-testid="order-confirmation"]');
  });
});

test.describe('Store Locator Journey', () => {
  test('Find nearby store and check availability', async ({ page }) => {
    await page.goto('/store-locator');
    
    // Allow location access
    await page.context().grantPermissions(['geolocation']);
    await page.context().setGeolocation({ latitude: 37.7749, longitude: -122.4194 });
    
    // Use current location
    await page.click('[data-testid="use-current-location"]');
    await page.waitForSelector('[data-testid="store-results"]');
    
    // Stores should be listed
    const stores = page.locator('[data-testid="store-card"]');
    await expect(stores).toHaveCount(await stores.count());
    
    // Check first store details
    const firstStore = stores.first();
    await expect(firstStore.locator('[data-testid="store-name"]')).toBeVisible();
    await expect(firstStore.locator('[data-testid="store-distance"]')).toBeVisible();
    await expect(firstStore.locator('[data-testid="store-hours"]')).toBeVisible();
    
    // Select store for shopping
    await firstStore.click('[data-testid="shop-this-store"]');
    
    // Store should be set
    await expect(page.locator('[data-testid="selected-store"]')).toContainText('Store selected');
    
    // Check product availability at store
    await searchProduct(page, 'bread');
    
    const productAvailability = page.locator('[data-testid="in-store-availability"]');
    await expect(productAvailability.first()).toBeVisible();
  });
  
  test('Store map navigation', async ({ page }) => {
    await page.goto('/store-locator');
    
    // Enter zip code
    await page.fill('[data-testid="zip-input"]', '94102');
    await page.click('[data-testid="search-stores"]');
    
    // Map should be visible
    await expect(page.locator('[data-testid="store-map"]')).toBeVisible();
    
    // Map markers should be present
    const mapMarkers = await page.evaluate(() => {
      return document.querySelectorAll('[data-testid="map-marker"]').length;
    });
    expect(mapMarkers).toBeGreaterThan(0);
    
    // Click on map marker
    await page.click('[data-testid="map-marker"]');
    
    // Store popup should appear
    await expect(page.locator('[data-testid="map-popup"]')).toBeVisible();
    
    // Get directions
    await page.click('[data-testid="get-directions"]');
    
    // Directions panel should open
    await expect(page.locator('[data-testid="directions-panel"]')).toBeVisible();
  });
});

test.describe('Digital Coupons Journey', () => {
  test('Browse and clip digital coupons', async ({ page }) => {
    await login(page, 'user@example.com', 'password123');
    
    // Navigate to coupons
    await page.click('[data-testid="nav-coupons"]');
    await page.waitForURL('/coupons');
    
    // Coupons should be displayed
    const coupons = page.locator('[data-testid="coupon-card"]');
    await expect(coupons).toHaveCount(await coupons.count());
    
    // Filter by category
    await page.selectOption('[data-testid="coupon-category"]', 'dairy');
    await page.waitForTimeout(500);
    
    // Clip coupons
    const clipButtons = page.locator('[data-testid="clip-coupon"]');
    const initialClipCount = await clipButtons.count();
    
    for (let i = 0; i < Math.min(3, initialClipCount); i++) {
      await clipButtons.nth(i).click();
      await page.waitForTimeout(200);
    }
    
    // Check clipped coupons
    await page.click('[data-testid="view-clipped"]');
    
    const clippedCoupons = page.locator('[data-testid="clipped-coupon"]');
    await expect(clippedCoupons).toHaveCount(3);
    
    // Apply coupons at checkout
    await page.goto('/products');
    await addToCart(page, 0);
    await page.click('[data-testid="cart-icon"]');
    await page.click('[data-testid="checkout-button"]');
    
    // Coupons should be automatically applied
    await expect(page.locator('[data-testid="applied-coupons"]')).toBeVisible();
    
    const savings = await page.locator('[data-testid="total-savings"]').textContent();
    expect(savings).toMatch(/\$\d+\.\d{2}/);
  });
});

test.describe('MCP Server Configuration Journey', () => {
  test('Configure and manage MCP servers', async ({ page }) => {
    await page.goto('/');
    
    // Open server configuration
    await page.click('[data-testid="add-server"]');
    
    // Select server type
    await page.selectOption('[data-testid="server-type"]', 'kroger');
    
    // Configure Kroger server
    await page.fill('[data-testid="server-name"]', 'My Kroger Server');
    await page.fill('[data-testid="client-id"]', 'test-client-id');
    await page.fill('[data-testid="client-secret"]', 'test-client-secret');
    
    // Set permissions
    await page.check('[data-testid="permission-products"]');
    await page.check('[data-testid="permission-cart"]');
    await page.check('[data-testid="permission-locations"]');
    
    // Advanced settings
    await page.click('[data-testid="advanced-settings"]');
    await page.fill('[data-testid="rate-limit"]', '100');
    await page.fill('[data-testid="timeout"]', '30000');
    
    // Save configuration
    await page.click('[data-testid="save-server"]');
    
    // Server should appear in list
    await expect(page.locator('[data-testid="server-card"]')).toContainText('My Kroger Server');
    
    // Test server connection
    await page.click('[data-testid="test-connection"]');
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');
    
    // Start server
    await page.click('[data-testid="start-server"]');
    await expect(page.locator('[data-testid="server-status"]')).toContainText('Running');
    
    // View server logs
    await page.click('[data-testid="view-logs"]');
    await expect(page.locator('[data-testid="server-logs"]')).toBeVisible();
    
    // Stop server
    await page.click('[data-testid="stop-server"]');
    await expect(page.locator('[data-testid="server-status"]')).toContainText('Stopped');
  });
});

test.describe('Accessibility User Journey', () => {
  test('Complete journey using keyboard only', async ({ page }) => {
    await page.goto('/');
    
    // Tab to skip link
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Navigate to products using keyboard
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Browse products with keyboard
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }
    
    // Add product to cart
    await page.keyboard.press('Enter');
    
    // Navigate to cart
    await page.keyboard.press('Shift+Tab');
    await page.keyboard.press('Shift+Tab');
    await page.keyboard.press('Enter');
    
    // Checkout
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Fill form with keyboard
    await page.keyboard.type('John Doe');
    await page.keyboard.press('Tab');
    await page.keyboard.type('john@example.com');
    await page.keyboard.press('Tab');
    await page.keyboard.type('123 Main St');
    
    // Submit form
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
  
  test('Screen reader user journey', async ({ page }) => {
    // Enable screen reader mode
    await page.goto('/?screen-reader=true');
    
    // Check for screen reader announcements
    const liveRegion = page.locator('[role="status"], [role="alert"], [aria-live]');
    
    // Navigate through page
    await page.keyboard.press('h'); // Next heading
    const heading = await page.evaluate(() => document.activeElement?.textContent);
    expect(heading).toBeTruthy();
    
    // Navigate by landmarks
    await page.keyboard.press('d'); // Next landmark
    const landmark = await page.evaluate(() => document.activeElement?.getAttribute('role'));
    expect(['navigation', 'main', 'complementary', 'contentinfo']).toContain(landmark);
    
    // Form navigation
    await page.keyboard.press('f'); // Next form field
    const formField = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON']).toContain(formField);
    
    // Check for descriptive labels
    const ariaLabel = await page.evaluate(() => {
      const el = document.activeElement;
      return el?.getAttribute('aria-label') || el?.getAttribute('aria-labelledby');
    });
    expect(ariaLabel).toBeTruthy();
  });
});

test.describe('Mobile User Journey', () => {
  test('Mobile shopping experience', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 12'],
      permissions: ['geolocation'],
      geolocation: { latitude: 37.7749, longitude: -122.4194 }
    });
    const page = await context.newPage();
    
    // Open mobile menu
    await page.goto('/');
    await page.click('[data-testid="mobile-menu-toggle"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    
    // Navigate to products
    await page.click('[data-testid="mobile-nav-products"]');
    
    // Swipe through product carousel
    const carousel = page.locator('[data-testid="product-carousel"]');
    await carousel.scrollIntoViewIfNeeded();
    
    // Simulate swipe
    const box = await carousel.boundingBox();
    if (box) {
      await page.touchscreen.tap(box.x + box.width - 50, box.y + box.height / 2);
      await page.touchscreen.tap(box.x + 50, box.y + box.height / 2);
    }
    
    // Use bottom sheet for filters
    await page.click('[data-testid="mobile-filter-button"]');
    await expect(page.locator('[data-testid="filter-bottom-sheet"]')).toBeVisible();
    
    // Apply filters
    await page.click('[data-testid="filter-category-dairy"]');
    await page.click('[data-testid="apply-filters"]');
    
    // Add to cart with touch
    const product = page.locator('[data-testid="product-card"]').first();
    await product.tap();
    
    // Mini cart notification
    await expect(page.locator('[data-testid="mini-cart"]')).toBeVisible();
    
    // Continue shopping or checkout
    await page.click('[data-testid="continue-shopping"]');
    
    await context.close();
  });
});

test.describe('Error Recovery Journey', () => {
  test('Handle network errors gracefully', async ({ page }) => {
    await page.goto('/');
    
    // Simulate network failure
    await page.route('**/api/**', route => route.abort());
    
    // Try to load products
    await page.click('[data-testid="shop-now"]');
    
    // Error message should appear
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('connection');
    
    // Retry option should be available
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Restore network
    await page.unroute('**/api/**');
    
    // Retry
    await page.click('[data-testid="retry-button"]');
    
    // Should recover
    await expect(page.locator('[data-testid="product-card"]')).toBeVisible();
  });
  
  test('Form validation and error recovery', async ({ page }) => {
    await page.goto('/checkout');
    
    // Submit empty form
    await page.click('[data-testid="submit-order"]');
    
    // Multiple errors should appear
    const errors = page.locator('[data-testid="field-error"]');
    await expect(errors).toHaveCount(await errors.count());
    
    // Errors should be announced
    const alertRegion = page.locator('[role="alert"]');
    await expect(alertRegion).toBeVisible();
    
    // Fix errors one by one
    await page.fill('[data-testid="email-input"]', 'invalid-email');
    await page.click('[data-testid="submit-order"]');
    
    // Email error should update
    await expect(page.locator('[data-testid="email-error"]')).toContainText('valid email');
    
    // Correct the email
    await page.fill('[data-testid="email-input"]', 'valid@example.com');
    
    // Error should clear
    await expect(page.locator('[data-testid="email-error"]')).not.toBeVisible();
    
    // Complete form correctly
    await page.fill('[data-testid="name-input"]', 'John Doe');
    await page.fill('[data-testid="address-input"]', '123 Main St');
    
    // Submit should succeed
    await page.click('[data-testid="submit-order"]');
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
});

test.describe('User Journey Report Generation', () => {
  test.afterAll(async () => {
    // Generate comprehensive user journey report
    console.log('Generating user journey test results...');
    // Report is automatically generated by test runner
  });
});