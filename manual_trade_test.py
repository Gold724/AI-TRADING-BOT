# manual_trade_test.py

import os
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from login_bulenox import login_bulenox_with_profile
from executor_bulenox import execute_trade
from slack_reporter import send_slack_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"manual_trade_test_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('manual_trade_test')

# Load environment variables
load_dotenv()

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs(os.path.join("logs", "screenshots"), exist_ok=True)

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

def update_heartbeat_status(status):
    """Update the heartbeat status file
    
    Args:
        status (str): The current status message
    """
    try:
        with open(HEARTBEAT_STATUS_FILE, 'w') as f:
            f.write(f"{status}\n{datetime.now().isoformat()}")
        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")

def run_manual_trade_test():
    """Run a manual trade test
    
    This function:
    1. Logs into Bulenox using a saved Chrome profile
    2. Executes a test trade
    3. Logs the result
    4. Updates the heartbeat status
    """
    # Generate a unique session ID for this run
    session_id = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logger.info(f"Starting manual trade test - Session: {session_id}")
    
    # Update status
    update_heartbeat_status("🔄 Initializing test session...")
    
    # Test signal
    test_signal = {
        "symbol": "GOLD",
        "direction": "buy",
        "entry_price": 2395.50,
        "take_profit": 2405.50,
        "stop_loss": 2387.50,
        "quantity": 1,
        # Add aliases for executor_bulenox.py compatibility
        "tp": 2405.50,
        "sl": 2387.50,
        "price": 2395.50
    }
    
    # Step 1: Login to Bulenox
    update_heartbeat_status("🔐 Logging into Bulenox...")
    logger.info("Attempting to login to Bulenox...")
    
    # Try login up to 3 times
    driver = None
    login_attempts = 0
    max_login_attempts = 3
    
    while driver is None and login_attempts < max_login_attempts:
        login_attempts += 1
        logger.info(f"Login attempt {login_attempts}/{max_login_attempts}")
        
        try:
            driver = login_bulenox_with_profile(debug=True)
            
            if driver:
                logger.info("Login successful")
                update_heartbeat_status("✅ Login successful")
                
                # Send Slack notification
                send_slack_notification(
                    message="Login successful",
                    message_type="login_success",
                    session_id=session_id
                )
            else:
                logger.error(f"Login attempt {login_attempts} failed")
                update_heartbeat_status(f"❌ Login failed. Retrying... ({login_attempts}/{max_login_attempts})")
                
                # Wait before retrying
                time.sleep(5)
        except Exception as e:
            logger.error(f"Exception during login attempt {login_attempts}: {e}")
            update_heartbeat_status(f"❌ Login error: {str(e)[:50]}...")
            time.sleep(5)
    
    # Check if login was successful
    if not driver:
        logger.error("All login attempts failed")
        update_heartbeat_status("❌ All login attempts failed. Test aborted.")
        
        # Send Slack notification
        send_slack_notification(
            message="All login attempts failed",
            message_type="login_fail",
            session_id=session_id
        )
        
        return
    
    # Step 2: Execute trade
    try:
        update_heartbeat_status(f"📈 Executing {test_signal['direction']} trade for {test_signal['symbol']}...")
        logger.info(f"Executing trade: {test_signal}")
        
        # Execute the trade
        trade_result = execute_trade(driver, test_signal, session_id=session_id, debug=True)
        logger.info(f"Trade execution result: {trade_result}")
        
        # Update status based on result
        if trade_result.get('success', False):
            update_heartbeat_status(f"✅ Trade executed: {test_signal['symbol']} {test_signal['direction']}")
            
            # Send Slack notification
            send_slack_notification(
                message=f"Trade executed: {test_signal['symbol']} {test_signal['direction']}",
                message_type="trade_executed",
                session_id=session_id,
                symbol=test_signal['symbol'],
                direction=test_signal['direction'],
                entry=test_signal['entry_price'],
                tp=test_signal['take_profit'],
                sl=test_signal['stop_loss']
            )
        else:
            error_msg = trade_result.get('error', 'Unknown error')
            update_heartbeat_status(f"❌ Trade failed: {error_msg[:50]}...")
            
            # Send Slack notification
            send_slack_notification(
                message=f"Trade failed: {test_signal['symbol']} {test_signal['direction']}",
                message_type="trade_failed",
                session_id=session_id,
                symbol=test_signal['symbol'],
                direction=test_signal['direction'],
                reason=error_msg
            )
    
    except Exception as e:
        logger.error(f"Exception during trade execution: {e}")
        update_heartbeat_status(f"❌ Trade error: {str(e)[:50]}...")
        
        # Send Slack notification
        send_slack_notification(
            message=f"Error during trade execution: {str(e)}",
            message_type="trade_failed",
            session_id=session_id,
            symbol=test_signal['symbol'],
            direction=test_signal['direction'],
            reason=str(e)
        )
    
    finally:
        # Close the browser
        logger.info("Closing browser...")
        update_heartbeat_status("🔄 Test completed. Closing browser...")
        
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
        
        update_heartbeat_status("✅ Test completed")

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        logger.warning(".env file not found. Creating default .env file...")
        
        with open(".env", "w") as f:
            f.write("# Bulenox Login Settings\n")
            f.write("BULENOX_USERNAME=your_username\n")
            f.write("BULENOX_PASSWORD=your_password\n")
            f.write("BULENOX_PROFILE_PATH=C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data\n")
            f.write("BULENOX_PROFILE_NAME=Profile 13\n\n")
            f.write("# Slack Notifications\n")
            f.write("SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL\n\n")
            f.write("# Debug Settings\n")
            f.write("DEBUG=true\n")
        
        logger.info("Created default .env file. Please update with your credentials.")
        print("⚠️ Created default .env file. Please update with your credentials before running again.")
    else:
        # Run the test
        run_manual_trade_test()