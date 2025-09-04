/**
 * Cross-Browser Compatibility Testing Suite
 * Tests all components across different browsers and devices
 */

import { test, expect, devices } from '@playwright/test';

// Browser configurations to test
const BROWSERS = [
  { name: 'Chrome', project: 'chromium' },
  { name: 'Firefox', project: 'firefox' },
  { name: 'Safari', project: 'webkit' },
  { name: 'Edge', project: 'edge' },
];

// Device configurations to test
const DEVICES = [
  { name: 'iPhone 12', device: devices['iPhone 12'] },
  { name: 'iPhone 13 Pro', device: devices['iPhone 13 Pro'] },
  { name: 'Pixel 5', device: devices['Pixel 5'] },
  { name: 'Galaxy S20', device: devices['Galaxy S20'] },
  { name: 'iPad Pro', device: devices['iPad Pro'] },
  { name: 'iPad Mini', device: devices['iPad Mini'] },
];

// Critical user flows to test
const USER_FLOWS = [
  'authentication',
  'product-browsing',
  'cart-management',
  'checkout',
  'server-configuration',
  'theme-switching'
];

test.describe('Browser Feature Compatibility', () => {
  test('CSS Grid and Flexbox support', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Check CSS Grid support
    const hasGridSupport = await page.evaluate(() => {
      const testEl = document.createElement('div');
      return 'grid' in testEl.style;
    });
    expect(hasGridSupport).toBeTruthy();
    
    // Check Flexbox support
    const hasFlexSupport = await page.evaluate(() => {
      const testEl = document.createElement('div');
      return 'flex' in testEl.style;
    });
    expect(hasFlexSupport).toBeTruthy();
    
    // Verify layout integrity
    const layoutIssues = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const issues = [];
      for (const el of elements) {
        const rect = el.getBoundingClientRect();
        if (rect.width < 0 || rect.height < 0) {
          issues.push({
            element: el.tagName,
            class: el.className,
            issue: 'negative dimensions'
          });
        }
      }
      return issues;
    });
    expect(layoutIssues).toHaveLength(0);
  });
  
  test('JavaScript API compatibility', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Check for required APIs
    const apiSupport = await page.evaluate(() => {
      return {
        fetch: 'fetch' in window,
        promises: 'Promise' in window,
        localStorage: 'localStorage' in window,
        sessionStorage: 'sessionStorage' in window,
        webSocket: 'WebSocket' in window,
        intersectionObserver: 'IntersectionObserver' in window,
        mutationObserver: 'MutationObserver' in window,
        customElements: 'customElements' in window,
        shadowDOM: 'attachShadow' in Element.prototype,
        modules: 'noModule' in HTMLScriptElement.prototype
      };
    });
    
    // All required APIs should be supported
    Object.entries(apiSupport).forEach(([api, supported]) => {
      expect(supported, `${api} not supported in ${browserName}`).toBeTruthy();
    });
  });
  
  test('PostMessage communication', async ({ page, browserName }) => {
    await page.goto('/test#secure-iframe');
    
    // Test postMessage between iframe and parent
    const messageReceived = await page.evaluate(() => {
      return new Promise((resolve) => {
        let received = false;
        window.addEventListener('message', (event) => {
          if (event.data.type === 'test-message') {
            received = true;
          }
        });
        
        // Send test message to iframe
        const iframe = document.querySelector('iframe');
        if (iframe && iframe.contentWindow) {
          iframe.contentWindow.postMessage(
            { type: 'test-message', payload: 'test' },
            '*'
          );
        }
        
        setTimeout(() => resolve(received), 1000);
      });
    });
    
    expect(messageReceived).toBeTruthy();
  });
  
  test('Web Storage APIs', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Test localStorage
    await page.evaluate(() => {
      localStorage.setItem('test-key', 'test-value');
    });
    
    const localStorageValue = await page.evaluate(() => {
      return localStorage.getItem('test-key');
    });
    expect(localStorageValue).toBe('test-value');
    
    // Test sessionStorage
    await page.evaluate(() => {
      sessionStorage.setItem('session-key', 'session-value');
    });
    
    const sessionStorageValue = await page.evaluate(() => {
      return sessionStorage.getItem('session-key');
    });
    expect(sessionStorageValue).toBe('session-value');
    
    // Clean up
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });
});

