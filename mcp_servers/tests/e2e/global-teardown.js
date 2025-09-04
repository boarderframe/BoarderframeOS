/**
 * Playwright global teardown - runs once after all tests
 */
const fs = require('fs');
const path = require('path');

async function globalTeardown(config) {
  console.log('🧹 Starting E2E test teardown...');
  
  // Clean up authentication state file
  const authStatePath = 'tests/e2e/auth-state.json';
  if (fs.existsSync(authStatePath)) {
    fs.unlinkSync(authStatePath);
    console.log('🗑️  Cleaned up authentication state');
  }
  
  // Clean up test artifacts if needed
  const testResultsDir = 'test-results/e2e';
  if (fs.existsSync(testResultsDir)) {
    console.log('📁 E2E test results saved to:', testResultsDir);
  }
  
  // Additional cleanup can be added here
  // For example: reset test database, clean up test files, etc.
  
  console.log('✅ E2E test teardown completed');
}

module.exports = globalTeardown;