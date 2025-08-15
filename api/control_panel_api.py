#!/usr/bin/env python3

import os
import sys
import json
import time
import uuid
import logging
import argparse
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
from liveops.dreamer_mode import DreamerMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.control_panel_api")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Default configuration
DEFAULT_CONFIG = {
    "api": {
        "port": 5000,
        "host": "0.0.0.0",
        "debug": False,
        "use_https": False,
        "cert_path": "",
        "key_path": "",
        "jwt_secret_key": "",
        "access_token_expiry": 24,  # hours
        "users": []
    }
}


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return DEFAULT_CONFIG


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to file.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        config_path (str): Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False


def load_data_file(file_path: str, default: Any = None) -> Any:
    """Load data from JSON file.
    
    Args:
        file_path (str): Path to JSON file
        default (Any, optional): Default value if file doesn't exist. Defaults to None.
        
    Returns:
        Any: Data from file or default value
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"Error loading data file {file_path}: {e}")
        return default if default is not None else {}


def save_data_file(data: Any, file_path: str) -> bool:
    """Save data to JSON file.
    
    Args:
        data (Any): Data to save
        file_path (str): Path to JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving data file {file_path}: {e}")
        return False


def setup_jwt(app: Flask, config: Dict[str, Any]):
    """Setup JWT authentication.
    
    Args:
        app (Flask): Flask application
        config (Dict[str, Any]): Configuration dictionary
    """
    # Generate JWT secret key if not present
    if not config["api"].get("jwt_secret_key"):
        config["api"]["jwt_secret_key"] = str(uuid.uuid4())
        logger.info("Generated new JWT secret key")
    
    # Configure JWT
    app.config["JWT_SECRET_KEY"] = config["api"]["jwt_secret_key"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=config["api"].get("access_token_expiry", 24))
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Create default admin user if no users exist
    if not config["api"].get("users"):
        default_password = str(uuid.uuid4())[:8]
        config["api"]["users"] = [{
            "username": "admin",
            "password_hash": generate_password_hash(default_password),
            "role": "admin",
            "created_at": datetime.now().isoformat()
        }]
        logger.info(f"Created default admin user with password: {default_password}")
        logger.info("Please change this password immediately after first login")


# API routes
@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login route."""
    data = request.get_json()
    
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Missing username or password"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    # Find user
    user = None
    for u in app.config["users"]:
        if u["username"] == username:
            user = u
            break
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Create access token
    access_token = create_access_token(identity={
        "username": user["username"],
        "role": user["role"]
    })
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "username": user["username"],
            "role": user["role"]
        }
    }), 200


@app.route("/api/auth/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Change password route."""
    data = request.get_json()
    
    if not data or not data.get("current_password") or not data.get("new_password"):
        return jsonify({"error": "Missing current or new password"}), 400
    
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    # Get current user
    current_user = get_jwt_identity()
    username = current_user["username"]
    
    # Find user
    user = None
    for i, u in enumerate(app.config["users"]):
        if u["username"] == username:
            user = u
            user_index = i
            break
    
    if not user or not check_password_hash(user["password_hash"], current_password):
        return jsonify({"error": "Invalid current password"}), 401
    
    # Update password
    app.config["users"][user_index]["password_hash"] = generate_password_hash(new_password)
    app.config["users"][user_index]["updated_at"] = datetime.now().isoformat()
    
    # Save configuration
    config = load_config(app.config["config_path"])
    config["api"]["users"] = app.config["users"]
    save_config(config, app.config["config_path"])
    
    return jsonify({"message": "Password changed successfully"}), 200


