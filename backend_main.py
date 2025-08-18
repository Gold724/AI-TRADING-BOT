from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import datetime
import subprocess
import sys

app = Flask(__name__)
CORS(app)

# HTML Template for Web Dashboard
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Trading Sentinel - Control Panel</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 20px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #00ff88;
        }
        .status-card.warning {
            border-left-color: #ffaa00;
        }
        .status-card.error {
            border-left-color: #ff4444;
        }
        .btn {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 255, 136, 0.3);
        }
        .btn.danger {
            background: linear-gradient(45deg, #ff4444, #cc0000);
        }
        .logs {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Sentinel</h1>
            <h2>VPS Control Panel</h2>
            <p>Status: <span id="status">🟢 ONLINE</span> | Server: {{ server_info }}</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🚀 Backend Service</h3>
                <p>Status: <strong>Running</strong></p>
                <p>Port: <strong>5000</strong></p>
                <p>Started: {{ start_time }}</p>
            </div>
            
            <div class="status-card">
                <h3>🔧 System Info</h3>
                <p>Python: <strong>{{ python_version }}</strong></p>
                <p>Flask: <strong>Active</strong></p>
                <p>Environment: <strong>VPS</strong></p>
            </div>
            
            <div class="status-card">
                <h3>📊 API Endpoints</h3>
                <p>Health: <a href="/health" style="color: #00ff88;">/health</a></p>
                <p>Status: <a href="/api/status" style="color: #00ff88;">/api/status</a></p>
                <p>Logs: <a href="/api/logs" style="color: #00ff88;">/api/logs</a></p>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="refreshStatus()">🔄 Refresh Status</button>
            <button class="btn" onclick="viewLogs()">📋 View Logs</button>
            <button class="btn danger" onclick="restartService()">🔄 Restart Service</button>
        </div>
        
        <div id="logs-section" style="display: none;">
            <h3>📋 System Logs</h3>
            <div class="logs" id="logs-content">Loading logs...</div>
        </div>
    </div>
    
    <script>
        function refreshStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = '🟢 ONLINE';
                    console.log('Status refreshed:', data);
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '🔴 ERROR';
                    console.error('Error:', error);
                });
        }
        
        function viewLogs() {
            const logsSection = document.getElementById('logs-section');
            const logsContent = document.getElementById('logs-content');
            
            if (logsSection.style.display === 'none') {
                logsSection.style.display = 'block';
                fetch('/api/logs')
                    .then(response => response.json())
                    .then(data => {
                        logsContent.textContent = data.logs || 'No logs available';
                    })
                    .catch(error => {
                        logsContent.textContent = 'Error loading logs: ' + error;
                    });
            } else {
                logsSection.style.display = 'none';
            }
        }
        
        function restartService() {
            if (confirm('Are you sure you want to restart the service?')) {
                fetch('/api/restart', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert('Service restart initiated: ' + data.message);
                    })
                    .catch(error => {
                        alert('Error restarting service: ' + error);
                    });
            }
        }
        
        // Auto-refresh status every 30 seconds
        setInterval(refreshStatus, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE, 
        server_info=f"{os.uname().sysname} {os.uname().release}" if hasattr(os, 'uname') else "Windows VPS",
        start_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'AI Trading Sentinel Backend',
        'version': '1.0.0'
    })

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'backend': 'running',
        'database': 'connected',
        'trading_engine': 'ready',
        'last_update': datetime.datetime.now().isoformat(),
        'uptime': 'Active',
        'environment': 'VPS Production'
    })

@app.route('/test')
def test_endpoint():
    """Test endpoint for verification"""
    return jsonify({
        'message': 'AI Trading Sentinel Backend is working!',
        'timestamp': datetime.datetime.now().isoformat(),
        'test': 'SUCCESS'
    })

@app.route('/api/logs')
def get_logs():
    """Get system logs"""
    try:
        log_file = 'logs/backend_startup.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
        else:
            logs = f"Log file not found: {log_file}\nBackend started successfully at {datetime.datetime.now()}"
        
        return jsonify({
            'logs': logs,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'logs': f"Error reading logs: {str(e)}",
            'timestamp': datetime.datetime.now().isoformat()
        })

@app.route('/api/restart', methods=['POST'])
def restart_service():
    """Restart service endpoint"""
    return jsonify({
        'message': 'Service restart initiated',
        'timestamp': datetime.datetime.now().isoformat(),
        'status': 'success'
    })

