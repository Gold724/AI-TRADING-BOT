# bulenox_trade_sentinel.py
# AI Trading Sentinel - Bulenox Trade Execution System

import json
import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Import AI-powered login and execution modules
from ai_login_bulenox import ai_login_bulenox, update_heartbeat_status
from executor_bulenox import BulenoxExecutor, execute_trade

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bulenox_trade_sentinel")

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Global variables
driver = None
session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs(os.path.join("logs", "screenshots"), exist_ok=True)


@app.before_request
def check_api_key():
    """Check if the API key is valid"""
    # Skip API key check for health endpoint
    if request.path == "/api/health":
        return None

    # Get API key from environment variable
    api_key = os.getenv("API_KEY")
    
    # If no API key is set, allow all requests (development mode)
    if not api_key:
        logger.warning("No API key set. Running in development mode.")
        return None
    
    # Check if the API key is valid
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {api_key}":
        return jsonify({"error": "Unauthorized"}), 401


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    global driver
    
    # Check if driver is initialized
    driver_status = "active" if driver else "inactive"
    
    # Read heartbeat status if available
    heartbeat_status = "unknown"
    session_active = False
    timestamp = ""
    
    if os.path.exists(HEARTBEAT_STATUS_FILE):
        try:
            with open(HEARTBEAT_STATUS_FILE, "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    heartbeat_status = lines[0].strip()
                    timestamp = lines[1].strip()
                if len(lines) >= 3:
                    session_data = json.loads(lines[2].strip())
                    session_active = session_data.get("session_active", False)
        except Exception as e:
            logger.error(f"Error reading heartbeat status: {e}")
    
    return jsonify({
        "status": "ok",
        "driver": driver_status,
        "heartbeat": {
            "status": heartbeat_status,
            "timestamp": timestamp,
            "session_active": session_active
        },
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/login", methods=["POST"])
def login():
    """Login to Bulenox"""
    global driver
    
    # Check if already logged in
    if driver:
        try:
            # Check if the session is still valid
            current_url = driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # If we're already on a Bulenox page, we're logged in
            if "bulenox" in current_url.lower():
                update_heartbeat_status("✅ Already logged in to Bulenox")
                return jsonify({
                    "status": "success",
                    "message": "Already logged in",
                    "session_id": session_id
                })
        except Exception:
            # If there's an error, the driver is probably stale
            logger.warning("Existing driver is stale. Creating a new one.")
            try:
                driver.quit()
            except:
                pass
            driver = None
    
    # Get debug mode from request
    debug = request.json.get("debug", False) if request.is_json else False
    
    # Login to Bulenox using AI-powered login
    update_heartbeat_status("🔑 Initializing AI-powered login to Bulenox...")
    driver = ai_login_bulenox(debug=debug)
    
    if driver:
        update_heartbeat_status("✅ Successfully logged in to Bulenox", session_active=True)
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "session_id": session_id
        })
    else:
        update_heartbeat_status("❌ Login failed", session_active=False)
        return jsonify({
            "status": "error",
            "message": "Login failed",
            "session_id": session_id
        }), 500


@app.route("/api/trade", methods=["POST"])
def trade():
    """Execute a trade"""
    global driver, session_id
    
    # Check if logged in
    if not driver:
        update_heartbeat_status("❌ Not logged in. Cannot execute trade.", session_active=False)
        return jsonify({
            "status": "error",
            "message": "Not logged in. Please login first.",
            "session_id": session_id
        }), 400
    
    # Get signal from request
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Invalid request. JSON expected.",
            "session_id": session_id
        }), 400
    
    signal = request.json
    
    # Validate signal
    required_fields = ["symbol"]
    for field in required_fields:
        if field not in signal:
            return jsonify({
                "status": "error",
                "message": f"Missing required field: {field}",
                "session_id": session_id
            }), 400
    
    # Get debug mode from request
    debug = signal.pop("debug", False)
    
    # Execute trade
    update_heartbeat_status(f"🔄 Executing trade: {signal['symbol']} {signal.get('direction', 'buy')}")
    result = execute_trade(driver, signal, session_id=session_id, debug=debug)
    
    if result and result.get("success", False):
        return jsonify({
            "status": "success",
            "message": f"Trade executed successfully: {signal['symbol']} {signal.get('direction', 'buy')}",
            "result": result,
            "session_id": session_id
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Trade execution failed: {signal['symbol']} {signal.get('direction', 'buy')}",
            "result": result,
            "session_id": session_id
        }), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    """Logout from Bulenox"""
    global driver
    
    if driver:
        try:
            driver.quit()
            update_heartbeat_status("✅ Logged out from Bulenox", session_active=False)
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            update_heartbeat_status(f"⚠️ Error during logout: {str(e)[:50]}...", session_active=False)
        finally:
            driver = None
    
    return jsonify({
        "status": "success",
        "message": "Logged out",
        "session_id": session_id
    })


# Main entry point
if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 5000))
    
    # Get debug mode from environment variable
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    
    # Get auto-login setting from environment variable
    auto_login = os.getenv("AUTO_LOGIN", "True").lower() == "true"
    
    # Auto-login if enabled
    if auto_login:
        logger.info("Auto-login enabled. Attempting AI-powered login...")
        update_heartbeat_status("🔄 Auto-login enabled. Initializing AI-powered login...")
        driver = ai_login_bulenox(debug=debug_mode)
        
        if driver:
            update_heartbeat_status("✅ AI-powered auto-login successful", session_active=True)
            logger.info("AI-powered auto-login successful")
        else:
            update_heartbeat_status("❌ Auto-login failed", session_active=False)
            logger.error("Auto-login failed")
    
    # Start the Flask app
    logger.info(f"Starting Bulenox Trade Sentinel on port {port}")
    update_heartbeat_status(f"🚀 Starting Bulenox Trade Sentinel on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)