/**
 * Performance Testing Suite
 * Core Web Vitals and Performance Optimization Validation
 */

import { test, expect } from '@playwright/test';
import lighthouse from 'lighthouse';
import { chromium } from 'playwright';

// Performance thresholds
const PERFORMANCE_THRESHOLDS = {
  LCP: 2500, // Largest Contentful Paint (ms)
  FID: 100,  // First Input Delay (ms)
  CLS: 0.1,  // Cumulative Layout Shift
  FCP: 1800, // First Contentful Paint (ms)
  TTI: 3500, // Time to Interactive (ms)
  TBT: 200,  // Total Blocking Time (ms)
  SI: 3000,  // Speed Index (ms)
};

// Routes to test
const ROUTES_TO_TEST = [
  { name: 'Home', path: '/' },
  { name: 'Test Page', path: '/test' },
  { name: 'Debug Page', path: '/debug' },
];

test.describe('Core Web Vitals', () => {
  test('Largest Contentful Paint (LCP)', async ({ page }) => {
    await page.goto('/');
    
    // Measure LCP
    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          resolve(lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
      });
    });
    
    expect(lcp).toBeLessThan(PERFORMANCE_THRESHOLDS.LCP);
  });
  
  test('First Input Delay (FID)', async ({ page }) => {
    await page.goto('/');
    
    // Simulate user input to measure FID
    const fid = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let firstInput = true;
        
        const observer = new PerformanceObserver((list) => {
          if (firstInput) {
            const entry = list.getEntries()[0] as any;
            resolve(entry.processingStart - entry.startTime);
            firstInput = false;
          }
        });
        
        observer.observe({ entryTypes: ['first-input'] });
        
        // Simulate click after page load
        setTimeout(() => {
          document.body.click();
        }, 100);
      });
    });
    
    expect(fid).toBeLessThan(PERFORMANCE_THRESHOLDS.FID);
  });
  
  test('Cumulative Layout Shift (CLS)', async ({ page }) => {
    await page.goto('/');
    
    // Measure CLS
    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsScore = 0;
        
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsScore += (entry as any).value;
            }
          }
        }).observe({ entryTypes: ['layout-shift'] });
        
        // Wait for page to stabilize
        setTimeout(() => resolve(clsScore), 5000);
      });
    });
    
    expect(cls).toBeLessThan(PERFORMANCE_THRESHOLDS.CLS);
  });
  
  test('First Contentful Paint (FCP)', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    
    const fcp = await page.evaluate(() => {
      const entry = performance.getEntriesByName(window.location.href)[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint');
      return paint ? paint.startTime : 0;
    });
    
    expect(fcp).toBeLessThan(PERFORMANCE_THRESHOLDS.FCP);
  });
  
  test('Time to Interactive (TTI)', async ({ page }) => {
    await page.goto('/');
    
    const tti = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        if ('PerformanceObserver' in window) {
          const observer = new PerformanceObserver((list) => {
            const perfEntries = list.getEntries();
            const navigationEntry = perfEntries.find(
              entry => entry.entryType === 'navigation'
            ) as PerformanceNavigationTiming;
            
            if (navigationEntry) {
              resolve(navigationEntry.loadEventEnd);
            }
          });
          
          observer.observe({ entryTypes: ['navigation'] });
        }
        
        // Fallback
        window.addEventListener('load', () => {
          resolve(performance.now());
        });
      });
    });
    
    expect(tti).toBeLessThan(PERFORMANCE_THRESHOLDS.TTI);
  });
});

