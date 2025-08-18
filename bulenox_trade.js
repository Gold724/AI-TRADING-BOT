const dotenv = require('dotenv');
dotenv.config();
const playwright = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BULENOX_USERNAME = process.env.BULENOX_USERNAME;
const BULENOX_PASSWORD = process.env.BULENOX_PASSWORD;
const headless = process.env.HEADLESS !== 'false';

(async () => {
  let browser;
  try {
    browser = await playwright.chromium.launch({ headless });
    const context = await browser.newContext();
    const page = await context.newPage();
    page.setDefaultTimeout(30000);

    // Network interceptor for trade requests
    await page.route('**', async (route, request) => {
      if (request.method() === 'POST' &&
          /\/api\/trade|\/v1\/trade|\/trade(?![\w-])/i.test(request.url())) {
        const postData = request.postData();
        let isTrade = false;
        if (postData) {
          try {
            const json = JSON.parse(postData);
            if (json.symbol || json.amount || json.price || json.order || json.trade || json.buy || json.sell) {
              isTrade = true;
            }
          } catch {
            if (/symbol|amount|price|order|trade|buy|sell/i.test(postData)) {
              isTrade = true;
            }
          }
        }
        if (isTrade) {
          const curlCmd = `curl -X POST '${request.url()}' -H 'Content-Type: application/json' -d '${postData}'`;
          fs.writeFileSync('trade.sh', curlCmd);
          console.log('Trade request detected and cURL command saved to trade.sh');
          // Convert cURL to Python using curlconverter
          try {
            fs.writeFileSync('trade_curl.txt', curlCmd);
            execSync('python -m curlconverter trade_curl.txt > trade_request_full.py');
            console.log('Converted cURL to Python requests code in trade_request_full.py');
          } catch (err) {
            console.error('Failed to convert cURL to Python:', err);
          }
        }
      }
      route.continue();
    });

    // Helper for robust selector retries
    async function waitForSelectorWithRetries(page, selectors, retries = 3, delay = 2000) {
      for (let i = 0; i < retries; i++) {
        for (const selector of selectors) {
          try {
            const element = await page.waitForSelector(selector, { timeout: 5000 });
            if (element) return element;
          } catch {}
        }
        console.log(`Retrying wait for selectors after delay (${i + 1}/${retries})...`);
        await page.waitForTimeout(delay);
      }
      throw new Error(`None of the selectors found: ${selectors.join(', ')}`);
    }

    // --- STEP 1: Login ---
    await page.goto('https://bulenox.projectx.com/login', { waitUntil: 'networkidle' });
    const loginScreenshotPath = path.join(__dirname, 'login_page.png');
    await page.screenshot({ path: loginScreenshotPath });
    console.log(`Login page screenshot captured at ${loginScreenshotPath}`);
    try {
      await waitForSelectorWithRetries(page, [
        'input[name="username"]',
        'input#username',
        'input[placeholder*="User"]',
        'input[type="text"]',
        'input',
        'form input',
        'input:not([type="password"])'
      ]);
    } catch (loginSelectorError) {
      console.error('Failed to find username input:', loginSelectorError);
      const screenshotPath = path.join(__dirname, 'login_selector_error.png');
      await page.screenshot({ path: screenshotPath });
      console.log(`Screenshot captured at ${screenshotPath}`);
      throw loginSelectorError;
    }
    try {
      await waitForSelectorWithRetries(page, [
        'input[name="password"]',
        'input#password',
        'input[placeholder*="Pass"]',
        'input[type="password"]',
        'form input[type="password"]'
      ]);
    } catch (passwordSelectorError) {
      console.error('Failed to find password input:', passwordSelectorError);
      const screenshotPath = path.join(__dirname, 'password_selector_error.png');
      await page.screenshot({ path: screenshotPath });
      console.log(`Screenshot captured at ${screenshotPath}`);
      throw passwordSelectorError;
    }
    // Login selectors using input[name="userName"] and input[name="password"]
    const usernameInput = await page.waitForSelector('input[name="userName"]', {timeout: 10000});
    const passwordInput = await page.waitForSelector('input[name="password"]', {timeout: 10000});
    await usernameInput.fill(process.env.BULENOX_USERNAME);
    await passwordInput.fill(process.env.BULENOX_PASSWORD);
    console.log('Filled username and password');
    // Press Enter in password field to submit form
    await passwordInput.press('Enter');
    console.log('Pressed Enter in password field');

    // --- STEP 2: Handle Time Sync Warning ---
    try {
      await waitForSelectorWithRetries(page, ['div:has-text("Time Sync Warning")', '.time-sync-warning', '#timeSyncModal'], 2, 2000);
      await page.click('button:has-text("OK"), button:has-text("Close"), button.close');
      console.log('Time Sync Warning handled.');
    } catch {}

    // --- STEP 3: Confirm dashboard ---
    await waitForSelectorWithRetries(page, ['div.dashboard-root', 'nav[role="navigation"]', '#dashboard']);
    console.log('Dashboard detected, login successful.');

    // --- STEP 4: Navigate to trading page ---
    if (!page.url().includes('/trade') && !page.url().includes('/trading')) {
      console.log('Navigating to trading page...');
      await page.goto('https://bulenox.projectx.com/trade', { waitUntil: 'networkidle' });
    }
    await waitForSelectorWithRetries(page, ['input[placeholder*="Symbol"]', '#trade-symbol']);
    console.log('Trading interface detected.');

    // --- STEP 5: Place order ---
    try {
      console.log('Attempting order placement using ORDER tab exact selectors...');
      await page.fill('#\\:r1b\\:', 'GOLD');
      await page.fill('#\\:r19\\:', '0.01');
      await page.click('#orderCardTab button:has-text("Buy")');
      console.log('Order placed using ORDER tab exact selectors.');
    } catch (orderTabError) {
      console.warn('ORDER tab exact selectors failed:', orderTabError);
      try {
        console.log('Attempting order placement using DOM tab exact selectors...');
        await page.fill('#\\:r19\\:', 'GOLD');
        await page.click('#domTab button:has-text("Buy")');
        console.log('Order placed using DOM tab exact selectors.');
      } catch (domTabError) {
        console.warn('DOM tab exact selectors failed:', domTabError);
        try {
          console.log('Attempting order placement using fallback generic selectors...');
          const symbolInput = await page.$('input[placeholder*="Symbol"], input[placeholder*="Market"], input[placeholder*="search"]');
          if (symbolInput) {
            await symbolInput.fill('GOLD');
            console.log('Filled symbol with generic selector');
          } else {
            console.warn('No symbol input found with generic selectors.');
          }
          const amountInput = await page.$('input[placeholder*="Amount"], input[placeholder*="Volume"], input[placeholder*="Size"], input[placeholder*="Lot"], input[type="number"]');
          if (amountInput) {
            await amountInput.fill('0.01');
            console.log('Filled amount with generic selector');
          } else {
            console.warn('No amount input found with generic selectors.');
          }
          const buyButton = await page.$('button:has-text("Buy"), button.buy, button[class*="buy"], button[class*="green"], button[class*="success"]');
          if (buyButton) {
            await buyButton.click();
            console.log('Clicked Buy button with generic selector');
          } else {
            console.warn('No Buy button found with generic selectors.');
          }
        } catch (genericError) {
          console.error('Fallback generic selectors also failed:', genericError);
          const screenshotPath = path.join(__dirname, 'order_placement_error.png');
          await page.screenshot({ path: screenshotPath });
          console.log(`Screenshot captured at ${screenshotPath}`);
        }
      }
    }

    // --- STEP 6: Wait to capture trade request ---
    console.log('Waiting up to 15 seconds to capture trade requests...');
    await page.waitForTimeout(15000);
    if (fs.existsSync('trade.sh')) {
      console.log('✅ Successfully captured cURL command to trade.sh');
      const curlContent = fs.readFileSync('trade.sh', 'utf8');
      console.log('trade.sh contents:', curlContent);
      if (curlContent.includes('-X POST')) {
        console.log('✅ Captured a POST request for trade execution.');
      } else {
        console.warn('⚠️ Captured request is not a POST request; may not be the actual trade execution.');
      }
    } else {
      console.warn('❌ Failed to capture cURL command to trade.sh');
    }
    console.log('Script completed. Check trade.sh and trade_request_full.py for the cURL and Python code.');
    await browser.close();
  } catch (mainError) {
    console.error('Fatal error in script execution:', mainError);
    try {
      if (browser) await browser.close();
    } catch (closeError) {
      console.error('Error closing browser:', closeError);
    }
  }
})();
