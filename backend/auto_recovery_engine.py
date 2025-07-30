# O.R.I.G.I.N. Cloud Prime - Auto Recovery Engine
# Monitors and automatically recovers failed broker sessions

import os
import json
import time
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/auto_recovery.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auto_recovery")

class AutoRecoveryEngine:
    """Monitors and automatically recovers failed broker sessions"""
    
    def __init__(self, 
                 status_file: str = "recovery_status.json",
                 history_file: str = "recovery_history.json",
                 heartbeat_interval: int = 30,
                 max_failures: int = 3,
                 recovery_dir: str = "recovery"):
        """Initialize the auto recovery engine
        
        Args:
            status_file: Path to the recovery status file
            history_file: Path to the recovery history file
            heartbeat_interval: Interval in seconds to check session health
            max_failures: Maximum number of failures before recovery
            recovery_dir: Directory to store recovery artifacts
        """
        self.status_file = status_file
        self.history_file = history_file
        self.heartbeat_interval = heartbeat_interval
        self.max_failures = max_failures
        self.recovery_dir = recovery_dir
        
        # Create recovery directory if it doesn't exist
        os.makedirs(self.recovery_dir, exist_ok=True)
        
        # Initialize session tracking
        self.sessions = {}  # session_id -> session_info
        self.recovery_history = []
        self.notification_callbacks = []
        
        # Threading
        self.monitor_thread = None
        self.running = False
        self.lock = threading.Lock()
        
        # Load existing status and history
        self._load_status()
        self._load_history()
        
        logger.info(f"Auto Recovery Engine initialized with {len(self.sessions)} sessions")
    
    def _load_status(self) -> None:
        """Load session status from file"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    self.sessions = json.load(f)
                logger.info(f"Loaded {len(self.sessions)} sessions from status file")
        except Exception as e:
            logger.error(f"Error loading recovery status: {str(e)}")
    
    def _save_status(self) -> None:
        """Save session status to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving recovery status: {str(e)}")
    
    def _load_history(self) -> None:
        """Load recovery history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.recovery_history = json.load(f)
                logger.info(f"Loaded {len(self.recovery_history)} recovery events from history file")
        except Exception as e:
            logger.error(f"Error loading recovery history: {str(e)}")
    
    def _save_history(self) -> None:
        """Save recovery history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.recovery_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving recovery history: {str(e)}")
    
    def register_session(self, 
                        session_id: str, 
                        broker_id: str, 
                        health_check: Callable[[], bool],
                        recovery_func: Callable[[], bool],
                        metadata: Dict[str, Any] = None) -> bool:
        """Register a new session for monitoring
        
        Args:
            session_id: Unique identifier for the session
            broker_id: Identifier for the broker
            health_check: Function to check if session is healthy
            recovery_func: Function to recover the session
            metadata: Additional session metadata
            
        Returns:
            Success status
        """
        try:
            with self.lock:
                # Create session info
                session_info = {
                    "session_id": session_id,
                    "broker_id": broker_id,
                    "status": "healthy",
                    "last_heartbeat": time.time(),
                    "failure_count": 0,
                    "registered_at": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }
                
                # Store callable functions separately (can't be JSON serialized)
                self.sessions[session_id] = session_info
                setattr(self, f"health_check_{session_id}", health_check)
                setattr(self, f"recovery_func_{session_id}", recovery_func)
                
                # Save status
                self._save_status()
                
                # Start monitoring if not already running
                if not self.running:
                    self.start_monitoring()
                
                logger.info(f"Registered session {session_id} for broker {broker_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error registering session {session_id}: {str(e)}")
            return False
    
    def unregister_session(self, session_id: str) -> bool:
        """Unregister a session from monitoring
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Success status
        """
        try:
            with self.lock:
                if session_id in self.sessions:
                    del self.sessions[session_id]
                    
                    # Remove callable functions
                    if hasattr(self, f"health_check_{session_id}"):
                        delattr(self, f"health_check_{session_id}")
                    if hasattr(self, f"recovery_func_{session_id}"):
                        delattr(self, f"recovery_func_{session_id}")
                    
                    # Save status
                    self._save_status()
                    
                    logger.info(f"Unregistered session {session_id}")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for unregistration")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unregistering session {session_id}: {str(e)}")
            return False
    
    def update_heartbeat(self, session_id: str) -> bool:
        """Update the heartbeat for a session
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Success status
        """
        try:
            with self.lock:
                if session_id in self.sessions:
                    self.sessions[session_id]["last_heartbeat"] = time.time()
                    
                    # If session was failing, reset it to healthy
                    if self.sessions[session_id]["status"] == "failing":
                        self.sessions[session_id]["status"] = "healthy"
                        self.sessions[session_id]["failure_count"] = 0
                        logger.info(f"Session {session_id} recovered automatically")
                    
                    # Save status periodically (not on every heartbeat to reduce I/O)
                    if time.time() % 60 < 1:  # Save roughly once per minute
                        self._save_status()
                    
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for heartbeat update")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating heartbeat for session {session_id}: {str(e)}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start the monitoring thread
        
        Returns:
            Success status
        """
        try:
            if not self.running:
                self.running = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
                logger.info("Started monitoring thread")
                return True
            else:
                logger.warning("Monitoring thread already running")
                return False
                
        except Exception as e:
            logger.error(f"Error starting monitoring thread: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop the monitoring thread
        
        Returns:
            Success status
        """
        try:
            if self.running:
                self.running = False
                if self.monitor_thread:
                    self.monitor_thread.join(timeout=5)
                logger.info("Stopped monitoring thread")
                return True
            else:
                logger.warning("Monitoring thread not running")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping monitoring thread: {str(e)}")
            return False
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("Monitoring loop started")
        
        while self.running:
            try:
                # Check each session
                with self.lock:
                    for session_id, session_info in list(self.sessions.items()):
                        self._check_session(session_id, session_info)
                
                # Sleep until next check
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Sleep briefly before retrying
        
        logger.info("Monitoring loop stopped")
    
    def _check_session(self, session_id: str, session_info: Dict[str, Any]) -> None:
        """Check the health of a session
        
        Args:
            session_id: Unique identifier for the session
            session_info: Session information dictionary
        """
        try:
            # Check heartbeat age
            current_time = time.time()
            heartbeat_age = current_time - session_info["last_heartbeat"]
            
            # If heartbeat is too old, check session health
            if heartbeat_age > self.heartbeat_interval * 2:
                logger.warning(f"Session {session_id} heartbeat is {heartbeat_age:.1f}s old, checking health")
                
                # Get health check function
                health_check = getattr(self, f"health_check_{session_id}", None)
                if health_check and callable(health_check):
                    # Check health
                    is_healthy = False
                    try:
                        is_healthy = health_check()
                    except Exception as e:
                        logger.error(f"Health check failed for session {session_id}: {str(e)}")
                    
                    if not is_healthy:
                        # Increment failure count
                        session_info["failure_count"] += 1
                        session_info["status"] = "failing"
                        session_info["last_failure"] = datetime.now().isoformat()
                        
                        logger.warning(f"Session {session_id} is unhealthy (failure {session_info['failure_count']}/{self.max_failures})")
                        
                        # If max failures reached, attempt recovery
                        if session_info["failure_count"] >= self.max_failures:
                            self._recover_session(session_id, session_info)
                    else:
                        # Reset failure count if healthy
                        if session_info["status"] == "failing":
                            session_info["status"] = "healthy"
                            session_info["failure_count"] = 0
                            logger.info(f"Session {session_id} is healthy again")
                else:
                    logger.error(f"Health check function not found for session {session_id}")
            
            # Save status periodically
            if current_time % 60 < 1:  # Save roughly once per minute
                self._save_status()
                
        except Exception as e:
            logger.error(f"Error checking session {session_id}: {str(e)}")
    
    def _recover_session(self, session_id: str, session_info: Dict[str, Any]) -> None:
        """Attempt to recover a failed session
        
        Args:
            session_id: Unique identifier for the session
            session_info: Session information dictionary
        """
        try:
            logger.info(f"Attempting to recover session {session_id}")
            
            # Create recovery event
            recovery_id = str(uuid.uuid4())
            recovery_event = {
                "recovery_id": recovery_id,
                "session_id": session_id,
                "broker_id": session_info["broker_id"],
                "timestamp": datetime.now().isoformat(),
                "failure_count": session_info["failure_count"],
                "status": "in_progress",
                "metadata": session_info.get("metadata", {})
            }
            
            # Get recovery function
            recovery_func = getattr(self, f"recovery_func_{session_id}", None)
            if recovery_func and callable(recovery_func):
                # Attempt recovery
                success = False
                error_message = ""
                try:
                    success = recovery_func()
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Recovery function failed for session {session_id}: {error_message}")
                
                # Update session and recovery event based on result
                if success:
                    self._recovery_success(session_id, session_info, recovery_event)
                else:
                    self._recovery_failure(session_id, session_info, recovery_event, error_message)
            else:
                logger.error(f"Recovery function not found for session {session_id}")
                recovery_event["status"] = "failed"
                recovery_event["error"] = "Recovery function not found"
                self.recovery_history.append(recovery_event)
            
            # Save status and history
            self._save_status()
            self._save_history()
            
            # Send notifications
            self._send_notifications(recovery_event)
                
        except Exception as e:
            logger.error(f"Error recovering session {session_id}: {str(e)}")
    
    def _recovery_success(self, session_id: str, session_info: Dict[str, Any], recovery_event: Dict[str, Any]) -> None:
        """Handle successful session recovery
        
        Args:
            session_id: Unique identifier for the session
            session_info: Session information dictionary
            recovery_event: Recovery event dictionary
        """
        # Update session
        session_info["status"] = "healthy"
        session_info["failure_count"] = 0
        session_info["last_heartbeat"] = time.time()
        session_info["last_recovery"] = datetime.now().isoformat()
        
        # Update recovery event
        recovery_event["status"] = "success"
        recovery_event["completed_at"] = datetime.now().isoformat()
        
        # Add to history
        self.recovery_history.append(recovery_event)
        
        logger.info(f"Successfully recovered session {session_id}")
    
    def _recovery_failure(self, session_id: str, session_info: Dict[str, Any], recovery_event: Dict[str, Any], error_message: str) -> None:
        """Handle failed session recovery
        
        Args:
            session_id: Unique identifier for the session
            session_info: Session information dictionary
            recovery_event: Recovery event dictionary
            error_message: Error message from recovery attempt
        """
        # Update session
        session_info["status"] = "failed"
        session_info["last_recovery_attempt"] = datetime.now().isoformat()
        
        # Update recovery event
        recovery_event["status"] = "failed"
        recovery_event["error"] = error_message
        recovery_event["completed_at"] = datetime.now().isoformat()
        
        # Add to history
        self.recovery_history.append(recovery_event)
        
        logger.error(f"Failed to recover session {session_id}: {error_message}")
    
    def _send_notifications(self, recovery_event: Dict[str, Any]) -> None:
        """Send notifications about a recovery event
        
        Args:
            recovery_event: Recovery event dictionary
        """
        try:
            for callback in self.notification_callbacks:
                try:
                    callback(recovery_event)
                except Exception as e:
                    logger.error(f"Error in notification callback: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
    
    def add_notification_callback(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Add a notification callback
        
        Args:
            callback: Function to call with recovery events
            
        Returns:
            Success status
        """
        try:
            if callable(callback):
                self.notification_callbacks.append(callback)
                logger.info(f"Added notification callback {callback.__name__}")
                return True
            else:
                logger.error("Notification callback is not callable")
                return False
        except Exception as e:
            logger.error(f"Error adding notification callback: {str(e)}")
            return False
    
    def get_session_status(self, session_id: str = None) -> Dict[str, Any]:
        """Get the status of sessions
        
        Args:
            session_id: Optional specific session to get status for
            
        Returns:
            Dictionary with session status
        """
        try:
            with self.lock:
                if session_id:
                    if session_id in self.sessions:
                        return self.sessions[session_id].copy()
                    else:
                        return {"error": f"Session {session_id} not found"}
                else:
                    return {k: v.copy() for k, v in self.sessions.items()}
        except Exception as e:
            logger.error(f"Error getting session status: {str(e)}")
            return {"error": str(e)}
    
    def get_recovery_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the recovery history
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recovery events
        """
        try:
            return self.recovery_history[-limit:] if limit > 0 else self.recovery_history.copy()
        except Exception as e:
            logger.error(f"Error getting recovery history: {str(e)}")
            return []

# Create a global instance
recovery_engine = AutoRecoveryEngine()

# Example notification callbacks
def log_notification(recovery_event: Dict[str, Any]) -> None:
    """Log a recovery event"""
    status = recovery_event["status"]
    session_id = recovery_event["session_id"]
    broker_id = recovery_event["broker_id"]
    
    if status == "success":
        logger.info(f"NOTIFICATION: Successfully recovered session {session_id} for broker {broker_id}")
    else:
        error = recovery_event.get("error", "Unknown error")
        logger.error(f"NOTIFICATION: Failed to recover session {session_id} for broker {broker_id}: {error}")

def slack_notification(recovery_event: Dict[str, Any]) -> None:
    """Send a Slack notification about a recovery event"""
    # This is a placeholder for actual Slack integration
    status = recovery_event["status"]
    session_id = recovery_event["session_id"]
    broker_id = recovery_event["broker_id"]
    
    message = f"Recovery event for {broker_id} (session {session_id}): {status}"
    if status == "failed" and "error" in recovery_event:
        message += f" - Error: {recovery_event['error']}"
    
    logger.info(f"SLACK: {message}")
    # In a real implementation, this would send to Slack
    # requests.post(slack_webhook_url, json={"text": message})

# Register example notification callbacks
recovery_engine.add_notification_callback(log_notification)
# Uncomment to enable Slack notifications
# recovery_engine.add_notification_callback(slack_notification)