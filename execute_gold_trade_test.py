import os
import time
from datetime import datetime

from dotenv import load_dotenv
from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade

# Load environment variables
load_dotenv()


def execute_gold_trade_test():
    """
    Execute a test gold trade on Bulenox platform
    This function will login to Bulenox, place a small gold trade, and close it for a small profit
    """
    print("\n" + "=" * 80)
    print("🤖 BULENOX GOLD TRADE TEST")
    print("=" * 80)
    
    # Record start time
    start_time = time.time()
    
    # Define trade parameters
    symbol = "XAUUSD"  # Gold
    side = "buy"  # Buy direction
    quantity = 1  # 1 contract (minimum size)
    
    # Get current gold price (this would normally come from market data)
    # For testing, we'll use approximate values
    current_price = 2400.00  # Example price
    
    # Set stop loss and take profit for a small $10 profit
    # Gold is approximately $100 per $1 price movement per contract
    # So for $10 profit we need about $0.10 price movement
    stop_loss = current_price - 0.20  # $20 risk
    take_profit = current_price + 0.10  # $10 profit target
    
    print(f"\n📊 Trade Parameters:")
    print(f"  Symbol: {symbol} (Gold)")
    print(f"  Direction: {side.upper()}")
    print(f"  Quantity: {quantity} contract")
    print(f"  Approximate Entry: ${current_price:.2f}")
    print(f"  Stop Loss: ${stop_loss:.2f}")
    print(f"  Take Profit: ${take_profit:.2f}")
    print(f"  Expected Profit: ~$10.00")
    
    # Place the trade
    print("\n🔄 Placing gold trade...")
    success = place_bulenox_trade(
        symbol=symbol,
        side=side,
        quantity=quantity,
        stop_loss=stop_loss,
        take_profit=take_profit,
        debug=True  # Enable screenshots
    )
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    if success:
        print(f"\n✅ Gold trade placed successfully in {execution_time:.2f} seconds!")
        print("\n🔔 Trade Information:")
        print("  - The trade has been placed with take profit set to close automatically")
        print("  - Expected profit: ~$10.00 when take profit is hit")
        print("  - The platform will automatically close the trade when the target is reached")
    else:
        print(f"\n❌ Failed to place gold trade after {execution_time:.2f} seconds")
        print("  Please check the screenshots in logs/screenshots directory for details")
    
    print("\n" + "=" * 80)
    print("Gold Trade Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    execute_gold_trade_test()