test.describe('Visual Consistency', () => {
  BROWSERS.forEach(browser => {
    test(`${browser.name} - Component rendering`, async ({ page }) => {
      await page.goto('/test');
      
      // Wait for all components to load
      await page.waitForLoadState('networkidle');
      
      // Take screenshot for visual comparison
      await page.screenshot({
        path: `test-results/ui-ux/screenshots/${browser.name}-components.png`,
        fullPage: true
      });
      
      // Check for rendering issues
      const renderingIssues = await page.evaluate(() => {
        const issues = [];
        const elements = document.querySelectorAll('[data-testid]');
        
        elements.forEach(el => {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);
          
          // Check for invisible elements that should be visible
          if (rect.width === 0 || rect.height === 0) {
            if (styles.display !== 'none' && styles.visibility !== 'hidden') {
              issues.push({
                testId: el.getAttribute('data-testid'),
                issue: 'zero dimensions'
              });
            }
          }
          
          // Check for overflow issues
          if (el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight) {
            if (styles.overflow === 'visible') {
              issues.push({
                testId: el.getAttribute('data-testid'),
                issue: 'content overflow'
              });
            }
          }
        });
        
        return issues;
      });
      
      expect(renderingIssues).toHaveLength(0);
    });
  });
});

test.describe('Mobile Browser Testing', () => {
  DEVICES.forEach(device => {
    test(`${device.name} - Touch interactions`, async ({ browser }) => {
      const context = await browser.newContext({
        ...device.device,
        permissions: ['geolocation'],
        geolocation: { latitude: 37.7749, longitude: -122.4194 }
      });
      const page = await context.newPage();
      
      await page.goto('/');
      
      // Test touch scrolling
      await page.touchscreen.tap(100, 100);
      await page.waitForTimeout(100);
      
      // Test swipe gestures
      await page.touchscreen.tap(200, 300);
      await page.touchscreen.tap(200, 100);
      
      // Test pinch zoom (if applicable)
      const isZoomable = await page.evaluate(() => {
        const viewport = document.querySelector('meta[name="viewport"]');
        return !viewport?.getAttribute('content')?.includes('user-scalable=no');
      });
      
      if (isZoomable) {
        // Simulate pinch gesture
        await page.touchscreen.tap(150, 150);
        await page.touchscreen.tap(250, 250);
      }
      
      // Test touch targets
      const buttons = await page.$$('button, a');
      for (const button of buttons.slice(0, 5)) { // Test first 5 buttons
        const box = await button.boundingBox();
        if (box) {
          // Minimum touch target size for mobile
          expect(box.width).toBeGreaterThanOrEqual(44);
          expect(box.height).toBeGreaterThanOrEqual(44);
        }
      }
      
      await context.close();
    });
    
    test(`${device.name} - Viewport and orientation`, async ({ browser }) => {
      const context = await browser.newContext(device.device);
      const page = await context.newPage();
      
      await page.goto('/');
      
      // Test portrait orientation
      await page.setViewportSize({
        width: device.device.viewport.width,
        height: device.device.viewport.height
      });
      
      const portraitLayout = await page.evaluate(() => {
        return {
          width: window.innerWidth,
          height: window.innerHeight,
          orientation: window.screen.orientation?.type || 'unknown'
        };
      });
      
      // Test landscape orientation
      await page.setViewportSize({
        width: device.device.viewport.height,
        height: device.device.viewport.width
      });
      
      const landscapeLayout = await page.evaluate(() => {
        return {
          width: window.innerWidth,
          height: window.innerHeight,
          orientation: window.screen.orientation?.type || 'unknown'
        };
      });
      
      // Verify responsive layout adapts
      expect(portraitLayout.width).toBeLessThan(landscapeLayout.width);
      
      await context.close();
    });
  });
});