@app.route("/api/dashboard/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics."""
    # Load data files
    trades_file = os.path.join(app.config["data_dir"], "trades.json")
    signals_file = os.path.join(app.config["data_dir"], "signals.json")
    accounts_file = os.path.join(app.config["data_dir"], "accounts.json")
    
    trades = load_data_file(trades_file, [])
    signals = load_data_file(signals_file, [])
    accounts = load_data_file(accounts_file, {})
    
    # Calculate statistics
    total_trades = len(trades)
    total_signals = len(signals)
    
    # Calculate profit/loss
    total_pnl = 0
    winning_trades = 0
    losing_trades = 0
    
    for trade in trades:
        if trade.get("status") == "closed":
            pnl = trade.get("profit_loss", 0)
            total_pnl += pnl
            
            if pnl > 0:
                winning_trades += 1
            elif pnl < 0:
                losing_trades += 1
    
    # Calculate win rate
    closed_trades = winning_trades + losing_trades
    win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0
    
    # Get account balances
    account_balances = {}
    for account_id, account in accounts.items():
        account_balances[account_id] = {
            "name": account.get("name", account_id),
            "balance": account.get("balance", 0),
            "equity": account.get("equity", 0),
            "currency": account.get("currency", "USD")
        }
    
    # Get recent trades
    recent_trades = sorted(
        trades,
        key=lambda x: x.get("timestamp", 0),
        reverse=True
    )[:10]
    
    # Get recent signals
    recent_signals = sorted(
        signals,
        key=lambda x: x.get("timestamp", 0),
        reverse=True
    )[:10]
    
    # Check if dreamer mode is active
    dreamer_mode_active = os.path.exists(os.path.join(app.config["data_dir"], "dreamer_mode.json"))
    
    # Check if TRAE AI Agent is running
    trae_ai_active = False
    try:
        with open(os.path.join(app.config["data_dir"], "trae_ai_status.json"), "r") as f:
            trae_ai_status = json.load(f)
            last_update = trae_ai_status.get("last_update", 0)
            trae_ai_active = (time.time() - last_update) < 300  # Active if updated in last 5 minutes
    except:
        pass
    
    return jsonify({
        "stats": {
            "total_trades": total_trades,
            "total_signals": total_signals,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades
        },
        "accounts": account_balances,
        "recent_trades": recent_trades,
        "recent_signals": recent_signals,
        "system_status": {
            "dreamer_mode": dreamer_mode_active,
            "trae_ai_active": trae_ai_active
        }
    }), 200


@app.route("/api/trades", methods=["GET"])
@jwt_required()
def get_trades():
    """Get trades."""
    trades_file = os.path.join(app.config["data_dir"], "trades.json")
    trades = load_data_file(trades_file, [])
    
    # Filter and sort trades
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)
    sort_by = request.args.get("sort_by", default="timestamp", type=str)
    sort_order = request.args.get("sort_order", default="desc", type=str)
    
    # Apply filters
    status = request.args.get("status")
    symbol = request.args.get("symbol")
    account_id = request.args.get("account_id")
    
    filtered_trades = trades
    
    if status:
        filtered_trades = [t for t in filtered_trades if t.get("status") == status]
    
    if symbol:
        filtered_trades = [t for t in filtered_trades if t.get("symbol") == symbol]
    
    if account_id:
        filtered_trades = [t for t in filtered_trades if t.get("account_id") == account_id]
    
    # Sort trades
    reverse = sort_order.lower() == "desc"
    sorted_trades = sorted(
        filtered_trades,
        key=lambda x: x.get(sort_by, 0),
        reverse=reverse
    )
    
    # Paginate
    paginated_trades = sorted_trades[offset:offset + limit]
    
    return jsonify({
        "trades": paginated_trades,
        "total": len(filtered_trades),
        "limit": limit,
        "offset": offset
    }), 200


