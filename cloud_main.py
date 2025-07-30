import os
import sys
import json
import logging
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the CloudTradeExecutor
from cloud_trade_executor import CloudTradeExecutor

# Load environment variables
load_dotenv()

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "cloud_main.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("CLOUD_MAIN")

# Create Flask app
app = Flask(__name__)

# Configure CORS with environment variables
cors_origins = os.getenv('CORS_ORIGINS', '*')
CORS(app, resources={r"/*": {"origins": cors_origins.split(',') if ',' in cors_origins else cors_origins}})

# Store active sessions
active_sessions = {}

# Root route
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "ok",
        "message": "AI Trading Sentinel Cloud API",
        "version": "0.3.0-cloud",
        "endpoints": [
            "/api/health",
            "/api/login",
            "/api/trade",
            "/api/sessions",
            "/api/status",
            "/api/strategy",
            "/api/logs"
        ]
    }), 200

# Health check
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", 
        "timestamp": datetime.datetime.now().isoformat(),
        "active_sessions": len(active_sessions),
        "environment": "cloud" if os.getenv('HEADLESS', 'true').lower() == 'true' else "local"
    }), 200

# Login route
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        account_id = data.get("account_id", os.getenv('BULENOX_ACCOUNT_ID', 'BX64883'))
        session_id = data.get("session_id")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"{account_id}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Check if session already exists
        if session_id in active_sessions:
            logger.info(f"Session {session_id} already exists, reusing")
            executor = active_sessions[session_id]
        else:
            # Create new executor
            logger.info(f"Creating new session {session_id} for account {account_id}")
            executor = CloudTradeExecutor(account_id=account_id, session_id=session_id)
            active_sessions[session_id] = executor
        
        # Set API_MODE environment variable to prevent input prompt
        os.environ['API_MODE'] = 'true'
        
        # Perform login
        executor.login()
        
        if executor.driver:
            logger.info(f"Login successful for session {session_id}")
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "session_id": session_id,
                "account_id": account_id
            }), 200
        else:
            logger.error(f"Login failed for session {session_id}")
            # Clean up failed session
            if session_id in active_sessions:
                executor.close()
                del active_sessions[session_id]
            
            return jsonify({
                "status": "error",
                "message": "Login failed"
            }), 401
    
    except Exception as e:
        logger.exception(f"Error during login: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Trade execution route
@app.route("/api/trade", methods=["POST"])
def execute_trade():
    try:
        data = request.get_json()
        account_id = data.get("account_id", os.getenv('BULENOX_ACCOUNT_ID', 'BX64883'))
        session_id = data.get("session_id")
        signal = data.get("signal", {})
        
        # Validate signal
        if not signal or not isinstance(signal, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid or missing signal data"
            }), 400
        
        # Ensure required signal fields
        required_fields = ["symbol", "side"]
        for field in required_fields:
            if field not in signal:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field in signal: {field}"
                }), 400
        
        # Set default quantity if not provided
        if "quantity" not in signal:
            signal["quantity"] = 1
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"{account_id}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Check if session exists
        if session_id in active_sessions:
            logger.info(f"Using existing session {session_id}")
            executor = active_sessions[session_id]
        else:
            # Create new executor and login
            logger.info(f"Creating new session {session_id} for account {account_id}")
            executor = CloudTradeExecutor(account_id=account_id, session_id=session_id)
            active_sessions[session_id] = executor
            
            executor.login()
            if not executor.driver:
                logger.error(f"Login failed for new session {session_id}")
                # Clean up failed session
                executor.close()
                del active_sessions[session_id]
                
                return jsonify({
                    "status": "error",
                    "message": "Login failed, cannot execute trade"
                }), 401
        
        # Execute trade
        logger.info(f"Executing trade for session {session_id}: {signal}")
        success = executor.execute_trade(signal)
        
        if success:
            logger.info(f"Trade executed successfully for session {session_id}")
            return jsonify({
                "status": "success",
                "message": "Trade executed successfully",
                "session_id": session_id,
                "account_id": account_id,
                "signal": signal
            }), 200
        else:
            logger.error(f"Trade execution failed for session {session_id}")
            return jsonify({
                "status": "error",
                "message": "Trade execution failed"
            }), 500
    
    except Exception as e:
        logger.exception(f"Error during trade execution: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# List active sessions
@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    sessions = []
    for session_id, executor in active_sessions.items():
        sessions.append({
            "session_id": session_id,
            "account_id": executor.account_id,
            "created_at": session_id.split("-")[-2] + "-" + session_id.split("-")[-1] if "-" in session_id else "unknown"
        })
    
    return jsonify({
        "status": "success",
        "sessions": sessions,
        "count": len(sessions)
    }), 200

# Get status information
@app.route("/api/status", methods=["GET"])
def get_status():
    # Read status.json if it exists
    status_file = os.path.join(log_dir, "status.json")
    status_data = {"trades": [], "last_update": None}
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status_data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading status file: {e}")
    
    # Add active sessions info
    status_data["active_sessions"] = len(active_sessions)
    status_data["sessions"] = []
    
    for session_id, executor in active_sessions.items():
        status_data["sessions"].append({
            "session_id": session_id,
            "account_id": executor.account_id
        })
    
    return jsonify(status_data), 200

# Logs endpoint to view application logs
@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        # Get query parameters
        log_type = request.args.get("type", "main")  # main, session, or trade
        session_id = request.args.get("session_id")  # Optional session ID for session logs
        lines = int(request.args.get("lines", 100))  # Number of lines to return
        
        # Determine which log file to read
        if log_type == "main":
            log_file = os.path.join(log_dir, "cloud_main.log")
        elif log_type == "executor":
            log_file = os.path.join(log_dir, "cloud_trade_executor.log")
        elif log_type == "session" and session_id:
            log_file = os.path.join(log_dir, f"{session_id}.log")
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid log type or missing session_id for session logs"
            }), 400
        
        # Check if log file exists
        if not os.path.exists(log_file):
            return jsonify({
                "status": "error",
                "message": f"Log file not found: {os.path.basename(log_file)}"
            }), 404
        
        # Read the last N lines from the log file
        with open(log_file, 'r') as f:
            # Use a deque with maxlen to efficiently get the last N lines
            from collections import deque
            last_lines = deque(maxlen=lines)
            for line in f:
                last_lines.append(line.strip())
        
        return jsonify({
            "status": "success",
            "log_type": log_type,
            "session_id": session_id,
            "filename": os.path.basename(log_file),
            "lines": list(last_lines),
            "timestamp": datetime.datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving logs: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Strategy selection endpoint
@app.route("/api/strategy", methods=["GET", "POST"])
def manage_strategy():
    if request.method == "GET":
        # Get current strategy
        strategy_file = os.path.join(log_dir, "strategy.json")
        if os.path.exists(strategy_file):
            try:
                with open(strategy_file, 'r') as f:
                    strategy_data = json.load(f)
                return jsonify(strategy_data), 200
            except Exception as e:
                logger.error(f"Error reading strategy file: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            # Return default strategy if no file exists
            return jsonify({
                "status": "success",
                "strategy": "default",
                "parameters": {}
            }), 200
    
    elif request.method == "POST":
        # Update strategy
        try:
            data = request.get_json()
            strategy_name = data.get("strategy")
            parameters = data.get("parameters", {})
            
            if not strategy_name:
                return jsonify({"status": "error", "message": "Strategy name is required"}), 400
            
            # Save strategy to file
            strategy_file = os.path.join(log_dir, "strategy.json")
            strategy_data = {
                "status": "success",
                "strategy": strategy_name,
                "parameters": parameters,
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            with open(strategy_file, 'w') as f:
                json.dump(strategy_data, f, indent=2)
            
            logger.info(f"Strategy updated to {strategy_name} with parameters {parameters}")
            return jsonify(strategy_data), 200
            
        except Exception as e:
            logger.exception(f"Error updating strategy: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

# Webhook endpoint for trade signals
@app.route("/api/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        logger.info(f"Received webhook: {data}")
        
        # Extract account_id and signal
        account_id = data.get("account_id", os.getenv('BULENOX_ACCOUNT_ID', 'BX64883'))
        signal = data.get("signal", {})
        
        # Validate signal
        if not signal or not isinstance(signal, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid or missing signal data"
            }), 400
        
        # Generate session ID
        session_id = f"{account_id}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create new executor and login
        logger.info(f"Creating new session {session_id} for account {account_id} from webhook")
        executor = CloudTradeExecutor(account_id=account_id, session_id=session_id)
        active_sessions[session_id] = executor
        
        executor.login()
        if not executor.driver:
            logger.error(f"Login failed for webhook session {session_id}")
            # Clean up failed session
            executor.close()
            del active_sessions[session_id]
            
            return jsonify({
                "status": "error",
                "message": "Login failed, cannot execute trade"
            }), 401
        
        # Execute trade
        logger.info(f"Executing trade for webhook session {session_id}: {signal}")
        success = executor.execute_trade(signal)
        
        # Close session after webhook trade (don't keep it open)
        executor.close()
        del active_sessions[session_id]
        
        if success:
            logger.info(f"Webhook trade executed successfully for session {session_id}")
            return jsonify({
                "status": "success",
                "message": "Trade executed successfully",
                "session_id": session_id,
                "account_id": account_id,
                "signal": signal
            }), 200
        else:
            logger.error(f"Webhook trade execution failed for session {session_id}")
            return jsonify({
                "status": "error",
                "message": "Trade execution failed"
            }), 500
    
    except Exception as e:
        logger.exception(f"Error during webhook processing: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Main entry point
if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting AI Trading Sentinel Cloud API on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {'cloud' if os.getenv('HEADLESS', 'true').lower() == 'true' else 'local'}")
    logger.info(f"CORS origins: {cors_origins}")
    
    app.run(host=host, port=port, debug=debug)