/**
 * Component-Specific UI/UX Testing Suite
 * Individual component validation and interaction testing
 */

import { test, expect } from '@playwright/test';

test.describe('ServerCard Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });
  
  test('Visual hierarchy and layout', async ({ page }) => {
    const serverCard = page.locator('[data-testid="server-card"]').first();
    await expect(serverCard).toBeVisible();
    
    // Check component structure
    await expect(serverCard.locator('[data-testid="server-name"]')).toBeVisible();
    await expect(serverCard.locator('[data-testid="server-status"]')).toBeVisible();
    await expect(serverCard.locator('[data-testid="server-actions"]')).toBeVisible();
    
    // Check responsive behavior
    const viewports = [
      { width: 375, height: 667 },  // Mobile
      { width: 768, height: 1024 }, // Tablet
      { width: 1920, height: 1080 } // Desktop
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await expect(serverCard).toBeVisible();
      
      // Card should adapt to viewport
      const cardWidth = await serverCard.evaluate(el => el.getBoundingClientRect().width);
      expect(cardWidth).toBeLessThanOrEqual(viewport.width - 32); // Account for padding
    }
  });
  
  test('Interactive states and feedback', async ({ page }) => {
    const serverCard = page.locator('[data-testid="server-card"]').first();
    
    // Hover state
    await serverCard.hover();
    const hoverStyles = await serverCard.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        transform: styles.transform,
        boxShadow: styles.boxShadow
      };
    });
    expect(hoverStyles.transform || hoverStyles.boxShadow).toBeTruthy();
    
    // Focus state
    await serverCard.focus();
    const focusStyles = await serverCard.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        boxShadow: styles.boxShadow
      };
    });
    expect(focusStyles.outline || focusStyles.boxShadow).toBeTruthy();
    
    // Click feedback
    await serverCard.click();
    await expect(page.locator('[data-testid="server-details-modal"]')).toBeVisible();
  });
  
  test('Status indicators and real-time updates', async ({ page }) => {
    const serverCard = page.locator('[data-testid="server-card"]').first();
    const statusIndicator = serverCard.locator('[data-testid="server-status"]');
    
    // Check status color coding
    const statusColor = await statusIndicator.evaluate(el => {
      return window.getComputedStyle(el).backgroundColor;
    });
    
    // Status should have appropriate color
    expect(statusColor).toMatch(/rgb/);
    
    // Test real-time status updates
    await page.evaluate(() => {
      // Simulate WebSocket status update
      window.dispatchEvent(new CustomEvent('server-status-update', {
        detail: { serverId: 'test-server', status: 'error' }
      }));
    });
    
    // Status should update
    await expect(statusIndicator).toHaveAttribute('data-status', 'error');
  });
});

test.describe('ProductCard Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/test#product-card');
  });
  
  test('Product information display', async ({ page }) => {
    const productCard = page.locator('[data-testid="product-card"]').first();
    
    // Essential elements
    await expect(productCard.locator('[data-testid="product-image"]')).toBeVisible();
    await expect(productCard.locator('[data-testid="product-name"]')).toBeVisible();
    await expect(productCard.locator('[data-testid="product-price"]')).toBeVisible();
    await expect(productCard.locator('[data-testid="add-to-cart"]')).toBeVisible();
    
    // Image loading
    const image = productCard.locator('[data-testid="product-image"]');
    await expect(image).toHaveAttribute('alt');
    
    const imageSrc = await image.getAttribute('src');
    expect(imageSrc).toBeTruthy();
    
    // Price formatting
    const price = await productCard.locator('[data-testid="product-price"]').textContent();
    expect(price).toMatch(/\$\d+\.\d{2}/);
  });
  
  test('Add to cart interaction', async ({ page }) => {
    const productCard = page.locator('[data-testid="product-card"]').first();
    const addToCartBtn = productCard.locator('[data-testid="add-to-cart"]');
    
    // Initial state
    await expect(addToCartBtn).toHaveText('Add to Cart');
    
    // Click to add
    await addToCartBtn.click();
    
    // Button should show feedback
    await expect(addToCartBtn).toHaveText('Added!');
    
    // Cart count should update
    const cartCount = page.locator('[data-testid="cart-count"]');
    await expect(cartCount).toHaveText('1');
    
    // Animation should play
    const animation = await productCard.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.animation || styles.transition;
    });
    expect(animation).toBeTruthy();
  });
  
  test('Product quick view', async ({ page }) => {
    const productCard = page.locator('[data-testid="product-card"]').first();
    
    // Hover to show quick view
    await productCard.hover();
    const quickViewBtn = productCard.locator('[data-testid="quick-view"]');
    await expect(quickViewBtn).toBeVisible();
    
    // Open quick view
    await quickViewBtn.click();
    
    // Modal should open with product details
    const modal = page.locator('[data-testid="quick-view-modal"]');
    await expect(modal).toBeVisible();
    await expect(modal.locator('[data-testid="product-description"]')).toBeVisible();
    await expect(modal.locator('[data-testid="product-specs"]')).toBeVisible();
  });
});

