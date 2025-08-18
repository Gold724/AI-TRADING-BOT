#!/usr/bin/env python3
"""
Enhanced Bulenox Login Debugging Script
Comprehensive troubleshooting for login failures with network monitoring, form analysis, and anti-bot detection
"""

import os
import json
import asyncio
import random
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError, Request, Response

# Enhanced stealth import with better error handling
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
    print("✅ playwright-stealth available")
except ImportError:
    STEALTH_AVAILABLE = False
    print("⚠️ playwright-stealth NOT available - install with: pip install playwright-stealth")
    async def stealth_async(page: Page):
        return None

# Configuration from environment variables
USERNAME = os.getenv("BULENOX_USERNAME", "")
PASSWORD = os.getenv("BULENOX_PASSWORD", "")
HEADLESS = os.getenv("BULENOX_HEADLESS", "false").lower() == "true"  # Default to visible for debugging

# Enhanced debugging constants
DEBUG_MODE = True
VERBOSE_NETWORK = True
CAPTURE_REQUESTS = True
MAX_RETRIES = 2  # Reduced for faster debugging
STORAGE_FILE = "bulenox_debug_state.json"
SCREENSHOT_DIR = "debug_screenshots"
HTML_DIR = "debug_html"
NETWORK_LOG = "network_requests.json"

# Ensure directories exist
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

# Multi-domain configuration with debug info
DOMAIN_CONFIGS = [
    {
        "login_url": "https://bulenox.projectx.com/login",
        "trade_url": "https://bulenox.projectx.com/trade",
        "trading_url": "https://bulenox.projectx.com/trading",
        "name": "ProjectX Domain (Primary)",
        "expected_title": "Bulenox",
        "csrf_selectors": ["meta[name='csrf-token']", "input[name='_token']"]
    },
    {
        "login_url": "https://bulenox.projectx.com/login",
        "trade_url": "https://bulenox.projectx.com/trade",
        "trading_url": "https://bulenox.projectx.com/trading",
        "name": "Main Domain - Member Login",
        "expected_title": "Bulenox",
        "csrf_selectors": ["meta[name='csrf-token']", "input[name='_token']"]
    },
    {
        "login_url": "https://bulenox.projectx.com/login",
        "trade_url": "https://bulenox.projectx.com/trade",
        "trading_url": "https://bulenox.projectx.com/trading",
        "name": "Main Domain - Direct Login", 
        "expected_title": "Bulenox",
        "csrf_selectors": ["meta[name='csrf-token']", "input[name='_token']"]
    }
]

# Enhanced selectors with debugging info
USERNAME_SELECTORS = [
    {"selector": "input[name='userName']", "priority": 1, "description": "Exact userName field"},
    {"selector": "input[name='username']", "priority": 1, "description": "Standard username field"},
    {"selector": "input[name='email']", "priority": 2, "description": "Email field"},
    {"selector": "input[type='email']", "priority": 2, "description": "Email input type"},
    {"selector": "input[placeholder*='Email' i]", "priority": 3, "description": "Email placeholder"},
    {"selector": "input[placeholder*='Username' i]", "priority": 3, "description": "Username placeholder"},
    {"selector": "input[id*='email' i]", "priority": 4, "description": "Email ID"},
    {"selector": "input[id*='username' i]", "priority": 4, "description": "Username ID"},
    {"selector": "input[autocomplete='username']", "priority": 5, "description": "Username autocomplete"},
    {"selector": "input[autocomplete='email']", "priority": 5, "description": "Email autocomplete"}
]

PASSWORD_SELECTORS = [
    {"selector": "input[type='password']", "priority": 1, "description": "Password input type"},
    {"selector": "input[name='password']", "priority": 1, "description": "Password name field"},
    {"selector": "input[placeholder*='Password' i]", "priority": 2, "description": "Password placeholder"},
    {"selector": "input[id*='password' i]", "priority": 3, "description": "Password ID"},
    {"selector": "input[autocomplete='current-password']", "priority": 4, "description": "Current password autocomplete"}
]

LOGIN_BUTTON_SELECTORS = [
    {"selector": "button[type='submit']", "priority": 1, "description": "Submit button"},
    {"selector": "input[type='submit']", "priority": 1, "description": "Submit input"},
    {"selector": "button:has-text('Log in')", "priority": 2, "description": "Log in text"},
    {"selector": "button:has-text('Sign in')", "priority": 2, "description": "Sign in text"},
    {"selector": "button:has-text('Login')", "priority": 2, "description": "Login text"},
    {"selector": ".login-button", "priority": 3, "description": "Login button class"},
    {"selector": ".signin-button", "priority": 3, "description": "Signin button class"}
]

# Network request tracking
network_requests = []
login_requests = []

