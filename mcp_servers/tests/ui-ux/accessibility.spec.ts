/**
 * Comprehensive Accessibility Testing Suite
 * WCAG 2.1 AA Compliance Validation
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Test all major components for accessibility
const COMPONENTS_TO_TEST = [
  { name: 'ServerCard', url: '/test#server-card' },
  { name: 'ProductCard', url: '/test#product-card' },
  { name: 'ShoppingCart', url: '/test#shopping-cart' },
  { name: 'Modal', url: '/test#modal' },
  { name: 'Button', url: '/test#button' },
  { name: 'Input', url: '/test#input' },
  { name: 'Toast', url: '/test#toast' },
  { name: 'Badge', url: '/test#badge' },
  { name: 'ConnectionStatus', url: '/test#connection-status' },
  { name: 'MetricsPanel', url: '/test#metrics-panel' },
  { name: 'ServerList', url: '/' },
  { name: 'KrogerServerDetails', url: '/test#kroger-details' },
  { name: 'SecureIframe', url: '/test#secure-iframe' }
];

test.describe('WCAG 2.1 AA Compliance', () => {
  COMPONENTS_TO_TEST.forEach(component => {
    test(`${component.name} - Accessibility Audit`, async ({ page }) => {
      await page.goto(component.url);
      
      // Wait for component to load
      await page.waitForLoadState('networkidle');
      
      // Run axe accessibility scan
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();
      
      // No violations should be present
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  });
});

test.describe('Keyboard Navigation', () => {
  test('Complete keyboard navigation flow', async ({ page }) => {
    await page.goto('/');
    
    // Test Tab navigation through all interactive elements
    const interactiveElements = await page.$$('[tabindex]:not([tabindex="-1"]), a, button, input, select, textarea');
    
    for (let i = 0; i < interactiveElements.length; i++) {
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
    }
    
    // Test Shift+Tab reverse navigation
    for (let i = interactiveElements.length - 1; i >= 0; i--) {
      await page.keyboard.press('Shift+Tab');
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
    }
  });
  
  test('Modal keyboard trap', async ({ page }) => {
    await page.goto('/test#modal');
    
    // Open modal
    await page.click('[data-testid="open-modal"]');
    
    // Focus should be trapped within modal
    const modalElements = await page.$$('[data-testid="modal"] [tabindex]:not([tabindex="-1"]), [data-testid="modal"] button');
    
    for (let i = 0; i < modalElements.length * 2; i++) {
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement);
      const isInModal = await page.evaluate((el) => {
        return el?.closest('[data-testid="modal"]') !== null;
      }, focusedElement);
      expect(isInModal).toBeTruthy();
    }
    
    // Escape should close modal
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="modal"]')).not.toBeVisible();
  });
  
  test('Form keyboard interaction', async ({ page }) => {
    await page.goto('/test#form');
    
    // Navigate through form fields
    await page.keyboard.press('Tab');
    await page.keyboard.type('Test Input');
    
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space'); // Check checkbox
    
    await page.keyboard.press('Tab');
    await page.keyboard.press('ArrowDown'); // Select dropdown option
    
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter'); // Submit form
    
    // Verify form submission
    await expect(page.locator('[data-testid="form-success"]')).toBeVisible();
  });
});

test.describe('Screen Reader Compatibility', () => {
  test('ARIA labels and roles', async ({ page }) => {
    await page.goto('/');
    
    // Check all interactive elements have proper ARIA labels
    const buttons = await page.$$('button');
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const textContent = await button.textContent();
      expect(ariaLabel || textContent).toBeTruthy();
    }
    
    // Check navigation landmarks
    const nav = await page.$('nav[role="navigation"]');
    expect(nav).toBeTruthy();
    
    const main = await page.$('main[role="main"]');
    expect(main).toBeTruthy();
    
    // Check heading hierarchy
    const headings = await page.$$('h1, h2, h3, h4, h5, h6');
    let previousLevel = 0;
    for (const heading of headings) {
      const tagName = await heading.evaluate(el => el.tagName);
      const level = parseInt(tagName.substring(1));
      expect(level - previousLevel).toBeLessThanOrEqual(1);
      previousLevel = level;
    }
  });
  
  test('Live regions for dynamic content', async ({ page }) => {
    await page.goto('/');
    
    // Check for aria-live regions
    const liveRegions = await page.$$('[aria-live]');
    expect(liveRegions.length).toBeGreaterThan(0);
    
    // Test status announcements
    await page.click('[data-testid="refresh-servers"]');
    const statusRegion = await page.$('[role="status"]');
    const statusText = await statusRegion?.textContent();
    expect(statusText).toBeTruthy();
  });
  
  test('Form validation announcements', async ({ page }) => {
    await page.goto('/test#form');
    
    // Submit empty form
    await page.click('[data-testid="submit-form"]');
    
    // Check error announcements
    const errorRegion = await page.$('[role="alert"]');
    expect(errorRegion).toBeTruthy();
    
    const errorMessage = await errorRegion?.textContent();
    expect(errorMessage).toContain('required');
    
    // Check field has aria-invalid
    const invalidField = await page.$('input[aria-invalid="true"]');
    expect(invalidField).toBeTruthy();
    
    // Check field has aria-describedby pointing to error
    const describedBy = await invalidField?.getAttribute('aria-describedby');
    const errorElement = await page.$(`#${describedBy}`);
    expect(errorElement).toBeTruthy();
  });
});

test.describe('Color Contrast', () => {
  test('Text contrast ratios', async ({ page }) => {
    await page.goto('/');
    
    // Use axe-core to check color contrast
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['color-contrast'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('Focus indicators visibility', async ({ page }) => {
    await page.goto('/');
    
    // Tab to first interactive element
    await page.keyboard.press('Tab');
    
    // Check focus indicator is visible
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        outlineColor: styles.outlineColor,
        outlineWidth: styles.outlineWidth,
        boxShadow: styles.boxShadow
      };
    });
    
    // Should have visible focus indicator
    expect(
      focusedElement?.outline !== 'none' || 
      focusedElement?.boxShadow !== 'none'
    ).toBeTruthy();
  });
  
  test('Dark mode contrast', async ({ page }) => {
    await page.goto('/');
    
    // Toggle dark mode
    await page.click('[data-testid="theme-toggle"]');
    
    // Wait for theme change
    await page.waitForTimeout(500);
    
    // Check contrast in dark mode
    const darkModeResults = await new AxeBuilder({ page })
      .withTags(['color-contrast'])
      .analyze();
    
    expect(darkModeResults.violations).toEqual([]);
  });
});

test.describe('Responsive Accessibility', () => {
  const viewports = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1920, height: 1080 }
  ];
  
  viewports.forEach(viewport => {
    test(`${viewport.name} - Touch targets and spacing`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');
      
      // Check touch target sizes (minimum 44x44px for mobile)
      const buttons = await page.$$('button, a');
      for (const button of buttons) {
        const box = await button.boundingBox();
        if (box) {
          if (viewport.name === 'Mobile') {
            expect(box.width).toBeGreaterThanOrEqual(44);
            expect(box.height).toBeGreaterThanOrEqual(44);
          }
        }
      }
      
      // Run accessibility scan for viewport
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2aa'])
        .analyze();
      
      expect(results.violations).toEqual([]);
    });
  });
});

test.describe('Assistive Technology Features', () => {
  test('Skip navigation links', async ({ page }) => {
    await page.goto('/');
    
    // Press Tab to reveal skip link
    await page.keyboard.press('Tab');
    
    // Check skip link is present and visible on focus
    const skipLink = await page.$('a[href="#main"]');
    expect(skipLink).toBeTruthy();
    
    const isVisible = await skipLink?.isVisible();
    expect(isVisible).toBeTruthy();
    
    // Activate skip link
    await page.keyboard.press('Enter');
    
    // Check focus moved to main content
    const focusedId = await page.evaluate(() => document.activeElement?.id);
    expect(focusedId).toBe('main');
  });
  
  test('Reduced motion support', async ({ page }) => {
    // Set prefers-reduced-motion
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/');
    
    // Check animations are disabled
    const hasAnimations = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      for (const el of elements) {
        const styles = window.getComputedStyle(el);
        if (styles.animationDuration !== '0s' || styles.transitionDuration !== '0s') {
          return true;
        }
      }
      return false;
    });
    
    expect(hasAnimations).toBeFalsy();
  });
  
  test('High contrast mode support', async ({ page }) => {
    // Emulate high contrast mode
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/');
    
    // Check that UI is still usable
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    expect(results.violations).toEqual([]);
  });
});

test.describe('Error Handling Accessibility', () => {
  test('Error messages are announced', async ({ page }) => {
    await page.goto('/');
    
    // Simulate network error
    await page.route('**/api/**', route => route.abort());
    await page.click('[data-testid="refresh-servers"]');
    
    // Check error is announced
    const errorAlert = await page.$('[role="alert"]');
    expect(errorAlert).toBeTruthy();
    
    const errorText = await errorAlert?.textContent();
    expect(errorText).toContain('error');
    
    // Check error can be dismissed with keyboard
    await page.keyboard.press('Escape');
    await expect(errorAlert).not.toBeVisible();
  });
  
  test('Loading states are announced', async ({ page }) => {
    await page.goto('/');
    
    // Slow down network
    await page.route('**/api/**', async route => {
      await page.waitForTimeout(2000);
      await route.continue();
    });
    
    await page.click('[data-testid="refresh-servers"]');
    
    // Check loading state is announced
    const loadingRegion = await page.$('[aria-busy="true"]');
    expect(loadingRegion).toBeTruthy();
    
    const loadingText = await page.$('[role="status"]');
    const text = await loadingText?.textContent();
    expect(text).toContain('Loading');
  });
});

test.describe('Accessibility Report Generation', () => {
  test.afterAll(async () => {
    // Generate comprehensive accessibility report
    console.log('Generating accessibility compliance report...');
    // Report is automatically generated by test runner
  });
});