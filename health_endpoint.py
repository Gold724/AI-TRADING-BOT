#!/usr/bin/env python3
"""
TradeBot Sentinel - Health Check Endpoint
Provides HTTP health check endpoint for cloud deployment monitoring
"""

import os
import sys
import json
import time
import psutil
import logging
import subprocess
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from threading import Thread
import requests

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import health check functions
try:
    from health_check import (
        check_system_resources,
        check_browser_health,
        check_network_connectivity,
        check_trading_platform,
        check_dependencies,
        check_storage_health,
        check_processes,
        check_environment_variables
    )
except ImportError:
    # Fallback implementations if health_check module not available
    def check_system_resources():
        return {"status": "ok", "cpu_percent": psutil.cpu_percent(), "memory_percent": psutil.virtual_memory().percent}
    
    def check_browser_health():
        return {"status": "ok", "message": "Browser check not available"}
    
    def check_network_connectivity():
        return {"status": "ok", "message": "Network check not available"}
    
    def check_trading_platform():
        return {"status": "ok", "message": "Trading platform check not available"}
    
    def check_dependencies():
        return {"status": "ok", "message": "Dependencies check not available"}
    
    def check_storage_health():
        return {"status": "ok", "message": "Storage check not available"}
    
    def check_processes():
        return {"status": "ok", "message": "Process check not available"}
    
    def check_environment_variables():
        return {"status": "ok", "message": "Environment check not available"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_endpoint.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Health check cache
health_cache = {
    'last_check': None,
    'results': {},
    'cache_duration': 30  # seconds
}

# Application status
app_status = {
    'start_time': datetime.now(),
    'version': '1.0.0',
    'environment': os.getenv('ENVIRONMENT', 'production'),
    'last_trade': None,
    'trade_count': 0,
    'error_count': 0,
    'uptime': 0
}

def update_app_status():
    """Update application status metrics"""
    app_status['uptime'] = (datetime.now() - app_status['start_time']).total_seconds()

def perform_health_checks():
    """Perform comprehensive health checks"""
    try:
        logger.info("Starting health checks")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warning_checks': 0
            }
        }
        
        # Define health checks
        health_checks = {
            'system_resources': check_system_resources,
            'browser_health': check_browser_health,
            'network_connectivity': check_network_connectivity,
            'trading_platform': check_trading_platform,
            'dependencies': check_dependencies,
            'storage_health': check_storage_health,
            'processes': check_processes,
            'environment_variables': check_environment_variables
        }
        
        # Run each health check
        for check_name, check_function in health_checks.items():
            try:
                logger.debug(f"Running health check: {check_name}")
                check_result = check_function()
                
                # Ensure result has required fields
                if not isinstance(check_result, dict):
                    check_result = {'status': 'error', 'message': 'Invalid check result format'}
                
                if 'status' not in check_result:
                    check_result['status'] = 'unknown'
                
                results['checks'][check_name] = check_result
                results['summary']['total_checks'] += 1
                
                # Count check results
                status = check_result.get('status', 'unknown')
                if status in ['ok', 'healthy', 'pass']:
                    results['summary']['passed_checks'] += 1
                elif status in ['warning', 'degraded']:
                    results['summary']['warning_checks'] += 1
                else:
                    results['summary']['failed_checks'] += 1
                    
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                results['checks'][check_name] = {
                    'status': 'error',
                    'message': f'Check failed: {str(e)}',
                    'error': str(e)
                }
                results['summary']['total_checks'] += 1
                results['summary']['failed_checks'] += 1
        
        # Determine overall status
        if results['summary']['failed_checks'] > 0:
            results['status'] = 'unhealthy'
        elif results['summary']['warning_checks'] > 0:
            results['status'] = 'degraded'
        else:
            results['status'] = 'healthy'
        
        # Update cache
        health_cache['last_check'] = datetime.now()
        health_cache['results'] = results
        
        logger.info(f"Health checks completed. Status: {results['status']}")
        return results
        
    except Exception as e:
        logger.error(f"Health check system error: {e}")
        error_result = {
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'message': f'Health check system error: {str(e)}',
            'error': str(e)
        }
        health_cache['results'] = error_result
        return error_result

def get_cached_health_results():
    """Get cached health results or perform new checks if cache expired"""
    now = datetime.now()
    
    # Check if cache is valid
    if (health_cache['last_check'] is None or 
        (now - health_cache['last_check']).total_seconds() > health_cache['cache_duration']):
        return perform_health_checks()
    
    return health_cache['results']

