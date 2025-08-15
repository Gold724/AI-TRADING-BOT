import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

class SignalProcessor:
    """Processor for trading signals from various sources.
    
    This class handles the processing of trading signals from different sources
    (webhook, file, Tremius, Trae.ai) and prepares them for execution.
    """
    
    def __init__(self, 
                 signals_dir: str = "data",
                 process_callback: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None):
        """Initialize the signal processor.
        
        Args:
            signals_dir (str, optional): Directory for storing signals. Defaults to "data".
            process_callback (Optional[Callable], optional): Callback function for processing signals.
                Defaults to None.
        """
        self.logger = logging.getLogger("trae.signal_processor")
        self.signals_dir = signals_dir
        self.process_callback = process_callback
        
        # Ensure signals directory exists
        os.makedirs(signals_dir, exist_ok=True)
        
        # Create necessary files if they don't exist
        self._initialize_files()
        
        self.logger.info("Signal processor initialized")
    
    def _initialize_files(self):
        """Initialize necessary files."""
        files = [
            "incoming_signals.json",
            "processed_signals.json",
            "failed_signals.json"
        ]
        
        for file in files:
            file_path = os.path.join(self.signals_dir, file)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    if file == "processed_signals.json":
                        f.write("[]")
                    else:
                        pass  # Create empty file
    
    def process_pending_signals(self) -> int:
        """Process all pending signals.
        
        Returns:
            int: Number of signals processed
        """
        signals_file = os.path.join(self.signals_dir, "incoming_signals.json")
        processed_file = os.path.join(self.signals_dir, "processed_signals.json")
        failed_file = os.path.join(self.signals_dir, "failed_signals.json")
        
        # Load processed signal IDs
        try:
            with open(processed_file, "r") as f:
                processed_signals = json.load(f)
        except json.JSONDecodeError:
            processed_signals = []
        
        # Get processed signal IDs
        processed_ids = [p.get("id") for p in processed_signals]
        
        # Check for new signals
        count = 0
        new_processed = []
        failed_signals = []
        
        if os.path.exists(signals_file):
            pending_signals = []
            
            # Read all pending signals
            with open(signals_file, "r") as f:
                for line in f:
                    try:
                        signal = json.loads(line.strip())
                        pending_signals.append(signal)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid JSON in signals file: {line}")
            
            # Clear the signals file
            with open(signals_file, "w") as f:
                pass
            
            # Process each signal
            for signal in pending_signals:
                try:
                    signal_id = signal.get("id", str(hash(json.dumps(signal))))
                    
                    # Skip already processed signals
                    if signal_id in processed_ids:
                        continue
                    
                    # Normalize signal format
                    signal = self._normalize_signal(signal)
                    
                    # Process the signal
                    self.logger.info(f"Processing signal: {signal_id}")
                    
                    result = None
                    if self.process_callback:
                        result = self.process_callback(signal)
                    
                    # Record processed signal
                    processed_record = {
                        "id": signal_id,
                        "timestamp": datetime.now().isoformat(),
                        "signal": signal,
                        "result": result
                    }
                    new_processed.append(processed_record)
                    count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing signal: {e}")
                    failed_signals.append({
                        "timestamp": datetime.now().isoformat(),
                        "signal": signal,
                        "error": str(e)
                    })
        
        # Update processed signals file
        if new_processed:
            processed_signals.extend(new_processed)
            with open(processed_file, "w") as f:
                json.dump(processed_signals, f, indent=2)
        
        # Update failed signals file
        if failed_signals:
            with open(failed_file, "a") as f:
                for failed in failed_signals:
                    f.write(json.dumps(failed) + "\n")
        
        return count
    
    def _normalize_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize signal format from different sources.
        
        Args:
            signal (Dict[str, Any]): Original signal
            
        Returns:
            Dict[str, Any]: Normalized signal
        """
        normalized = signal.copy()
        
        # Ensure required fields exist
        if "timestamp" not in normalized:
            normalized["timestamp"] = datetime.now().isoformat()
        
        if "id" not in normalized:
            normalized["id"] = f"{datetime.now().timestamp()}-{hash(json.dumps(signal))}"
        
        # Normalize symbol format
        if "symbol" in normalized:
            normalized["symbol"] = normalized["symbol"].upper()
        
        # Normalize action/direction
        if "action" in normalized and "direction" not in normalized:
            action = normalized["action"].upper()
            if action in ["BUY", "LONG"]:
                normalized["direction"] = "BUY"
            elif action in ["SELL", "SHORT"]:
                normalized["direction"] = "SELL"
            else:
                normalized["direction"] = action
        
        # Normalize source
        if "source" not in normalized:
            # Try to determine source from signal format
            if "tremius_id" in normalized:
                normalized["source"] = "tremius"
            elif "trae_id" in normalized:
                normalized["source"] = "trae_ai"
            else:
                normalized["source"] = "unknown"
        
        return normalized
    
    def add_signal(self, signal: Dict[str, Any]) -> bool:
        """Add a new signal for processing.
        
        Args:
            signal (Dict[str, Any]): Signal data
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            signals_file = os.path.join(self.signals_dir, "incoming_signals.json")
            
            # Normalize signal
            normalized = self._normalize_signal(signal)
            
            # Save to file
            with open(signals_file, "a") as f:
                f.write(json.dumps(normalized) + "\n")
            
            self.logger.info(f"Added signal: {normalized.get('id')}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding signal: {e}")
            return False
    
    def get_processed_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get processed signals.
        
        Args:
            limit (int, optional): Maximum number of signals to return. Defaults to 100.
            
        Returns:
            List[Dict[str, Any]]: List of processed signals
        """
        processed_file = os.path.join(self.signals_dir, "processed_signals.json")
        
        try:
            with open(processed_file, "r") as f:
                processed = json.load(f)
            
            # Return most recent signals first
            return sorted(
                processed, 
                key=lambda x: x.get("timestamp", ""), 
                reverse=True
            )[:limit]
        except Exception as e:
            self.logger.error(f"Error getting processed signals: {e}")
            return []
    
    def get_failed_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get failed signals.
        
        Args:
            limit (int, optional): Maximum number of signals to return. Defaults to 100.
            
        Returns:
            List[Dict[str, Any]]: List of failed signals
        """
        failed_file = os.path.join(self.signals_dir, "failed_signals.json")
        failed = []
        
        try:
            if os.path.exists(failed_file):
                with open(failed_file, "r") as f:
                    for line in f:
                        try:
                            failed.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            pass
            
            # Return most recent signals first
            return sorted(
                failed, 
                key=lambda x: x.get("timestamp", ""), 
                reverse=True
            )[:limit]
        except Exception as e:
            self.logger.error(f"Error getting failed signals: {e}")
            return []