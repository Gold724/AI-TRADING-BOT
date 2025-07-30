import os
import sys
import json
import time
import psutil
import logging
import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, jsonify, request, current_app

# Import lunar phase utility
from utils.lunar_phase import get_lunar_phase

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "dashboard_api.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("DASHBOARD_API")

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Add lunar phase endpoint to the blueprint
# This will be accessible at /api/dashboard/lunar

# Path to store dashboard data
DASHBOARD_DATA_FILE = os.path.join(log_dir, "dashboard_data.json")

# Default dashboard data
default_dashboard_data = {
    "system": {
        "cpu_usage": 0,
        "memory_usage": 0,
        "disk_usage": 0,
        "uptime": 0,
        "lunar_phase": get_lunar_phase(),
        "last_update": datetime.datetime.now().isoformat()
    },
    "trading": {
        "active_sessions": 0,
        "total_trades": 0,
        "successful_trades": 0,
        "failed_trades": 0,
        "pending_trades": 0,
        "last_trade_time": None
    },
    "brokers": {
        "bulenox": {
            "status": "unknown",
            "session_count": 0,
            "last_activity": None
        },
        "binance": {
            "status": "unknown",
            "session_count": 0,
            "last_activity": None
        },
        "exness": {
            "status": "unknown",
            "session_count": 0,
            "last_activity": None
        }
    },
    "strategies": {
        "active_strategy": None,
        "available_strategies": [],
        "last_mutation": None
    },
    "signals": {
        "total_signals": 0,
        "processed_signals": 0,
        "pending_signals": 0,
        "last_signal_time": None
    },
    "health": {
        "overall_status": "unknown",
        "recovery_events": 0,
        "last_recovery": None,
        "issues": []
    }
}

# Load dashboard data
def load_dashboard_data():
    """Load dashboard data from file."""
    try:
        if os.path.exists(DASHBOARD_DATA_FILE):
            with open(DASHBOARD_DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            # Initialize with default data
            save_dashboard_data(default_dashboard_data)
            return default_dashboard_data
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}")
        return default_dashboard_data

# Save dashboard data
def save_dashboard_data(data):
    """Save dashboard data to file."""
    try:
        with open(DASHBOARD_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving dashboard data: {str(e)}")
        return False

# Update system metrics
def update_system_metrics():
    """Update system metrics in dashboard data."""
    try:
        data = load_dashboard_data()
        
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Update system section
        data["system"] = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "uptime": uptime,
            "lunar_phase": get_lunar_phase(),
            "last_update": datetime.datetime.now().isoformat()
        }
        
        save_dashboard_data(data)
        return data["system"]
    except Exception as e:
        logger.error(f"Error updating system metrics: {str(e)}")
        return None

# Update trading metrics
def update_trading_metrics(metrics):
    """Update trading metrics in dashboard data."""
    try:
        data = load_dashboard_data()
        
        # Update with provided metrics
        if "active_sessions" in metrics:
            data["trading"]["active_sessions"] = metrics["active_sessions"]
        if "total_trades" in metrics:
            data["trading"]["total_trades"] = metrics["total_trades"]
        if "successful_trades" in metrics:
            data["trading"]["successful_trades"] = metrics["successful_trades"]
        if "failed_trades" in metrics:
            data["trading"]["failed_trades"] = metrics["failed_trades"]
        if "pending_trades" in metrics:
            data["trading"]["pending_trades"] = metrics["pending_trades"]
        
        # Always update last_trade_time if any metrics were updated
        if metrics:
            data["trading"]["last_trade_time"] = datetime.datetime.now().isoformat()
        
        save_dashboard_data(data)
        return data["trading"]
    except Exception as e:
        logger.error(f"Error updating trading metrics: {str(e)}")
        return None

# Update broker status
def update_broker_status(broker_id, status, session_count=None):
    """Update broker status in dashboard data."""
    try:
        data = load_dashboard_data()
        
        # Ensure broker exists in data
        if broker_id not in data["brokers"]:
            data["brokers"][broker_id] = {
                "status": "unknown",
                "session_count": 0,
                "last_activity": None
            }
        
        # Update broker status
        data["brokers"][broker_id]["status"] = status
        if session_count is not None:
            data["brokers"][broker_id]["session_count"] = session_count
        data["brokers"][broker_id]["last_activity"] = datetime.datetime.now().isoformat()
        
        save_dashboard_data(data)
        return data["brokers"][broker_id]
    except Exception as e:
        logger.error(f"Error updating broker status: {str(e)}")
        return None

# Update strategy information
def update_strategy_info(active_strategy=None, available_strategies=None, last_mutation=None):
    """Update strategy information in dashboard data."""
    try:
        data = load_dashboard_data()
        
        # Update with provided info
        if active_strategy is not None:
            data["strategies"]["active_strategy"] = active_strategy
        if available_strategies is not None:
            data["strategies"]["available_strategies"] = available_strategies
        if last_mutation is not None:
            data["strategies"]["last_mutation"] = last_mutation
        
        save_dashboard_data(data)
        return data["strategies"]
    except Exception as e:
        logger.error(f"Error updating strategy info: {str(e)}")
        return None