test.describe('ShoppingCart Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/test#shopping-cart');
    // Add items to cart
    await page.evaluate(() => {
      window.localStorage.setItem('cart', JSON.stringify([
        { id: '1', name: 'Product 1', price: 19.99, quantity: 2 },
        { id: '2', name: 'Product 2', price: 29.99, quantity: 1 }
      ]));
    });
    await page.reload();
  });
  
  test('Cart display and calculations', async ({ page }) => {
    const cart = page.locator('[data-testid="shopping-cart"]');
    
    // Cart items display
    const items = cart.locator('[data-testid="cart-item"]');
    await expect(items).toHaveCount(2);
    
    // Quantity controls
    const firstItem = items.first();
    const quantityInput = firstItem.locator('[data-testid="quantity-input"]');
    await expect(quantityInput).toHaveValue('2');
    
    // Increase quantity
    await firstItem.locator('[data-testid="increase-quantity"]').click();
    await expect(quantityInput).toHaveValue('3');
    
    // Total calculation
    const total = cart.locator('[data-testid="cart-total"]');
    const totalText = await total.textContent();
    expect(totalText).toContain('$89.97'); // (19.99 * 3) + 29.99
  });
  
  test('Remove items and empty state', async ({ page }) => {
    const cart = page.locator('[data-testid="shopping-cart"]');
    
    // Remove first item
    await cart.locator('[data-testid="remove-item"]').first().click();
    await expect(cart.locator('[data-testid="cart-item"]')).toHaveCount(1);
    
    // Remove last item
    await cart.locator('[data-testid="remove-item"]').click();
    
    // Empty cart state
    await expect(cart.locator('[data-testid="empty-cart"]')).toBeVisible();
    await expect(cart.locator('[data-testid="empty-cart"]')).toContainText('Your cart is empty');
  });
  
  test('Checkout flow', async ({ page }) => {
    const cart = page.locator('[data-testid="shopping-cart"]');
    
    // Click checkout
    await cart.locator('[data-testid="checkout-button"]').click();
    
    // Should navigate to checkout
    await expect(page).toHaveURL(/checkout/);
    
    // Cart data should persist
    const checkoutData = await page.evaluate(() => {
      return window.localStorage.getItem('checkout-data');
    });
    expect(checkoutData).toBeTruthy();
  });
});

test.describe('Modal Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/test#modal');
  });
  
  test('Modal lifecycle and animations', async ({ page }) => {
    const openBtn = page.locator('[data-testid="open-modal"]');
    const modal = page.locator('[data-testid="modal"]');
    const overlay = page.locator('[data-testid="modal-overlay"]');
    
    // Initially hidden
    await expect(modal).not.toBeVisible();
    
    // Open modal
    await openBtn.click();
    
    // Modal and overlay visible
    await expect(modal).toBeVisible();
    await expect(overlay).toBeVisible();
    
    // Animation plays
    const animation = await modal.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.animation || styles.transition;
    });
    expect(animation).toBeTruthy();
    
    // Close via X button
    await modal.locator('[data-testid="modal-close"]').click();
    await expect(modal).not.toBeVisible();
  });
  
  test('Focus management', async ({ page }) => {
    await page.locator('[data-testid="open-modal"]').click();
    const modal = page.locator('[data-testid="modal"]');
    
    // Focus should be trapped in modal
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toContain('modal');
    
    // Tab through modal elements
    const focusableElements = await modal.locator('button, input, [tabindex="0"]').count();
    for (let i = 0; i < focusableElements * 2; i++) {
      await page.keyboard.press('Tab');
      const inModal = await page.evaluate(() => {
        return document.activeElement?.closest('[data-testid="modal"]') !== null;
      });
      expect(inModal).toBeTruthy();
    }
  });
  
  test('Overlay click and escape key', async ({ page }) => {
    await page.locator('[data-testid="open-modal"]').click();
    const modal = page.locator('[data-testid="modal"]');
    const overlay = page.locator('[data-testid="modal-overlay"]');
    
    // Click overlay to close
    await overlay.click({ position: { x: 10, y: 10 } });
    await expect(modal).not.toBeVisible();
    
    // Reopen
    await page.locator('[data-testid="open-modal"]').click();
    await expect(modal).toBeVisible();
    
    // Press Escape to close
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });
});

