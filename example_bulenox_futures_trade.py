import os
import time
from dotenv import load_dotenv

from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade

# Load environment variables
load_dotenv()


def example_futures_trade():
    """Example of placing a futures trade on Bulenox using AI-enhanced Selenium"""
    print("\n" + "=" * 80)
    print("🤖 BULENOX FUTURES TRADING EXAMPLE")
    print("=" * 80)
    
    # Display the difference between contracts and lot sizes
    print("\n📊 Trading Units Comparison:")
    print("  - Bulenox: Uses CONTRACTS (1, 3, 5, etc.)")
    print("  - Exness:  Uses LOT SIZES (0.01, 0.02, etc.)")
    
    # Example 1: Using the all-in-one function
    print("\n🔄 Example 1: Using the all-in-one function")
    print("Placing a trade for 1 contract of Gold futures...")
    
    success = place_bulenox_trade(
        symbol="XAUUSD",  # Will be mapped to GC (Gold futures)
        side="buy",
        quantity=1,  # 1 contract
        stop_loss=1920.50,  # Optional
        take_profit=1950.00,  # Optional
        debug=True  # Enable screenshots
    )
    
    if success:
        print("✅ Trade placed successfully!")
    else:
        print("❌ Trade placement failed")
        
        # Try Example 2 with manual approach
        print("\n🔄 Example 2: Using the manual approach")
        print("Logging in and placing a trade for 2 contracts of E-mini S&P 500...")
        
        # Login
        bulenox = login_bulenox_ai(debug=True)
        
        if bulenox:
            try:
                # Navigate to trading
                bulenox.navigate_to_trading()
                
                # Search for symbol
                bulenox.search_symbol("ES")  # E-mini S&P 500
                
                # Place trade manually
                success = bulenox.place_trade(
                    symbol="ES",
                    side="buy",
                    quantity=2,  # 2 contracts
                    stop_loss=None,
                    take_profit=None
                )
                
                if success:
                    print("✅ Trade placed successfully!")
                else:
                    print("❌ Trade placement failed")
                    
            finally:
                # Keep browser open for inspection
                print("\n🔍 Browser will remain open for manual inspection")
                print("Press Enter to close the browser and exit")
                input()
                bulenox.close()


if __name__ == "__main__":
    example_futures_trade()