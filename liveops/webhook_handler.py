import os
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from flask import Flask, request, jsonify

class WebhookHandler:
    """Handler for webhook-based signal reception.
    
    This class provides a Flask-based webhook server for receiving trading signals
    from external sources like Tremius, Trae.ai, or other signal providers.
    """
    
    def __init__(self, 
                 port: int = 5000, 
                 signals_dir: str = "data",
                 signal_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Initialize the webhook handler.
        
        Args:
            port (int, optional): Port to listen on. Defaults to 5000.
            signals_dir (str, optional): Directory for storing signals. Defaults to "data".
            signal_callback (Optional[Callable], optional): Callback function for processing signals.
                Defaults to None.
        """
        self.logger = logging.getLogger("trae.webhook_handler")
        self.port = port
        self.signals_dir = signals_dir
        self.signal_callback = signal_callback
        self.app = Flask("trae_webhook")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        self.server_thread = None
        self.running = False
        
        # Ensure signals directory exists
        os.makedirs(signals_dir, exist_ok=True)
        
        # Set up routes
        self._setup_routes()
        
        self.logger.info(f"Webhook handler initialized on port {port}")
    
    def _setup_routes(self):
        """Set up Flask routes."""
        @self.app.route("/signal", methods=["POST"])
        def receive_signal():
            # Verify webhook secret if provided
            if self.webhook_secret:
                auth_header = request.headers.get("Authorization", "")
                if not auth_header or auth_header != f"Bearer {self.webhook_secret}":
                    self.logger.warning("Unauthorized webhook access attempt")
                    return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
            # Process signal
            try:
                signal_data = request.json
                self.logger.info(f"Received signal: {signal_data}")
                
                # Add timestamp and unique ID if not present
                if "timestamp" not in signal_data:
                    signal_data["timestamp"] = datetime.now().isoformat()
                if "id" not in signal_data:
                    signal_data["id"] = f"{datetime.now().timestamp()}-{hash(json.dumps(signal_data))}"
                
                # Save signal to file
                self._save_signal(signal_data)
                
                # Call callback if provided
                if self.signal_callback:
                    try:
                        self.signal_callback(signal_data)
                    except Exception as e:
                        self.logger.error(f"Error in signal callback: {e}")
                
                return jsonify({"status": "success", "message": "Signal received"})
            except Exception as e:
                self.logger.error(f"Error processing webhook signal: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route("/health", methods=["GET"])
        def health_check():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })
    
    def _save_signal(self, signal_data: Dict[str, Any]):
        """Save signal data to file.
        
        Args:
            signal_data (Dict[str, Any]): Signal data to save
        """
        try:
            signals_file = os.path.join(self.signals_dir, "incoming_signals.json")
            
            with open(signals_file, "a") as f:
                f.write(json.dumps(signal_data) + "\n")
                
            self.logger.debug(f"Saved signal to {signals_file}")
        except Exception as e:
            self.logger.error(f"Error saving signal: {e}")
    
    def start(self):
        """Start the webhook server.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Webhook server already running")
            return False
        
        try:
            self.running = True
            self.server_thread = threading.Thread(
                target=lambda: self.app.run(
                    host="0.0.0.0", 
                    port=self.port, 
                    debug=False,
                    use_reloader=False
                ),
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"Webhook server started on port {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting webhook server: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the webhook server.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Webhook server not running")
            return False
        
        try:
            # Flask doesn't have a clean shutdown mechanism in this context
            # We'll just mark it as not running
            self.running = False
            self.logger.info("Webhook server stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping webhook server: {e}")
            return False
    
    def get_pending_signals(self) -> List[Dict[str, Any]]:
        """Get pending signals from file.
        
        Returns:
            List[Dict[str, Any]]: List of pending signals
        """
        signals = []
        signals_file = os.path.join(self.signals_dir, "incoming_signals.json")
        
        if os.path.exists(signals_file):
            try:
                with open(signals_file, "r") as f:
                    for line in f:
                        try:
                            signal = json.loads(line.strip())
                            signals.append(signal)
                        except json.JSONDecodeError:
                            self.logger.warning(f"Invalid JSON in signals file: {line}")
            except Exception as e:
                self.logger.error(f"Error reading signals file: {e}")
        
        return signals
    
    def clear_pending_signals(self):
        """Clear pending signals file.
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        signals_file = os.path.join(self.signals_dir, "incoming_signals.json")
        
        try:
            with open(signals_file, "w") as f:
                pass
            
            self.logger.debug("Cleared pending signals")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing pending signals: {e}")
            return False