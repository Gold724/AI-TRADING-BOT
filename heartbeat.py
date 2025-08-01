# heartbeat.py

import time
import uuid
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from executor_bulenox import execute_trade
from login_bulenox import login_bulenox_with_profile
from slack_reporter import send_slack_notification
from strategy_filter import validate_signal
from trae_signal_fetcher import get_next_signal

# Import GitHub integration
from utils.github_integration import check_for_updates, pull_updates, update_heartbeat_status as github_status_update

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"heartbeat_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('heartbeat')

# Load environment variables
load_dotenv()

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

def update_heartbeat_status(status, session_active=True):
    """
    Update the heartbeat status file with current status and timestamp
    
    Args:
        status (str): The current status message
        session_active (bool): Flag indicating if a trading session is active
    """
    try:
        timestamp = datetime.now().isoformat()
        status_data = {
            "status": status,
            "timestamp": timestamp,
            "session_active": session_active
        }
        
        # Write to heartbeat status file
        with open(HEARTBEAT_STATUS_FILE, 'w') as f:
            f.write(f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}")
            
        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")


def run_heartbeat(debug=False, check_github_updates=True):
    """
    Main function to run the trading sentinel heartbeat.
    Continuously polls for signals, validates them, logs into broker,
    executes trades, and sends notifications.
    
    Args:
        debug (bool): Enable debug mode with additional logging and screenshots
        check_github_updates (bool): Check for GitHub updates on startup and periodically
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.path.join("logs", "screenshots"), exist_ok=True)
    
    # Generate a unique session ID for this run
    session_id = str(uuid.uuid4())[:8]
    logger.info(f"Starting Sentinel HEARTBEAT Session: {session_id}")
    
    # Update heartbeat status
    update_heartbeat_status(f"🚀 Sentinel HEARTBEAT started - Session: {session_id}")
    
    # Send startup notification
    send_slack_notification(
        message=f"🚀 Sentinel HEARTBEAT started - Session: {session_id}",
        notification_type="startup",
        session_id=session_id
    )
    
    # Check for GitHub updates on startup if enabled
    if check_github_updates:
        try:
            logger.info("Checking for GitHub updates...")
            update_heartbeat_status("🔄 Checking for GitHub updates...")
            
            updates_available, details = check_for_updates()
            if updates_available:
                logger.info(f"GitHub updates available: {details}")
                update_heartbeat_status("⚠️ GitHub updates available")
                
                # Notify about available updates
                send_slack_notification(
                    message=f"⚠️ GitHub updates available for Sentinel:\n```{details}```",
                    notification_type="github_update",
                    session_id=session_id
                )
                
                # Auto-update if configured
                if os.getenv('AUTO_UPDATE_GITHUB', 'false').lower() == 'true':
                    logger.info("Auto-updating from GitHub...")
                    update_heartbeat_status("🔄 Auto-updating from GitHub...")
                    
                    success, result = pull_updates()
                    if success:
                        logger.info(f"GitHub auto-update successful: {result}")
                        update_heartbeat_status("✅ GitHub auto-update successful")
                        
                        # Notify about successful update
                        send_slack_notification(
                            message=f"✅ GitHub auto-update successful for Sentinel:\n```{result}```",
                            notification_type="github_update",
                            session_id=session_id
                        )
                        
                        # Restart the application if configured
                        if os.getenv('RESTART_AFTER_UPDATE', 'false').lower() == 'true':
                            logger.info("Restarting application after update...")
                            update_heartbeat_status("🔄 Restarting application after update...")
                            send_slack_notification(
                                message=f"🔄 Restarting Sentinel after GitHub update",
                                notification_type="restart",
                                session_id=session_id
                            )
                            
                            # Update GitHub status before restart
                            github_status_update("restarting", {"reason": "update applied"})
                            
                            # Exit with special code for wrapper script to handle restart
                            os._exit(42)
                    else:
                        logger.error(f"GitHub auto-update failed: {result}")
                        update_heartbeat_status("❌ GitHub auto-update failed")
                        
                        # Notify about failed update
                        send_slack_notification(
                            message=f"❌ GitHub auto-update failed for Sentinel:\n```{result}```",
                            notification_type="github_update_error",
                            session_id=session_id
                        )
            else:
                logger.info(f"No GitHub updates available: {details}")
                update_heartbeat_status("✅ No GitHub updates available")
        except Exception as e:
            logger.error(f"Error checking for GitHub updates: {e}")
            update_heartbeat_status(f"❌ Error checking for GitHub updates: {str(e)[:50]}...")
            
            # Notify about update check error
            send_slack_notification(
                message=f"❌ Error checking for GitHub updates: {str(e)}",
                notification_type="github_update_error",
                session_id=session_id
            )
    
    # Track active driver to avoid repeated logins
    active_driver = None
    last_login_time = None
    login_timeout = int(os.getenv('LOGIN_TIMEOUT_MINUTES', '30')) * 60  # Convert to seconds
    
    # Track GitHub update checks
    last_github_check_time = datetime.now()
    github_check_interval = int(os.getenv('GITHUB_CHECK_INTERVAL_MINUTES', '60')) * 60  # Convert to seconds
    
    while True:
        try:
            # Periodic GitHub update check if enabled
            if check_github_updates and (datetime.now() - last_github_check_time).total_seconds() >= github_check_interval:
                logger.info("Performing periodic GitHub update check...")
                update_heartbeat_status("🔄 Checking for GitHub updates...")
                
                try:
                    updates_available, details = check_for_updates()
                    if updates_available:
                        logger.info(f"GitHub updates available: {details}")
                        update_heartbeat_status("⚠️ GitHub updates available")
                        
                        # Notify about available updates
                        send_slack_notification(
                            message=f"⚠️ GitHub updates available for Sentinel:\n```{details}```",
                            notification_type="github_update",
                            session_id=session_id
                        )
                        
                        # Auto-update if configured
                        if os.getenv('AUTO_UPDATE_GITHUB', 'false').lower() == 'true':
                            logger.info("Auto-updating from GitHub...")
                            update_heartbeat_status("🔄 Auto-updating from GitHub...")
                            
                            success, result = pull_updates()
                            if success:
                                logger.info(f"GitHub auto-update successful: {result}")
                                update_heartbeat_status("✅ GitHub auto-update successful")
                                
                                # Notify about successful update
                                send_slack_notification(
                                    message=f"✅ GitHub auto-update successful for Sentinel:\n```{result}```",
                                    notification_type="github_update",
                                    session_id=session_id
                                )
                                
                                # Restart the application if configured
                                if os.getenv('RESTART_AFTER_UPDATE', 'false').lower() == 'true':
                                    logger.info("Restarting application after update...")
                                    update_heartbeat_status("🔄 Restarting application after update...")
                                    send_slack_notification(
                                        message=f"🔄 Restarting Sentinel after GitHub update",
                                        notification_type="restart",
                                        session_id=session_id
                                    )
                                    
                                    # Update GitHub status before restart
                                    github_status_update("restarting", {"reason": "update applied"})
                                    
                                    # Exit with special code for wrapper script to handle restart
                                    os._exit(42)
                            else:
                                logger.error(f"GitHub auto-update failed: {result}")
                                update_heartbeat_status("❌ GitHub auto-update failed")
                                
                                # Notify about failed update
                                send_slack_notification(
                                    message=f"❌ GitHub auto-update failed for Sentinel:\n```{result}```",
                                    notification_type="github_update_error",
                                    session_id=session_id
                                )
                    else:
                        logger.info(f"No GitHub updates available: {details}")
                        update_heartbeat_status("✅ No GitHub updates available")
                except Exception as e:
                    logger.error(f"Error checking for GitHub updates: {e}")
                    update_heartbeat_status(f"❌ Error checking for GitHub updates: {str(e)[:50]}...")
                    
                    # Notify about update check error
                    send_slack_notification(
                        message=f"❌ Error checking for GitHub updates: {str(e)}",
                        notification_type="github_update_error",
                        session_id=session_id
                    )
                
                # Update last check time
                last_github_check_time = datetime.now()
            
            # STEP 1: FETCH SIGNAL
            update_heartbeat_status("🔄 Waiting for signals...")
            signal = get_next_signal()
            if not signal:
                logger.info("No signal yet... waiting")
                time.sleep(int(os.getenv('POLLING_INTERVAL_SECONDS', '15')))
                continue
            
            logger.info(f"Received signal: {signal}")
            
            # STEP 2: VALIDATE STRATEGY
            update_heartbeat_status(f"🔍 Validating signal: {signal.get('symbol')} {signal.get('direction')}")
            if not validate_signal(signal):
                logger.warning("Signal rejected by strategy filter")
                update_heartbeat_status(f"🚫 Signal rejected: {signal.get('symbol')} {signal.get('direction')}")
                send_slack_notification(
                    message=f"🚫 Signal rejected: {signal.get('symbol')} ({signal.get('direction')})",
                    notification_type="signal_rejected",
                    session_id=session_id
                )
                continue
            
            logger.info("Signal passed strategy validation")
            
            # STEP 3: LOGIN TO BROKER (if needed)
            current_time = time.time()
            
            # Check if we need to login again (driver is None or login timed out)
            if (active_driver is None or 
                last_login_time is None or 
                (current_time - last_login_time) > login_timeout):
                
                # Close existing driver if it exists
                if active_driver:
                    try:
                        active_driver.quit()
                    except Exception as e:
                        logger.error(f"Error closing existing driver: {e}")
                    active_driver = None
                
                logger.info("Logging into Bulenox...")
                update_heartbeat_status("🔐 Logging into Bulenox...")
                active_driver = login_bulenox_with_profile(debug=debug)
                last_login_time = time.time()
                
                if not active_driver:
                    logger.error("Login failed, skipping this signal")
                    update_heartbeat_status("❌ Bulenox login failed - skipping signal")
                    send_slack_notification(
                        message="❌ Bulenox login failed - skipping signal",
                        notification_type="login_failed",
                        session_id=session_id
                    )
                    # Wait longer after a login failure
                    time.sleep(int(os.getenv('ERROR_WAIT_SECONDS', '60')))
                    continue
                
                logger.info("Login successful")
                update_heartbeat_status("✅ Bulenox login successful")
                send_slack_notification(
                    message="✅ Bulenox login successful",
                    notification_type="login_success",
                    session_id=session_id
                )
            
            # STEP 4: EXECUTE TRADE
            update_heartbeat_status(f"📈 Executing {signal.get('direction')} trade for {signal.get('symbol')}...")
            trade_result = execute_trade(active_driver, signal, session_id=session_id)
            logger.info(f"Trade execution result: {trade_result}")
            
            # STEP 5: SEND SLACK ALERT
            if trade_result.get('success', False):
                success_message = f"✅ Trade executed: {signal.get('symbol')} {signal.get('direction')}"
                update_heartbeat_status(success_message)
                
                message = (
                    f"🚀 Trade executed: {signal.get('symbol')} ({signal.get('direction')})\n"
                    f"Quantity: {signal.get('quantity')}\n"
                    f"Entry: {trade_result.get('entry_price')}\n"
                    f"TP: {signal.get('tp')}\n"
                    f"SL: {signal.get('sl')}"
                )
                send_slack_notification(
                    message=message,
                    notification_type="trade_executed",
                    session_id=session_id,
                    trade_data={
                        'symbol': signal.get('symbol'),
                        'direction': signal.get('direction'),
                        'quantity': signal.get('quantity'),
                        'entry_price': trade_result.get('entry_price'),
                        'tp': signal.get('tp'),
                        'sl': signal.get('sl')
                    }
                )
            else:
                error_msg = trade_result.get('error', 'Unknown error')
                update_heartbeat_status(f"❌ Trade failed: {error_msg[:50]}...")
                
                message = (
                    f"❌ Trade execution failed: {signal.get('symbol')} ({signal.get('direction')})\n"
                    f"Error: {error_msg}"
                )
                send_slack_notification(
                    message=message,
                    notification_type="trade_failed",
                    session_id=session_id
                )
            
            # STEP 6: LOOP OR PAUSE
            logger.info("Waiting for next signal...")
            update_heartbeat_status("🔄 Waiting for next signal...")
            time.sleep(int(os.getenv('POST_TRADE_WAIT_SECONDS', '20')))
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected, shutting down...")
            update_heartbeat_status("⚠️ Sentinel HEARTBEAT stopped (keyboard interrupt)", session_active=False)
            if active_driver:
                active_driver.quit()
            send_slack_notification(
                message=f"⚠️ Sentinel HEARTBEAT stopped (keyboard interrupt) - Session: {session_id}",
                notification_type="shutdown",
                session_id=session_id
            )
            break
            
        except Exception as e:
            logger.error(f"Exception in heartbeat: {e}", exc_info=True)
            update_heartbeat_status(f"🔥 Error in Sentinel: {str(e)[:50]}...")
            send_slack_notification(
                message=f"🔥 Error in Sentinel: {str(e)}",
                notification_type="error",
                session_id=session_id
            )
            if debug:
                import traceback
                traceback.print_exc()
            time.sleep(int(os.getenv('ERROR_WAIT_SECONDS', '30')))


if __name__ == "__main__":
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# Bulenox Login Settings\n")
            f.write("BULENOX_PROFILE_PATH=C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data\n")
            f.write("BULENOX_PROFILE_NAME=Profile 13\n\n")
            f.write("# Slack Notifications\n")
            f.write("SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL\n\n")
            f.write("# Trading Settings\n")
            f.write("DEFAULT_QUANTITY=0.01\n")
            f.write("MAX_QUANTITY=0.05\n\n")
            f.write("# Timing Settings\n")
            f.write("POLLING_INTERVAL_SECONDS=15\n")
            f.write("POST_TRADE_WAIT_SECONDS=20\n")
            f.write("ERROR_WAIT_SECONDS=30\n")
            f.write("LOGIN_TIMEOUT_MINUTES=30\n\n")
            f.write("# GitHub Integration Settings\n")
            f.write("GITHUB_USERNAME=your-username\n")
            f.write("GITHUB_PAT=your-personal-access-token\n")
            f.write("GITHUB_REPO=ai-trading-sentinel\n")
            f.write("GITHUB_CHECK_INTERVAL_MINUTES=60\n")
            f.write("AUTO_UPDATE_GITHUB=false\n")
            f.write("RESTART_AFTER_UPDATE=false\n")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Heartbeat')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-github', action='store_true', help='Disable GitHub update checks')
    args = parser.parse_args()
    
    # Run the heartbeat
    run_heartbeat(debug=args.debug, check_github_updates=not args.no_github)