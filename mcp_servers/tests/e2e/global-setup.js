/**
 * Playwright global setup - runs once before all tests
 */
const { chromium } = require('@playwright/test');

async function globalSetup(config) {
  console.log('🚀 Starting E2E test setup...');
  
  // Set up test environment
  process.env.NODE_ENV = 'test';
  process.env.REACT_APP_API_URL = 'http://localhost:8000';
  
  // Wait for services to be ready
  await waitForService('http://localhost:8000/health', 'Backend API');
  await waitForService('http://localhost:3000', 'Frontend');
  
  // Create browser instance for authentication
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Perform login to get authentication state
    console.log('🔐 Setting up authentication...');
    
    await page.goto('http://localhost:3000/login');
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    // Wait for successful login
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    
    // Save authentication state
    await context.storageState({ path: 'tests/e2e/auth-state.json' });
    
    console.log('✅ Authentication state saved');
    
  } catch (error) {
    console.error('❌ Failed to set up authentication:', error);
    throw error;
  } finally {
    await browser.close();
  }
  
  console.log('✅ E2E test setup completed');
}

async function waitForService(url, serviceName, maxAttempts = 30) {
  console.log(`⏳ Waiting for ${serviceName} at ${url}...`);
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`✅ ${serviceName} is ready`);
        return;
      }
    } catch (error) {
      // Service not ready yet
    }
    
    console.log(`⏳ Attempt ${attempt}/${maxAttempts} - ${serviceName} not ready yet...`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  throw new Error(`❌ ${serviceName} failed to start after ${maxAttempts} attempts`);
}

module.exports = globalSetup;