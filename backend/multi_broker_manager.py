# O.R.I.G.I.N. Cloud Prime - Multi-Broker Manager
# Manages trading across multiple brokers (Exness, Binance, Bulenox)

import os
import json
import time
import uuid
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/multi_broker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("multi_broker")

class BrokerSession:
    """Represents a trading session with a specific broker"""
    
    def __init__(self, 
                 session_id: str,
                 broker_id: str,
                 account_id: str = None,
                 metadata: Dict[str, Any] = None):
        """Initialize a broker session
        
        Args:
            session_id: Unique identifier for the session
            broker_id: Identifier for the broker (e.g., 'exness', 'binance', 'bulenox')
            account_id: Optional account identifier
            metadata: Additional session metadata
        """
        self.session_id = session_id
        self.broker_id = broker_id.lower()
        self.account_id = account_id
        self.metadata = metadata or {}
        self.status = "initializing"
        self.created_at = datetime.now().isoformat()
        self.last_activity = time.time()
        self.trades = []
        self.driver = None  # Will hold the Selenium WebDriver instance
        self.js_helper = None  # Will hold the JSSeleniumHelper instance
        self.recovery_registered = False
        
        logger.info(f"Created broker session {session_id} for {broker_id}")
    
    def update_status(self, status: str) -> None:
        """Update the session status
        
        Args:
            status: New status (initializing, connected, trading, error, closed)
        """
        self.status = status
        self.last_activity = time.time()
        logger.info(f"Session {self.session_id} status updated to {status}")
    
    def add_trade(self, trade_data: Dict[str, Any]) -> str:
        """Add a trade to the session history
        
        Args:
            trade_data: Trade information
            
        Returns:
            Trade ID
        """
        trade_id = str(uuid.uuid4())
        trade = {
            "trade_id": trade_id,
            "session_id": self.session_id,
            "broker_id": self.broker_id,
            "timestamp": datetime.now().isoformat(),
            **trade_data
        }
        self.trades.append(trade)
        self.last_activity = time.time()
        logger.info(f"Added trade {trade_id} to session {self.session_id}")
        return trade_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary
        
        Returns:
            Session information as dictionary
        """
        return {
            "session_id": self.session_id,
            "broker_id": self.broker_id,
            "account_id": self.account_id,
            "status": self.status,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "trade_count": len(self.trades),
            "metadata": self.metadata
        }

class MultiBrokerManager:
    """Manages trading across multiple brokers"""
    
    def __init__(self, 
                 sessions_file: str = "broker_sessions.json",
                 trades_file: str = "broker_trades.json"):
        """Initialize the multi-broker manager
        
        Args:
            sessions_file: Path to the sessions storage file
            trades_file: Path to the trades storage file
        """
        self.sessions_file = sessions_file
        self.trades_file = trades_file
        self.sessions: Dict[str, BrokerSession] = {}
        self.lock = threading.Lock()
        
        # Load existing sessions and trades
        self._load_sessions()
        
        logger.info(f"Multi-Broker Manager initialized with {len(self.sessions)} sessions")
    
    def _load_sessions(self) -> None:
        """Load sessions from file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                
                for session_id, session_data in sessions_data.items():
                    # Create session objects from data
                    session = BrokerSession(
                        session_id=session_id,
                        broker_id=session_data["broker_id"],
                        account_id=session_data.get("account_id"),
                        metadata=session_data.get("metadata", {})
                    )
                    session.status = session_data.get("status", "unknown")
                    session.created_at = session_data.get("created_at", session.created_at)
                    session.last_activity = session_data.get("last_activity", time.time())
                    
                    self.sessions[session_id] = session
                
                logger.info(f"Loaded {len(self.sessions)} sessions from file")
                
                # Load trades if available
                if os.path.exists(self.trades_file):
                    with open(self.trades_file, 'r') as f:
                        trades_data = json.load(f)
                    
                    for session_id, trades in trades_data.items():
                        if session_id in self.sessions:
                            self.sessions[session_id].trades = trades
                    
                    logger.info(f"Loaded trades for {len(trades_data)} sessions")
        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
    
    def _save_sessions(self) -> None:
        """Save sessions to file"""
        try:
            sessions_data = {}
            for session_id, session in self.sessions.items():
                sessions_data[session_id] = session.to_dict()
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            
            logger.info(f"Saved {len(self.sessions)} sessions to file")
        except Exception as e:
            logger.error(f"Error saving sessions: {str(e)}")
    
    def _save_trades(self) -> None:
        """Save trades to file"""
        try:
            trades_data = {}
            for session_id, session in self.sessions.items():
                if session.trades:
                    trades_data[session_id] = session.trades
            
            with open(self.trades_file, 'w') as f:
                json.dump(trades_data, f, indent=2)
            
            logger.info(f"Saved trades for {len(trades_data)} sessions to file")
        except Exception as e:
            logger.error(f"Error saving trades: {str(e)}")
    
    def create_session(self, 
                      broker_id: str, 
                      account_id: str = None, 
                      metadata: Dict[str, Any] = None) -> str:
        """Create a new broker session
        
        Args:
            broker_id: Identifier for the broker
            account_id: Optional account identifier
            metadata: Additional session metadata
            
        Returns:
            Session ID
        """
        try:
            with self.lock:
                session_id = str(uuid.uuid4())
                session = BrokerSession(
                    session_id=session_id,
                    broker_id=broker_id,
                    account_id=account_id,
                    metadata=metadata
                )
                
                self.sessions[session_id] = session
                self._save_sessions()
                
                logger.info(f"Created new session {session_id} for broker {broker_id}")
                return session_id
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return ""
    
    def get_session(self, session_id: str) -> Optional[BrokerSession]:
        """Get a session by ID
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            BrokerSession if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def get_sessions_by_broker(self, broker_id: str) -> List[BrokerSession]:
        """Get all sessions for a specific broker
        
        Args:
            broker_id: Broker identifier
            
        Returns:
            List of BrokerSession objects
        """
        broker_id = broker_id.lower()
        return [s for s in self.sessions.values() if s.broker_id == broker_id]
    
    def get_sessions_by_account(self, account_id: str) -> List[BrokerSession]:
        """Get all sessions for a specific account
        
        Args:
            account_id: Account identifier
            
        Returns:
            List of BrokerSession objects
        """
        return [s for s in self.sessions.values() if s.account_id == account_id]
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update a session's status
        
        Args:
            session_id: Session ID to update
            status: New status
            
        Returns:
            Success status
        """
        try:
            with self.lock:
                if session_id in self.sessions:
                    self.sessions[session_id].update_status(status)
                    self._save_sessions()
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for status update")
                    return False
        except Exception as e:
            logger.error(f"Error updating session status: {str(e)}")
            return False
    
    def add_trade(self, session_id: str, trade_data: Dict[str, Any]) -> str:
        """Add a trade to a session
        
        Args:
            session_id: Session ID to add trade to
            trade_data: Trade information
            
        Returns:
            Trade ID if successful, empty string otherwise
        """
        try:
            with self.lock:
                if session_id in self.sessions:
                    trade_id = self.sessions[session_id].add_trade(trade_data)
                    self._save_trades()
                    return trade_id
                else:
                    logger.warning(f"Session {session_id} not found for adding trade")
                    return ""
        except Exception as e:
            logger.error(f"Error adding trade: {str(e)}")
            return ""
    
    def close_session(self, session_id: str) -> bool:
        """Close a broker session
        
        Args:
            session_id: Session ID to close
            
        Returns:
            Success status
        """
        try:
            with self.lock:
                if session_id in self.sessions:
                    # Update status to closed
                    self.sessions[session_id].update_status("closed")
                    
                    # Clean up Selenium driver if present
                    if self.sessions[session_id].driver:
                        try:
                            self.sessions[session_id].driver.quit()
                        except Exception as driver_e:
                            logger.warning(f"Error closing driver for session {session_id}: {str(driver_e)}")
                    
                    # Save before removing
                    self._save_sessions()
                    self._save_trades()
                    
                    # Keep the session in memory for history
                    # but mark it as closed
                    
                    logger.info(f"Closed session {session_id}")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for closing")
                    return False
        except Exception as e:
            logger.error(f"Error closing session: {str(e)}")
            return False
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get information about all sessions
        
        Returns:
            List of session information dictionaries
        """
        return [session.to_dict() for session in self.sessions.values()]
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about active sessions
        
        Returns:
            List of active session information dictionaries
        """
        return [session.to_dict() for session in self.sessions.values() 
                if session.status not in ["closed", "error"]]
    
    def get_trades(self, session_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trades for a session or all sessions
        
        Args:
            session_id: Optional session ID to filter trades
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        all_trades = []
        
        if session_id:
            # Get trades for specific session
            if session_id in self.sessions:
                all_trades = self.sessions[session_id].trades[-limit:] if limit > 0 else self.sessions[session_id].trades
        else:
            # Get trades for all sessions
            for session in self.sessions.values():
                all_trades.extend(session.trades)
            
            # Sort by timestamp (newest first) and limit
            all_trades.sort(key=lambda t: t.get("timestamp", ""), reverse=True)
            if limit > 0:
                all_trades = all_trades[:limit]
        
        return all_trades
    
    def register_with_recovery_engine(self, session_id: str, recovery_engine) -> bool:
        """Register a session with the auto-recovery engine
        
        Args:
            session_id: Session ID to register
            recovery_engine: AutoRecoveryEngine instance
            
        Returns:
            Success status
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for recovery registration")
                return False
            
            if session.recovery_registered:
                logger.warning(f"Session {session_id} already registered with recovery engine")
                return True
            
            # Define health check function
            def session_health_check():
                # Check if session is active and not too old
                if session.status in ["closed", "error"]:
                    return False
                
                # Check if last activity is recent (within 5 minutes)
                if time.time() - session.last_activity > 300:  # 5 minutes
                    return False
                
                # If driver exists, check if it's responsive
                if session.driver:
                    try:
                        # Try to get the current URL as a simple check
                        current_url = session.driver.current_url
                        return True
                    except Exception:
                        return False
                
                return True
            
            # Define recovery function
            def session_recovery():
                try:
                    # Close the existing driver if it exists
                    if session.driver:
                        try:
                            session.driver.quit()
                        except Exception:
                            pass
                    
                    # Mark session for reconnection
                    session.update_status("reconnecting")
                    
                    # In a real implementation, this would restart the browser
                    # and reconnect to the broker
                    # For now, we'll just simulate success
                    
                    # Update session status
                    session.update_status("connected")
                    return True
                except Exception as e:
                    logger.error(f"Error recovering session {session_id}: {str(e)}")
                    session.update_status("error")
                    return False
            
            # Register with recovery engine
            success = recovery_engine.register_session(
                session_id=session_id,
                broker_id=session.broker_id,
                health_check=session_health_check,
                recovery_func=session_recovery,
                metadata={
                    "account_id": session.account_id,
                    **session.metadata
                }
            )
            
            if success:
                session.recovery_registered = True
                logger.info(f"Registered session {session_id} with recovery engine")
            
            return success
        except Exception as e:
            logger.error(f"Error registering session with recovery engine: {str(e)}")
            return False
    
    def route_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route a trade to the appropriate broker session
        
        Args:
            trade_data: Trade information including broker_id or account_id
            
        Returns:
            Dictionary with result information
        """
        try:
            broker_id = trade_data.get("broker_id", "").lower()
            account_id = trade_data.get("account_id")
            
            target_session = None
            
            # Find the appropriate session
            if account_id:
                # Try to find by account ID first
                sessions = self.get_sessions_by_account(account_id)
                if sessions:
                    target_session = sessions[0]  # Use the first matching session
            
            if not target_session and broker_id:
                # Try to find by broker ID
                sessions = self.get_sessions_by_broker(broker_id)
                if sessions:
                    # Use the first active session for this broker
                    active_sessions = [s for s in sessions if s.status not in ["closed", "error"]]
                    if active_sessions:
                        target_session = active_sessions[0]
            
            if not target_session:
                return {
                    "success": False,
                    "error": f"No active session found for broker_id={broker_id}, account_id={account_id}"
                }
            
            # Add the trade to the session
            trade_id = self.add_trade(target_session.session_id, trade_data)
            
            if not trade_id:
                return {
                    "success": False,
                    "error": "Failed to add trade to session"
                }
            
            # In a real implementation, this would execute the trade
            # For now, we'll just simulate success
            
            return {
                "success": True,
                "trade_id": trade_id,
                "session_id": target_session.session_id,
                "broker_id": target_session.broker_id,
                "account_id": target_session.account_id,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error routing trade: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a global instance
broker_manager = MultiBrokerManager()

# Example usage
def create_example_sessions():
    """Create example broker sessions for testing"""
    # Create Exness session
    exness_session_id = broker_manager.create_session(
        broker_id="exness",
        account_id="EX123456",
        metadata={
            "currency": "USD",
            "leverage": 1000,
            "platform": "MT5"
        }
    )
    
    # Create Binance session
    binance_session_id = broker_manager.create_session(
        broker_id="binance",
        account_id="BI789012",
        metadata={
            "currency": "USDT",
            "futures": True,
            "platform": "Binance Futures"
        }
    )
    
    # Create Bulenox session
    bulenox_session_id = broker_manager.create_session(
        broker_id="bulenox",
        account_id="BU345678",
        metadata={
            "currency": "EUR",
            "leverage": 500,
            "platform": "Proprietary"
        }
    )
    
    # Update statuses
    broker_manager.update_session_status(exness_session_id, "connected")
    broker_manager.update_session_status(binance_session_id, "connected")
    broker_manager.update_session_status(bulenox_session_id, "connected")
    
    # Add example trades
    broker_manager.add_trade(exness_session_id, {
        "symbol": "EURUSD",
        "type": "BUY",
        "volume": 0.1,
        "price": 1.0876,
        "sl": 1.0826,
        "tp": 1.0926
    })
    
    broker_manager.add_trade(binance_session_id, {
        "symbol": "BTCUSDT",
        "type": "SELL",
        "volume": 0.01,
        "price": 42500.0,
        "sl": 43000.0,
        "tp": 41500.0
    })
    
    return [exness_session_id, binance_session_id, bulenox_session_id]