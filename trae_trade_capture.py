#!/usr/bin/env python3
"""
TradeBot Sentinel - Bulenox Trading Platform Automation
Expert automation agent specialized in interacting with Bulenox ProjectX's trading platform via Playwright.

Features:
- Secure login using environment variables with robust fallback selectors
- Time Sync Warning modal detection and handling
- Trading interface detection with retries and delays
- Network request interception for trade execution capture
- cURL command generation and Python conversion
- Screenshot capture on critical failures
- Verbose console logging for traceability
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os
import sys
import json
from datetime import datetime

# Configure verbose logging
def log(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    stream = sys.stderr if str(level).upper() in ("ERROR", "WARN") else sys.stdout
    print(f"[{timestamp}] [{level}] {message}", file=stream, flush=True)

def log_info(message):
    log("INFO", message)

def log_warn(message):
    log("WARN", message)

def log_error(message):
    log("ERROR", message)

def log_debug(message):
    log("DEBUG", message)

def log_success(message):
    log("SUCCESS", message)

# Helper utilities with retries
async def wait_for_any(page, selectors, timeout=5000, retries=3, delay_sec=2):
    """Wait for any of the provided selectors with retry logic"""
    last_err = None
    for attempt in range(1, retries + 1):
        for sel in selectors:
            try:
                log_debug(f"Attempt {attempt}/{retries}: waiting for selector -> {sel}")
                el = await page.wait_for_selector(sel, timeout=timeout, state="visible")
                log_success(f"Found selector: {sel}")
                return el
            except Exception as e:
                last_err = e
        if attempt < retries:
            log_warn(f"Retry in {delay_sec}s...")
            await asyncio.sleep(delay_sec)
    raise last_err or Exception("None of the selectors appeared")

async def take_screenshot(page, name):
    try:
        path = f"{name}.png"
        await page.screenshot(path=path, full_page=True)
        log_info(f"Screenshot saved: {path}")
    except Exception as e:
        log_warn(f"Failed to take screenshot {name}: {e}")

async def safe_click(page, selectors, retries=3, delay_sec=2):
    if isinstance(selectors, str):
        selectors = [selectors]
    last_err = None
    for attempt in range(1, retries + 1):
        for sel in selectors:
            try:
                log_debug(f"Attempt {attempt}/{retries}: clicking -> {sel}")
                await page.click(sel, timeout=7000)
                log_success(f"Clicked: {sel}")
                return True
            except Exception as e:
                log_warn(f"Failed for {sel}: {e}")
                last_err = e
        if attempt < retries:
            log_warn(f"Retry in {delay_sec}s...")
            await asyncio.sleep(delay_sec)
    raise last_err or Exception("Failed to click any selector")

async def safe_click_cross(page, selectors, retries=3, delay_sec=2):
    if isinstance(selectors, str):
        selectors = [selectors]
    targets = [page] + page.frames
    last_err = None
    for attempt in range(1, retries + 1):
        for target in targets:
            for sel in selectors:
                try:
                    log_debug(f"Attempt {attempt}/{retries}: clicking -> {sel} on {'main' if target is page else 'frame'}")
                    await target.click(sel, timeout=7000)
                    log_success(f"Clicked: {sel}")
                    return target, sel
                except Exception as e:
                    last_err = e
                    continue
        if attempt < retries:
            log_warn(f"Retry in {delay_sec}s...")
            await asyncio.sleep(delay_sec)
    raise last_err or Exception("Failed to click any selector across frames")

async def safe_fill(page, selector, value, retries=3, delay_sec=2):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            log_debug(f"Attempt {attempt}/{retries}: {selector} = {value}")
            await page.fill(selector, value, timeout=7000)
            log_success(f"Filled: {selector}")
            return True
        except Exception as e:
            log_warn(f"Failed for {selector}: {e}")
            last_err = e
            await asyncio.sleep(delay_sec)
    raise last_err or Exception(f"Failed to fill {selector}")

async def safe_fill_any(page, selectors, value, retries=3, delay_sec=2):
    if isinstance(selectors, str):
        selectors = [selectors]
    last_err = None
    for attempt in range(1, retries + 1):
        for sel in selectors:
            try:
                log_debug(f"Attempt {attempt}/{retries}: try fill {sel} = {value}")
                await page.fill(sel, value, timeout=7000)
                log_success(f"Filled: {sel}")
                return sel
            except Exception as e:
                log_warn(f"Failed fill for {sel}: {e}")
                last_err = e
        if attempt < retries:
            log_warn(f"Retry in {delay_sec}s...")
            await asyncio.sleep(delay_sec)
    raise last_err or Exception("Failed to fill any selector")

async def safe_type_any_cross(page, selectors, value, typing_delay_ms=50, retries=3, delay_sec=2):
    if isinstance(selectors, str):
        selectors = [selectors]
    targets = [page] + page.frames
    last_err = None
    for attempt in range(1, retries + 1):
        for target in targets:
            for sel in selectors:
                try:
                    log_debug(f"Attempt {attempt}/{retries}: type into {sel} -> {value}")
                    await target.click(sel, timeout=7000)
                    await target.fill(sel, "", timeout=7000)
                    await target.type(sel, value, delay=typing_delay_ms)
                    log_success(f"Typed into: {sel}")
                    return target, sel
                except Exception as e:
                    last_err = e
                    continue
        if attempt < retries:
            log_warn(f"Retry in {delay_sec}s...")
            await asyncio.sleep(delay_sec)
    raise last_err or Exception("Failed to type into any selector across frames")

async def submit_enclosing_form(target, field_selector):
    try:
        js = """
        (sel) => {
            const el = document.querySelector(sel);
            if (!el) return false;
            const form = el.closest('form');
            if (form && typeof form.requestSubmit === 'function') {
                form.requestSubmit();
                return true;
            }
            if (form) {
                form.submit();
                return true;
            }
            return false;
        }
        """
        ok = await target.evaluate(js, field_selector)
        log_info(f"Form submit via DOM {'succeeded' if ok else 'not available'} for {field_selector}")
        return ok
    except Exception as e:
        log_warn(f"Form submit via DOM failed: {e}")
        return False

async def dismiss_cookie_banner(page):
    selectors = [
        'button:has-text("Accept")', 'button:has-text("I Accept")', 'button:has-text("I Agree")',
        'button:has-text("Agree")', 'button:has-text("Accept All")', 'button:has-text("Allow all")',
        '[aria-label*="accept"]', '[id*="accept"]', '[class*="cookie"] button'
    ]
    try:
        await safe_click_cross(page, selectors, retries=1, delay_sec=1)
        log_info("Cookie banner dismissed")
        return True
    except Exception:
        return False

async def dismiss_time_sync_modal(page):
    try:
        modal_texts = [
            "time sync", "time-syn", "time synchronization", "sync your time",
            "clock", "time is not synchronized", "time is out",
        ]
        buttons = [
            'button:has-text("I Understand")',
            'button:has-text("Continue")',
            'button:has-text("OK")',
            'button:has-text("Ok")',
            'button:has-text("Dismiss")',
            'button[aria-label="Close"]',
            'button:has(svg[aria-label="Close"])',
        ]
        for t in modal_texts:
            try:
                el = await page.wait_for_selector(f'text=/{t}/i', timeout=1500)
                if el:
                    log_info(f"Detected possible Time Sync modal with text pattern: {t}")
                    for b in buttons:
                        try:
                            await page.click(b, timeout=1000)
                            log_info(f"Clicked dismiss button: {b}")
                            await asyncio.sleep(0.5)
                            return True
                        except Exception:
                            continue
            except Exception:
                continue
        return False
    except Exception as e:
        log_warn(f"No Time Sync modal handled or error occurred: {e}")
        return False

async def find_trading_interface(page_or_frame):
    """Enhanced trading interface detection with exact selectors from the screenshot"""
    try:
        frame_url = getattr(page_or_frame, 'url', 'frame')
    except Exception:
        frame_url = 'frame'
    log_info(f"Searching for trading interface on: {frame_url}")
    
    # Based on the screenshot, look for these specific trading interface indicators
    trading_indicators = [
        # Exact selectors from the Node.js working version and screenshot analysis
        '#\\:r1b\\:',  # Symbol input field
        '#\\:r19\\:',  # Amount/quantity input field
        '#orderCardTab',  # Order tab
        '#domTab',  # DOM tab
        'button:has-text("BUY MARKET")',
        'button:has-text("SELL MARKET")',
        # Generic fallbacks based on visual inspection
        'input[placeholder*="Symbol"]',
        'input[placeholder*="search"]',
        'input[placeholder*="Market"]',
        'input[placeholder*="Qty"]',
        'input[placeholder*="Amount"]',
        'button[class*="buy"]',
        'button[class*="sell"]',
        'div[class*="trading"]',
        'div[class*="order"]',
        '[role="tablist"]',
        'text=Order',
        'text=Chart',
        'text=DOM',
        # Additional indicators
        'text=Position',
        'text=Positions',
        'text=Portfolio',
        'div[id*="order"]',
        'div[id*="trade"]',
        'div[class*="book"]',
        'div[class*="dom"]',
        'button:has-text("Buy")',
        'button:has-text("Sell")'
    ]
    
    for indicator in trading_indicators:
        try:
            await page_or_frame.wait_for_selector(indicator, timeout=2000, state="visible")
            log_success(f"Trading interface detected with: {indicator}")
            return page_or_frame
        except Exception:
            continue
    
    log_warn("No trading interface indicators found")
    return None

async def navigate_to_trade_interface(page):
    """Navigate to trade interface and find the correct frame"""
    log_info("Ensuring we're on the trade page...")
    
    # If not already on trade page, navigate there
    if "/trade" not in page.url:
        await page.goto("https://bulenox.projectx.com/trade", wait_until="networkidle")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
    
    # Wait for page to fully load
    await asyncio.sleep(3)
    
    # First, try main page
    trading_page = await find_trading_interface(page)
    if trading_page:
        return trading_page
    
    # Then try all iframes
    log_info("Checking all iframes for trading interface...")
    try:
        # wait a bit in case iframes are lazy-loaded
        await page.wait_for_timeout(1500)
        frames = page.frames
        log_info(f"Found {len(frames)} frames total")
        
        for i, frame in enumerate(frames):
            try:
                frame_url = frame.url
                log_debug(f"Checking frame {i}: {frame_url}")
                trading_frame = await find_trading_interface(frame)
                if trading_frame:
                    log_success(f"Trading interface found in frame {i}")
                    return trading_frame
            except Exception as e:
                log_warn(f"Error checking frame {i}: {e}")
                continue
                
    except Exception as e:
        log_warn(f"No iframes found or error: {e}")
    
    # Dump HTML on failure for diagnostics
    try:
        html = await page.content()
        with open("trade_interface_dump.html", "w", encoding="utf-8") as f:
            f.write(html)
        log_info("Page HTML saved to trade_interface_dump.html")
    except Exception as e:
        log_warn(f"Failed to dump page HTML: {e}")
    
    log_error("No trading interface found in any frame")
    return None

def curlify_request(request):
    method = request.method
    url = request.url
    headers = request.headers
    post_data = request.post_data
    curl_cmd = ["curl", "-X", method, f'"{url}"']
    for k, v in headers.items():
        curl_cmd.append(f'-H "{k}: {v}"')
    if post_data:
        curl_cmd.append(f'--data-raw "{post_data}"')
    return " ".join(curl_cmd)

async def try_login_domains(page, username, password):
    """Try multiple Bulenox domain configurations"""
    domain_configs = [
        # Primary configuration
        {
            "login_url": "https://bulenox.projectx.com/login",
            "trade_url": "https://bulenox.projectx.com/trade",
            "trading_url": "https://bulenox.projectx.com/trading",
            "name": "ProjectX Domain"
        },
        # Alternative configurations
        {
            "login_url": "https://bulenox.projectx.com/login", 
            "trade_url": "https://bulenox.com/trade",
            "trading_url": "https://bulenox.com/trading",
            "name": "Main Domain - Member Login"
        },
        {
            "login_url": "https://bulenox.com/login",
            "trade_url": "https://bulenox.com/trade", 
            "trading_url": "https://bulenox.com/trading",
            "name": "Main Domain - Direct Login"
        }
    ]
    
    for config in domain_configs:
        log_info(f"Trying {config['name']}: {config['login_url']}")
        try:
            await page.goto(config['login_url'], wait_until="networkidle", timeout=30000)
            await page.wait_for_load_state("networkidle")
            await dismiss_time_sync_modal(page)
            await take_screenshot(page, f"login_page_{config['name'].lower().replace(' ', '_')}")
            
            # Try login with this domain
            success = await attempt_login(page, username, password)
            if success:
                log_success(f"Login successful with {config['name']}")
                return config
            else:
                log_warn(f"Login failed with {config['name']}")
                
        except Exception as e:
            log_warn(f"Domain {config['name']} failed: {e}")
            continue
    
    return None

async def attempt_login(page, username, password):
    """Attempt login and return success/failure"""
    try:
        await dismiss_cookie_banner(page)
        
        # First, wait for any login form element to be visible
        form_detection_selectors = [
            'input[name="userName"]', 'input[name="username"]', 'input#username',
            'input[type="password"]', 'form', '[class*="login"]', '[id*="login"]'
        ]
        
        try:
            await wait_for_any(page, form_detection_selectors, timeout=10000, retries=2, delay_sec=2)
            log_info("Login form detected")
        except Exception as e:
            log_error(f"No login form detected: {e}")
            return False
        
        # Fill username with cross-frame fallbacks (enhanced selectors)
        username_selectors = [
            'input[name="userName"]', 'input[name="username"]', 'input#username', 
            'input[placeholder*="User"]', 'input[placeholder*="Email"]',
            'input[autocomplete="username"]', 'input[type="email"]', 
            'input[type="text"]:first-of-type', 'form input[type="text"]',
            'input:not([type="password"]):not([type="hidden"]):not([type="submit"])'
        ]
        target_user, used_user_sel = await safe_type_any_cross(page, username_selectors, username)
        log_info(f"Username entered via: {used_user_sel}")
        
        # Fill password with cross-frame fallbacks
        password_selectors = [
            'input[name="password"]', 'input#password', 'input[placeholder*="Pass"]', 
            'input[autocomplete="current-password"]', 'input[type="password"]', 'form input[type="password"]'
        ]
        target_pass, used_pass_sel = await safe_type_any_cross(page, password_selectors, password)
        log_info(f"Password entered via: {used_pass_sel}")
        
        # Submit login
        try:
            await safe_click_cross(page, [
                'button:has-text("Login")', 'button:has-text("Log in")',
                'button:has-text("Sign In")', 'button:has-text("Sign in")',
                'button[type="submit"]', 'form button[type="submit"]',
                'button:has-text("SIGN IN")', 'button:has-text("LOG IN")',
                'input[type="submit"]', '[role="button"][type="submit"]'
            ], retries=2, delay_sec=1)
            log_info("Clicked explicit login button")
        except Exception:
            log_debug("No explicit login button clicked, trying form submission and Enter key")
            await submit_enclosing_form(target_pass, used_pass_sel)
            try:
                await target_pass.press(used_pass_sel, 'Enter')
            except Exception:
                try:
                    await target_pass.keyboard.press('Enter')
                except Exception:
                    pass
        
        log_info("Submitted credentials")
        await take_screenshot(page, "post_login_submit")
        
        await asyncio.sleep(3)
        await dismiss_time_sync_modal(page)
        await page.wait_for_load_state("networkidle")
        
        # Check if login was successful
        current_url = page.url
        log_info(f"Current URL after login: {current_url}")
        
        # If we're no longer on login page, assume success
        if "/login" not in current_url.lower():
            return True
            
        # Check for error messages
        error_selectors = [
            'div[class*="error"]', 'span[class*="error"]', 'p[class*="error"]',
            'div[class*="alert"]', 'div[class*="warning"]', 'div[class*="message"]',
            'text=Invalid', 'text=incorrect', 'text=failed', 'text=error'
        ]
        
        for error_sel in error_selectors:
            try:
                error_el = await page.wait_for_selector(error_sel, timeout=1000, state="visible")
                if error_el:
                    error_text = await error_el.text_content()
                    log_error(f"Login error detected: {error_text}")
                    return False
            except Exception:
                continue
        
        # Check storage for auth tokens
        try:
            cookies = await page.context.cookies()
            auth_cookies = [c for c in cookies if any(k in c.get('name','').lower() for k in ['token','auth','session','jwt'])]
            if auth_cookies:
                log_success(f"Auth cookies present: {[c['name'] for c in auth_cookies]}")
                return True
                
            keys = await page.evaluate('Object.keys(window.localStorage)')
            auth_keys = [k for k in keys if any(x in k.lower() for x in ['token','auth','jwt'])]
            if auth_keys:
                log_success(f"Auth localStorage keys present: {auth_keys}")
                return True
        except Exception as st_e:
            log_warn(f"Storage check failed: {st_e}")
        
        return False
        
    except Exception as e:
        log_error(f"Login attempt failed: {e}")
        return False

async def main():
    # Environment variables with defaults
    USERNAME = os.getenv("BULENOX_USERNAME", "your_username")
    PASSWORD = os.getenv("BULENOX_PASSWORD", "your_password")
    SYMBOL = os.getenv("BULENOX_SYMBOL", "GOLD")
    ORDER_TYPE = os.getenv("BULENOX_ORDER_TYPE", "Market")
    QUANTITY = os.getenv("BULENOX_QUANTITY", "0.01")
    SIDE = os.getenv("BULENOX_SIDE", "Buy")
    HEADLESS = os.getenv("BULENOX_HEADLESS", "true").lower() == "true"
    SLOW_MO = int(os.getenv("BULENOX_SLOWMO_MS", "1000"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = await browser.new_context()
        page = await context.new_page()
        trade_curl = None
        login_success_by_network = False
        successful_config = None

        # Enhanced network interceptor
        def on_request(request):
            nonlocal trade_curl
            try:
                if request.method.upper() == "POST":
                    log_info(f"POST -> {request.url}")
                    
                    # More specific trade detection patterns - avoid chart/data endpoints
                    trade_url_patterns = ["/api/trade", "/v1/trade", "/trade/execute", "/order", "/position", "/submit", "/place"]
                    # Exclude chart/data endpoints that contain trading symbols but aren't actual trades
                    # CRITICAL FIX: Add /charts exclusion pattern
                    exclude_patterns = ["/charts", "/data", "/quote", "/price", "/history", "/candles", "/ohlc", "/market-data", "/chart"]
                    
                    url_lower = request.url.lower()
                    url_matches = any(pattern in url_lower for pattern in trade_url_patterns)
                    is_excluded = any(pattern in url_lower for pattern in exclude_patterns)
                    
                    log_debug(f"URL '{request.url}' - matches trade patterns: {url_matches}, is excluded: {is_excluded}")
                    
                    data_matches = False
                    keyword_count = 0
                    if request.post_data and not is_excluded:
                        pd = request.post_data.lower()
                        # Look for actual trade/order keywords, not just symbols
                        trade_keywords = ["order", "trade", "buy", "sell", "quantity", "volume", "side", "market", "limit", "stop", "position", "execute", "place"]
                        # Require multiple trade keywords to avoid false positives
                        keyword_count = sum(1 for k in trade_keywords if k in pd)
                        data_matches = keyword_count >= 2  # Require at least 2 trade keywords
                        
                        found_keywords = [k for k in trade_keywords if k in pd]
                        log_debug(f"POST data keywords found: {keyword_count} ({found_keywords}) - {'TRADE DETECTED' if data_matches else 'NOT A TRADE'}")
                    
                    final_decision = (url_matches and not is_excluded) or data_matches
                    
                    if final_decision:
                        curl_cmd = curlify_request(request)
                        trade_curl = curl_cmd
                        log_success(f"⚡ TRADE DETECTED: {request.url}")
                        log_debug(f"cURL: {curl_cmd}")
                        
                        # Save with timestamp to avoid overwriting
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        try:
                            with open("trade.sh", "w") as f:
                                f.write(curl_cmd)
                            with open(f"trade_{timestamp}.sh", "w") as f:
                                f.write(curl_cmd)
                            with open("trade_curl.txt", "w") as f:
                                f.write(curl_cmd)
                            with open(f"trade_curl_{timestamp}.txt", "w") as f:
                                f.write(curl_cmd)
                            log_success(f"Saved trade cURL to trade.sh, trade_{timestamp}.sh, trade_curl.txt, and trade_curl_{timestamp}.txt")
                        except Exception as fe:
                            log_warn(f"Failed to write trade.sh: {fe}")
                    else:
                        log_debug(f"❌ Ignoring non-trade POST to {request.url} (excluded: {is_excluded})")
            except Exception as e:
                log_warn(f"Network interceptor error: {e}")

        # Response handler to detect successful login
        async def on_response_async(response):
            nonlocal login_success_by_network
            try:
                url_lower = response.url.lower()
                if "login" in url_lower and response.request.method.upper() == "POST":
                    status = response.status
                    body_preview = ""
                    try:
                        text = await response.text()
                        body_preview = text[:500]
                    except Exception:
                        text = ""
                    log_info(f"Login response {status} from {response.url} body preview: {body_preview}")
                    if status in (200, 201):
                        # Heuristics for success
                        tl = (text or "").lower()
                        if any(k in tl for k in ["token", "success", "auth", "jwt", '"isSuccess":true']):
                            login_success_by_network = True
                            log_success("Login success inferred from network response")
            except Exception as e:
                log_warn(f"Response handler error: {e}")

        def on_response(response):
            try:
                import asyncio as _asyncio
                _asyncio.create_task(on_response_async(response))
            except Exception as e:
                log_warn(f"Failed to schedule response handler: {e}")

        context.on("request", on_request)
        page.on("request", on_request)
        context.on("response", on_response)
        page.on("response", on_response)
        log_info("Network interceptors attached.")

        # Try multiple domain configurations for login
        log_info("Starting multi-domain login process...")
        successful_config = await try_login_domains(page, USERNAME, PASSWORD)
        
        if not successful_config:
            log_error("Failed to login with all domain configurations")
            await take_screenshot(page, "all_domains_failed")
            await browser.close()
            sys.exit(1)
        
        log_success(f"Login successful with {successful_config['name']}")
        
        # Use the successful configuration for trade navigation
        TRADE_URL = successful_config.get('trade_url') or successful_config.get('trading_url')
        
        # Enhanced trading interface navigation with multiple URL attempts
        log_info("Looking for trading interface...")
        trade_urls_to_try = [
            successful_config.get('trade_url'),
            successful_config.get('trading_url'),
            successful_config['login_url'].replace('/login', '/trade'),
            successful_config['login_url'].replace('/login', '/trading'),
            successful_config['login_url'].replace('/member/login', '/trade'),
            successful_config['login_url'].replace('/member/login', '/trading'),
            # Additional variations found in codebase
            successful_config['login_url'].replace('/login', '/platform'),
            successful_config['login_url'].replace('/login', '/app'),
            successful_config['login_url'].replace('/member/login', '/platform'),
            successful_config['login_url'].replace('/member/login', '/app')
        ]
        
        # Remove None and duplicates
        trade_urls_to_try = list(dict.fromkeys([url for url in trade_urls_to_try if url]))
        
        trading_page = None
        for trade_url in trade_urls_to_try:
            log_info(f"Trying trade URL: {trade_url}")
            for attempt in range(1, 4):
                try:
                    log_info(f"Attempt {attempt} navigating to {trade_url}")
                    await page.goto(trade_url, wait_until="networkidle")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    # Try to find trading interface
                    trading_page = await find_trading_interface(page)
                    if trading_page:
                        log_success(f"Trading interface found at: {trade_url}")
                        break
                    # Check frames if not found on main page
                    frames = page.frames
                    log_info(f"Checking {len(frames)} frames for trading interface...")
                    for i, frame in enumerate(frames):
                        try:
                            frame_url = frame.url
                            log_debug(f"Checking frame {i}: {frame_url}")
                            trading_frame = await find_trading_interface(frame)
                            if trading_frame:
                                log_success(f"Trading interface found in frame {i} at {trade_url}")
                                trading_page = trading_frame
                                break
                        except Exception as e:
                            log_warn(f"Error checking frame {i}: {e}")
                            continue
                    if trading_page:
                        break
                    await asyncio.sleep(2)
                except Exception as e:
                    log_warn(f"Failed to access {trade_url} (attempt {attempt}): {e}")
                    await asyncio.sleep(2)
                    continue
            if trading_page:
                break
        
        if not trading_page:
            log_error("Could not find trading interface on any URL")
            await take_screenshot(page, "trade_interface_error")
            # Save page HTML for debugging
            try:
                html = await page.content()
                with open("trade_interface_dump.html", "w", encoding="utf-8") as f:
                    f.write(html)
                log_info("Page HTML saved to trade_interface_dump.html")
            except Exception:
                pass
            await browser.close()
            sys.exit(1)

        log_success("Trading interface found! Placing order...")
        
        # Try exact selectors first (from Node.js working version)
        try:
            log_info("Using exact selectors from working Node.js version...")
            await trading_page.fill('#\\:r1b\\:', SYMBOL)  # Symbol field
            await trading_page.fill('#\\:r19\\:', QUANTITY)  # Quantity field
            
            # Click the appropriate button based on SIDE
            if SIDE.lower() in ['buy', 'b']:
                await trading_page.click('#orderCardTab button:has-text("Buy")')
                log_success("BUY order placed using exact selectors")
            else:
                await trading_page.click('#orderCardTab button:has-text("Sell")')
                log_success("SELL order placed using exact selectors")
                
        except Exception as e:
            log_warn(f"Exact selectors failed: {e}")
            
            # Fallback to DOM tab selectors
            try:
                log_info("Trying DOM tab selectors...")
                await trading_page.fill('#\\:r19\\:', SYMBOL)  # Try symbol in quantity field
                if SIDE.lower() in ['buy', 'b']:
                    await trading_page.click('#domTab button:has-text("Buy")')
                    log_success("BUY order placed using DOM tab selectors")
                else:
                    await trading_page.click('#domTab button:has-text("Sell")')
                    log_success("SELL order placed using DOM tab selectors")
                    
            except Exception as e2:
                log_debug(f"DOM tab selectors failed: {e2}")
                
                # Final fallback to generic selectors
                try:
                    log_info("Using generic fallback selectors...")
                    
                    # Try to find and fill symbol
                    symbol_selectors = ['input[placeholder*="Symbol"]', 'input[placeholder*="Market"]', 'input[placeholder*="search"]']
                    for sel in symbol_selectors:
                        try:
                            await trading_page.fill(sel, SYMBOL)
                            log_success(f"Symbol filled with: {sel}")
                            break
                        except Exception:
                            continue
                    
                    # Try to find and fill quantity
                    qty_selectors = ['input[placeholder*="Amount"]', 'input[placeholder*="Volume"]', 'input[placeholder*="Size"]', 'input[type="number"]']
                    for sel in qty_selectors:
                        try:
                            await trading_page.fill(sel, QUANTITY)
                            log_success(f"Quantity filled with: {sel}")
                            break
                        except Exception:
                            continue
                    
                    # Try to click buy/sell button
                    if SIDE.lower() in ['buy', 'b']:
                        buy_selectors = ['button:has-text("Buy")', 'button.buy', 'button[class*="buy"]', 'button[class*="green"]']
                        for sel in buy_selectors:
                            try:
                                await trading_page.click(sel)
                                log_success(f"BUY clicked with: {sel}")
                                break
                            except Exception:
                                continue
                    else:
                        sell_selectors = ['button:has-text("Sell")', 'button.sell', 'button[class*="sell"]', 'button[class*="red"]']
                        for sel in sell_selectors:
                            try:
                                await trading_page.click(sel)
                                log_success(f"SELL clicked with: {sel}")
                                break
                            except Exception:
                                continue
                                
                except Exception as e3:
                    log_error(f"All selector approaches failed: {e3}")
                    await take_screenshot(page, "trade_debug")

        # Handle any confirmation dialogs
        try:
            confirm_selectors = ['button:has-text("Confirm")', 'button:has-text("OK")', 'button:has-text("Submit")']
            await wait_for_any(trading_page, confirm_selectors, timeout=3000, retries=1)
            await safe_click(trading_page, confirm_selectors)
            log_success("Order confirmed")
        except Exception:
            log_info("No confirmation dialog appeared")

        # Wait to capture network requests
        log_info("Waiting to capture trade requests (15s)...")
        await asyncio.sleep(15)

        if trade_curl:
            log_success("Trade cURL saved to trade.sh.")
            try:
                log_info("Converting cURL to Python requests code...")
                from curlconverter import convert
                
                # Convert cURL command to Python
                python_code_raw = convert(trade_curl)
                
                # Wrap the generated code with additional comments and error handling
                python_code = f"""#!/usr/bin/env python
