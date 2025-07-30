from flask import Blueprint, jsonify, request, current_app
import os
import json
import time
from datetime import datetime

# Import QuantConnect integration
try:
    from quantconnect_integration import QuantConnectIntegration
    qc_available = True
except ImportError:
    qc_available = False
    print("QuantConnect integration not available")

# Create blueprint
quantconnect_bp = Blueprint('quantconnect', __name__)

# Helper function to check if QuantConnect is configured
def is_qc_configured():
    """Check if QuantConnect integration is properly configured"""
    if not qc_available:
        return False
    
    qc_api_key = os.environ.get('QC_API_KEY')
    qc_project_id = os.environ.get('QC_PROJECT_ID')
    
    return qc_api_key and qc_project_id

@quantconnect_bp.route('/status', methods=['GET'])
def get_qc_status():
    """Get QuantConnect integration status"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured. Please set QC_API_KEY and QC_PROJECT_ID in your .env file.'
        }), 400
    
    try:
        qc = QuantConnectIntegration()
        project = qc.get_project()
        
        if not project:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve project details from QuantConnect API'
            }), 500
        
        # Check live algorithm status
        live_status = qc.check_live_algorithm_status()
        
        return jsonify({
            'status': 'configured',
            'project': project,
            'live_algorithm': live_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error connecting to QuantConnect: {str(e)}'
        }), 500

@quantconnect_bp.route('/backtests', methods=['GET'])
def get_backtests():
    """Get list of backtests from QuantConnect"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        qc = QuantConnectIntegration()
        backtests = qc.list_backtests()
        
        return jsonify({
            'status': 'success',
            'backtests': backtests,
            'count': len(backtests) if backtests else 0,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving backtests: {str(e)}'
        }), 500

@quantconnect_bp.route('/backtest/<backtest_id>', methods=['GET'])
def get_backtest(backtest_id):
    """Get details of a specific backtest"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        qc = QuantConnectIntegration()
        backtest = qc.get_backtest(backtest_id)
        
        if not backtest:
            return jsonify({
                'status': 'error',
                'message': f'Backtest with ID {backtest_id} not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'backtest': backtest,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving backtest: {str(e)}'
        }), 500

@quantconnect_bp.route('/create-backtest', methods=['POST'])
def create_backtest():
    """Create a new backtest"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        data = request.json
        name = data.get('name', f'Sentinel Backtest {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        qc = QuantConnectIntegration()
        backtest_id = qc.create_backtest(name)
        
        if not backtest_id:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create backtest'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Backtest created successfully',
            'backtest_id': backtest_id,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error creating backtest: {str(e)}'
        }), 500

@quantconnect_bp.route('/deploy-live', methods=['POST'])
def deploy_live():
    """Deploy algorithm to live trading"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        data = request.json
        brokerage = data.get('brokerage', 'Interactive')
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({
                'status': 'error',
                'message': 'account_id is required'
            }), 400
        
        qc = QuantConnectIntegration()
        deployment_id = qc.deploy_live(brokerage, account_id)
        
        if not deployment_id:
            return jsonify({
                'status': 'error',
                'message': 'Failed to deploy algorithm to live trading'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Algorithm deployed to live trading',
            'deployment_id': deployment_id,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deploying to live trading: {str(e)}'
        }), 500

@quantconnect_bp.route('/stop-live', methods=['POST'])
def stop_live():
    """Stop live trading algorithm"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        qc = QuantConnectIntegration()
        success = qc.stop_live_algorithm()
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Failed to stop live algorithm'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Live algorithm stopped successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error stopping live algorithm: {str(e)}'
        }), 500

@quantconnect_bp.route('/equity', methods=['GET'])
def get_equity():
    """Get equity curve data"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        qc = QuantConnectIntegration()
        equity_data = qc.get_equity()
        
        return jsonify({
            'status': 'success',
            'equity': equity_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving equity data: {str(e)}'
        }), 500

@quantconnect_bp.route('/signals', methods=['GET'])
def get_signals():
    """Get latest trading signals from QuantConnect"""
    if not is_qc_configured():
        return jsonify({
            'status': 'not_configured',
            'message': 'QuantConnect integration is not configured'
        }), 400
    
    try:
        qc = QuantConnectIntegration()
        live_status = qc.check_live_algorithm_status()
        
        if not live_status or live_status.get('status') != 'Running':
            return jsonify({
                'status': 'not_running',
                'message': 'Live algorithm is not running',
                'live_status': live_status
            })
        
        # Get runtime statistics which should contain signals
        results = qc.get_live_results()
        signals = []
        
        if results and 'RuntimeStatistics' in results:
            runtime_stats = results['RuntimeStatistics']
            if 'Signals' in runtime_stats:
                try:
                    signals = json.loads(runtime_stats['Signals'])
                except:
                    pass
        
        return jsonify({
            'status': 'success',
            'signals': signals,
            'timestamp': datetime.now().isoformat(),
            'performance': {
                'drawdown': results.get('RuntimeStatistics', {}).get('Drawdown', 'N/A'),
                'total_return': results.get('RuntimeStatistics', {}).get('TotalReturn', 'N/A')
            } if results else {}
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving signals: {str(e)}'
        }), 500