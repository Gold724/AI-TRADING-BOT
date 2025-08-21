import os
import csv
from playwright.sync_api import sync_playwright
from curlconverter import to_python
import time

ACCOUNTS_FILE = "accounts.csv"
TARGET_KEYWORD = "/trade"  # API endpoint to match
OUTPUT_FILE = "trade_request.py"

def save_request_as_python(request):
    """Convert cURL to Python requests code and save."""
    curl_command = request.to_curl()
    py_code = to_python(curl_command)
    with open(OUTPUT_FILE, "w") as f:
        f.write(py_code)
    print(f"[✅] Saved trade request to {OUTPUT_FILE}")

def login_and_trigger_trade(email, password, playwright):
    """Login and trigger a dummy trade to capture request."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    captured = False

    def handle_request(request):
        nonlocal captured
        if TARGET_KEYWORD in request.url and request.method == "POST":
            print(f"[🎯] Found target API request: {request.url}")
            save_request_as_python(request)
            captured = True

    page.on("request", handle_request)

    print(f"[🚀] Logging in as {email}")
    page.goto("https://bulenox.projectx.com/login")

    # Fill login form
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    print("[✅] Logged in, triggering dummy trade...")

    # Navigate to trading page
    page.goto("https://bulenox.projectx.com/trade")
    page.wait_for_load_state("networkidle")

    # Select a market using selectors from bulenox_sentinel.py
    try:
        # Try to find and use symbol search field
        symbol_selectors = [
            "input[placeholder='Search symbol'], input[placeholder='Symbol'], input[placeholder*='search']",
            "div.symbol-search input",
            "div.search-box input"
        ]
        
        for selector in symbol_selectors:
            if page.locator(selector).count() > 0:
                print(f"Found symbol field with selector: {selector}")
                page.fill(selector, "EURUSD")
                page.wait_for_timeout(1000)  # Wait for dropdown
                
                # Try to select from dropdown
                dropdown_selectors = [
                    "div:text('EURUSD')",
                    "span:text('EURUSD')",
                    "li:text('EURUSD')"
                ]
                
                dropdown_found = False
                for dropdown_selector in dropdown_selectors:
                    if page.locator(dropdown_selector).count() > 0:
                        page.click(dropdown_selector)
                        dropdown_found = True
                        print(f"Selected EURUSD from dropdown with selector: {dropdown_selector}")
                        break
                
                if not dropdown_found:
                    # Press Enter as fallback
                    page.press(selector, "Enter")
                    print("Pressed Enter to select symbol")
                
                break
    except Exception as e:
        print(f"Error selecting market: {e}")
        # Try clicking on symbol in list as fallback
        try:
            page.click("div:text('EURUSD'), span:text('EURUSD'), td:text('EURUSD')")
            print("Clicked on EURUSD in symbol list")
        except Exception as e:
            print(f"Error clicking symbol in list: {e}")

    # Enter small amount
    try:
        volume_selectors = [
            "input[placeholder='Volume'], input[placeholder='Lot Size'], input[placeholder='Size']",
            "input.volume, input.lot-size, input.size",
            "div:text('Volume') ~ input, div:text('Lot Size') ~ input, div:text('Size') ~ input"
        ]
        
        for selector in volume_selectors:
            if page.locator(selector).count() > 0:
                page.fill(selector, "0.01")
                print(f"Set volume to 0.01 using selector: {selector}")
                break
    except Exception as e:
        print(f"Error setting volume: {e}")

    # Click buy button
    try:
        buy_selectors = [
            "button:text('Buy')",
            "button.buy",
            "div.button:text('Buy')",
            "div.buy.button"
        ]
        
        for selector in buy_selectors:
            if page.locator(selector).count() > 0:
                page.click(selector)
                print(f"Clicked Buy button with selector: {selector}")
                break
    except Exception as e:
        print(f"Error clicking Buy button: {e}")

    # Check for and handle confirmation dialog if it appears
    try:
        confirm_selectors = [
            "button:text('Confirm'), button:text('OK'), button:text('Yes')",
            "div.dialog button:text('Confirm'), div.dialog button:text('OK')",
            "div.modal button:text('Confirm'), div.modal button:text('OK')"
        ]
        
        for selector in confirm_selectors:
            if page.locator(selector).count() > 0:
                page.click(selector)
                print(f"Clicked confirmation button with selector: {selector}")
                break
    except Exception as e:
        print(f"No confirmation dialog or error: {e}")

    # Wait a bit to allow capture
    timeout = time.time() + 10
    while time.time() < timeout and not captured:
        time.sleep(0.5)

    browser.close()
    return captured

def main():
    with sync_playwright() as p:
        with open(ACCOUNTS_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if login_and_trigger_trade(row['email'], row['password'], p):
                    print("[🏁] Capture complete, stopping rotation.")
                    break
            else:
                print("[❌] No trade request captured from any account.")

if __name__ == "__main__":
    main()