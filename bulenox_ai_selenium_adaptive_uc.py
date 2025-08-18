#!/usr/bin/env python3
"""
bulenox_ai_selenium_adaptive_uc.py
Adaptive Selenium runner supporting:
 - classic selenium, undetected-chromedriver (uc), and stealth patching
 - proxy rotation hooks
 - selenium-wire request capture -> logs/requests_curl.txt (JSONL)
 - adaptive retries and headless/headful switching
Purpose: login, trade execution and scraping for Bulenox (use only on accounts you own)
"""

import os
import time
import json
import random
import logging
import threading
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# selenium-wire for request capturing
from seleniumwire import webdriver as sw_webdriver

# undetected chromedriver for stealth
import undetected_chromedriver as uc

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------
# Logging + paths
# -----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bulenox_adaptive")

ROOT = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
REQUESTS_FILE = os.path.join(LOG_DIR, "requests_curl.txt")
SCREEN_DIR = os.path.join(LOG_DIR, "screenshots")
os.makedirs(SCREEN_DIR, exist_ok=True)
HEARTBEAT = os.path.join(LOG_DIR, "heartbeat_status.txt")

load_dotenv(os.path.join(ROOT, ".env"))

# -----------------------
# Config via .env
# -----------------------
BULENOX_USERNAME = os.getenv("BULENOX_USERNAME")
BULENOX_PASSWORD = os.getenv("BULENOX_PASSWORD")
PROFILE_PATH = os.getenv("BULENOX_PROFILE_PATH")  # optional
PROFILE_NAME = os.getenv("BULENOX_PROFILE_NAME")  # optional
PROXY_LIST = os.getenv("PROXY_LIST")  # comma separated list
PROXIES_FILE = os.getenv("PROXIES_FILE")  # or path to file
DEBUG = bool(int(os.getenv("DEBUG", "0")))
DRIVER_MODE = os.getenv("DRIVER_MODE", "uc")  # options: "uc", "selenium", "stealth"

LOGIN_URL = os.getenv("BULENOX_LOGIN_URL", "https://bulenox.projectx.com/login")
TRADING_URL = os.getenv("BULENOX_TRADING_URL", "https://bulenox.projectx.com/trading")

# -----------------------
# Helpers
# -----------------------
def heartbeat(status: str, active=True):
    try:
        with open(HEARTBEAT, "w") as f:
            f.write(json.dumps({"status": status, "ts": datetime.utcnow().isoformat(), "active": active}))
        logger.info("HEARTBEAT: %s", status)
    except Exception as e:
        logger.debug("heartbeat write error: %s", e)

class ProxyRotator:
    def __init__(self):
        self.list = []
        if PROXY_LIST:
            self.list = [p.strip() for p in PROXY_LIST.split(",") if p.strip()]
        elif PROXIES_FILE and os.path.exists(PROXIES_FILE):
            with open(PROXIES_FILE, "r") as f:
                self.list = [l.strip() for l in f if l.strip()]
        random.shuffle(self.list)
        self.i = 0
    def next(self) -> Optional[str]:
        if not self.list:
            return None
        proxy = self.list[self.i % len(self.list)]
        self.i += 1
        return proxy

proxy_rotator = ProxyRotator()

# -----------------------
# Element selectors (kept concise but effective)
# -----------------------
SELECTORS = {
    "username": [
        (By.ID, "email"),
        (By.NAME, "email"),
        (By.XPATH, "//input[@type='email']"),
    ],
    "password": [
        (By.ID, "password"),
        (By.NAME, "password"),
        (By.XPATH, "//input[@type='password']"),
    ],
    "login_button": [
        (By.XPATH, "//button[@type='submit']"),
        (By.XPATH, "//button[contains(text(),'Login')]"),
    ],
    "symbol_search": [
        (By.ID, "symbol-search"),
        (By.XPATH, "//input[contains(@placeholder,'Search')]"),
    ],
    "buy_button": [
        (By.XPATH, "//button[contains(@class,'buy-button')]"),
        (By.XPATH, "//button[contains(text(),'Buy')]"),
    ],
    "sell_button": [
        (By.XPATH, "//button[contains(@class,'sell-button')]"),
        (By.XPATH, "//button[contains(text(),'Sell')]"),
    ],
    "quantity_input": [(By.ID, "quantity"), (By.NAME, "quantity")],
    "confirm_button": [(By.XPATH, "//button[contains(text(),'Confirm')]"), (By.CSS_SELECTOR, ".confirm-btn")],
}

