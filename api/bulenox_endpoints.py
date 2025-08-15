#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Bulenox AI Controller
from bulenox_ai_controller import BulenoxAIController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'bulenox', 'api.log'), mode='a')
    ]
)

logger = logging.getLogger("trae.bulenox.api")

# Create logs directory
os.makedirs(os.path.join('logs', 'bulenox'), exist_ok=True)

# Create Blueprint
bulenox_bp = Blueprint('bulenox', __name__, url_prefix='/api/bulenox')

# Initialize controller
controller = None


def require_api_key(f):
    """Decorator to require API key for endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get API key from request
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'API key is required'
            }), 401
        
        # Check API key
        config_path = os.path.join('config', 'bulenox_controller_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check if API key is required and valid
                if config.get('security', {}).get('api_key_required', True):
                    expected_key = config.get('security', {}).get('api_key')
                    
                    # Check if expected key is an environment variable reference
                    if expected_key and expected_key.startswith('${') and expected_key.endswith('}'):
                        env_var = expected_key[2:-1]
                        expected_key = os.environ.get(env_var)
                    
                    if not expected_key or api_key != expected_key:
                        return jsonify({
                            'success': False,
                            'message': 'Invalid API key'
                        }), 401
            except Exception as e:
                logger.error(f"Error checking API key: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error checking API key: {str(e)}'
                }), 500
        
        return f(*args, **kwargs)
    return decorated


def get_controller() -> BulenoxAIController:
    """Get or initialize the Bulenox AI Controller.
    
    Returns:
        BulenoxAIController: The controller instance
    """
    global controller
    if controller is None:
        config_path = os.path.join('config', 'bulenox_controller_config.json')
        controller = BulenoxAIController(config_path=config_path)
        logger.info("Bulenox AI Controller initialized")
    return controller


@bulenox_bp.route('/status', methods=['GET'])
@require_api_key
def get_status():
    """Get the status of the Bulenox AI Controller."""
    try:
        controller = get_controller()
        health = controller.check_session_health()
        
        # Get Dreamer Mode status
        dreamer_mode = controller.config.get('dreamer_mode', {}).get('enabled', False)
        
        return jsonify({
            'success': True,
            'session': health,
            'dreamer_mode': dreamer_mode,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bulenox_bp.route('/session/start', methods=['POST'])
@require_api_key
def start_session():
    """Start a Bulenox trading session."""
    try:
        # Get parameters
        data = request.json or {}
        headless = data.get('headless')
        debug = data.get('debug')
        
        controller = get_controller()
        success = controller.start_session(headless=headless, debug=debug)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bulenox session started successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start Bulenox session'
            }), 500
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bulenox_bp.route('/session/end', methods=['POST'])
@require_api_key
def end_session():
    """End the Bulenox trading session."""
    try:
        controller = get_controller()
        success = controller.end_session()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bulenox session ended successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to end Bulenox session'
            }), 500
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bulenox_bp.route('/trade/execute', methods=['POST'])
@require_api_key
def execute_trade():
    """Execute a trade based on a signal."""
    try:
        # Get signal from request
        signal = request.json
        if not signal:
            return jsonify({
                'success': False,
                'message': 'No signal provided'
            }), 400
        
        # Validate signal
        required_fields = ['symbol', 'direction']
        for field in required_fields:
            if field not in signal:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Add signal ID if not present
        if 'signal_id' not in signal:
            signal['signal_id'] = f"bulenox_{int(time.time())}"
        
        # Execute trade
        controller = get_controller()
        result = controller.execute_trade(signal)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bulenox_bp.route('/dreamer/toggle', methods=['POST'])
@require_api_key
def toggle_dreamer_mode():
    """Toggle Dreamer Mode."""
    try:
        # Get parameters
        data = request.json or {}
        enabled = data.get('enabled')
        
        if enabled is None:
            return jsonify({
                'success': False,
                'message': 'Missing required field: enabled'
            }), 400
        
        # Toggle Dreamer Mode
        controller = get_controller()
        result = controller.toggle_dreamer_mode(enabled)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error toggling Dreamer Mode: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bulenox_bp.route('/logs', methods=['GET'])
@require_api_key
def get_logs():
    """Get Bulenox trade logs."""
    try:
        # Get parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        simulated = request.args.get('simulated', None)
        if simulated is not None:
            simulated = simulated.lower() == 'true'
        
        # Get logs
        trade_log_path = os.path.join('logs', 'bulenox', 'trades.json')
        if not os.path.exists(trade_log_path):
            return jsonify({
                'success': True,
                'logs': [],
                'total': 0,
                'limit': limit,
                'offset': offset
            })
        
        with open(trade_log_path, 'r') as f:
            logs = json.load(f)
        
        # Filter by simulated if specified
        if simulated is not None:
            logs = [log for log in logs if log.get('simulated', False) == simulated]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        total = len(logs)
        logs = logs[offset:offset+limit]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bulenox_bp.route('/test/signal', methods=['GET'])
@require_api_key
def get_test_signal():
    """Get a test signal for validation."""
    try:
        # Generate test signal
        test_signal = {
            'signal_id': f"test_{int(time.time())}",
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'quantity': 1,
            'take_profit': 50,
            'stop_loss': 30,
            'timestamp': datetime.now().isoformat(),
            'source': 'test'
        }
        
        return jsonify({
            'success': True,
            'signal': test_signal
        })
    except Exception as e:
        logger.error(f"Error generating test signal: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


def init_app(app):
    """Initialize the Flask app with Bulenox endpoints.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(bulenox_bp)
    logger.info("Bulenox API endpoints registered")