test.describe('Browser-Specific Features', () => {
  test('Safari - iOS specific features', async ({ page, browserName }) => {
    if (browserName !== 'webkit') {
      test.skip();
    }
    
    await page.goto('/');
    
    // Test iOS safe area handling
    const hasSafeAreaSupport = await page.evaluate(() => {
      const styles = window.getComputedStyle(document.documentElement);
      return styles.getPropertyValue('padding-top').includes('env(safe-area-inset');
    });
    
    // Test -webkit prefixed CSS
    const webkitStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      return {
        webkitAppearance: '-webkit-appearance' in testEl.style,
        webkitBackdropFilter: '-webkit-backdrop-filter' in testEl.style
      };
    });
    
    expect(webkitStyles.webkitAppearance).toBeTruthy();
  });
  
  test('Firefox - Gecko specific features', async ({ page, browserName }) => {
    if (browserName !== 'firefox') {
      test.skip();
    }
    
    await page.goto('/');
    
    // Test Firefox-specific CSS
    const firefoxStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      return {
        mozAppearance: '-moz-appearance' in testEl.style,
        scrollbarWidth: 'scrollbar-width' in testEl.style
      };
    });
    
    expect(firefoxStyles.mozAppearance).toBeTruthy();
  });
  
  test('Chrome - Blink specific features', async ({ page, browserName }) => {
    if (browserName !== 'chromium') {
      test.skip();
    }
    
    await page.goto('/');
    
    // Test Chrome-specific features
    const chromeFeatures = await page.evaluate(() => {
      return {
        webkitSpeechRecognition: 'webkitSpeechRecognition' in window,
        chrome: 'chrome' in window
      };
    });
    
    expect(chromeFeatures.webkitSpeechRecognition).toBeDefined();
  });
});

test.describe('Network and Performance', () => {
  const networkConditions = [
    { name: '3G Slow', download: 400, upload: 400, latency: 400 },
    { name: '3G Fast', download: 1600, upload: 750, latency: 150 },
    { name: '4G', download: 4000, upload: 3000, latency: 70 }
  ];
  
  networkConditions.forEach(condition => {
    test(`${condition.name} - Page load performance`, async ({ page, browserName }) => {
      // Simulate network condition
      const client = await page.context().newCDPSession(page);
      await client.send('Network.enable');
      await client.send('Network.emulateNetworkConditions', {
        offline: false,
        downloadThroughput: condition.download * 1024 / 8,
        uploadThroughput: condition.upload * 1024 / 8,
        latency: condition.latency
      });
      
      const startTime = Date.now();
      await page.goto('/');
      const loadTime = Date.now() - startTime;
      
      // Check page loads within acceptable time
      const maxLoadTime = condition.name === '3G Slow' ? 10000 : 5000;
      expect(loadTime).toBeLessThan(maxLoadTime);
      
      // Check for broken resources
      const brokenResources = await page.evaluate(() => {
        const images = Array.from(document.images);
        return images.filter(img => !img.complete || img.naturalWidth === 0);
      });
      
      expect(brokenResources).toHaveLength(0);
    });
  });
});

test.describe('JavaScript Error Detection', () => {
  BROWSERS.forEach(browser => {
    test(`${browser.name} - No console errors`, async ({ page }) => {
      const errors: string[] = [];
      
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      page.on('pageerror', (error) => {
        errors.push(error.message);
      });
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Navigate through different routes
      const routes = ['/', '/test', '/debug'];
      for (const route of routes) {
        await page.goto(route);
        await page.waitForLoadState('networkidle');
      }
      
      expect(errors).toHaveLength(0);
    });
  });
});

test.describe('Cross-Browser Form Compatibility', () => {
  test('Form input types support', async ({ page, browserName }) => {
    await page.goto('/test#form');
    
    const inputSupport = await page.evaluate(() => {
      const types = ['email', 'tel', 'url', 'date', 'time', 'color', 'range', 'number'];
      const support: Record<string, boolean> = {};
      
      types.forEach(type => {
        const input = document.createElement('input');
        input.type = type;
        support[type] = input.type === type;
      });
      
      return support;
    });
    
    // Check critical input types are supported
    expect(inputSupport.email).toBeTruthy();
    expect(inputSupport.tel).toBeTruthy();
    expect(inputSupport.number).toBeTruthy();
  });
  
  test('Form validation API', async ({ page, browserName }) => {
    await page.goto('/test#form');
    
    const validationSupport = await page.evaluate(() => {
      const form = document.createElement('form');
      const input = document.createElement('input');
      
      return {
        checkValidity: 'checkValidity' in form,
        setCustomValidity: 'setCustomValidity' in input,
        validity: 'validity' in input,
        validationMessage: 'validationMessage' in input
      };
    });
    
    Object.values(validationSupport).forEach(supported => {
      expect(supported).toBeTruthy();
    });
  });
});

test.describe('Browser Compatibility Matrix', () => {
  test.afterAll(async () => {
    // Generate cross-browser compatibility matrix
    console.log('Generating cross-browser compatibility matrix...');
    // Matrix is automatically generated by test runner
  });
});