test.describe('JavaScript Bundle Analysis', () => {
  test('Bundle size optimization', async ({ page }) => {
    const coverage = await page.coverage.startJSCoverage();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const jsCoverage = await page.coverage.stopJSCoverage();
    
    let totalBytes = 0;
    let usedBytes = 0;
    
    for (const entry of jsCoverage) {
      totalBytes += entry.text.length;
      
      for (const range of entry.ranges) {
        usedBytes += range.end - range.start - 1;
      }
    }
    
    const unusedPercentage = ((totalBytes - usedBytes) / totalBytes) * 100;
    
    // Check that unused JavaScript is less than 30%
    expect(unusedPercentage).toBeLessThan(30);
    
    // Check total bundle size (gzipped estimate)
    const gzippedEstimate = totalBytes * 0.3; // Rough gzip estimate
    expect(gzippedEstimate).toBeLessThan(200 * 1024); // 200KB limit
  });
  
  test('Code splitting effectiveness', async ({ page }) => {
    const resources: string[] = [];
    
    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('.js') && response.status() === 200) {
        resources.push(url);
      }
    });
    
    // Navigate to different routes to test code splitting
    await page.goto('/');
    const homeResources = [...resources];
    
    resources.length = 0;
    await page.goto('/test');
    const testResources = [...resources];
    
    resources.length = 0;
    await page.goto('/debug');
    const debugResources = [...resources];
    
    // Verify route-specific chunks are loaded
    const hasCodeSplitting = 
      testResources.some(r => r.includes('test')) ||
      debugResources.some(r => r.includes('debug'));
    
    expect(hasCodeSplitting).toBeTruthy();
  });
});

test.describe('Image Optimization', () => {
  test('Image loading performance', async ({ page }) => {
    const images: Array<{url: string, size: number, loadTime: number}> = [];
    
    page.on('response', async (response) => {
      const url = response.url();
      if (response.request().resourceType() === 'image') {
        const buffer = await response.body();
        images.push({
          url,
          size: buffer.length,
          loadTime: response.timing().responseEnd - response.timing().requestStart
        });
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check image optimization
    for (const image of images) {
      // Images should be reasonably sized
      expect(image.size).toBeLessThan(500 * 1024); // 500KB max per image
      
      // Images should load quickly
      expect(image.loadTime).toBeLessThan(2000); // 2s max load time
    }
  });
  
  test('Lazy loading implementation', async ({ page }) => {
    await page.goto('/');
    
    // Get all images
    const images = await page.$$('img');
    
    // Check for lazy loading attributes
    for (const img of images) {
      const loading = await img.getAttribute('loading');
      const isAboveFold = await img.evaluate((el) => {
        const rect = el.getBoundingClientRect();
        return rect.top < window.innerHeight;
      });
      
      // Below-fold images should have lazy loading
      if (!isAboveFold) {
        expect(loading).toBe('lazy');
      }
    }
  });
  
  test('Responsive images', async ({ page }) => {
    await page.goto('/');
    
    const responsiveImages = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img'));
      return imgs.map(img => ({
        src: img.src,
        srcset: img.srcset,
        sizes: img.sizes,
        naturalWidth: img.naturalWidth,
        displayWidth: img.getBoundingClientRect().width
      }));
    });
    
    for (const img of responsiveImages) {
      // Images should not be unnecessarily large
      expect(img.naturalWidth).toBeLessThanOrEqual(img.displayWidth * 2);
      
      // Responsive images should have srcset
      if (img.displayWidth > 200) {
        expect(img.srcset).toBeTruthy();
      }
    }
  });
});

test.describe('Network Performance', () => {
  test('HTTP/2 and compression', async ({ page }) => {
    const responses: Array<{url: string, headers: any}> = [];
    
    page.on('response', (response) => {
      responses.push({
        url: response.url(),
        headers: response.headers()
      });
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for compression
    const textResources = responses.filter(r => 
      r.url.endsWith('.js') || 
      r.url.endsWith('.css') || 
      r.url.endsWith('.html')
    );
    
    for (const resource of textResources) {
      const encoding = resource.headers['content-encoding'];
      expect(['gzip', 'br', 'deflate']).toContain(encoding);
    }
  });
  
  test('API response times', async ({ page }) => {
    const apiCalls: Array<{url: string, duration: number}> = [];
    
    page.on('response', async (response) => {
      if (response.url().includes('/api/')) {
        const timing = response.timing();
        apiCalls.push({
          url: response.url(),
          duration: timing.responseEnd - timing.requestStart
        });
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // All API calls should be fast
    for (const call of apiCalls) {
      expect(call.duration).toBeLessThan(1000); // 1s max for API calls
    }
  });
  
  test('Resource hints', async ({ page }) => {
    await page.goto('/');
    
    const resourceHints = await page.evaluate(() => {
      const hints = {
        preconnect: document.querySelectorAll('link[rel="preconnect"]').length,
        dnsPrefetch: document.querySelectorAll('link[rel="dns-prefetch"]').length,
        preload: document.querySelectorAll('link[rel="preload"]').length,
        prefetch: document.querySelectorAll('link[rel="prefetch"]').length
      };
      return hints;
    });
    
    // Should have resource hints for performance
    expect(resourceHints.preconnect + resourceHints.dnsPrefetch).toBeGreaterThan(0);
  });
});

test.describe('Memory Management', () => {
  test('Memory leaks detection', async ({ page }) => {
    // Navigate to page
    await page.goto('/');
    
    // Take initial heap snapshot
    const initialMetrics = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory;
      }
      return null;
    });
    
    if (initialMetrics) {
      // Perform actions that might cause memory leaks
      for (let i = 0; i < 10; i++) {
        await page.click('[data-testid="refresh-servers"]');
        await page.waitForTimeout(500);
      }
      
      // Force garbage collection if available
      await page.evaluate(() => {
        if ('gc' in window) {
          (window as any).gc();
        }
      });
      
      // Take final heap snapshot
      const finalMetrics = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory;
        }
        return null;
      });
      
      if (finalMetrics) {
        const memoryGrowth = finalMetrics.usedJSHeapSize - initialMetrics.usedJSHeapSize;
        const growthPercentage = (memoryGrowth / initialMetrics.usedJSHeapSize) * 100;
        
        // Memory growth should be reasonable (less than 50%)
        expect(growthPercentage).toBeLessThan(50);
      }
    }
  });
  
  test('DOM node cleanup', async ({ page }) => {
    await page.goto('/');
    
    // Count initial DOM nodes
    const initialNodeCount = await page.evaluate(() => {
      return document.querySelectorAll('*').length;
    });
    
    // Open and close modals multiple times
    for (let i = 0; i < 5; i++) {
      await page.click('[data-testid="open-modal"]');
      await page.waitForTimeout(100);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(100);
    }
    
    // Count final DOM nodes
    const finalNodeCount = await page.evaluate(() => {
      return document.querySelectorAll('*').length;
    });
    
    // DOM nodes should be cleaned up
    expect(finalNodeCount).toBeLessThanOrEqual(initialNodeCount * 1.1);
  });
});