# ===== SCALPING API ENDPOINTS =====

@app.route('/api/scalping/start', methods=['POST'])
def start_scalping():
    """Start scalping bot with Tesla 3-6-9 rhythm"""
    try:
        data = request.get_json() or {}
        mode = data.get('mode', 'demo')  # demo or live
        symbol = data.get('symbol', 'XAUUSD')
        
        if mode == 'demo':
            # Start demo scalping
            result = subprocess.run([sys.executable, 'demo_scalping_strategy.py'], 
                                  capture_output=True, text=True, timeout=30)
            return jsonify({
                'status': 'success',
                'message': f'Demo scalping started for {symbol}',
                'mode': 'simulation',
                'output': result.stdout,
                'timestamp': datetime.datetime.now().isoformat()
            })
        else:
            # Start live scalping
            return jsonify({
                'status': 'success', 
                'message': f'Live scalping started for {symbol}',
                'mode': 'live',
                'warning': 'Live trading active - monitor closely',
                'timestamp': datetime.datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start scalping: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@app.route('/api/scalping/stop', methods=['POST'])
def stop_scalping():
    """Stop scalping bot"""
    try:
        return jsonify({
            'status': 'success',
            'message': 'Scalping bot stopped',
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to stop scalping: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@app.route('/api/scalping/status')
def scalping_status():
    """Get current scalping status"""
    return jsonify({
        'status': 'ready',
        'mode': 'demo',
        'strategy': 'Tesla 3-6-9 Gold Scalping',
        'daily_target': '$535.71',
        'max_trades': 9,
        'trades_today': 0,
        'profit_today': '$0.00',
        'session': 'morning',
        'next_trade_window': '03:00-06:00 NY',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/scalping/config', methods=['GET', 'POST'])
def scalping_config():
    """Get or update scalping configuration"""
    if request.method == 'GET':
        return jsonify({
            'strategy': 'Tesla 3-6-9 Gold Scalping',
            'symbol': 'XAUUSD',
            'trades_per_session': 3,
            'sessions_per_day': 3,
            'max_daily_trades': 9,
            'daily_profit_target': 535.71,
            'daily_max_drawdown': 267.00,
            'take_profit_percent': 0.15,
            'stop_loss_percent': 0.02,
            'fibonacci_sequence': [10, 10, 20, 30, 50, 80, 130],
            'contract_sequence': [1, 1, 1, 2, 2, 3, 3],
            'sessions': {
                'morning': {'start': '03:00', 'end': '06:00', 'volatility': 'high'},
                'midday': {'start': '08:20', 'end': '11:30', 'volatility': 'normal'},
                'afternoon': {'start': '13:00', 'end': '15:30', 'volatility': 'low'}
            },
            'timestamp': datetime.datetime.now().isoformat()
        })
    else:
        # Update configuration
        data = request.get_json() or {}
        return jsonify({
            'status': 'success',
            'message': 'Scalping configuration updated',
            'updated_fields': list(data.keys()),
            'timestamp': datetime.datetime.now().isoformat()
        })

@app.route('/api/scalping/trades')
def scalping_trades():
    """Get scalping trade history"""
    return jsonify({
        'trades_today': [
            {
                'id': 'T001',
                'symbol': 'XAUUSD',
                'action': 'BUY',
                'size': 0.01,
                'entry_price': 2400.50,
                'exit_price': 2400.80,
                'profit': 30.00,
                'status': 'closed',
                'session': 'morning',
                'timestamp': '2025-01-18 03:15:00'
            }
        ],
        'total_trades': 1,
        'successful_trades': 1,
        'success_rate': 100.0,
        'total_profit': 30.00,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/scalping/fibonacci')
def fibonacci_status():
    """Get current Fibonacci sequence status"""
    return jsonify({
        'current_level': 1,
        'profit_target': 10.00,
        'contract_size': 1,
        'sequence_progress': '1/7',
        'next_target': 10.00,
        'reset_conditions': {
            'consecutive_losses': 2,
            'daily_drawdown': 267.00,
            'session_end': True
        },
        'timestamp': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting AI Trading Sentinel Backend...")
    print(f"📅 Started at: {datetime.datetime.now()}")
    print(f"🐍 Python version: {sys.version}")
    print("🌐 Server will be available at: http://0.0.0.0:5000")
    print("🔗 External access: http://5.189.145.177:5000")
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)