# -----------------------
# Driver factory + stealth
# -----------------------
def random_user_agent():
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]
    return random.choice(uas)

def make_sw_driver_uc(proxy: Optional[str]=None, headless: bool=False):
    """
    Create a selenium-wire driver backed by undetected-chromedriver (uc).
    """
    ua = random_user_agent()
    
    # For newer versions of undetected-chromedriver
    try:
        # First try with direct uc.Chrome approach
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        if PROFILE_PATH and PROFILE_NAME:
            options.add_argument(f"--user-data-dir={PROFILE_PATH}")
            options.add_argument(f"--profile-directory={PROFILE_NAME}")
        if headless:
            options.add_argument("--headless=new")
        options.add_argument(f"--user-agent={ua}")
        
        # Set a random window size
        w = random.choice([1200,1366,1440,1600,1920])
        h = random.choice([700,768,800,900,1080])
        options.add_argument(f"--window-size={w},{h}")
        
        # Create driver directly with undetected-chromedriver
        logger.info("Attempting to create Chrome with undetected-chromedriver")
        driver = uc.Chrome(options=options)
        logger.info("Successfully created Chrome with undetected-chromedriver")
        
        # Apply stealth patches
        try:
            patch = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4]});
            Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
            """
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": patch})
        except Exception as e:
            logger.debug("Could not apply stealth patch: %s", e)
        
        return driver
          
    except Exception as e:
        logger.error(f"Error with undetected-chromedriver: {e}")
        
        # Fallback to standard selenium-wire Chrome
        try:
            logger.info("Falling back to standard selenium-wire Chrome")
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            if PROFILE_PATH and PROFILE_NAME:
                options.add_argument(f"--user-data-dir={PROFILE_PATH}")
                options.add_argument(f"--profile-directory={PROFILE_NAME}")
            if headless:
                options.add_argument("--headless=new")
            options.add_argument(f"--user-agent={ua}")
            options.add_argument(f"--window-size={w},{h}")
            
            # Add seleniumwire options
            sw_opts = {"request_storage_base_dir": os.path.join(LOG_DIR, "seleniumwire"), "disable_encoding": True}
            if proxy:
                sw_opts["proxy"] = {"http": proxy, "https": proxy, "no_proxy": "localhost,127.0.0.1"}
                logger.info("Using proxy: %s", proxy)
            
            # Try with WebDriverManager
            service = Service(ChromeDriverManager().install())
            driver = sw_webdriver.Chrome(service=service, options=options, seleniumwire_options=sw_opts)
            logger.info("Successfully created Chrome with WebDriverManager")
            
            # Apply stealth patches
            try:
                patch = """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4]});
                Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
                """
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": patch})
            except Exception as e:
                logger.debug("Could not apply stealth patch: %s", e)
                
            return driver
            
        except Exception as e2:
            logger.error(f"Error with WebDriverManager: {e2}")
            raise Exception(f"Failed to initialize Chrome driver: {e} and {e2}")

def make_sw_driver_classic(proxy: Optional[str]=None, headless: bool=False):
    # Not used widely because uc gives better stealth; kept for fallback
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    if proxy:
        # classic Chrome does not have built-in selenium-wire proxy mapping here; handled by sw_webdriver wrapper normally
        pass
    driver = sw_webdriver.Chrome(options=opts)
    return driver

# -----------------------
# Request logger thread
# -----------------------
def start_request_logger(driver, stop_event):
    seen = set()
    def worker():
        logger.info("Request logger started")
        while not stop_event.is_set():
            try:
                for req in list(driver.requests):
                    if req.id in seen:
                        continue
                    if req.response:
                        seen.add(req.id)
                        try:
                            curl = req.curl()
                        except Exception:
                            curl = None
                        entry = {"ts": datetime.utcnow().isoformat()+"Z", "url": req.url, "method": req.method,
                                 "status": getattr(req.response, "status_code", None), "curl": curl}
                        with open(REQUESTS_FILE, "a", encoding="utf-8") as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        if DEBUG:
                            logger.info("Logged: %s %s", req.method, req.url)
                time.sleep(0.5)
            except Exception as e:
                logger.debug("Request logger error: %s", e)
                time.sleep(1)
        logger.info("Request logger stopped")
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t

# -----------------------
# Small AI-like helpers (element finding with multiple tries)
# -----------------------
def find_element_multi(driver, key, timeout=8):
    if key not in SELECTORS:
        return None
    for by, val in SELECTORS[key]:
        try:
            el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, val)))
            return el
        except TimeoutException:
            continue
        except Exception:
            continue
    # fallback generic inputs/buttons
    try:
        if key in ("username","password"):
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if inputs:
                return inputs[0] if key=="username" else (inputs[1] if len(inputs)>1 else inputs[0])
    except Exception:
        pass
    return None

# -----------------------
# Main class
# -----------------------
class BulenoxBot:
    def __init__(self):
        self.driver = None
        self.request_logger_thread = None
        self.request_logger_stop = threading.Event()
        self.mode = DRIVER_MODE.lower()
        self.headless_try = True  # try headless first, fallback to headful if detection triggers
    def _init_driver(self, proxy=None, headless=False):
        heartbeat("Initializing driver")
        try:
            if self.mode == "uc":
                d = make_sw_driver_uc(proxy=proxy, headless=headless)
            elif self.mode == "selenium":
                d = make_sw_driver_classic(proxy=proxy, headless=headless)
            else:
                d = make_sw_driver_uc(proxy=proxy, headless=headless)  # stealth default
            self.driver = d
            self.request_logger_thread = start_request_logger(self.driver, self.request_logger_stop)
            return True
        except Exception as e:
            logger.error("Driver init error: %s", e)
            return False

    def _close(self):
        try:
            self.request_logger_stop.set()
            if self.request_logger_thread:
                self.request_logger_thread.join(timeout=2)
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
        finally:
            self.driver = None
            self.request_logger_thread = None
            self.request_logger_stop.clear()

    def login(self, retries=3):
        attempt = 0
        while attempt < retries:
            attempt += 1
            proxy = proxy_rotator.next()
            headless = self.headless_try
            ok = self._init_driver(proxy=proxy, headless=headless)
            if not ok:
                time.sleep(1)
                continue
            try:
                self.driver.get(LOGIN_URL)
                time.sleep(2)
                # if already logged in (basic check)
                if "dashboard" in (self.driver.current_url or ""):
                    heartbeat("Already logged in", True)
                    return True
                u = find_element_multi(self.driver, "username", timeout=6)
                p = find_element_multi(self.driver, "password", timeout=6)
                if not u or not p:
                    raise Exception("login form not found")
                u.clear()
                u.send_keys(BULENOX_USERNAME)
                p.clear()
                p.send_keys(BULENOX_PASSWORD)
                btn = find_element_multi(self.driver, "login_button", timeout=4)
                if btn:
                    try:
                        btn.click()
                    except Exception:
                        p.send_keys(Keys.ENTER)
                else:
                    p.send_keys(Keys.ENTER)
                time.sleep(4)
                # quick success heuristic
                if "dashboard" in (self.driver.current_url or "") or find_element_multi(self.driver, "confirm_button", timeout=2):
                    heartbeat("Login success", True)
                    return True
                # if still on login page: maybe blocked because headless; retry with headful
                if headless and attempt < retries:
                    logger.info("Login failed in headless; retrying headful")
                    self._close()
                    self.headless_try = False
                    time.sleep(1)
                    continue
                raise Exception("login failed")
            except Exception as e:
                logger.warning("Login attempt %d failed: %s", attempt, e)
                self._close()
                time.sleep(1 + random.random()*2)
                continue
        heartbeat("Login failed", False)
        return False

    def navigate_to_trading(self):
        if not self.driver:
            raise Exception("driver not initialized")
        self.driver.get(TRADING_URL)
        time.sleep(2)
        return "trading" in (self.driver.current_url or "")

    def search_symbol(self, symbol):
        el = find_element_multi(self.driver, "symbol_search", timeout=6)
        if not el:
            logger.warning("symbol_search not found")
            return False
        el.clear()
        el.send_keys(symbol)
        time.sleep(1)
        el.send_keys(Keys.RETURN)
        time.sleep(2)
        return True

    def place_trade(self, symbol, side, quantity, stop_loss=None, take_profit=None):
        try:
            if not self.navigate_to_trading():
                logger.warning("navigate_to_trading failed")
            self.search_symbol(symbol)
            btn_key = "buy_button" if side.lower()=="buy" else "sell_button"
            btn = find_element_multi(self.driver, btn_key, timeout=6)
            if not btn:
                raise Exception("trade button missing")
            btn.click()
            time.sleep(1)
            qty = find_element_multi(self.driver, "quantity_input", timeout=4)
            if qty:
                qty.clear()
                qty.send_keys(str(quantity))
            if stop_loss is not None:
                sl = find_element_multi(self.driver, "stop_loss_input", timeout=2)
                if sl:
                    sl.clear()
                    sl.send_keys(str(stop_loss))
            if take_profit is not None:
                tp = find_element_multi(self.driver, "take_profit_input", timeout=2)
                if tp:
                    tp.clear()
                    tp.send_keys(str(take_profit))
            confirm = find_element_multi(self.driver, "confirm_button", timeout=4)
            if confirm:
                confirm.click()
            time.sleep(3)
            # success detection by looking for "Order Placed" or similar in captured responses or UI — basic heuristic:
            logger.info("Placed trade (UI click attempted); check logs/requests_curl.txt for actual API call captured")
            return True
        except Exception as e:
            logger.error("place_trade error: %s", e)
            return False

    def close(self):
        self._close()
        heartbeat("Closed", False)

# -----------------------
# Convenience CLI usage
# -----------------------
def main():
    bot = BulenoxBot()
    # simple orchestrator: login, then optionally place a test trade (comment out if you only want session alive)
    if not bot.login(retries=4):
        logger.error("Login failed after retries; exiting")
        bot.close()
        return
    # example: place a dummy trade - change to desired symbol/side/qty
    # bot.place_trade("GBPUSD", "buy", 1, stop_loss=None, take_profit=None)
    logger.info("Bot is now running (session active). Press Ctrl-C to stop.")
    try:
        # keep process alive so systemd can supervise and the request logger keeps collecting
        while True:
            time.sleep(10)
            heartbeat("running", True)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        bot.close()

def place_bulenox_trade(symbol, side, quantity, stop_loss=None, take_profit=None, debug=False):
    """
    Place a trade on Bulenox using contract sizes (not lot sizes).
    
    Args:
        symbol (str): Trading symbol (e.g., "EURUSD", "GBPUSD")
        side (str): Trade direction - "buy" or "sell"
        quantity (int): Number of contracts (NOT lot sizes)
        stop_loss (float, optional): Stop loss in pips
        take_profit (float, optional): Take profit in pips
        debug (bool): Enable debug logging
        
    Returns:
        bool: True if trade was placed successfully, False otherwise
        
    Note:
        This function uses CONTRACTS, not lot sizes. For Bulenox:
        - 1 contract = 1 contract (not 0.01 lot)
        - Minimum quantity is typically 1 contract
        - Maximum depends on account and symbol
    """
    logger = logging.getLogger("place_bulenox_trade")
    
    if debug:
        logger.setLevel(logging.DEBUG)
        
    try:
        # Validate inputs
        if not symbol or not side:
            logger.error("Symbol and side are required")
            return False
            
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            logger.error(f"Invalid quantity: {quantity}. Must be positive number of contracts")
            return False
            
        side = side.lower()
        if side not in ["buy", "sell"]:
            logger.error(f"Invalid side: {side}. Must be 'buy' or 'sell'")
            return False
            
        # Ensure quantity is an integer (contracts)
        quantity = int(quantity)
        if quantity < 1:
            logger.warning(f"Quantity {quantity} rounded up to 1 contract (minimum)")
            quantity = 1
            
        logger.info(f"Placing {side} order: {quantity} contracts of {symbol}")
        if stop_loss:
            logger.info(f"Stop Loss: {stop_loss} pips")
        if take_profit:
            logger.info(f"Take Profit: {take_profit} pips")
            
        # Create bot instance
        bot = BulenoxAISeleniumAdaptiveUC(debug=debug)
        
        try:
            # Login first
            logger.info("Logging into Bulenox...")
            login_success = bot.login()
            if not login_success:
                logger.error("Failed to login to Bulenox")
                return False
                
            # Place the trade
            logger.info(f"Executing trade: {side} {quantity} contracts of {symbol}")
            trade_success = bot.place_trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if trade_success:
                logger.info("✅ Trade placed successfully!")
                return True
            else:
                logger.error("❌ Failed to place trade")
                return False
                
        finally:
            # Always close the bot session
            bot.close()
            
    except Exception as e:
        logger.error(f"Error placing trade: {e}")
        if debug:
            logger.exception("Full traceback:")
        return False


if __name__ == "__main__":
    main()
