import os
import json
import time
import logging
import shutil
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SignalFileHandler(FileSystemEventHandler):
    """Handler for file-based signal reception.
    
    This class monitors a directory for new signal files and processes them.
    """
    
    def __init__(self, 
                 watch_dir: str,
                 signals_dir: str = "data",
                 file_patterns: List[str] = [".json", ".csv"],
                 signal_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Initialize the file handler.
        
        Args:
            watch_dir (str): Directory to watch for new files
            signals_dir (str, optional): Directory for storing processed signals. Defaults to "data".
            file_patterns (List[str], optional): File extensions to watch for. Defaults to [".json", ".csv"].
            signal_callback (Optional[Callable], optional): Callback function for processing signals.
                Defaults to None.
        """
        self.logger = logging.getLogger("trae.file_handler")
        self.watch_dir = watch_dir
        self.signals_dir = signals_dir
        self.file_patterns = file_patterns
        self.signal_callback = signal_callback
        self.observer = None
        self.running = False
        
        # Ensure directories exist
        os.makedirs(watch_dir, exist_ok=True)
        os.makedirs(signals_dir, exist_ok=True)
        os.makedirs(os.path.join(watch_dir, "processed"), exist_ok=True)
        
        self.logger.info(f"File handler initialized watching {watch_dir}")
    
    def on_created(self, event):
        """Handle file creation events.
        
        Args:
            event: File system event
        """
        if not event.is_directory:
            file_path = event.src_path
            
            # Check if file matches patterns
            if any(file_path.endswith(pattern) for pattern in self.file_patterns):
                self.logger.info(f"New signal file detected: {file_path}")
                
                # Process the file
                self._process_file(file_path)
    
    def _process_file(self, file_path: str):
        """Process a signal file.
        
        Args:
            file_path (str): Path to the signal file
        """
        try:
            # Wait a moment to ensure file is completely written
            time.sleep(1)
            
            # Read the file
            signals = []
            
            if file_path.endswith(".json"):
                signals = self._read_json_file(file_path)
            elif file_path.endswith(".csv"):
                signals = self._read_csv_file(file_path)
            
            # Process signals
            for signal in signals:
                # Add timestamp and unique ID if not present
                if "timestamp" not in signal:
                    signal["timestamp"] = datetime.now().isoformat()
                if "id" not in signal:
                    signal["id"] = f"{datetime.now().timestamp()}-{hash(json.dumps(signal))}"
                
                # Save signal to file
                self._save_signal(signal)
                
                # Call callback if provided
                if self.signal_callback:
                    try:
                        self.signal_callback(signal)
                    except Exception as e:
                        self.logger.error(f"Error in signal callback: {e}")
            
            # Move file to processed directory
            processed_dir = os.path.join(os.path.dirname(file_path), "processed")
            processed_file = os.path.join(
                processed_dir, 
                f"{os.path.basename(file_path)}.{int(time.time())}"
            )
            shutil.move(file_path, processed_file)
            
            self.logger.info(f"Processed signal file: {file_path} -> {processed_file}")
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
    
    def _read_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read signals from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            List[Dict[str, Any]]: List of signals
        """
        try:
            with open(file_path, "r") as f:
                content = json.load(f)
                
                # Handle both single signal and array of signals
                if isinstance(content, list):
                    return content
                else:
                    return [content]
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
            return []
    
    def _read_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read signals from a CSV file.
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            List[Dict[str, Any]]: List of signals
        """
        try:
            import csv
            signals = []
            
            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    signals.append(dict(row))
            
            return signals
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {e}")
            return []
    
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
        """Start the file handler.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("File handler already running")
            return False
        
        try:
            self.running = True
            self.observer = Observer()
            self.observer.schedule(self, self.watch_dir, recursive=False)
            self.observer.start()
            
            self.logger.info(f"File handler started watching {self.watch_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting file handler: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the file handler.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("File handler not running")
            return False
        
        try:
            self.running = False
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            self.logger.info("File handler stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping file handler: {e}")
            return False