import os
import csv
import sys
from dotenv import load_dotenv
import time

# Load environment variables for fallback credentials
load_dotenv()

# Configuration
ACCOUNTS_FILE = "accounts.csv"
TARGET_KEYWORD = "/trade"  # match part of API URL
OUTPUT_DIR = "trade_requests"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_curl_command(curl_command, account_email):
    """Save the curl command to a file with instructions for manual conversion."""
    py_code = f"""# Generated from Bulenox trade request
# Original cURL command:
"""
    py_code += curl_command
    py_code += """

# To convert this to Python code:
# 1. Install curlconverter: pip install curlconverter
# 2. Use: from curlconverter import convert; print(convert('''curl_command_here'''))
# Or use an online converter like https://curl.trillworks.com

# Example Python requests code structure:
# import requests
# 
# headers = {
#     # Headers from the curl command
# }
# 
# data = {
#     # Data from the curl command
# }
# 
# response = requests.post('URL_FROM_CURL', headers=headers, json=data)
# print(response.text)
"""
    
    # Create a sanitized filename from the email
    filename = account_email.replace("@", "_at_").replace(".", "_") + "_trade.py"
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    with open(output_path, "w") as f:
        f.write(py_code)
    print(f"[✅] Saved trade request to {output_path}")
    
    # Also save the latest one to a standard location
    with open("trade_request.py", "w") as f:
        f.write(py_code)
    print(f"[✅] Also saved to trade_request.py")

def create_sample_trade_request():
    """Create a sample trade request file for demonstration purposes."""
    # Create a sample trade request file for demonstration
    sample_curl = """curl 'https://bulenox.com/api/trade' \
  -H 'authority: bulenox.com' \
  -H 'accept: application/json' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'content-type: application/json' \
  -H 'origin: https://bulenox.com' \
  -H 'referer: https://bulenox.com/trade' \
  -H 'sec-ch-ua: "Chromium";v="112"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36' \
  --data-raw '{"symbol":"EURUSD","volume":0.01,"side":"buy","type":"market"}' \
  --compressed"""
    
    print("\n[ℹ️] Creating a sample trade request file for demonstration purposes...")
    save_curl_command(sample_curl, "sample_account")
    print("\n[ℹ️] You can manually convert this curl command to Python code using the instructions in the file.")

def main():
    try:
        # Try to import playwright - this will fail if not installed
        from playwright.sync_api import sync_playwright
        
        def save_request_as_python(request, account_email):
            """Convert cURL to Python requests code and save."""
            curl_command = request.to_curl()
            save_curl_command(curl_command, account_email)
        
        def login_and_trigger_trade(email, password, playwright):
            """Login and trigger a dummy trade to capture request."""
            try:
                browser = playwright.chromium.launch(headless=False)  # Set True for headless
                context = browser.new_context()
                page = context.new_page()
                
                captured = False
                
                def handle_request(request):
                    nonlocal captured
                    if TARGET_KEYWORD in request.url and request.method == "POST":
                        print(f"[🎯] Found trade API request: {request.url}")
                        save_request_as_python(request, email)
                        captured = True
                
                page.on("request", handle_request)
                
                print(f"[🚀] Opening Bulenox login for {email}...")
                page.goto("https://bulenox.com/login")
                
                # Login
                page.fill('input[name="email"]', email)
                page.fill('input[name="password"]', password)
                page.click('button[type="submit"]')
                
                # Wait for dashboard
                page.wait_for_load_state("networkidle")
                print(f"[✅] Logged in as {email}.")
                
                # Navigate to trade panel
                page.goto("https://bulenox.com/trade")
                page.wait_for_load_state("networkidle")
                print("[📈] Trade panel ready.")
                
                # --- AUTO-TRIGGER DUMMY TRADE ---
                # Select a market using selectors from bulenox_sentinel.py
                try:
                    # Try to find and use symbol search field
                    symbol_selectors = [
                        "input[placeholder='Search symbol'], input[placeholder='Symbol'], input[placeholder*='search']",
                        "div.symbol-search input",
                        "div.search-box input",
                        "input[name='symbol']"
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
                        "div:text('Volume') ~ input, div:text('Lot Size') ~ input, div:text('Size') ~ input",
                        "input[name='amount']"
                    ]
                    
                    for selector in volume_selectors:
                        if page.locator(selector).count() > 0:
                            page.fill(selector, "0.01")
                            print(f"Set volume to 0.01 using selector: {selector}")
                            break
                except Exception as e:
                    print(f"Error setting volume: {e}")
                
                # Handle side selection if it exists
                try:
                    side_selectors = [
                        "select[name='side']",
                        "select.side-selector"
                    ]
                    
                    for selector in side_selectors:
                        if page.locator(selector).count() > 0:
                            page.select_option(selector, "buy")
                            print(f"Selected 'buy' from side dropdown with selector: {selector}")
                            break
                except Exception as e:
                    print(f"No side selection dropdown or error: {e}")
                
                # Click buy button
                try:
                    buy_selectors = [
                        "button:text('Buy')",
                        "button.buy",
                        "div.button:text('Buy')",
                        "div.buy.button",
                        "button[type='submit']"
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
                
                print("[⚡] Dummy trade submitted, waiting for API capture...")
                
                # Wait a bit to allow capture
                timeout = time.time() + 10
                while time.time() < timeout and not captured:
                    time.sleep(0.5)
                
                browser.close()
                return captured
            except Exception as e:
                print(f"[❌] Error during browser automation: {e}")
                return False
        
        # Check if accounts.csv exists, if not, use environment variables
        if not os.path.exists(ACCOUNTS_FILE):
            print(f"[⚠️] {ACCOUNTS_FILE} not found, using environment variables.")
            email = os.getenv("BULENOX_EMAIL")
            password = os.getenv("BULENOX_PASSWORD")
            
            if not email or not password:
                print("[❌] No credentials found in environment variables.")
                create_sample_trade_request()
                return
            
            with sync_playwright() as p:
                if login_and_trigger_trade(email, password, p):
                    print("[🏁] Capture complete.")
                else:
                    print("[❌] No trade request captured.")
                    create_sample_trade_request()
        else:
            # Use accounts from CSV file
            success = False
            with sync_playwright() as p:
                with open(ACCOUNTS_FILE, newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        print(f"\n[🔄] Trying account: {row['email']}")
                        if login_and_trigger_trade(row['email'], row['password'], p):
                            print("[🏁] Capture complete, stopping rotation.")
                            success = True
                            break
                    if not success:
                        print("[❌] No trade request captured from any account.")
                        create_sample_trade_request()
    
    except ImportError as e:
        print(f"[❌] Error: {e}")
        print("\n[ℹ️] Installation instructions:")
        print("1. Install required packages: pip install playwright python-dotenv")
        print("2. Install browser drivers: python -m playwright install")
        print("\nIf you're having network issues with playwright install, you can:")
        print("1. Try using a VPN or different network connection")
        print("2. Manually download browsers from https://playwright.dev/docs/browsers")
        
        create_sample_trade_request()

if __name__ == "__main__":
    main()