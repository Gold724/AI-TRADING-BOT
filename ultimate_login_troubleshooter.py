#!/usr/bin/env python3
"""
TRAE AI Trading Sentinel - Ultimate Login Troubleshooter
=========================================================

This script provides comprehensive troubleshooting for Playwright login automation
issues with advanced debugging, network monitoring, and anti-bot detection.

Author: TradeBot Sentinel
Version: 1.0.0
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import base64
import hashlib

# Ensure required packages are available
def ensure_dependencies():
    """Ensure all required packages are installed"""
    packages = [
        ('playwright', 'playwright'),
        ('playwright_stealth', 'playwright-stealth')
    ]
    
    missing = []
    for import_name, pip_name in packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        print(f"🔧 Installing missing packages: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        print("✅ Packages installed successfully")

# Install dependencies if needed
try:
    ensure_dependencies()
except Exception as e:
    print(f"❌ Failed to install dependencies: {e}")
    sys.exit(1)

# Import playwright modules after ensuring they're installed
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Route

# Try to import stealth
STEALTH_AVAILABLE = False
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
    print("✅ Playwright stealth mode available")
except ImportError:
    print("⚠️  Playwright stealth not available, using manual stealth techniques")

# Configuration
DEBUG_DIR = Path("login_debug")
DEBUG_DIR.mkdir(exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DEBUG_DIR / "troubleshooter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colored_print(message: str, color: str = Colors.WHITE) -> None:
    """Print colored message to console"""
    print(f"{color}{message}{Colors.END}")

# Enhanced Domain Configurations
DOMAIN_CONFIGS = [
    {
        "name": "Primary Domain",
        "login_url": "https://bulenox.projectx.com/login",
        "dashboard_urls": ["https://bulenox.projectx.com/dashboard", "https://bulenox.projectx.com/trade"],
        "priority": 1
    },
    {
        "name": "Alt Domain 1", 
        "login_url": "https://app.bulenox.projectx.com/login",
        "dashboard_urls": ["https://app.bulenox.com/dashboard", "https://app.bulenox.com/trade"],
        "priority": 2
    },
    {
        "name": "Alt Domain 2",
        "login_url": "https://trade.bulenox.projectx.com/login", 
        "dashboard_urls": ["https://trade.bulenox.com/dashboard", "https://trade.bulenox.com/trade"],
        "priority": 3
    }
]

# Enhanced Selectors with AI-powered alternatives
SELECTORS = {
    "username": [
        # Standard email/username selectors
        'input[name="username"]',
        'input[name="email"]',
        'input[name="user"]',
        'input[type="email"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="username" i]',
        'input[placeholder*="user" i]',
        '#username',
        '#email',
        '#user',
        '.username input',
        '.email input',
        '.user input',
        # Generic fallbacks
        'input[type="text"]:first-of-type',
        'form input[type="text"]:first-child',
        'input:not([type="password"]):not([type="hidden"]):not([type="submit"]):first-of-type'
    ],
    "password": [
        # Standard password selectors
        'input[name="password"]',
        'input[type="password"]',
        '#password',
        '.password input',
        'input[placeholder*="password" i]',
        # Fallbacks
        'input[type="password"]:first-of-type',
        'form input[type="password"]'
    ],
    "login_button": [
        # Standard login button selectors
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Login")',
        'button:has-text("Sign In")',
        'button:has-text("Log In")',
        'button:has-text("Submit")',
        '[data-testid="login-button"]',
        '[data-cy="login-button"]',
        '.login-btn',
        '.btn-login',
        '#login-btn',
        '#loginButton',
        # Generic fallbacks
        'form button',
        'button[class*="login" i]',
        'button[class*="submit" i]',
        'input[value*="login" i]',
        'input[value*="sign" i]'
    ],
    "dashboard": [
        # Dashboard indicators
        '[data-testid="dashboard"]',
        '.dashboard',
        '#dashboard',
        '.main-content',
        '.user-dashboard',
        '[class*="dashboard" i]',
        # Trading interface indicators
        '.trading-interface',
        '[data-testid="trading"]',
        '.trade-panel',
        '.portfolio',
        # Navigation indicators
        '.navbar',
        '.sidebar',
        '.main-nav',
        # Profile/user indicators
        '.user-profile',
        '.account-info',
        '[data-testid="user-menu"]'
    ],
    "error_messages": [
        # Error message selectors
        '.error',
        '.alert-danger',
        '.message-error',
        '.login-error',
        '[class*="error" i]',
        '[role="alert"]',
        '.notification-error',
        '.toast-error',
        # Text-based error detection
        ':has-text("Invalid")',
        ':has-text("incorrect")',
        ':has-text("failed")',
        ':has-text("error")',
        ':has-text("wrong")'
    ]
}

class NetworkInterceptor:
    """Advanced network request/response interceptor"""
    
    def __init__(self):
        self.requests: List[Dict] = []
        self.responses: List[Dict] = []
        self.login_requests: List[Dict] = []
        
    async def intercept_request(self, route: Route) -> None:
        """Intercept and log all requests"""
        request = route.request
        
        # Log request details
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "post_data": None
        }
        
        # Capture POST data
        if request.method == "POST":
            try:
                post_data = request.post_data
                if post_data:
                    request_data["post_data"] = post_data
                    
                    # Check if this might be a login request
                    if any(keyword in post_data.lower() for keyword in 
                          ['username', 'email', 'password', 'login', 'signin']):
                        # Don't log actual credentials, but mark as login request
                        login_req = request_data.copy()
                        login_req["post_data"] = "[LOGIN_DATA_REDACTED]"
                        self.login_requests.append(login_req)
                        logger.info(f"🔐 Detected login request to: {request.url}")
            except Exception as e:
                logger.warning(f"Could not capture POST data: {e}")
        
        self.requests.append(request_data)
        
        # Continue with the request
        await route.continue_()
        
    async def intercept_response(self, response) -> None:
        """Intercept and log responses"""
        try:
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "url": response.url,
                "status": response.status,
                "headers": dict(response.headers),
                "ok": response.ok
            }
            self.responses.append(response_data)
            
            # Log failed responses
            if not response.ok:
                logger.warning(f"❌ Failed response: {response.status} - {response.url}")
                
        except Exception as e:
            logger.warning(f"Error intercepting response: {e}")
    
    def save_network_logs(self) -> None:
        """Save network logs to files"""
        try:
            # Save all requests
            with open(DEBUG_DIR / "network_requests.json", "w") as f:
                json.dump(self.requests, f, indent=2)
            
            # Save all responses  
            with open(DEBUG_DIR / "network_responses.json", "w") as f:
                json.dump(self.responses, f, indent=2)
                
            # Save login requests separately
            with open(DEBUG_DIR / "login_requests.json", "w") as f:
                json.dump(self.login_requests, f, indent=2)
                
            logger.info(f"📊 Network logs saved: {len(self.requests)} requests, {len(self.responses)} responses")
            
        except Exception as e:
            logger.error(f"Failed to save network logs: {e}")

class UltimateLoginTroubleshooter:
    """Ultimate login troubleshooter with comprehensive debugging"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.network_interceptor = NetworkInterceptor()
        self.screenshot_counter = 0
        
    async def setup_browser(self, headless: bool = False) -> None:
        """Setup browser with enhanced anti-detection"""
        colored_print("🚀 Setting up enhanced browser...", Colors.BLUE)
        
        playwright = await async_playwright().start()
        
        # Enhanced browser arguments for stealth
        browser_args = [
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor",
            "--disable-ipc-flooding-protection",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--disable-crash-reporter",
            "--disable-oopr-debug-crash-dump",
            "--no-crash-upload",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-low-res-tiling",
            "--log-level=3",
            "--silent",
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--no-sandbox",
            "--ignore-certificate-errors-spki-list",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors-list=*",
            "--ignore-ssl-errors"
        ]
        
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # Setup network interception
        await self.context.route("**/*", self.network_interceptor.intercept_request)
        self.context.on("response", self.network_interceptor.intercept_response)
        
        self.page = await self.context.new_page()
        
        # Apply stealth techniques
        await self.apply_stealth_techniques()
        
        colored_print("✅ Browser setup complete with enhanced stealth", Colors.GREEN)
    
    async def apply_stealth_techniques(self) -> None:
        """Apply comprehensive stealth techniques"""
        colored_print("🥷 Applying stealth techniques...", Colors.MAGENTA)
        
        # Apply playwright-stealth if available
        if STEALTH_AVAILABLE:
            try:
                await stealth_async(self.page)
                colored_print("✅ Playwright-stealth applied", Colors.GREEN)
            except Exception as e:
                logger.warning(f"Failed to apply playwright-stealth: {e}")
        
        # Manual stealth techniques
        await self.page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Override chrome property
            window.chrome = {
                runtime: {}
            };
            
            // Mock headless detection
            Object.defineProperty(window, 'outerHeight', {
                get: () => window.innerHeight,
            });
            
            Object.defineProperty(window, 'outerWidth', {
                get: () => window.innerWidth,
            });
        """)
        
        colored_print("✅ Manual stealth techniques applied", Colors.GREEN)
    
    async def take_screenshot(self, name: str) -> str:
        """Take screenshot with timestamp"""
        self.screenshot_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{self.screenshot_counter:02d}_{timestamp}_{name}.png"
        filepath = DEBUG_DIR / filename
        
        try:
            await self.page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"📸 Screenshot saved: {filename}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ""
    
    async def save_html_source(self, name: str) -> str:
        """Save HTML source with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"html_{timestamp}_{name}.html"
        filepath = DEBUG_DIR / filename
        
        try:
            content = await self.page.content()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"📄 HTML source saved: {filename}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save HTML source: {e}")
            return ""
    
    async def analyze_page_elements(self) -> Dict[str, Any]:
        """Analyze page elements for debugging"""
        colored_print("🔍 Analyzing page elements...", Colors.BLUE)
        
        analysis = {
            "title": await self.page.title(),
            "url": self.page.url,
            "input_fields": [],
            "buttons": [],
            "forms": [],
            "error_indicators": []
        }
        
        try:
            # Find all input fields
            inputs = await self.page.query_selector_all("input")
            for input_elem in inputs:
                input_info = {
                    "type": await input_elem.get_attribute("type") or "text",
                    "name": await input_elem.get_attribute("name") or "",
                    "id": await input_elem.get_attribute("id") or "",
                    "placeholder": await input_elem.get_attribute("placeholder") or "",
                    "class": await input_elem.get_attribute("class") or ""
                }
                analysis["input_fields"].append(input_info)
            
            # Find all buttons
            buttons = await self.page.query_selector_all("button, input[type='submit']")
            for button in buttons:
                button_info = {
                    "type": await button.get_attribute("type") or "",
                    "text": await button.inner_text() or "",
                    "class": await button.get_attribute("class") or "",
                    "id": await button.get_attribute("id") or ""
                }
                analysis["buttons"].append(button_info)
            
            # Find forms
            forms = await self.page.query_selector_all("form")
            for form in forms:
                form_info = {
                    "action": await form.get_attribute("action") or "",
                    "method": await form.get_attribute("method") or "GET",
                    "class": await form.get_attribute("class") or ""
                }
                analysis["forms"].append(form_info)
            
            # Check for error indicators
            for selector in SELECTORS["error_messages"]:
                try:
                    error_elem = await self.page.query_selector(selector)
                    if error_elem:
                        error_text = await error_elem.inner_text()
                        if error_text.strip():
                            analysis["error_indicators"].append({
                                "selector": selector,
                                "text": error_text.strip()
                            })
                except:
                    continue
            
            # Save analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(DEBUG_DIR / f"page_analysis_{timestamp}.json", "w") as f:
                json.dump(analysis, f, indent=2)
            
            colored_print(f"✅ Page analysis complete: {len(analysis['input_fields'])} inputs, {len(analysis['buttons'])} buttons", Colors.GREEN)
            
        except Exception as e:
            logger.error(f"Failed to analyze page elements: {e}")
        
        return analysis
    
    async def human_like_type(self, element, text: str) -> None:
        """Type text with human-like timing"""
        await element.click()
        await element.clear()
        await asyncio.sleep(0.2)
        
        for char in text:
            await element.type(char)
            await asyncio.sleep(0.05 + (0.05 * (hash(char) % 10) / 10))
    
    async def find_best_selector(self, selector_list: List[str], element_type: str) -> Optional[str]:
        """Find the best working selector from a list"""
        colored_print(f"🎯 Finding best selector for {element_type}...", Colors.BLUE)
        
        for selector in selector_list:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    # Check if element is visible and enabled
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        colored_print(f"✅ Found working selector for {element_type}: {selector}", Colors.GREEN)
                        return selector
                    else:
                        logger.debug(f"Selector found but element not usable: {selector} (visible: {is_visible}, enabled: {is_enabled})")
            except Exception as e:
                logger.debug(f"Selector failed: {selector} - {e}")
                continue
        
        colored_print(f"❌ No working selector found for {element_type}", Colors.RED)
        return None
    
    async def attempt_login_with_domain(self, domain_config: Dict[str, Any], username: str, password: str) -> bool:
        """Attempt login with comprehensive debugging"""
        domain_name = domain_config["name"]
        login_url = domain_config["login_url"]
        
        colored_print(f"🌐 Attempting login with {domain_name}: {login_url}", Colors.CYAN)
        
        try:
            # Navigate to login page
            colored_print("📍 Navigating to login page...", Colors.BLUE)
            await self.page.goto(login_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Take initial screenshot
            await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_initial")
            await self.save_html_source(f"{domain_name.lower().replace(' ', '_')}_initial")
            
            # Analyze page elements
            page_analysis = await self.analyze_page_elements()
            
            # Handle common modals/overlays
            await self.handle_common_modals()
            
            # Check if already logged in
            dashboard_element = await self.check_dashboard_presence()
            if dashboard_element:
                colored_print("✅ Already logged in!", Colors.GREEN)
                return True
            
            # Find and fill username
            colored_print("👤 Looking for username field...", Colors.BLUE)
            username_selector = await self.find_best_selector(SELECTORS["username"], "username")
            if not username_selector:
                colored_print("❌ Could not find username field", Colors.RED)
                await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_no_username_field")
                return False
            
            username_element = await self.page.query_selector(username_selector)
            colored_print(f"✅ Found username field with selector: {username_selector}", Colors.GREEN)
            
            # Fill username
            colored_print("📝 Filling username...", Colors.BLUE)
            await self.human_like_type(username_element, username)
            await asyncio.sleep(1)
            
            # Verify username was filled
            filled_username = await username_element.input_value()
            if filled_username != username:
                colored_print(f"⚠️  Username verification failed: expected '{username}', got '{filled_username}'", Colors.YELLOW)
            else:
                colored_print("✅ Username filled successfully", Colors.GREEN)
            
            # Find and fill password
            colored_print("🔒 Looking for password field...", Colors.BLUE)
            password_selector = await self.find_best_selector(SELECTORS["password"], "password")
            if not password_selector:
                colored_print("❌ Could not find password field", Colors.RED)
                await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_no_password_field")
                return False
            
            password_element = await self.page.query_selector(password_selector)
            colored_print(f"✅ Found password field with selector: {password_selector}", Colors.GREEN)
            
            # Fill password
            colored_print("📝 Filling password...", Colors.BLUE)
            await self.human_like_type(password_element, password)
            await asyncio.sleep(1)
            
            # Take screenshot before login attempt
            await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_before_login")
            
            # Find and click login button
            colored_print("🔘 Looking for login button...", Colors.BLUE)
            login_button_selector = await self.find_best_selector(SELECTORS["login_button"], "login button")
            if not login_button_selector:
                colored_print("❌ Could not find login button", Colors.RED)
                await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_no_login_button")
                return False
            
            login_button = await self.page.query_selector(login_button_selector)
            colored_print(f"✅ Found login button with selector: {login_button_selector}", Colors.GREEN)
            
            # Click login button
            colored_print("🚀 Clicking login button...", Colors.BLUE)
            await login_button.click()
            
            # Wait for navigation or error messages
            colored_print("⏳ Waiting for login response...", Colors.BLUE)
            await asyncio.sleep(3)
            
            # Take screenshot after login attempt
            await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_after_login")
            await self.save_html_source(f"{domain_name.lower().replace(' ', '_')}_after_login")
            
            # Check for error messages
            error_found = await self.check_for_errors()
            if error_found:
                colored_print(f"❌ Login failed with errors", Colors.RED)
                return False
            
            # Check for successful login (dashboard presence)
            dashboard_element = await self.check_dashboard_presence()
            if dashboard_element:
                colored_print("🎉 Login successful!", Colors.GREEN)
                await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_success")
                return True
            
            # Check if URL changed (might indicate success)
            current_url = self.page.url
            if current_url != login_url and any(dash_url in current_url for dash_url in domain_config["dashboard_urls"]):
                colored_print("🎉 Login successful (URL changed to dashboard)!", Colors.GREEN)
                await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_success_url_change")
                return True
            
            colored_print("❌ Login failed - no success indicators found", Colors.RED)
            return False
            
        except Exception as e:
            colored_print(f"❌ Exception during login attempt: {e}", Colors.RED)
            logger.error(f"Login attempt failed: {traceback.format_exc()}")
            await self.take_screenshot(f"{domain_name.lower().replace(' ', '_')}_exception")
            return False
    
    async def handle_common_modals(self) -> None:
        """Handle common modals and overlays"""
        colored_print("🔍 Checking for modals/overlays...", Colors.BLUE)
        
        modal_selectors = [
            # Cookie banners
            '[class*="cookie" i]',
            '.cookie-banner',
            '#cookie-banner',
            # Generic modals
            '.modal',
            '.popup',
            '.overlay',
            '[role="dialog"]',
            # Time sync warnings
            '.time-sync-warning',
            '.sync-warning',
            '[class*="warning" i]'
        ]
        
        for selector in modal_selectors:
            try:
                modal = await self.page.query_selector(selector)
                if modal and await modal.is_visible():
                    # Try to find close button
                    close_selectors = [
                        f'{selector} button:has-text("Close")',
                        f'{selector} button:has-text("Accept")',
                        f'{selector} button:has-text("OK")',
                        f'{selector} .close',
                        f'{selector} [aria-label="Close"]'
                    ]
                    
                    for close_selector in close_selectors:
                        try:
                            close_btn = await self.page.query_selector(close_selector)
                            if close_btn and await close_btn.is_visible():
                                await close_btn.click()
                                colored_print(f"✅ Closed modal with selector: {close_selector}", Colors.GREEN)
                                await asyncio.sleep(1)
                                break
                        except:
                            continue
            except:
                continue
    
    async def check_dashboard_presence(self) -> bool:
        """Check if dashboard elements are present"""
        colored_print("🏠 Checking for dashboard presence...", Colors.BLUE)
        
        for selector in SELECTORS["dashboard"]:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    colored_print(f"✅ Dashboard detected with selector: {selector}", Colors.GREEN)
                    return True
            except:
                continue
        
        return False
    
    async def check_for_errors(self) -> bool:
        """Check for error messages"""
        colored_print("🔍 Checking for error messages...", Colors.BLUE)
        
        errors_found = []
        
        for selector in SELECTORS["error_messages"]:
            try:
                error_element = await self.page.query_selector(selector)
                if error_element and await error_element.is_visible():
                    error_text = await error_element.inner_text()
                    if error_text.strip():
                        errors_found.append({
                            "selector": selector,
                            "text": error_text.strip()
                        })
            except:
                continue
        
        if errors_found:
            colored_print(f"❌ Found {len(errors_found)} error(s):", Colors.RED)
            for error in errors_found:
                colored_print(f"   • {error['text']}", Colors.RED)
            
            # Save errors to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(DEBUG_DIR / f"errors_{timestamp}.json", "w") as f:
                json.dump(errors_found, f, indent=2)
            
            return True
        
        return False
    
    async def run_ultimate_troubleshooter(self) -> bool:
        """Run the ultimate login troubleshooter"""
        colored_print("🎯 Starting Ultimate Login Troubleshooter", Colors.BOLD + Colors.CYAN)
        colored_print("=" * 70, Colors.CYAN)
        
        # Get credentials
        username = os.getenv("BULENOX_USERNAME")
        password = os.getenv("BULENOX_PASSWORD")
        headless = os.getenv("BULENOX_HEADLESS", "false").lower() == "true"
        
        if not username or not password:
            colored_print("❌ Missing credentials! Set BULENOX_USERNAME and BULENOX_PASSWORD environment variables", Colors.RED)
            return False
        
        colored_print(f"🔑 Using credentials: {username[:3]}***@{username.split('@')[1] if '@' in username else '***'}", Colors.BLUE)
        colored_print(f"🖥️  Headless mode: {headless}", Colors.BLUE)
        
        try:
            # Setup browser
            await self.setup_browser(headless=headless)
            
            # Try each domain
            for domain_config in sorted(DOMAIN_CONFIGS, key=lambda x: x["priority"]):
                colored_print(f"\n{'='*50}", Colors.CYAN)
                colored_print(f"Trying {domain_config['name']}", Colors.CYAN)
                colored_print(f"{'='*50}", Colors.CYAN)
                
                success = await self.attempt_login_with_domain(domain_config, username, password)
                
                if success:
                    colored_print(f"\n🎉 SUCCESS! Login successful with {domain_config['name']}", Colors.BOLD + Colors.GREEN)
                    
                    # Save successful configuration
                    success_config = {
                        "timestamp": datetime.now().isoformat(),
                        "successful_domain": domain_config,
                        "login_url": domain_config["login_url"],
                        "final_url": self.page.url
                    }
                    
                    with open(DEBUG_DIR / "successful_login_config.json", "w") as f:
                        json.dump(success_config, f, indent=2)
                    
                    # Save network logs
                    self.network_interceptor.save_network_logs()
                    
                    return True
                else:
                    colored_print(f"❌ Failed with {domain_config['name']}", Colors.RED)
                    await asyncio.sleep(2)  # Brief pause between attempts
            
            colored_print("\n❌ All login attempts failed", Colors.RED)
            return False
            
        except Exception as e:
            colored_print(f"❌ Critical error: {e}", Colors.RED)
            logger.error(f"Critical error: {traceback.format_exc()}")
            return False
        
        finally:
            # Save network logs regardless of outcome
            self.network_interceptor.save_network_logs()
            
            # Cleanup
            if self.browser:
                await self.browser.close()
    
    async def generate_troubleshooting_report(self) -> None:
        """Generate comprehensive troubleshooting report"""
        colored_print("📊 Generating troubleshooting report...", Colors.BLUE)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "browser_info": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "stealth_available": STEALTH_AVAILABLE
            },
            "domains_tested": DOMAIN_CONFIGS,
            "selectors_used": SELECTORS,
            "debug_files": []
        }
        
        # List all debug files
        for file_path in DEBUG_DIR.glob("*"):
            if file_path.is_file():
                report["debug_files"].append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        # Save report
        with open(DEBUG_DIR / "troubleshooting_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        colored_print("✅ Troubleshooting report saved", Colors.GREEN)

async def main():
    """Main execution function"""
    print("\n" + "="*70)
    colored_print("🤖 TRAE AI Trading Sentinel - Ultimate Login Troubleshooter", Colors.BOLD + Colors.CYAN)
    colored_print("Version 1.0.0 - Advanced Playwright Debugging", Colors.CYAN)
    print("="*70 + "\n")
    
    troubleshooter = UltimateLoginTroubleshooter()
    
    try:
        success = await troubleshooter.run_ultimate_troubleshooter()
        
        # Generate report regardless of outcome
        await troubleshooter.generate_troubleshooting_report()
        
        print("\n" + "="*70)
        if success:
            colored_print("🎉 ULTIMATE TROUBLESHOOTER COMPLETED SUCCESSFULLY!", Colors.BOLD + Colors.GREEN)
            colored_print("✅ Login automation should now work properly", Colors.GREEN)
        else:
            colored_print("❌ TROUBLESHOOTING COMPLETED WITH ISSUES", Colors.BOLD + Colors.RED)
            colored_print("🔍 Check debug files for detailed analysis:", Colors.YELLOW)
            colored_print(f"   Debug Directory: {DEBUG_DIR.absolute()}", Colors.WHITE)
            
            # List key debug files
            key_files = [
                "troubleshooting_report.json",
                "network_requests.json", 
                "login_requests.json",
                "successful_login_config.json"
            ]
            
            for filename in key_files:
                filepath = DEBUG_DIR / filename
                if filepath.exists():
                    colored_print(f"   📄 {filename}", Colors.WHITE)
        
        print("="*70)
        
        return success
        
    except KeyboardInterrupt:
        colored_print("\n⚠️  Interrupted by user", Colors.YELLOW)
        return False
    except Exception as e:
        colored_print(f"\n❌ Fatal error: {e}", Colors.RED)
        logger.error(f"Fatal error: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)