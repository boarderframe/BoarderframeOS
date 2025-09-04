const puppeteer = require('puppeteer');

(async () => {
  console.log('Starting browser test...');
  
  const browser = await puppeteer.launch({
    headless: false,
    devtools: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Listen to console logs
  page.on('console', msg => {
    const text = msg.text();
    if (!text.includes('Download the React DevTools')) {
      console.log('[BROWSER]:', text);
    }
  });
  
  // Listen to errors
  page.on('pageerror', err => {
    console.error('[ERROR]:', err.message);
  });
  
  console.log('Navigating to http://localhost:5173...');
  await page.goto('http://localhost:5173', { 
    waitUntil: 'networkidle0',
    timeout: 30000 
  });
  
  console.log('Page loaded, waiting 3 seconds...');
  await page.waitForTimeout(3000);
  
  // Check if splash screen is still visible
  const splashVisible = await page.evaluate(() => {
    const splash = document.getElementById('splash-screen');
    return splash && splash.style.display !== 'none';
  });
  
  console.log('Splash screen still visible:', splashVisible);
  
  // Check for the loaded state
  const bodyContent = await page.evaluate(() => {
    return document.body.innerText.substring(0, 500);
  });
  
  console.log('Body content preview:', bodyContent);
  
  // Check if auth page is showing
  const hasAuthContent = await page.evaluate(() => {
    const text = document.body.innerText.toLowerCase();
    return text.includes('sign in') || text.includes('login') || text.includes('email') || text.includes('password');
  });
  
  console.log('Has auth content:', hasAuthContent);
  
  // Take a screenshot
  await page.screenshot({ path: 'app-screenshot.png' });
  console.log('Screenshot saved as app-screenshot.png');
  
  console.log('Test complete. Browser will remain open for 5 seconds...');
  await page.waitForTimeout(5000);
  
  await browser.close();
  console.log('Done!');
})();