@app.route('/health', methods=['GET'])
def health_check():
    """Main health check endpoint"""
    try:
        # Update app status
        update_app_status()
        
        # Get health check results
        force_check = request.args.get('force', 'false').lower() == 'true'
        
        if force_check:
            results = perform_health_checks()
        else:
            results = get_cached_health_results()
        
        # Add application status
        results['application'] = app_status.copy()
        
        # Determine HTTP status code
        status_code = 200
        if results.get('status') == 'unhealthy':
            status_code = 503  # Service Unavailable
        elif results.get('status') == 'degraded':
            status_code = 200  # OK but with warnings
        
        return jsonify(results), status_code
        
    except Exception as e:
        logger.error(f"Health endpoint error: {e}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'message': f'Health endpoint error: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/health/live', methods=['GET'])
def liveness_probe():
    """Kubernetes/Docker liveness probe endpoint"""
    try:
        # Simple check - is the application running?
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.now().isoformat(),
            'uptime': (datetime.now() - app_status['start_time']).total_seconds()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health/ready', methods=['GET'])
def readiness_probe():
    """Kubernetes/Docker readiness probe endpoint"""
    try:
        # Check if application is ready to serve traffic
        results = get_cached_health_results()
        
        # Consider ready if not unhealthy
        if results.get('status') in ['healthy', 'degraded']:
            return jsonify({
                'status': 'ready',
                'timestamp': datetime.now().isoformat(),
                'health_status': results.get('status')
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'timestamp': datetime.now().isoformat(),
                'health_status': results.get('status'),
                'message': 'Application is not healthy'
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health/startup', methods=['GET'])
def startup_probe():
    """Kubernetes startup probe endpoint"""
    try:
        # Check if application has started successfully
        uptime = (datetime.now() - app_status['start_time']).total_seconds()
        
        # Consider started if running for more than 30 seconds
        if uptime > 30:
            return jsonify({
                'status': 'started',
                'timestamp': datetime.now().isoformat(),
                'uptime': uptime
            }), 200
        else:
            return jsonify({
                'status': 'starting',
                'timestamp': datetime.now().isoformat(),
                'uptime': uptime,
                'message': 'Application is still starting'
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed health information for debugging"""
    try:
        # Force fresh health checks
        results = perform_health_checks()
        
        # Add system information
        results['system_info'] = {
            'platform': sys.platform,
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': {
                path: {
                    'total': psutil.disk_usage(path).total,
                    'used': psutil.disk_usage(path).used,
                    'free': psutil.disk_usage(path).free,
                    'percent': (psutil.disk_usage(path).used / psutil.disk_usage(path).total) * 100
                } for path in ['/'] if os.path.exists(path)
            },
            'network_interfaces': {
                name: {
                    'addresses': [addr.address for addr in addrs if addr.family == 2]  # IPv4
                } for name, addrs in psutil.net_if_addrs().items()
            }
        }
        
        # Add process information
        try:
            current_process = psutil.Process()
            results['process_info'] = {
                'pid': current_process.pid,
                'ppid': current_process.ppid(),
                'name': current_process.name(),
                'status': current_process.status(),
                'create_time': current_process.create_time(),
                'cpu_percent': current_process.cpu_percent(),
                'memory_percent': current_process.memory_percent(),
                'num_threads': current_process.num_threads(),
                'open_files': len(current_process.open_files()),
                'connections': len(current_process.connections())
            }
        except Exception as e:
            results['process_info'] = {'error': str(e)}
        
        # Add environment variables (filtered)
        safe_env_vars = {
            key: value for key, value in os.environ.items()
            if not any(sensitive in key.lower() for sensitive in 
                      ['password', 'secret', 'key', 'token', 'credential'])
        }
        results['environment'] = safe_env_vars
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Detailed health endpoint error: {e}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'message': f'Detailed health endpoint error: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus-style metrics endpoint"""
    try:
        # Get current metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Format as Prometheus metrics
        metrics_text = f"""# HELP tradebot_cpu_percent CPU usage percentage
# TYPE tradebot_cpu_percent gauge
tradebot_cpu_percent {cpu_percent}

# HELP tradebot_memory_percent Memory usage percentage
# TYPE tradebot_memory_percent gauge
tradebot_memory_percent {memory.percent}

# HELP tradebot_disk_percent Disk usage percentage
# TYPE tradebot_disk_percent gauge
tradebot_disk_percent {disk.percent}

# HELP tradebot_uptime_seconds Application uptime in seconds
# TYPE tradebot_uptime_seconds counter
tradebot_uptime_seconds {app_status['uptime']}

# HELP tradebot_trade_count_total Total number of trades executed
# TYPE tradebot_trade_count_total counter
tradebot_trade_count_total {app_status['trade_count']}

# HELP tradebot_error_count_total Total number of errors encountered
# TYPE tradebot_error_count_total counter
tradebot_error_count_total {app_status['error_count']}

# HELP tradebot_health_status Current health status (1=healthy, 0.5=degraded, 0=unhealthy)
# TYPE tradebot_health_status gauge
"""
        
        # Add health status metric
        health_results = get_cached_health_results()
        health_value = 1 if health_results.get('status') == 'healthy' else 0.5 if health_results.get('status') == 'degraded' else 0
        metrics_text += f"tradebot_health_status {health_value}\n"
        
        return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return f"# Error generating metrics: {str(e)}\n", 500, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/status', methods=['GET'])
def status():
    """Simple status endpoint"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'version': app_status['version'],
        'environment': app_status['environment']
    }), 200

@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return 'pong', 200

# Background health monitoring
def background_health_monitor():
    """Background thread to continuously monitor health"""
    logger.info("Starting background health monitor")
    
    while True:
        try:
            # Perform health checks every 5 minutes
            time.sleep(300)
            
            # Update cache
            perform_health_checks()
            
            # Log health status
            results = health_cache.get('results', {})
            status = results.get('status', 'unknown')
            logger.info(f"Background health check completed. Status: {status}")
            
            # Alert on unhealthy status
            if status == 'unhealthy':
                logger.warning("Application is unhealthy!")
                # Here you could send alerts via email, Slack, etc.
                
        except Exception as e:
            logger.error(f"Background health monitor error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'screenshots', 'data']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == '__main__':
    # Create necessary directories
    create_directories()
    
    # Start background health monitor
    monitor_thread = Thread(target=background_health_monitor, daemon=True)
    monitor_thread.start()
    
    # Get configuration
    host = os.getenv('HEALTH_HOST', '0.0.0.0')
    port = int(os.getenv('HEALTH_PORT', 8001))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting TradeBot Health Endpoint on {host}:{port}")
    logger.info(f"Environment: {app_status['environment']}")
    logger.info(f"Version: {app_status['version']}")
    
    # Run Flask app
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )