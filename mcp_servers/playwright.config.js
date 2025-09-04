/**
 * Playwright configuration for end-to-end testing
 */
import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/e2e/results.json' }],
    ['junit', { outputFile: 'test-results/e2e/junit.xml' }]
  ],
  
  /* Shared settings for all projects */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Take screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Record video on failure */
    video: 'retain-on-failure',
    
    /* Global timeout for each action */
    actionTimeout: 10000,
    
    /* Navigation timeout */
    navigationTimeout: 30000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* Test against branded browsers */
    {
      name: 'Microsoft Edge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
  ],

  /* Configure global setup and teardown */
  globalSetup: require.resolve('./tests/e2e/global-setup.js'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.js'),

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'npm run start:backend',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
    {
      command: 'npm run start:frontend',
      port: 3000,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],

  /* Test timeout */
  timeout: 30000,

  /* Expect timeout */
  expect: {
    timeout: 5000,
  },

  /* Output directory */
  outputDir: 'test-results/e2e',

  /* Metadata */
  metadata: {
    'test-environment': process.env.NODE_ENV || 'test',
    'api-url': process.env.REACT_APP_API_URL || 'http://localhost:8000',
    'frontend-url': process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
  },
});