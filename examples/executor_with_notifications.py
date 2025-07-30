import os
import sys
import time
from datetime import datetime

# Add parent directory to path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the notification functions
from utils.executor_notifications import (
    notify_login_success,
    notify_login_failure,
    notify_trade_success,
    notify_trade_failure,
    notify_custom
)


class MockExecutor:
    """
    A mock executor class that simulates the behavior of a real trading executor
    but uses the notification system to send alerts.
    """
    
    def __init__(self, username=None, password=None, broker="bulenox"):
        self.username = username or os.getenv("BULENOX_USERNAME", "BX64883")
        self.password = password or os.getenv("BULENOX_PASSWORD", "password")
        self.broker = broker
        self.session_id = f"{self.username}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.driver = None
        self.logged_in = False
        
        print(f"Initialized {self.broker} executor with session ID: {self.session_id}")
    
    def login(self):
        """
        Simulate logging into the trading platform.
        """
        print(f"\nAttempting to log in to {self.broker} as {self.username}...")
        time.sleep(2)  # Simulate login process
        
        # In a real executor, this would be the result of the actual login attempt
        login_success = True
        
        if login_success:
            self.logged_in = True
            self.driver = "MOCK_DRIVER"  # In a real executor, this would be a Selenium WebDriver instance
            print(f"✅ Successfully logged in to {self.broker}")
            
            # Send login success notification
            notify_login_success(self.session_id)
            
            return True
        else:
            print(f"❌ Failed to log in to {self.broker}")
            
            # Send login failure notification
            notify_login_failure(self.session_id)
            
            return False
    
    def execute_trade(self, signal):
        """
        Simulate executing a trade based on the provided signal.
        
        Args:
            signal (dict): The trading signal with symbol, side, quantity, etc.
            
        Returns:
            bool: True if the trade was executed successfully, False otherwise
        """
        if not self.logged_in or not self.driver:
            print("❌ Cannot execute trade: Not logged in")
            return False
        
        symbol = signal.get("symbol", "EURUSD")
        side = signal.get("side", "buy")
        quantity = signal.get("quantity", 0.01)
        entry = signal.get("entry", 1.0750)  # In a real system, this would be the actual entry price
        
        print(f"\nExecuting trade: {symbol} {side.upper()} {quantity} @ {entry}...")
        time.sleep(3)  # Simulate trade execution
        
        # In a real executor, this would be determined by the actual trade result
        trade_success = True
        
        if trade_success:
            # In a real system, these would be the actual trade details
            profit = 120.50  # Example profit
            
            print(f"✅ Trade executed successfully: {symbol} {side.upper()} {quantity} @ {entry}")
            print(f"💰 Profit: ${profit}")
            
            # Send trade success notification
            notify_trade_success(
                symbol=symbol,
                entry=entry,
                direction=side,
                profit=profit,
                session_id=self.session_id
            )
            
            return True
        else:
            # In a real system, this would be the actual failure reason
            status = "Insufficient margin"
            
            print(f"❌ Trade execution failed: {symbol} {side.upper()} @ {entry}")
            print(f"🔁 Status: {status}")
            
            # Send trade failure notification
            notify_trade_failure(
                symbol=symbol,
                entry=entry,
                direction=side,
                status=status,
                session_id=self.session_id
            )
            
            return False
    
    def close(self):
        """
        Simulate closing the executor and cleaning up resources.
        """
        print(f"\nClosing {self.broker} executor session: {self.session_id}")
        
        if self.driver:
            # In a real executor, this would close the WebDriver
            self.driver = None
            self.logged_in = False
            
            # Send custom notification
            notify_custom(
                message=f"Session {self.session_id} closed successfully",
                session_id=self.session_id
            )
            
            print("✅ Session closed successfully")
            return True
        else:
            print("⚠️ No active session to close")
            return False


def run_demo():
    """
    Run a demonstration of the executor with notifications.
    """
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Using existing environment variables.")
    
    # Create and initialize the mock executor
    executor = MockExecutor()
    
    # Login to the trading platform
    if not executor.login():
        print("Demo aborted due to login failure")
        return
    
    # Execute a trade
    signal = {
        "symbol": "EURUSD",
        "side": "buy",
        "quantity": 0.01,
        "stopLoss": 1.0700,
        "takeProfit": 1.0800
    }
    executor.execute_trade(signal)
    
    # Execute another trade (this one could be configured to fail for demonstration)
    signal = {
        "symbol": "GBPJPY",
        "side": "sell",
        "quantity": 0.01,
        "stopLoss": 183.000,
        "takeProfit": 182.000
    }
    executor.execute_trade(signal)
    
    # Close the executor
    executor.close()
    
    print("\n✅ Demo completed successfully")


if __name__ == "__main__":
    print("=== AI Trading Sentinel - Executor with Notifications Example ===")
    run_demo()