# Update signal metrics
def update_signal_metrics(metrics):
    """Update signal metrics in dashboard data."""
    try:
        data = load_dashboard_data()
        
        # Update with provided metrics
        if "total_signals" in metrics:
            data["signals"]["total_signals"] = metrics["total_signals"]
        if "processed_signals" in metrics:
            data["signals"]["processed_signals"] = metrics["processed_signals"]
        if "pending_signals" in metrics:
            data["signals"]["pending_signals"] = metrics["pending_signals"]
        
        # Always update last_signal_time if any metrics were updated
        if metrics:
            data["signals"]["last_signal_time"] = datetime.datetime.now().isoformat()
        
        save_dashboard_data(data)
        return data["signals"]
    except Exception as e:
        logger.error(f"Error updating signal metrics: {str(e)}")
        return None

# Update health status
def update_health_status(overall_status=None, recovery_events=None, last_recovery=None, issues=None):
    """Update health status in dashboard data."""
    try:
        data = load_dashboard_data()
        
        # Update with provided info
        if overall_status is not None:
            data["health"]["overall_status"] = overall_status
        if recovery_events is not None:
            data["health"]["recovery_events"] = recovery_events
        if last_recovery is not None:
            data["health"]["last_recovery"] = last_recovery
        if issues is not None:
            data["health"]["issues"] = issues
        
        save_dashboard_data(data)
        return data["health"]
    except Exception as e:
        logger.error(f"Error updating health status: {str(e)}")
        return None

# API Routes

@dashboard_bp.route('/api/dashboard/status', methods=['GET'])
def get_dashboard_status():
    """Get the current dashboard status."""
    try:
        # Update system metrics before returning
        update_system_metrics()
        
        # Load and return dashboard data
        data = load_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        logger.error(f"Error getting dashboard status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/trading', methods=['GET'])
def get_trading_metrics():
    """Get trading metrics."""
    try:
        data = load_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data["trading"]
        })
    except Exception as e:
        logger.error(f"Error getting trading metrics: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/brokers', methods=['GET'])
def get_broker_status():
    """Get broker status."""
    try:
        data = load_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data["brokers"]
        })
    except Exception as e:
        logger.error(f"Error getting broker status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/strategies', methods=['GET'])
def get_strategy_info():
    """Get strategy information."""
    try:
        data = load_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data["strategies"]
        })
    except Exception as e:
        logger.error(f"Error getting strategy info: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/signals', methods=['GET'])
def get_signal_metrics():
    """Get signal metrics."""
    try:
        data = load_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data["signals"]
        })
    except Exception as e:
        logger.error(f"Error getting signal metrics: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/health', methods=['GET'])
def get_health_status():
    """Get health status."""
    try:
        data = load_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data["health"]
        })
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/lunar', methods=['GET'])
def get_lunar_phase_info():
    """Get current lunar phase information."""
    try:
        today = datetime.date.today()
        lunar_phase = get_lunar_phase(today)
        
        # Get tomorrow's phase
        tomorrow = today + datetime.timedelta(days=1)
        tomorrow_phase = get_lunar_phase(tomorrow)
        
        # Get yesterday's phase
        yesterday = today - datetime.timedelta(days=1)
        yesterday_phase = get_lunar_phase(yesterday)
        
        return jsonify({
            "status": "success",
            "data": {
                "current_date": today.isoformat(),
                "current_phase": lunar_phase,
                "yesterday_phase": yesterday_phase,
                "tomorrow_phase": tomorrow_phase
            }
        })
    except Exception as e:
        logger.error(f"Error getting lunar phase: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/update', methods=['POST'])
def update_dashboard():
    """Update dashboard data."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Update sections based on provided data
        if "trading" in data:
            update_trading_metrics(data["trading"])
        
        if "brokers" in data:
            for broker_id, broker_data in data["brokers"].items():
                update_broker_status(
                    broker_id,
                    broker_data.get("status"),
                    broker_data.get("session_count")
                )
        
        if "strategies" in data:
            update_strategy_info(
                data["strategies"].get("active_strategy"),
                data["strategies"].get("available_strategies"),
                data["strategies"].get("last_mutation")
            )
        
        if "signals" in data:
            update_signal_metrics(data["signals"])
        
        if "health" in data:
            update_health_status(
                data["health"].get("overall_status"),
                data["health"].get("recovery_events"),
                data["health"].get("last_recovery"),
                data["health"].get("issues")
            )
        
        # Always update system metrics
        update_system_metrics()
        
        return jsonify({
            "status": "success",
            "message": "Dashboard updated successfully"
        })
    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500