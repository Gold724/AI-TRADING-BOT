#!/usr/bin/env python3
"""
AI Trading Sentinel - VNC Browser Testing Script
Comprehensive Playwright browser testing for VNC environment
"""

import asyncio
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page
import json

# Configuration
PROJECT_DIR = Path.home() / "ai-trading-sentinel"
SCREENSHOT_DIR = PROJECT_DIR / "screenshots" / "vnc_tests"
TEST_RESULTS_FILE = PROJECT_DIR / "vnc_test_results.json"

# Ensure directories exist
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def show_notification(message: str, msg_type: str = "info"):
    """Show desktop notification and colored terminal output"""
    # Desktop notification
    try:
        subprocess.run([
            "notify-send", 
            "Trading Bot Browser Test", 
            message,
            "--icon=dialog-information"
        ], check=False, capture_output=True)
    except:
        pass
    
    # Terminal output with colors
    color_map = {
        "success": Colors.GREEN + "✅",
        "error": Colors.RED + "❌",
        "warning": Colors.YELLOW + "⚠️",
        "info": Colors.BLUE + "ℹ️",
        "progress": Colors.CYAN + "🔄"
    }
    
    icon = color_map.get(msg_type, Colors.BLUE + "📋")
    print(f"{icon} {message}{Colors.NC}")

