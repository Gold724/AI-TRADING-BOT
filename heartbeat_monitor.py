# heartbeat_monitor.py

import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "heartbeat_monitor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('heartbeat_monitor')

# Load environment variables
load_dotenv()

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

# Slack notification (optional)
try:
    from slack_reporter import send_slack_notification
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("Slack reporter not available. Notifications will be logged only.")

def read_heartbeat_status():
    """
    Read the current heartbeat status from the status file
    
    Returns:
        dict: Status information including status message, timestamp, and session_active flag
    """
    try:
        if not os.path.exists(HEARTBEAT_STATUS_FILE):
            logger.warning(f"Heartbeat status file not found: {HEARTBEAT_STATUS_FILE}")
            return {
                "status": "[UNKNOWN] Unknown - No status file found",
                "timestamp": datetime.now().isoformat(),
                "session_active": False,
                "file_exists": False
            }
        
        with open(HEARTBEAT_STATUS_FILE, 'r') as f:
            lines = f.read().strip().split('\n')
            
            status_data = {
                "status": lines[0] if len(lines) >= 1 else "[UNKNOWN] Unknown",
                "timestamp": lines[1] if len(lines) >= 2 else datetime.now().isoformat(),
                "session_active": False,
                "file_exists": True
            }
            
            # Parse session_active from JSON in third line if available
            if len(lines) >= 3:
                try:
                    session_data = json.loads(lines[2])  # Third line is index 2
                    if "session_active" in session_data:
                        status_data["session_active"] = session_data["session_active"]
                except (json.JSONDecodeError, IndexError):
                    # Fallback to checking status text
                    status_text = status_data["status"].lower()
                    if "login successful" in status_text or "trade executed" in status_text:
                        status_data["session_active"] = True
            
            return status_data
            
    except Exception as e:
        logger.error(f"Error reading heartbeat status: {e}")
        return {
            "status": f"[ERROR] Error reading status: {str(e)[:50]}...",
            "timestamp": datetime.now().isoformat(),
            "session_active": False,
            "file_exists": os.path.exists(HEARTBEAT_STATUS_FILE)
        }

def check_heartbeat_health(max_age_minutes=5):
    """
    Check if the heartbeat is healthy based on the status file age
    
    Args:
        max_age_minutes (int): Maximum age in minutes for the heartbeat to be considered healthy
        
    Returns:
        tuple: (is_healthy, status_data, age_minutes)
    """
    status_data = read_heartbeat_status()
    
    # Check if file exists
    if not status_data.get("file_exists", False):
        return False, status_data, None
    
    # Parse timestamp
    try:
        timestamp = datetime.fromisoformat(status_data["timestamp"])
        now = datetime.now()
        age = now - timestamp
        age_minutes = age.total_seconds() / 60
        
        # Check if heartbeat is too old
        is_healthy = age_minutes <= max_age_minutes
        
        # Add age information to status data
        status_data["age_minutes"] = age_minutes
        status_data["is_healthy"] = is_healthy
        
        return is_healthy, status_data, age_minutes
        
    except Exception as e:
        logger.error(f"Error checking heartbeat health: {e}")
        return False, status_data, None

def monitor_heartbeat(interval_seconds=60, max_age_minutes=5, notify=True, restart_cmd=None):
    """
    Continuously monitor the heartbeat status
    
    Args:
        interval_seconds (int): How often to check the heartbeat status
        max_age_minutes (int): Maximum age in minutes for the heartbeat to be considered healthy
        notify (bool): Whether to send notifications for status changes
        restart_cmd (str): Optional command to restart the heartbeat if it's unhealthy
    """
    logger.info(f"Starting heartbeat monitor (interval={interval_seconds}s, max_age={max_age_minutes}m)")
    
    last_status = None
    last_health = None
    consecutive_unhealthy = 0
    
    while True:
        try:
            # Check heartbeat health
            is_healthy, status_data, age_minutes = check_heartbeat_health(max_age_minutes)
            
            # Log status
            current_status = status_data["status"]
            if current_status != last_status:
                logger.info(f"Heartbeat status: {current_status}")
                last_status = current_status
            
            # Check for health changes
            if is_healthy != last_health:
                if is_healthy:
                    message = f"[OK] Heartbeat is now HEALTHY - Status: {current_status}"
                    logger.info(message)
                    consecutive_unhealthy = 0
                    if notify and SLACK_AVAILABLE:
                        send_slack_notification(message, notification_type="heartbeat_healthy")
                else:
                    message = f"[ERROR] Heartbeat is UNHEALTHY - Age: {age_minutes:.1f} minutes, Status: {current_status}"
                    logger.warning(message)
                    if notify and SLACK_AVAILABLE:
                        send_slack_notification(message, notification_type="heartbeat_unhealthy")
                
                last_health = is_healthy
            
            # Handle unhealthy heartbeat
            if not is_healthy:
                consecutive_unhealthy += 1
                
                # Log periodic warnings
                if consecutive_unhealthy % 5 == 0:
                    logger.warning(f"Heartbeat still unhealthy after {consecutive_unhealthy} checks")
                
                # Try to restart if command provided and multiple consecutive failures
                if restart_cmd and consecutive_unhealthy >= 3:
                    logger.warning(f"Attempting to restart heartbeat: {restart_cmd}")
                    try:
                        import subprocess
                        subprocess.Popen(restart_cmd, shell=True)
                        
                        if notify and SLACK_AVAILABLE:
                            send_slack_notification(
                                f"[RESTART] Attempting to restart heartbeat after {consecutive_unhealthy} unhealthy checks",
                                notification_type="heartbeat_restart"
                            )
                        
                        # Reset counter and wait longer to give restart time
                        consecutive_unhealthy = 0
                        time.sleep(interval_seconds * 2)
                        continue
                        
                    except Exception as e:
                        logger.error(f"Error restarting heartbeat: {e}")
            
            # Wait for next check
            time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("Heartbeat monitor stopped by user")
            break
            
        except Exception as e:
            logger.error(f"Error in heartbeat monitor: {e}")
            time.sleep(interval_seconds)

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Monitor the AI Trading Sentinel heartbeat")
    parser.add_argument(
        "--interval", "-i", type=int, default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--max-age", "-m", type=int, default=5,
        help="Maximum age in minutes for heartbeat to be considered healthy (default: 5)"
    )
    parser.add_argument(
        "--no-notify", "-n", action="store_true",
        help="Disable Slack notifications"
    )
    parser.add_argument(
        "--restart", "-r", type=str,
        help="Command to restart heartbeat if unhealthy (e.g., 'python heartbeat.py')"
    )
    parser.add_argument(
        "--check", "-c", action="store_true",
        help="Just check current status and exit"
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Just check current status if requested
    if args.check:
        is_healthy, status_data, age_minutes = check_heartbeat_health(args.max_age)
        print(f"Heartbeat Status: {status_data['status']}")
        print(f"Timestamp: {status_data['timestamp']}")
        if age_minutes is not None:
            print(f"Age: {age_minutes:.1f} minutes")
        print(f"Health: {'[OK] HEALTHY' if is_healthy else '[ERROR] UNHEALTHY'}")
        print(f"Session Active: {'[OK] Yes' if status_data.get('session_active', False) else '[ERROR] No'}")
        return
    
    # Start continuous monitoring
    monitor_heartbeat(
        interval_seconds=args.interval,
        max_age_minutes=args.max_age,
        notify=not args.no_notify,
        restart_cmd=args.restart
    )

if __name__ == "__main__":
    main()