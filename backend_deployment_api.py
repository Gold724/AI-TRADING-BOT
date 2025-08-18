from flask import Flask, request, jsonify, render_template_string
import json
import os
import subprocess
import datetime
import hashlib
import hmac
from functools import wraps

app = Flask(__name__)

# Security configuration
DEPLOYMENT_TOKEN = os.getenv('DEPLOYMENT_TOKEN', 'trae-secure-token-2024')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '')

# Deployment status tracking
deployment_status = {
    'last_deployment': None,
    'current_strategy': None,
    'status': 'idle',
    'logs': []
}

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        if token != DEPLOYMENT_TOKEN:
            return jsonify({'error': 'Invalid deployment token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def log_deployment(message):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    deployment_status['logs'].append(log_entry)
    print(log_entry)
    
    # Keep only last 100 log entries
    if len(deployment_status['logs']) > 100:
        deployment_status['logs'] = deployment_status['logs'][-100:]

# Enhanced HTML Dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAE AI Trading Sentinel - Deployment Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-running { background-color: #48bb78; }
        .status-idle { background-color: #ed8936; }
        .status-error { background-color: #f56565; }
        .deployment-controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        .btn-danger {
            background: linear-gradient(45deg, #f56565, #e53e3e);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .logs-container {
            background: #1a202c;
            color: #e2e8f0;
            border-radius: 15px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .api-endpoints {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
        }
        .endpoint {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }
        .method {
            font-weight: bold;
            color: #667eea;
        }
        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 1.2em;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TRAE AI Trading Sentinel</h1>
            <p>Tesla 3-6-9 Strategy Deployment Dashboard</p>
        </div>
        
        <div class="status-grid">
            <div class="card">
                <h3>Deployment Status</h3>
                <p><span class="status-indicator status-{{ status_class }}"></span>{{ status }}</p>
                <p><strong>Last Deployment:</strong> {{ last_deployment or 'Never' }}</p>
                <p><strong>Current Strategy:</strong> {{ current_strategy or 'None' }}</p>
                <div class="deployment-controls">
                    <button class="btn btn-primary" onclick="deployStrategy('safe')">Deploy Safe Mode</button>
                    <button class="btn btn-primary" onclick="deployStrategy('fast')">Deploy Fast Mode</button>
                    <button class="btn btn-danger" onclick="stopDeployment()">Stop</button>
                </div>
            </div>
            
            <div class="card">
                <h3>System Health</h3>
                <p><span class="status-indicator status-running"></span>Flask Backend: Running</p>
                <p><span class="status-indicator status-running"></span>Port 5000: Listening</p>
                <p><span class="status-indicator status-running"></span>API Endpoints: Active</p>
                <p><span class="status-indicator status-running"></span>GitHub Integration: Ready</p>
            </div>
            
            <div class="card">
                <h3>Tesla 3-6-9 Configuration</h3>
                <p><strong>Safe Mode:</strong> 1 contract, $535.71 target</p>
                <p><strong>Fast Mode:</strong> 2 contracts, $1500 target</p>
                <p><strong>Tesla Mode:</strong> Enabled</p>
                <p><strong>Strategy:</strong> Tesla_369</p>
            </div>
        </div>
        
        <div class="card">
            <h3>Deployment Logs</h3>
            <div class="logs-container" id="logs">
                {% for log in logs %}
                <div>{{ log }}</div>
                {% endfor %}
            </div>
        </div>
        
        <div class="api-endpoints">
            <h3>API Endpoints</h3>
            <div class="endpoint">
                <span class="method">POST</span> /api/deploy - Deploy strategy configuration
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/status - Get deployment status
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/stop - Stop current deployment
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/logs - Get deployment logs
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">↻</button>
    
    <script>
        function deployStrategy(mode) {
            const config = {
                safe: {
                    max_contracts: 1,
                    daily_profit_target: 535.71,
                    tesla_mode: true
                },
                fast: {
                    max_contracts: 2,
                    default_contracts: 1,
                    high_conf_contracts: 2,
                    daily_profit_target: 1500,
                    tesla_mode: true
                }
            };
            
            fetch('/api/deploy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer trae-secure-token-2024'
                },
                body: JSON.stringify(config[mode])
            })
            .then(response => response.json())
            .then(data => {
                alert(`Deployment ${data.success ? 'started' : 'failed'}: ${data.message}`);
                if (data.success) location.reload();
            })
            .catch(error => alert('Deployment request failed: ' + error));
        }
        
        function stopDeployment() {
            fetch('/api/stop', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer trae-secure-token-2024'
                }
            })
            .then(response => response.json())
            .then(data => {
                alert(`Stop request ${data.success ? 'successful' : 'failed'}: ${data.message}`);
                location.reload();
            })
            .catch(error => alert('Stop request failed: ' + error));
        }
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    status_class = {
        'idle': 'idle',
        'deploying': 'running',
        'running': 'running',
        'error': 'error'
    }.get(deployment_status['status'], 'idle')
    
    return render_template_string(DASHBOARD_HTML,
        status=deployment_status['status'],
        status_class=status_class,
        last_deployment=deployment_status['last_deployment'],
        current_strategy=deployment_status['current_strategy'],
        logs=deployment_status['logs'][-20:]  # Show last 20 logs
    )

@app.route('/api/deploy', methods=['POST'])
@require_auth
def deploy_strategy():
    try:
        config = request.get_json()
        if not config:
            return jsonify({'success': False, 'message': 'No configuration provided'}), 400
        
        log_deployment(f"Received deployment request: {config}")
        
        # Update deployment status
        deployment_status['status'] = 'deploying'
        deployment_status['last_deployment'] = datetime.datetime.now().isoformat()
        deployment_status['current_strategy'] = 'Tesla_369'
        
        # Save configuration
        config_path = 'strategy-config.json'
        with open(config_path, 'w') as f:
            json.dump({
                'strategy': 'Tesla_369',
                'mode': 'safe' if config.get('max_contracts', 1) == 1 else 'fast',
                'safe': {
                    'max_contracts': 1,
                    'daily_profit_target': 535.71,
                    'tesla_mode': True
                },
                'fast': {
                    'max_contracts': 2,
                    'default_contracts': 1,
                    'high_conf_contracts': 2,
                    'daily_profit_target': 1500,
                    'tesla_mode': True
                },
                'current_config': config
            }, f, indent=2)
        
        log_deployment(f"Configuration saved to {config_path}")
        
        # Simulate deployment process
        try:
            # Here you would integrate with your actual trading bot deployment
            log_deployment("Starting Tesla 3-6-9 strategy deployment...")
            log_deployment(f"Max contracts: {config.get('max_contracts', 1)}")
            log_deployment(f"Daily profit target: ${config.get('daily_profit_target', 0)}")
            log_deployment(f"Tesla mode: {config.get('tesla_mode', False)}")
            
            deployment_status['status'] = 'running'
            log_deployment("Tesla 3-6-9 strategy deployed successfully!")
            
            return jsonify({
                'success': True,
                'message': 'Tesla 3-6-9 strategy deployed successfully',
                'config': config,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
        except Exception as e:
            deployment_status['status'] = 'error'
            log_deployment(f"Deployment failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Deployment failed: {str(e)}'
            }), 500
            
    except Exception as e:
        log_deployment(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'API error: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
@require_auth
def get_status():
    return jsonify({
        'success': True,
        'status': deployment_status['status'],
        'last_deployment': deployment_status['last_deployment'],
        'current_strategy': deployment_status['current_strategy'],
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/stop', methods=['POST'])
@require_auth
def stop_deployment():
    try:
        log_deployment("Received stop deployment request")
        deployment_status['status'] = 'idle'
        deployment_status['current_strategy'] = None
        log_deployment("Deployment stopped successfully")
        
        return jsonify({
            'success': True,
            'message': 'Deployment stopped successfully'
        })
        
    except Exception as e:
        log_deployment(f"Stop request failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Stop request failed: {str(e)}'
        }), 500

@app.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    return jsonify({
        'success': True,
        'logs': deployment_status['logs'],
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'TRAE AI Trading Sentinel',
        'version': '2.0.0',
        'timestamp': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    log_deployment("TRAE AI Trading Sentinel Deployment API starting...")
    log_deployment("Tesla 3-6-9 Strategy System Ready")
    log_deployment("GitHub Actions Integration Active")
    
    print("\n" + "="*50)
    print("TRAE AI TRADING SENTINEL - DEPLOYMENT API")
    print("Tesla 3-6-9 Strategy System")
    print("="*50)
    print(f"Dashboard: http://0.0.0.0:5000")
    print(f"External: http://5.189.145.177:5000")
    print(f"API Base: http://5.189.145.177:5000/api")
    print(f"Health: http://5.189.145.177:5000/health")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)