class VNCBrowserTester:
    """Comprehensive browser testing for VNC environment"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": "VNC",
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        self.browser = None
        self.page = None
    
    def add_test_result(self, test_name: str, status: str, message: str, details: dict = None):
        """Add test result to results collection"""
        result = {
            "name": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.results["tests"].append(result)
        self.results["summary"]["total"] += 1
        
        if status == "passed":
            self.results["summary"]["passed"] += 1
            show_notification(f"✅ {test_name}: {message}", "success")
        elif status == "failed":
            self.results["summary"]["failed"] += 1
            show_notification(f"❌ {test_name}: {message}", "error")
        else:
            self.results["summary"]["warnings"] += 1
            show_notification(f"⚠️ {test_name}: {message}", "warning")
    
    async def test_environment_setup(self):
        """Test VNC environment setup"""
        show_notification("Testing VNC environment setup...", "progress")
        
        # Check DISPLAY variable
        display = os.environ.get('DISPLAY')
        if display:
            self.add_test_result(
                "Display Environment", 
                "passed", 
                f"DISPLAY set to {display}",
                {"display": display}
            )
        else:
            self.add_test_result(
                "Display Environment", 
                "failed", 
                "DISPLAY environment variable not set"
            )
            # Try to set it
            os.environ['DISPLAY'] = ':1'
            show_notification("Set DISPLAY=:1 as fallback", "warning")
        
        # Check if we can access X11
        try:
            result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.add_test_result(
                    "X11 Access", 
                    "passed", 
                    "X11 display accessible"
                )
            else:
                self.add_test_result(
                    "X11 Access", 
                    "warning", 
                    "X11 display may not be accessible"
                )
        except Exception as e:
            self.add_test_result(
                "X11 Access", 
                "warning", 
                f"Could not test X11 access: {str(e)}"
            )
    
    async def test_playwright_installation(self):
        """Test Playwright installation and browser availability"""
        show_notification("Testing Playwright installation...", "progress")
        
        try:
            # Test Playwright import
            from playwright.async_api import async_playwright
            self.add_test_result(
                "Playwright Import", 
                "passed", 
                "Playwright successfully imported"
            )
            
            # Check browser installations
            browsers = ['chromium', 'firefox', 'webkit']
            available_browsers = []
            
            async with async_playwright() as p:
                for browser_name in browsers:
                    try:
                        browser_type = getattr(p, browser_name)
                        # Try to get executable path
                        executable_path = browser_type.executable_path
                        if os.path.exists(executable_path):
                            available_browsers.append(browser_name)
                            self.add_test_result(
                                f"{browser_name.title()} Browser", 
                                "passed", 
                                f"Browser available at {executable_path}",
                                {"executable_path": executable_path}
                            )
                        else:
                            self.add_test_result(
                                f"{browser_name.title()} Browser", 
                                "failed", 
                                f"Browser executable not found at {executable_path}"
                            )
                    except Exception as e:
                        self.add_test_result(
                            f"{browser_name.title()} Browser", 
                            "failed", 
                            f"Browser not available: {str(e)}"
                        )
            
            if available_browsers:
                self.add_test_result(
                    "Browser Availability", 
                    "passed", 
                    f"Available browsers: {', '.join(available_browsers)}",
                    {"available_browsers": available_browsers}
                )
            else:
                self.add_test_result(
                    "Browser Availability", 
                    "failed", 
                    "No browsers available"
                )
                
        except ImportError as e:
            self.add_test_result(
                "Playwright Import", 
                "failed", 
                f"Failed to import Playwright: {str(e)}"
            )
    
    async def test_browser_launch(self, headless: bool = False):
        """Test browser launch in VNC environment"""
        mode = "headless" if headless else "headed"
        show_notification(f"Testing browser launch ({mode} mode)...", "progress")
        
        try:
            async with async_playwright() as p:
                # Test Chromium launch
                browser = await p.chromium.launch(
                    headless=headless,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                page = await browser.new_page()
                
                # Test basic page operations
                await page.goto('data:text/html,<h1>VNC Browser Test</h1><p>Browser launched successfully!</p>')
                title = await page.title()
                
                # Take screenshot
                screenshot_path = SCREENSHOT_DIR / f"browser_launch_{mode}_{int(time.time())}.png"
                await page.screenshot(path=str(screenshot_path))
                
                await browser.close()
                
                self.add_test_result(
                    f"Browser Launch ({mode})", 
                    "passed", 
                    f"Browser launched successfully, screenshot saved",
                    {
                        "mode": mode,
                        "title": title,
                        "screenshot": str(screenshot_path)
                    }
                )
                
        except Exception as e:
            self.add_test_result(
                f"Browser Launch ({mode})", 
                "failed", 
                f"Failed to launch browser: {str(e)}"
            )
    
    async def test_web_navigation(self):
        """Test web navigation and page interactions"""
        show_notification("Testing web navigation...", "progress")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # Use headed mode for VNC
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                
                # Test navigation to real website
                test_sites = [
                    {'url': 'https://httpbin.org/get', 'name': 'HTTPBin API'},
                    {'url': 'https://example.com', 'name': 'Example.com'},
                    {'url': 'https://google.com', 'name': 'Google'}
                ]
                
                successful_navigations = 0
                
                for site in test_sites:
                    try:
                        await page.goto(site['url'], timeout=15000)
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        
                        title = await page.title()
                        url = page.url
                        
                        # Take screenshot
                        screenshot_path = SCREENSHOT_DIR / f"navigation_{site['name'].lower().replace('.', '_')}_{int(time.time())}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        successful_navigations += 1
                        
                        self.add_test_result(
                            f"Navigation - {site['name']}", 
                            "passed", 
                            f"Successfully navigated to {site['name']}",
                            {
                                "url": url,
                                "title": title,
                                "screenshot": str(screenshot_path)
                            }
                        )
                        
                    except Exception as e:
                        self.add_test_result(
                            f"Navigation - {site['name']}", 
                            "failed", 
                            f"Failed to navigate to {site['name']}: {str(e)}"
                        )
                
                await browser.close()
                
                if successful_navigations > 0:
                    self.add_test_result(
                        "Web Navigation", 
                        "passed", 
                        f"Successfully navigated to {successful_navigations}/{len(test_sites)} sites"
                    )
                else:
                    self.add_test_result(
                        "Web Navigation", 
                        "failed", 
                        "Failed to navigate to any test sites"
                    )
                    
        except Exception as e:
            self.add_test_result(
                "Web Navigation", 
                "failed", 
                f"Navigation test failed: {str(e)}"
            )
    
    async def test_form_interactions(self):
        """Test form interactions and JavaScript execution"""
        show_notification("Testing form interactions...", "progress")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                
                # Create a test page with forms
                test_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>VNC Browser Test - Forms</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ccc; }
                        input, button { margin: 5px; padding: 8px; }
                        #result { background: #f0f0f0; padding: 10px; margin: 10px 0; }
                    </style>
                </head>
                <body>
                    <h1>VNC Browser Test - Form Interactions</h1>
                    
                    <div class="test-section">
                        <h3>Text Input Test</h3>
                        <input type="text" id="textInput" placeholder="Enter test text">
                        <button onclick="testText()">Test Text Input</button>
                    </div>
                    
                    <div class="test-section">
                        <h3>Click Test</h3>
                        <button id="clickButton" onclick="testClick()">Click Me!</button>
                        <span id="clickCount">Clicks: 0</span>
                    </div>
                    
                    <div class="test-section">
                        <h3>JavaScript Test</h3>
                        <button onclick="testJS()">Test JavaScript</button>
                    </div>
                    
                    <div id="result"></div>
                    
                    <script>
                        let clicks = 0;
                        
                        function testText() {
                            const input = document.getElementById('textInput');
                            const result = document.getElementById('result');
                            result.innerHTML = 'Text input value: ' + input.value;
                        }
                        
                        function testClick() {
                            clicks++;
                            document.getElementById('clickCount').textContent = 'Clicks: ' + clicks;
                            const result = document.getElementById('result');
                            result.innerHTML = 'Button clicked ' + clicks + ' times';
                        }
                        
                        function testJS() {
                            const result = document.getElementById('result');
                            const now = new Date();
                            result.innerHTML = 'JavaScript executed at: ' + now.toLocaleString();
                        }
                    </script>
                </body>
                </html>
                """
                
                await page.goto(f"data:text/html,{test_html}")
                
                # Test text input
                await page.fill('#textInput', 'VNC Test Input')
                await page.click('button:has-text("Test Text Input")')
                
                # Test button clicking
                for i in range(3):
                    await page.click('#clickButton')
                    await asyncio.sleep(0.5)
                
                # Test JavaScript execution
                await page.click('button:has-text("Test JavaScript")')
                
                # Verify results
                result_text = await page.text_content('#result')
                click_count = await page.text_content('#clickCount')
                
                # Take screenshot
                screenshot_path = SCREENSHOT_DIR / f"form_interactions_{int(time.time())}.png"
                await page.screenshot(path=str(screenshot_path))
                
                await browser.close()
                
                if 'VNC Test Input' in result_text or 'JavaScript executed' in result_text:
                    self.add_test_result(
                        "Form Interactions", 
                        "passed", 
                        "Form interactions working correctly",
                        {
                            "result_text": result_text,
                            "click_count": click_count,
                            "screenshot": str(screenshot_path)
                        }
                    )
                else:
                    self.add_test_result(
                        "Form Interactions", 
                        "warning", 
                        "Form interactions may not be working properly",
                        {"result_text": result_text}
                    )
                    
        except Exception as e:
            self.add_test_result(
                "Form Interactions", 
                "failed", 
                f"Form interaction test failed: {str(e)}"
            )
    
    async def test_trading_simulation(self):
        """Test trading-specific browser functionality"""
        show_notification("Testing trading simulation...", "progress")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                
                # Simulate a trading platform login page
                trading_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Mock Trading Platform</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; background: #1a1a1a; color: white; }
                        .login-form { max-width: 400px; margin: 50px auto; padding: 30px; background: #2a2a2a; border-radius: 8px; }
                        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #555; background: #333; color: white; border-radius: 4px; }
                        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                        button:hover { background: #0056b3; }
                        .trading-panel { display: none; margin-top: 20px; }
                        .price { font-size: 24px; font-weight: bold; color: #00ff00; }
                        .trade-buttons { margin: 20px 0; }
                        .buy-btn { background: #28a745; }
                        .sell-btn { background: #dc3545; }
                    </style>
                </head>
                <body>
                    <div class="login-form">
                        <h2>Mock Trading Platform</h2>
                        <div id="loginSection">
                            <input type="text" id="username" placeholder="Username" value="demo_user">
                            <input type="password" id="password" placeholder="Password" value="demo_pass">
                            <button onclick="login()">Login</button>
                        </div>
                        
                        <div id="tradingPanel" class="trading-panel">
                            <h3>Trading Dashboard</h3>
                            <div>EUR/USD: <span class="price" id="price">1.0850</span></div>
                            <div class="trade-buttons">
                                <button class="buy-btn" onclick="trade('BUY')">BUY</button>
                                <button class="sell-btn" onclick="trade('SELL')">SELL</button>
                            </div>
                            <div id="tradeResult"></div>
                        </div>
                    </div>
                    
                    <script>
                        function login() {
                            const username = document.getElementById('username').value;
                            const password = document.getElementById('password').value;
                            
                            if (username && password) {
                                document.getElementById('loginSection').style.display = 'none';
                                document.getElementById('tradingPanel').style.display = 'block';
                                
                                // Simulate price updates
                                setInterval(updatePrice, 2000);
                            }
                        }
                        
                        function updatePrice() {
                            const price = (1.0800 + Math.random() * 0.01).toFixed(4);
                            document.getElementById('price').textContent = price;
                        }
                        
                        function trade(action) {
                            const price = document.getElementById('price').textContent;
                            const result = document.getElementById('tradeResult');
                            const timestamp = new Date().toLocaleTimeString();
                            result.innerHTML = `${action} order executed at ${price} (${timestamp})`;
                        }
                    </script>
                </body>
                </html>
                """
                
                await page.goto(f"data:text/html,{trading_html}")
                
                # Test login simulation
                await page.fill('#username', 'vnc_test_user')
                await page.fill('#password', 'vnc_test_pass')
                await page.click('button:has-text("Login")')
                
                # Wait for trading panel to appear
                await page.wait_for_selector('#tradingPanel', state='visible', timeout=5000)
                
                # Test trading actions
                await asyncio.sleep(2)  # Wait for price updates
                await page.click('.buy-btn')
                await asyncio.sleep(1)
                await page.click('.sell-btn')
                
                # Verify trade results
                trade_result = await page.text_content('#tradeResult')
                
                # Take screenshot
                screenshot_path = SCREENSHOT_DIR / f"trading_simulation_{int(time.time())}.png"
                await page.screenshot(path=str(screenshot_path))
                
                await browser.close()
                
                if 'order executed' in trade_result:
                    self.add_test_result(
                        "Trading Simulation", 
                        "passed", 
                        "Trading simulation completed successfully",
                        {
                            "trade_result": trade_result,
                            "screenshot": str(screenshot_path)
                        }
                    )
                else:
                    self.add_test_result(
                        "Trading Simulation", 
                        "warning", 
                        "Trading simulation may not be working properly"
                    )
                    
        except Exception as e:
            self.add_test_result(
                "Trading Simulation", 
                "failed", 
                f"Trading simulation test failed: {str(e)}"
            )
    
    def save_results(self):
        """Save test results to file"""
        try:
            with open(TEST_RESULTS_FILE, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            show_notification(f"Test results saved to {TEST_RESULTS_FILE}", "success")
            
        except Exception as e:
            show_notification(f"Failed to save results: {str(e)}", "error")
    
    def display_summary(self):
        """Display test summary"""
        summary = self.results["summary"]
        
        print(f"\n{Colors.BLUE}{'='*50}{Colors.NC}")
        print(f"{Colors.BLUE}VNC Browser Test Summary{Colors.NC}")
        print(f"{Colors.BLUE}{'='*50}{Colors.NC}")
        
        print(f"Total Tests: {summary['total']}")
        print(f"{Colors.GREEN}Passed: {summary['passed']}{Colors.NC}")
        print(f"{Colors.RED}Failed: {summary['failed']}{Colors.NC}")
        print(f"{Colors.YELLOW}Warnings: {summary['warnings']}{Colors.NC}")
        
        success_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if summary['failed'] == 0:
            print(f"\n{Colors.GREEN}🎉 All critical tests passed! Browser is ready for trading.{Colors.NC}")
        elif summary['failed'] <= 2:
            print(f"\n{Colors.YELLOW}⚠️  Some tests failed, but browser should work for basic operations.{Colors.NC}")
        else:
            print(f"\n{Colors.RED}❌ Multiple test failures. Browser may not work properly.{Colors.NC}")
        
        print(f"\nScreenshots saved to: {SCREENSHOT_DIR}")
        print(f"Detailed results: {TEST_RESULTS_FILE}")
    
    async def run_all_tests(self):
        """Run all browser tests"""
        show_notification("Starting comprehensive VNC browser tests...", "progress")
        
        # Run all test suites
        await self.test_environment_setup()
        await self.test_playwright_installation()
        await self.test_browser_launch(headless=True)   # Test headless mode
        await self.test_browser_launch(headless=False)  # Test headed mode
        await self.test_web_navigation()
        await self.test_form_interactions()
        await self.test_trading_simulation()
        
        # Save and display results
        self.save_results()
        self.display_summary()
        
        # Show final notification
        summary = self.results["summary"]
        if summary['failed'] == 0:
            show_notification("🎉 All browser tests completed successfully!", "success")
        else:
            show_notification(f"⚠️ Browser tests completed with {summary['failed']} failures", "warning")

def main():
    """Main function"""
    print(f"{Colors.BLUE}🧪 AI Trading Sentinel - VNC Browser Testing{Colors.NC}")
    print(f"{Colors.BLUE}{'='*50}{Colors.NC}")
    
    # Check if we're in VNC environment
    if not os.environ.get('DISPLAY'):
        print(f"{Colors.YELLOW}⚠️  DISPLAY not set, setting to :1{Colors.NC}")
        os.environ['DISPLAY'] = ':1'
    
    # Create tester instance and run tests
    tester = VNCBrowserTester()
    
    try:
        asyncio.run(tester.run_all_tests())
    except KeyboardInterrupt:
        show_notification("Browser testing interrupted by user", "warning")
        sys.exit(1)
    except Exception as e:
        show_notification(f"Browser testing failed: {str(e)}", "error")
        sys.exit(1)

if __name__ == "__main__":
    main()