def log_debug(message: str, level: str = "INFO"):
    """Enhanced logging with timestamps and levels"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {message}")

async def capture_network_request(request: Request):
    """Capture and analyze network requests"""
    if CAPTURE_REQUESTS:
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "post_data": None
        }
        
        # Capture POST data for login requests
        if request.method == "POST":
            try:
                post_data = request.post_data
                if post_data:
                    request_data["post_data"] = post_data
                    
                # Check if this looks like a login request
                if any(keyword in request.url.lower() for keyword in ["login", "auth", "signin"]):
                    login_requests.append(request_data)
                    log_debug(f"🔍 LOGIN REQUEST: {request.method} {request.url}")
                    if VERBOSE_NETWORK:
                        log_debug(f"   Headers: {dict(request.headers)}")
                        if post_data:
                            log_debug(f"   POST Data: {post_data}")
                            
            except Exception as e:
                log_debug(f"Error capturing POST data: {e}", "ERROR")
        
        network_requests.append(request_data)
        
        if VERBOSE_NETWORK and request.method in ["POST", "GET"] and any(
            keyword in request.url.lower() for keyword in ["login", "auth", "api", "csrf"]
        ):
            log_debug(f"📡 {request.method} {request.url}")

async def capture_network_response(response: Response):
    """Capture and analyze network responses"""
    if CAPTURE_REQUESTS and response.request.method == "POST":
        try:
            # Check for login-related responses
            if any(keyword in response.url.lower() for keyword in ["login", "auth", "signin"]):
                log_debug(f"📥 LOGIN RESPONSE: {response.status} {response.url}")
                if VERBOSE_NETWORK:
                    try:
                        response_text = await response.text()
                        log_debug(f"   Response: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                    except:
                        log_debug("   Response: (binary or unable to read)")
                        
        except Exception as e:
            log_debug(f"Error capturing response: {e}", "ERROR")

async def analyze_page_content(page: Page, label: str):
    """Comprehensive page analysis for debugging"""
    log_debug(f"🔍 Analyzing page content: {label}")
    
    # Basic page info
    current_url = page.url
    title = await page.title()
    log_debug(f"   URL: {current_url}")
    log_debug(f"   Title: {title}")
    
    # Check for common anti-bot indicators
    anti_bot_indicators = [
        "cloudflare", "captcha", "recaptcha", "bot detection", 
        "access denied", "blocked", "security check"
    ]
    
    page_content = await page.content()
    for indicator in anti_bot_indicators:
        if indicator.lower() in page_content.lower():
            log_debug(f"⚠️ ANTI-BOT INDICATOR FOUND: {indicator}", "WARN")
    
    # Check for JavaScript errors
    try:
        js_errors = await page.evaluate("window.jsErrors || []")
        if js_errors:
            log_debug(f"❌ JavaScript Errors: {js_errors}", "ERROR")
    except:
        pass
    
    # Form analysis
    forms = await page.query_selector_all("form")
    log_debug(f"   Forms found: {len(forms)}")
    
    for i, form in enumerate(forms):
        try:
            action = await form.get_attribute("action")
            method = await form.get_attribute("method")
            log_debug(f"   Form {i}: action='{action}', method='{method}'")
        except:
            pass
    
    # Input field analysis
    inputs = await page.query_selector_all("input")
    log_debug(f"   Input fields found: {len(inputs)}")
    
    for input_elem in inputs[:10]:  # Limit to first 10 for brevity
        try:
            name = await input_elem.get_attribute("name")
            type_attr = await input_elem.get_attribute("type")
            placeholder = await input_elem.get_attribute("placeholder")
            log_debug(f"   Input: name='{name}', type='{type_attr}', placeholder='{placeholder}'")
        except:
            pass

async def find_element_with_debug(page: Page, selectors: list, element_name: str = "element"):
    """Enhanced element finding with detailed debugging"""
    log_debug(f"🔍 Searching for {element_name}")
    
    for selector_info in selectors:
        selector = selector_info["selector"]
        description = selector_info["description"]
        priority = selector_info["priority"]
        
        try:
            log_debug(f"   Trying selector (priority {priority}): {selector} - {description}")
            
            elements = await page.query_selector_all(selector)
            if elements:
                log_debug(f"   ✅ Found {len(elements)} element(s) with: {selector}")
                
                # Return the first visible element
                for element in elements:
                    if await element.is_visible():
                        log_debug(f"   ✅ Using visible element: {selector}")
                        return element
                
                # If no visible elements, return the first one
                log_debug(f"   ⚠️ No visible elements, using first: {selector}")
                return elements[0]
                
        except Exception as e:
            log_debug(f"   ❌ Error with selector {selector}: {e}")
            continue
    
    log_debug(f"   ❌ No {element_name} found with any selector", "ERROR")
    return None

async def check_csrf_token(page: Page, domain_config: dict):
    """Check for CSRF tokens that might be required"""
    log_debug("🔍 Checking for CSRF tokens")
    
    csrf_token = None
    for selector in domain_config.get("csrf_selectors", []):
        try:
            element = await page.query_selector(selector)
            if element:
                if selector.startswith("meta"):
                    csrf_token = await element.get_attribute("content")
                else:
                    csrf_token = await element.get_attribute("value")
                
                if csrf_token:
                    log_debug(f"   ✅ CSRF token found: {csrf_token[:20]}...")
                    break
        except:
            continue
    
    if not csrf_token:
        log_debug("   ⚠️ No CSRF token found", "WARN")
    
    return csrf_token

async def enhanced_login_attempt(page: Page, domain_config: dict, username: str, password: str) -> bool:
    """Enhanced login attempt with comprehensive debugging"""
    try:
        log_debug(f"🚀 Starting enhanced login attempt: {domain_config['name']}")
        
        # Navigate to login page
        log_debug(f"📍 Navigating to: {domain_config['login_url']}")
        await page.goto(domain_config['login_url'], wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        
        # Save initial page state
        await page.screenshot(path=f"{SCREENSHOT_DIR}/01_initial_page_{domain_config['name'].lower().replace(' ', '_')}.png")
        
        # Analyze page content
        await analyze_page_content(page, "Initial Page Load")
        
        # Check for CSRF token
        csrf_token = await check_csrf_token(page, domain_config)
        
        # Wait for login form
        log_debug("⏳ Waiting for login form elements")
        await asyncio.sleep(2)  # Give page time to fully load
        
        # Find username field
        username_field = await find_element_with_debug(page, USERNAME_SELECTORS, "username field")
        if not username_field:
            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_no_username_field_{domain_config['name'].lower().replace(' ', '_')}.png")
            return False
        
        # Find password field
        password_field = await find_element_with_debug(page, PASSWORD_SELECTORS, "password field")
        if not password_field:
            await page.screenshot(path=f"{SCREENSHOT_DIR}/03_no_password_field_{domain_config['name'].lower().replace(' ', '_')}.png")
            return False
        
        # Find login button
        login_button = await find_element_with_debug(page, LOGIN_BUTTON_SELECTORS, "login button")
        if not login_button:
            await page.screenshot(path=f"{SCREENSHOT_DIR}/04_no_login_button_{domain_config['name'].lower().replace(' ', '_')}.png")
            return False
        
        # Clear and fill username
        log_debug("📝 Filling username field")
        await username_field.click()
        await username_field.fill("")  # Clear first
        await asyncio.sleep(0.5)
        await username_field.type(username, delay=random.randint(50, 150))
        
        # Verify username was entered
        username_value = await username_field.input_value()
        log_debug(f"   Username entered: '{username_value}' (matches: {username_value == username})")
        
        # Clear and fill password
        log_debug("🔒 Filling password field")
        await password_field.click()
        await password_field.fill("")  # Clear first
        await asyncio.sleep(0.5)
        await password_field.type(password, delay=random.randint(50, 150))
        
        # Verify password was entered (length only for security)
        password_value = await password_field.input_value()
        log_debug(f"   Password entered: {len(password_value)} characters (matches: {len(password_value) == len(password)})")
        
        # Save form filled state
        await page.screenshot(path=f"{SCREENSHOT_DIR}/05_form_filled_{domain_config['name'].lower().replace(' ', '_')}.png")
        
        # Clear previous login requests
        login_requests.clear()
        
        # Click login button
        log_debug("🖱️ Clicking login button")
        await login_button.click()
        
        # Wait for network activity
        log_debug("⏳ Waiting for login response...")
        await asyncio.sleep(3)  # Give time for login request
        
        # Analyze login requests
        if login_requests:
            log_debug(f"📡 Captured {len(login_requests)} login request(s)")
            for req in login_requests:
                log_debug(f"   Request: {req['method']} {req['url']}")
                if req.get('post_data'):
                    log_debug(f"   POST Data: {req['post_data']}")
        else:
            log_debug("⚠️ No login requests captured - possible JavaScript issue", "WARN")
        
        # Save post-login state
        await page.screenshot(path=f"{SCREENSHOT_DIR}/06_post_login_{domain_config['name'].lower().replace(' ', '_')}.png")
        
        # Analyze post-login page
        await analyze_page_content(page, "Post-Login")
        
        # Check for error messages
        error_selectors = [
            ".error-message", ".alert-danger", ".login-error", ".error",
            "[class*='error' i]", "[class*='invalid' i]", 
            "text='Invalid'", "text='Error'", "text='Failed'",
            "text='incorrect'", "text='wrong'"
        ]
        
        for error_selector in error_selectors:
            try:
                error_elem = page.locator(error_selector).first
                if await error_elem.is_visible(timeout=1000):
                    error_text = await error_elem.text_content()
                    log_debug(f"❌ LOGIN ERROR DETECTED: {error_text}", "ERROR")
                    await page.screenshot(path=f"{SCREENSHOT_DIR}/07_login_error_{domain_config['name'].lower().replace(' ', '_')}.png")
                    return False
            except:
                continue
        
        # Check for success indicators
        current_url = page.url
        success_indicators = [
            "dashboard", "trade", "trading", "account", "profile", "welcome"
        ]
        
        url_success = any(indicator in current_url.lower() for indicator in success_indicators)
        if url_success:
            log_debug(f"✅ SUCCESS: URL changed to {current_url}", "SUCCESS")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/08_login_success_{domain_config['name'].lower().replace(' ', '_')}.png")
            return True
        
        # Check for dashboard elements
        dashboard_selectors = [
            "div.dashboard", "#main-dashboard", ".main-dashboard",
            "[data-testid='dashboard']", ".trading-dashboard",
            ".user-menu", ".account-info", "[href*='/trade']"
        ]
        
        for dashboard_selector in dashboard_selectors:
            try:
                dashboard_elem = await page.query_selector(dashboard_selector)
                if dashboard_elem and await dashboard_elem.is_visible():
                    log_debug(f"✅ SUCCESS: Dashboard element found: {dashboard_selector}", "SUCCESS")
                    await page.screenshot(path=f"{SCREENSHOT_DIR}/08_login_success_{domain_config['name'].lower().replace(' ', '_')}.png")
                    return True
            except:
                continue
        
        log_debug(f"❌ Login failed - no success indicators found. Current URL: {current_url}", "ERROR")
        return False
        
    except Exception as e:
        log_debug(f"❌ Login attempt failed with exception: {str(e)}", "ERROR")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/09_exception_{domain_config['name'].lower().replace(' ', '_')}.png")
        return False

async def main():
    """Enhanced main function with comprehensive debugging"""
    log_debug("🚀 Starting Enhanced Bulenox Login Debug Session", "INFO")
    
    # Validate environment variables
    if not USERNAME or not PASSWORD:
        log_debug("❌ Missing credentials! Set BULENOX_USERNAME and BULENOX_PASSWORD", "ERROR")
        return False
    
    log_debug(f"👤 Username: {USERNAME[:3]}***{USERNAME[-3:]}")
    log_debug(f"🔒 Password: {'*' * len(PASSWORD)} ({len(PASSWORD)} chars)")
    log_debug(f"🖥️ Headless mode: {HEADLESS}")
    log_debug(f"🛡️ Stealth available: {STEALTH_AVAILABLE}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=[
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Set up network monitoring
        page.on("request", capture_network_request)
        page.on("response", capture_network_response)
        
        # Apply stealth if available
        if STEALTH_AVAILABLE:
            await stealth_async(page)
            log_debug("🛡️ Stealth mode applied")
        
        # Try each domain
        for i, domain_config in enumerate(DOMAIN_CONFIGS):
            log_debug(f"🌐 Attempting domain {i+1}/{len(DOMAIN_CONFIGS)}: {domain_config['name']}")
            
            success = await enhanced_login_attempt(page, domain_config, USERNAME, PASSWORD)
            
            if success:
                log_debug(f"🎉 LOGIN SUCCESSFUL with {domain_config['name']}!", "SUCCESS")
                
                # Save network logs
                with open(NETWORK_LOG, 'w') as f:
                    json.dump({
                        "network_requests": network_requests,
                        "login_requests": login_requests,
                        "successful_domain": domain_config['name']
                    }, f, indent=2)
                
                await browser.close()
                return True
            else:
                log_debug(f"❌ Failed with {domain_config['name']}")
                
                # Small delay before trying next domain
                if i < len(DOMAIN_CONFIGS) - 1:
                    log_debug("⏳ Waiting 3 seconds before trying next domain...")
                    await asyncio.sleep(3)
        
        # Save network logs even on failure
        with open(NETWORK_LOG, 'w') as f:
            json.dump({
                "network_requests": network_requests,
                "login_requests": login_requests,
                "all_domains_failed": True
            }, f, indent=2)
        
        log_debug("💥 ALL DOMAINS FAILED", "ERROR")
        await browser.close()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'='*60}")
    print(f"DEBUG SESSION COMPLETE - {'SUCCESS' if success else 'FAILED'}")
    print(f"Check {SCREENSHOT_DIR}/ for screenshots")
    print(f"Check {NETWORK_LOG} for network requests")
    print(f"{'='*60}")
    exit(0 if success else 1)