# trae_signal_fetcher.py

import os
import json
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trae_signal_fetcher')

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
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        
        # Write to heartbeat status file
        with open(HEARTBEAT_STATUS_FILE, 'w') as f:
            f.write(f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}")
            
        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")

# Signal source configuration
SIGNAL_SOURCE = os.getenv('SIGNAL_SOURCE', 'file')  # Options: 'file', 'webhook', 'api'
SIGNAL_FILE_PATH = os.getenv('SIGNAL_FILE_PATH', 'signals.json')
SIGNAL_API_URL = os.getenv('SIGNAL_API_URL', '')
SIGNAL_API_KEY = os.getenv('SIGNAL_API_KEY', '')
SIGNAL_POLL_INTERVAL = int(os.getenv('SIGNAL_POLL_INTERVAL', '60'))  # seconds

# Track processed signals to avoid duplicates
processed_signals = set()

def get_next_signal():
    """Get the next available trading signal
    
    Returns:
        dict: The next signal to process, or None if no signal is available
    """
    try:
        # Update heartbeat status when checking for signals
        update_heartbeat_status(f"🔄 Checking for signals from {SIGNAL_SOURCE} source...")
        
        if SIGNAL_SOURCE == 'file':
            signal = _get_signal_from_file()
        elif SIGNAL_SOURCE == 'webhook':
            signal = _get_signal_from_webhook()
        elif SIGNAL_SOURCE == 'api':
            signal = _get_signal_from_api()
        else:
            logger.error(f"Unknown signal source: {SIGNAL_SOURCE}")
            update_heartbeat_status(f"❌ Error: Unknown signal source: {SIGNAL_SOURCE}")
            return None
            
        if signal:
            update_heartbeat_status(f"🔔 Signal received: {signal.get('symbol')} {signal.get('direction')}")
        else:
            update_heartbeat_status("🔄 Waiting for signals...")
            
        return signal
    except Exception as e:
        logger.error(f"Error getting signal: {e}")
        update_heartbeat_status(f"❌ Error getting signal: {str(e)[:50]}...")
        return None

def _get_signal_from_file():
    """Get signal from a local JSON file"""
    try:
        if not os.path.exists(SIGNAL_FILE_PATH):
            logger.warning(f"Signal file {SIGNAL_FILE_PATH} not found")
            update_heartbeat_status(f"⚠️ Signal file not found: {SIGNAL_FILE_PATH}")
            return None
            
        # Read the signal file
        with open(SIGNAL_FILE_PATH, 'r') as f:
            signals = json.load(f)
            
        # Check if we have any signals
        if not signals or not isinstance(signals, list) or len(signals) == 0:
            return None
            
        # Get the first unprocessed signal
        for signal in signals:
            # Generate a unique ID for the signal if it doesn't have one
            if 'id' not in signal:
                signal['id'] = f"{signal.get('symbol', 'UNKNOWN')}-{signal.get('direction', 'UNKNOWN')}-{int(time.time())}"
                
            # Check if we've already processed this signal
            if signal['id'] in processed_signals:
                continue
                
            # Mark as processed
            processed_signals.add(signal['id'])
            
            # Add timestamp if not present
            if 'timestamp' not in signal:
                signal['timestamp'] = datetime.now().isoformat()
                
            return signal
            
        return None
        
    except Exception as e:
        logger.error(f"Error reading signal file: {e}")
        return None

def _get_signal_from_webhook():
    """Get signal from a webhook endpoint
    
    This is a placeholder for a webhook implementation.
    In a real system, you would set up a Flask or FastAPI endpoint
    to receive webhook calls from Trae or other signal sources.
    
    For now, this just simulates a webhook by checking a special file.
    """
    webhook_file = os.getenv('WEBHOOK_FILE_PATH', 'webhook_signals.json')
    
    try:
        if not os.path.exists(webhook_file):
            return None
            
        # Read the webhook file
        with open(webhook_file, 'r') as f:
            signals = json.load(f)
            
        # Check if we have any signals
        if not signals or not isinstance(signals, list) or len(signals) == 0:
            return None
            
        # Get the first unprocessed signal
        for i, signal in enumerate(signals):
            # Generate a unique ID for the signal if it doesn't have one
            if 'id' not in signal:
                signal['id'] = f"{signal.get('symbol', 'UNKNOWN')}-{signal.get('direction', 'UNKNOWN')}-{int(time.time())}"
                
            # Check if we've already processed this signal
            if signal['id'] in processed_signals:
                continue
                
            # Mark as processed
            processed_signals.add(signal['id'])
            
            # Add timestamp if not present
            if 'timestamp' not in signal:
                signal['timestamp'] = datetime.now().isoformat()
                
            # Remove the signal from the file
            signals.pop(i)
            with open(webhook_file, 'w') as f:
                json.dump(signals, f, indent=2)
                
            return signal
            
        return None
        
    except Exception as e:
        logger.error(f"Error reading webhook file: {e}")
        return None

def _get_signal_from_api():
    """Get signal from an API endpoint"""
    if not SIGNAL_API_URL:
        logger.error("API URL not configured")
        update_heartbeat_status("❌ Error: API URL not configured")
        return None
        
    try:
        # Set up headers with API key if provided
        headers = {}
        if SIGNAL_API_KEY:
            headers['Authorization'] = f"Bearer {SIGNAL_API_KEY}"
            
        # Make the API request
        response = requests.get(SIGNAL_API_URL, headers=headers, timeout=10)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}")
            update_heartbeat_status(f"❌ API request failed with status code {response.status_code}")
            return None
            
        # Parse the response
        data = response.json()
        
        # Check if we have a valid signal
        if not data or not isinstance(data, dict):
            return None
            
        # Generate a unique ID for the signal if it doesn't have one
        if 'id' not in data:
            data['id'] = f"{data.get('symbol', 'UNKNOWN')}-{data.get('direction', 'UNKNOWN')}-{int(time.time())}"
            
        # Check if we've already processed this signal
        if data['id'] in processed_signals:
            return None
            
        # Mark as processed
        processed_signals.add(data['id'])
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
            
        return data
        
    except Exception as e:
        logger.error(f"Error calling API: {e}")
        return None

# For testing
if __name__ == "__main__":
    # Create a test signal file if it doesn't exist
    if not os.path.exists(SIGNAL_FILE_PATH):
        test_signals = [
            {
                "symbol": "EURUSD",
                "direction": "buy",
                "price": 1.0750,
                "tp": 1.0800,
                "sl": 1.0700,
                "timestamp": datetime.now().isoformat()
            }
        ]
        with open(SIGNAL_FILE_PATH, 'w') as f:
            json.dump(test_signals, f, indent=2)
        print(f"Created test signal file: {SIGNAL_FILE_PATH}")
    
    # Test getting a signal
    signal = get_next_signal()
    print(f"Next signal: {signal}")