@app.route("/api/signals", methods=["GET"])
@jwt_required()
def get_signals():
    """Get signals."""
    signals_file = os.path.join(app.config["data_dir"], "signals.json")
    signals = load_data_file(signals_file, [])
    
    # Filter and sort signals
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)
    sort_by = request.args.get("sort_by", default="timestamp", type=str)
    sort_order = request.args.get("sort_order", default="desc", type=str)
    
    # Apply filters
    status = request.args.get("status")
    symbol = request.args.get("symbol")
    source = request.args.get("source")
    
    filtered_signals = signals
    
    if status:
        filtered_signals = [s for s in filtered_signals if s.get("status") == status]
    
    if symbol:
        filtered_signals = [s for s in filtered_signals if s.get("symbol") == symbol]
    
    if source:
        filtered_signals = [s for s in filtered_signals if s.get("source") == source]
    
    # Sort signals
    reverse = sort_order.lower() == "desc"
    sorted_signals = sorted(
        filtered_signals,
        key=lambda x: x.get(sort_by, 0),
        reverse=reverse
    )
    
    # Paginate
    paginated_signals = sorted_signals[offset:offset + limit]
    
    return jsonify({
        "signals": paginated_signals,
        "total": len(filtered_signals),
        "limit": limit,
        "offset": offset
    }), 200


@app.route("/api/accounts", methods=["GET"])
@jwt_required()
def get_accounts():
    """Get accounts."""
    accounts_file = os.path.join(app.config["data_dir"], "accounts.json")
    accounts = load_data_file(accounts_file, {})
    
    return jsonify({"accounts": accounts}), 200


