import os
import sys
import time
from datetime import datetime

# Add parent directory to path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Slack notification function
from utils.slack_notifications import send_slack_prophetic


def simulate_trading_with_notifications():
    """
    Simulate a trading session with Slack notifications for various events.
    This example demonstrates how to integrate Slack notifications into your trading code.
    """
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Using existing environment variables.")
    
    # Check if SLACK_WEBHOOK_URL is set
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url or webhook_url == "https://hooks.slack.com/services/YOUR_WEBHOOK_URL_HERE":
        print("❌ Error: SLACK_WEBHOOK_URL environment variable not set or using default value.")
        print("Please update your .env file with a valid Slack webhook URL.")
        return False
    
    # Generate a session ID (typically this would come from your trading system)
    session_id = f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"\n🔔 Starting simulated trading session: {session_id}")
    
    # 1. Simulate login
    print("\n📡 Attempting to log in to trading platform...")
    time.sleep(2)  # Simulate login process
    
    login_success = True  # In a real system, this would be the result of your login attempt
    
    if login_success:
        print("✅ Login successful")
        # Send login success notification
        send_slack_prophetic(
            message_type="login_success",
            session_id=session_id
        )
    else:
        print("❌ Login failed")
        # Send login failure notification
        send_slack_prophetic(
            message_type="login_fail",
            session_id=session_id
        )
        return False
    
    # 2. Simulate a successful trade
    print("\n📈 Executing trade: EURUSD BUY @ 1.0750...")
    time.sleep(3)  # Simulate trade execution
    
    # In a real system, these would be the actual trade details
    symbol = "EURUSD"
    entry = 1.0750
    direction = "buy"
    profit = 120.50
    
    print(f"✅ Trade executed successfully: {symbol} {direction.upper()} @ {entry}")
    print(f"💰 Profit: ${profit}")
    
    # Send profit notification
    send_slack_prophetic(
        message_type="profit",
        symbol=symbol,
        entry=entry,
        direction=direction,
        profit=profit,
        session_id=session_id
    )
    
    # 3. Simulate a failed trade
    print("\n📉 Executing trade: GBPJPY SELL @ 182.500...")
    time.sleep(2)  # Simulate trade execution
    
    # In a real system, these would be the actual trade details
    symbol = "GBPJPY"
    entry = 182.500
    direction = "sell"
    status = "Market closed"
    
    print(f"❌ Trade execution failed: {symbol} {direction.upper()} @ {entry}")
    print(f"🔁 Status: {status}")
    
    # Send failed trade notification
    send_slack_prophetic(
        message_type="fail",
        symbol=symbol,
        entry=entry,
        direction=direction,
        status=status,
        session_id=session_id
    )
    
    # 4. Send a custom message
    print("\n📊 Sending system status update...")
    
    # Send custom message
    send_slack_prophetic(
        message_type="System running at optimal capacity. All strategies active.",
        session_id=session_id
    )
    
    print("\n✅ Simulation completed successfully")
    return True


if __name__ == "__main__":
    print("=== AI Trading Sentinel - Slack Integration Example ===")
    simulate_trading_with_notifications()