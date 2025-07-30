import os
import sys
import json
import time
import logging
import datetime
import threading
import traceback
from typing import Dict, List, Any, Optional, Callable

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "auto_recovery.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("AUTO_RECOVERY")

class AutoRecoveryEngine:
    """Monitors and automatically recovers failed trading sessions."""
    
    def __init__(self, heartbeat_interval=60, max_failures=3, recovery_cooldown=300):
        self.heartbeat_interval = heartbeat_interval  # seconds
        self.max_failures = max_failures  # max consecutive failures before alerting
        self.recovery_cooldown = recovery_cooldown  # seconds between recovery attempts
        
        self.monitored_sessions = {}
        self.session_status = {}
        self.recovery_history = []
        
        self.heartbeat_file = os.path.join(log_dir, "heartbeat.log")
        self.status_file = os.path.join(log_dir, "recovery_status.json")
        self.history_file = os.path.join(log_dir, "recovery_history.json")
        
        self.screenshot_dir = os.path.join(log_dir, "crash_screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        self.monitor_thread = None
        self.running = False
        
        self.notification_callbacks = []
        
        logger.info("Auto Recovery Engine initialized")
        self.load_status()
        self.load_history()
    
    def load_status(self):
        """Load session status from file."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    self.session_status = json.load(f)
                logger.info(f"Loaded status for {len(self.session_status)} sessions")
        except Exception as e:
            logger.error(f"Error loading session status: {str(e)}")
            self.session_status = {}
    
    def save_status(self):
        """Save session status to file."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.session_status, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session status: {str(e)}")
    
    def load_history(self):
        """Load recovery history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.recovery_history = json.load(f)
                logger.info(f"Loaded {len(self.recovery_history)} recovery events from history")
        except Exception as e:
            logger.error(f"Error loading recovery history: {str(e)}")
            self.recovery_history = []
    
    def save_history(self):
        """Save recovery history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.recovery_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving recovery history: {str(e)}")
    
    def register_session(self, session_id, account_id, broker_id, 
                        recovery_func=None, health_check_func=None):
        """Register a session for monitoring.
        
        Args:
            session_id: Unique identifier for the session
            account_id: Account identifier
            broker_id: Broker identifier
            recovery_func: Function to call to recover the session
            health_check_func: Function to call to check session health
        """
        session_info = {
            "session_id": session_id,
            "account_id": account_id,
            "broker_id": broker_id,
            "recovery_func": recovery_func,
            "health_check_func": health_check_func,
            "registered_at": datetime.datetime.now().isoformat(),
            "last_heartbeat": datetime.datetime.now().isoformat(),
            "status": "healthy"
        }
        
        self.monitored_sessions[session_id] = session_info
        
        # Initialize status if not exists
        if session_id not in self.session_status:
            self.session_status[session_id] = {
                "status": "healthy",
                "failures": 0,
                "last_recovery": None,
                "recovery_count": 0
            }
        
        logger.info(f"Registered session {session_id} for monitoring")
        self.save_status()
        
        # Start monitoring thread if not already running
        if not self.running:
            self.start_monitoring()
        
        return True
    
    def unregister_session(self, session_id):
        """Unregister a session from monitoring."""
        if session_id in self.monitored_sessions:
            del self.monitored_sessions[session_id]
            logger.info(f"Unregistered session {session_id} from monitoring")
            return True
        
        logger.warning(f"Session {session_id} not found for unregistering")
        return False
    
    def update_heartbeat(self, session_id):
        """Update the heartbeat for a session."""
        if session_id in self.monitored_sessions:
            self.monitored_sessions[session_id]["last_heartbeat"] = datetime.datetime.now().isoformat()
            self.monitored_sessions[session_id]["status"] = "healthy"
            
            # Reset failure count if previously failing
            if self.session_status[session_id]["status"] != "healthy":
                self.session_status[session_id]["status"] = "healthy"
                self.session_status[session_id]["failures"] = 0
                self.save_status()
            
            # Log heartbeat
            with open(self.heartbeat_file, 'a') as f:
                f.write(f"{datetime.datetime.now().isoformat()},{session_id},healthy\n")
            
            return True
        
        logger.warning(f"Session {session_id} not found for heartbeat update")
        return False
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.running:
            logger.warning("Monitoring thread already running")
            return False
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Started monitoring thread")
        return True
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=self.heartbeat_interval * 2)
        
        logger.info("Stopped monitoring thread")
        return True
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_all_sessions()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(self.heartbeat_interval)
    
    def _check_all_sessions(self):
        """Check the health of all monitored sessions."""
        now = datetime.datetime.now()
        
        for session_id, session_info in list(self.monitored_sessions.items()):
            try:
                # Skip if in cooldown period after recovery
                if self.session_status[session_id]["last_recovery"]:
                    last_recovery = datetime.datetime.fromisoformat(self.session_status[session_id]["last_recovery"])
                    if (now - last_recovery).total_seconds() < self.recovery_cooldown:
                        logger.info(f"Session {session_id} in recovery cooldown, skipping check")
                        continue
                
                # Check heartbeat age
                last_heartbeat = datetime.datetime.fromisoformat(session_info["last_heartbeat"])
                heartbeat_age = (now - last_heartbeat).total_seconds()
                
                if heartbeat_age > self.heartbeat_interval * 2:
                    logger.warning(f"Session {session_id} heartbeat is stale ({heartbeat_age:.1f}s old)")
                    
                    # Check health if custom function provided
                    health_check_func = session_info.get("health_check_func")
                    is_healthy = True
                    
                    if health_check_func and callable(health_check_func):
                        try:
                            is_healthy = health_check_func(session_id)
                        except Exception as e:
                            logger.error(f"Error in health check for {session_id}: {str(e)}")
                            is_healthy = False
                    else:
                        # No health check function, assume unhealthy due to stale heartbeat
                        is_healthy = False
                    
                    if not is_healthy:
                        self._handle_session_failure(session_id, session_info)
                    else:
                        # Session is actually healthy despite stale heartbeat
                        self.update_heartbeat(session_id)
                
            except Exception as e:
                logger.error(f"Error checking session {session_id}: {str(e)}")
    
    def _handle_session_failure(self, session_id, session_info):
        """Handle a session failure."""
        # Update status
        self.session_status[session_id]["status"] = "failing"
        self.session_status[session_id]["failures"] += 1
        self.save_status()
        
        # Log failure
        with open(self.heartbeat_file, 'a') as f:
            f.write(f"{datetime.datetime.now().isoformat()},{session_id},failing,{self.session_status[session_id]['failures']}\n")
        
        logger.warning(f"Session {session_id} failure detected (count: {self.session_status[session_id]['failures']})")
        
        # Attempt recovery if max failures reached
        if self.session_status[session_id]["failures"] >= self.max_failures:
            self._recover_session(session_id, session_info)
    
    def _recover_session(self, session_id, session_info):
        """Attempt to recover a failed session."""
        logger.info(f"Attempting to recover session {session_id}")
        
        # Update status
        self.session_status[session_id]["status"] = "recovering"
        self.session_status[session_id]["last_recovery"] = datetime.datetime.now().isoformat()
        self.session_status[session_id]["recovery_count"] += 1
        self.save_status()
        
        # Create recovery event
        recovery_event = {
            "session_id": session_id,
            "account_id": session_info["account_id"],
            "broker_id": session_info["broker_id"],
            "timestamp": datetime.datetime.now().isoformat(),
            "failures": self.session_status[session_id]["failures"],
            "recovery_count": self.session_status[session_id]["recovery_count"],
            "success": False
        }
        
        # Call recovery function if provided
        recovery_func = session_info.get("recovery_func")
        recovery_success = False
        
        if recovery_func and callable(recovery_func):
            try:
                recovery_success = recovery_func(session_id)
                logger.info(f"Recovery function for {session_id} returned: {recovery_success}")
            except Exception as e:
                logger.error(f"Error in recovery function for {session_id}: {str(e)}")
                logger.error(traceback.format_exc())
                recovery_success = False
        else:
            logger.warning(f"No recovery function provided for {session_id}")
        
        # Update recovery event
        recovery_event["success"] = recovery_success
        self.recovery_history.append(recovery_event)
        self.save_history()
        
        # Update session status
        if recovery_success:
            self.session_status[session_id]["status"] = "recovered"
            self.session_status[session_id]["failures"] = 0
            logger.info(f"Session {session_id} recovered successfully")
        else:
            self.session_status[session_id]["status"] = "failed"
            logger.error(f"Failed to recover session {session_id}")
        
        self.save_status()
        
        # Send notifications
        self._send_recovery_notification(recovery_event)
        
        return recovery_success
    
    def _send_recovery_notification(self, recovery_event):
        """Send notifications about recovery events."""
        for callback in self.notification_callbacks:
            try:
                callback(recovery_event)
            except Exception as e:
                logger.error(f"Error in notification callback: {str(e)}")
    
    def add_notification_callback(self, callback):
        """Add a callback function for recovery notifications."""
        if callable(callback):
            self.notification_callbacks.append(callback)
            return True
        return False
    
    def get_session_status(self, session_id=None):
        """Get the status of a specific session or all sessions."""
        if session_id:
            return self.session_status.get(session_id)
        return self.session_status
    
    def get_recovery_history(self, limit=50):
        """Get the recovery history."""
        return self.recovery_history[-limit:] if limit > 0 else self.recovery_history

# Create a global instance of the recovery engine
recovery_engine = AutoRecoveryEngine()

# Example notification callbacks
def log_notification(recovery_event):
    """Log recovery events to a file."""
    log_file = os.path.join(log_dir, "recovery_notifications.log")
    with open(log_file, 'a') as f:
        f.write(f"{json.dumps(recovery_event)}\n")

def slack_notification(recovery_event):
    """Send recovery notifications to Slack."""
    # This is a placeholder - in a real implementation, this would use the Slack API
    logger.info(f"[SLACK] Recovery event: {recovery_event}")

# Register default notification callbacks
recovery_engine.add_notification_callback(log_notification)