test.describe('Lighthouse Audit', () => {
  test('Full Lighthouse performance audit', async () => {
    const browser = await chromium.launch({ headless: true });
    const port = 9222; // Chrome debugging port
    
    try {
      const browserWSEndpoint = browser.wsEndpoint();
      
      for (const route of ROUTES_TO_TEST) {
        const result = await lighthouse(
          `http://localhost:3001${route.path}`,
          {
            port,
            output: 'json',
            onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
            throttling: {
              rttMs: 150,
              throughputKbps: 1638.4,
              cpuSlowdownMultiplier: 4
            }
          }
        );
        
        if (result && result.lhr) {
          // Check performance score
          expect(result.lhr.categories.performance.score).toBeGreaterThan(0.9);
          
          // Check accessibility score
          expect(result.lhr.categories.accessibility.score).toBeGreaterThan(0.95);
          
          // Check best practices score
          expect(result.lhr.categories['best-practices'].score).toBeGreaterThan(0.9);
          
          // Check SEO score
          expect(result.lhr.categories.seo.score).toBeGreaterThan(0.9);
          
          // Check specific metrics
          const metrics = result.lhr.audits;
          expect(metrics['first-contentful-paint'].numericValue).toBeLessThan(PERFORMANCE_THRESHOLDS.FCP);
          expect(metrics['largest-contentful-paint'].numericValue).toBeLessThan(PERFORMANCE_THRESHOLDS.LCP);
          expect(metrics['cumulative-layout-shift'].numericValue).toBeLessThan(PERFORMANCE_THRESHOLDS.CLS);
          expect(metrics['total-blocking-time'].numericValue).toBeLessThan(PERFORMANCE_THRESHOLDS.TBT);
        }
      }
    } finally {
      await browser.close();
    }
  });
});

test.describe('Performance Report Generation', () => {
  test.afterAll(async () => {
    // Generate comprehensive performance report
    console.log('Generating performance metrics report...');
    // Report is automatically generated by test runner
  });
});