@app.route("/api/trade/manual", methods=["POST"])
@jwt_required()
def execute_manual_trade():
    """Execute manual trade."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Missing trade data"}), 400
    
    required_fields = ["account_id", "symbol", "action", "volume"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if dreamer mode is active
    dreamer_mode_active = os.path.exists(os.path.join(app.config["data_dir"], "dreamer_mode.json"))
    
    if dreamer_mode_active:
        # Execute trade in dreamer mode
        dreamer = DreamerMode(data_dir=app.config["data_dir"])
        result = dreamer.execute_trade(
            account_id=data["account_id"],
            symbol=data["symbol"],
            action=data["action"],
            volume=data["volume"],
            take_profit=data.get("take_profit"),
            stop_loss=data.get("stop_loss")
        )
        
        return jsonify(result), 200
    else:
        # Execute trade in real mode
        # Prepare payload for stealth executor
        payload = {
            "account_id": data["account_id"],
            "symbol": data["symbol"],
            "action": data["action"],
            "volume": data["volume"],
            "source": "manual",
            "source_id": f"manual_{int(time.time())}"
        }
        
        if "take_profit" in data and data["take_profit"]:
            payload["take_profit"] = data["take_profit"]
        
        if "stop_loss" in data and data["stop_loss"]:
            payload["stop_loss"] = data["stop_loss"]
        
        # Call stealth executor API
        import requests
        
        try:
            response = requests.post(
                "http://localhost:5000/api/trade/stealth",
                json=payload,
                headers={"X-API-Key": app.config.get("stealth_api_key", "")}
            )
            
            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                return jsonify({"error": f"Stealth executor error: {response.text}"}), response.status_code
        except Exception as e:
            return jsonify({"error": f"Error calling stealth executor: {str(e)}"}), 500


@app.route("/api/dreamer/toggle", methods=["POST"])
@jwt_required()
def toggle_dreamer_mode():
    """Toggle dreamer mode."""
    data = request.get_json()
    
    if not data or "enabled" not in data:
        return jsonify({"error": "Missing enabled field"}), 400
    
    enabled = data["enabled"]
    dreamer_file = os.path.join(app.config["data_dir"], "dreamer_mode.json")
    
    if enabled:
        # Enable dreamer mode
        dreamer = DreamerMode(data_dir=app.config["data_dir"])
        dreamer.save_state()
        
        return jsonify({"message": "Dreamer mode enabled", "status": "enabled"}), 200
    else:
        # Disable dreamer mode
        if os.path.exists(dreamer_file):
            os.remove(dreamer_file)
        
        return jsonify({"message": "Dreamer mode disabled", "status": "disabled"}), 200


@app.route("/api/trae-ai/toggle", methods=["POST"])
@jwt_required()
def toggle_trae_ai():
    """Toggle TRAE AI Agent."""
    data = request.get_json()
    
    if not data or "enabled" not in data:
        return jsonify({"error": "Missing enabled field"}), 400
    
    enabled = data["enabled"]
    
    if enabled:
        # Start TRAE AI Agent
        try:
            import subprocess
            
            # Run in background
            subprocess.Popen(
                [sys.executable, "trae_ai.py", "--start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return jsonify({"message": "TRAE AI Agent started", "status": "enabled"}), 200
        except Exception as e:
            return jsonify({"error": f"Error starting TRAE AI Agent: {str(e)}"}), 500
    else:
        # Stop TRAE AI Agent
        try:
            import subprocess
            
            # Run stop command
            subprocess.run(
                [sys.executable, "trae_ai.py", "--stop"],
                check=True
            )
            
            return jsonify({"message": "TRAE AI Agent stopped", "status": "disabled"}), 200
        except Exception as e:
            return jsonify({"error": f"Error stopping TRAE AI Agent: {str(e)}"}), 500


@app.route("/api/logs", methods=["GET"])
@jwt_required()
def get_logs():
    """Get logs."""
    log_type = request.args.get("type", default="system", type=str)
    limit = request.args.get("limit", default=100, type=int)
    
    log_file = None
    
    if log_type == "system":
        log_file = os.path.join(app.config["log_dir"], "system.log")
    elif log_type == "trades":
        log_file = os.path.join(app.config["log_dir"], "trades.log")
    elif log_type == "signals":
        log_file = os.path.join(app.config["log_dir"], "signals.log")
    elif log_type == "errors":
        log_file = os.path.join(app.config["log_dir"], "errors.log")
    else:
        return jsonify({"error": f"Invalid log type: {log_type}"}), 400
    
    if not os.path.exists(log_file):
        return jsonify({"logs": [], "type": log_type}), 200
    
    try:
        # Read last N lines from log file
        with open(log_file, "r") as f:
            lines = f.readlines()
        
        # Get last N lines
        logs = lines[-limit:] if len(lines) > limit else lines
        
        return jsonify({"logs": logs, "type": log_type}), 200
    except Exception as e:
        return jsonify({"error": f"Error reading log file: {str(e)}"}), 500


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE AI Trading Sentinel Control Panel API")
    parser.add_argument("--config", type=str, default="config/liveops_config.json", help="Path to configuration file")
    parser.add_argument("--port", type=int, help="Port to run the API on")
    parser.add_argument("--host", type=str, help="Host to run the API on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Ensure API configuration exists
    if "api" not in config:
        config["api"] = DEFAULT_CONFIG["api"]
    
    # Override configuration with command line arguments
    if args.port:
        config["api"]["port"] = args.port
    
    if args.host:
        config["api"]["host"] = args.host
    
    if args.debug:
        config["api"]["debug"] = True
    
    # Save configuration
    save_config(config, args.config)
    
    # Set application configuration
    app.config["config_path"] = args.config
    app.config["data_dir"] = config.get("system", {}).get("data_dir", "data")
    app.config["log_dir"] = config.get("system", {}).get("log_dir", "logs")
    app.config["users"] = config["api"].get("users", [])
    app.config["stealth_api_key"] = config.get("signal_sources", {}).get("webhook", {}).get("api_key", "")
    
    # Setup JWT
    setup_jwt(app, config)
    
    # Run application
    ssl_context = None
    if config["api"].get("use_https", False):
        cert_path = config["api"].get("cert_path")
        key_path = config["api"].get("key_path")
        
        if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = (cert_path, key_path)
        else:
            logger.warning("HTTPS is enabled but certificate or key is missing. Falling back to HTTP.")
    
    app.run(
        host=config["api"].get("host", "0.0.0.0"),
        port=config["api"].get("port", 5000),
        debug=config["api"].get("debug", False),
        ssl_context=ssl_context
    )


if __name__ == "__main__":
    main()