test.describe('Input Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/test#form');
  });
  
  test('Text input states and validation', async ({ page }) => {
    const input = page.locator('[data-testid="text-input"]');
    
    // Focus state
    await input.focus();
    const focusStyles = await input.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.borderColor || styles.boxShadow;
    });
    expect(focusStyles).toBeTruthy();
    
    // Type text
    await input.type('Test input');
    await expect(input).toHaveValue('Test input');
    
    // Clear and test required validation
    await input.clear();
    await input.blur();
    
    // Error state
    await expect(input).toHaveAttribute('aria-invalid', 'true');
    const errorMessage = page.locator('[data-testid="input-error"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('required');
  });
  
  test('Select dropdown interaction', async ({ page }) => {
    const select = page.locator('[data-testid="select-input"]');
    
    // Open dropdown
    await select.click();
    
    // Options should be visible
    const options = page.locator('[data-testid="select-option"]');
    await expect(options.first()).toBeVisible();
    
    // Select an option
    await options.nth(1).click();
    
    // Value should update
    const selectedValue = await select.inputValue();
    expect(selectedValue).toBeTruthy();
    
    // Dropdown should close
    await expect(options.first()).not.toBeVisible();
  });
  
  test('Checkbox and radio button states', async ({ page }) => {
    const checkbox = page.locator('[data-testid="checkbox-input"]');
    const radio = page.locator('[data-testid="radio-input"]');
    
    // Checkbox interaction
    await expect(checkbox).not.toBeChecked();
    await checkbox.click();
    await expect(checkbox).toBeChecked();
    
    // Visual feedback
    const checkboxStyles = await checkbox.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.backgroundColor || styles.borderColor;
    });
    expect(checkboxStyles).toBeTruthy();
    
    // Radio button interaction
    const radioOptions = page.locator('[data-testid="radio-option"]');
    await radioOptions.first().click();
    await expect(radioOptions.first()).toBeChecked();
    
    // Selecting another option
    await radioOptions.nth(1).click();
    await expect(radioOptions.first()).not.toBeChecked();
    await expect(radioOptions.nth(1)).toBeChecked();
  });
});

test.describe('Toast Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/test#toast');
  });
  
  test('Toast display and auto-dismiss', async ({ page }) => {
    // Trigger success toast
    await page.locator('[data-testid="show-success-toast"]').click();
    
    const toast = page.locator('[data-testid="toast-success"]');
    await expect(toast).toBeVisible();
    
    // Check toast content
    await expect(toast).toContainText('Success');
    
    // Auto-dismiss after timeout
    await expect(toast).not.toBeVisible({ timeout: 5000 });
  });
  
  test('Multiple toast stacking', async ({ page }) => {
    // Trigger multiple toasts
    await page.locator('[data-testid="show-success-toast"]').click();
    await page.locator('[data-testid="show-error-toast"]').click();
    await page.locator('[data-testid="show-warning-toast"]').click();
    
    // All toasts should be visible
    const toasts = page.locator('[data-testid^="toast-"]');
    await expect(toasts).toHaveCount(3);
    
    // Check stacking order
    const positions = await toasts.evaluateAll(elements => {
      return elements.map(el => el.getBoundingClientRect().top);
    });
    
    // Each toast should be below the previous one
    for (let i = 1; i < positions.length; i++) {
      expect(positions[i]).toBeGreaterThan(positions[i - 1]);
    }
  });
  
  test('Toast interaction and dismissal', async ({ page }) => {
    await page.locator('[data-testid="show-info-toast"]').click();
    
    const toast = page.locator('[data-testid="toast-info"]');
    await expect(toast).toBeVisible();
    
    // Manual dismiss
    await toast.locator('[data-testid="toast-close"]').click();
    await expect(toast).not.toBeVisible();
  });
});

test.describe('Theme Provider', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });
  
  test('Theme switching', async ({ page }) => {
    const themeToggle = page.locator('[data-testid="theme-toggle"]');
    
    // Check initial theme
    const initialTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });
    expect(initialTheme).toBe('light');
    
    // Switch to dark theme
    await themeToggle.click();
    
    const darkTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });
    expect(darkTheme).toBe('dark');
    
    // Colors should change
    const backgroundColor = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });
    expect(backgroundColor).toContain('rgb'); // Dark color
  });
  
  test('Theme persistence', async ({ page }) => {
    // Set dark theme
    await page.locator('[data-testid="theme-toggle"]').click();
    
    // Reload page
    await page.reload();
    
    // Theme should persist
    const theme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });
    expect(theme).toBe('dark');
  });
  
  test('System theme preference', async ({ page }) => {
    // Set system preference to dark
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.reload();
    
    // Should respect system preference
    const theme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });
    expect(theme).toBe('dark');
  });
});

test.describe('Component Showcase', () => {
  test('Interactive component explorer', async ({ page }) => {
    await page.goto('/test');
    
    // Component navigation
    const componentNav = page.locator('[data-testid="component-nav"]');
    const componentLinks = componentNav.locator('a');
    
    // Should have all components listed
    const componentCount = await componentLinks.count();
    expect(componentCount).toBeGreaterThan(10);
    
    // Navigate to each component
    for (let i = 0; i < Math.min(componentCount, 5); i++) {
      await componentLinks.nth(i).click();
      
      // Component should be displayed
      const componentDemo = page.locator('[data-testid="component-demo"]');
      await expect(componentDemo).toBeVisible();
      
      // Props editor should be available
      const propsEditor = page.locator('[data-testid="props-editor"]');
      await expect(propsEditor).toBeVisible();
      
      // Code preview should be shown
      const codePreview = page.locator('[data-testid="code-preview"]');
      await expect(codePreview).toBeVisible();
    }
  });
});

test.describe('Component Report Generation', () => {
  test.afterAll(async () => {
    // Generate component coverage report
    console.log('Generating component testing report...');
    // Report is automatically generated by test runner
  });
});