\"\"\"
Bulenox Trade API Request - Auto-generated from captured cURL

This file was automatically generated from a captured cURL command.
It contains the Python code to execute the same API request.

Original cURL command:
{trade_curl}
\"\"\"

{python_code_raw}

# Execute the request and print the response
if __name__ == "__main__":
    try:
        print(f"Sending trade request to {{url}}...")
        print(f"Response status code: {{response.status_code}}")
        print(f"Response body: {{response.text}}")
    except Exception as e:
        print(f"Error executing request: {{e}}")
"""
                
                # Save both standard and timestamped Python files
                with open("trade_request_full.py", "w") as f:
                    f.write(python_code)
                import datetime as _dt
                _ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f"trade_request_full_{_ts}.py", "w") as f:
                    f.write(python_code)
                log_success(f"Python code saved to trade_request_full.py and trade_request_full_{_ts}.py")
            except ImportError:
                log_warn("curlconverter not installed. Run: pip install curlconverter")
            except Exception as e:
                log_warn(f"Failed to convert cURL to Python: {e}")
                # Fallback: create basic template
                try:
                    python_code = f"""#!/usr/bin/env python
\"\"\"
Bulenox Trade API Request - Basic template

The automatic conversion failed, but here's the captured cURL command:
{trade_curl}

Install curlconverter for automatic conversion: pip install curlconverter
Or convert manually using online tools like https://curlconverter.com/
\"\"\"
import requests

# TODO: Extract and set these values from the cURL command above
url = "https://bulenox.projectx.com/api/trade"  # Update with actual URL
headers = {{
    # Add headers from cURL command
}}
data = {{
    # Add data from cURL command  
}}

# Execute the request (modify as needed)
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Response status: {{response.status_code}}")
    print(f"Response body: {{response.text}}")
except Exception as e:
    print(f"Error: {{e}}")
"""
                    with open("trade_request_full.py", "w") as f:
                        f.write(python_code)
                    log_info("Created fallback Python template in trade_request_full.py")
                except Exception:
                    pass
        else:
            log_error("No trade cURL captured.")
            await take_screenshot(page, "trade_debug")

        try:
            await browser.close()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())