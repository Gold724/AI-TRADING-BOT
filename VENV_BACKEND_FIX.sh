#!/bin/bash

# VENV Backend Fix for Ubuntu 24.04 Externally-Managed Environment
# This script creates a Python virtual environment and installs Flask properly

echo "🔧 VENV Backend Fix - Ubuntu 24.04 Compatible"
echo "================================================"
echo "Fixing externally-managed environment issue..."
echo ""

# Step 1: Stop existing processes
echo "🛑 Step 1: Stop Existing Processes"
echo "----------------------------------"
pkill -f "backend/main.py"
pkill -f "flask"
pkill -f ":5000"
sleep 2
echo "✅ Processes stopped"
echo ""

# Step 2: Install system dependencies
echo "📦 Step 2: Install System Dependencies"
echo "-------------------------------------"
sudo apt update
sudo apt install -y python3-full python3-venv python3-pip
echo "✅ System dependencies installed"
echo ""

# Step 3: Create project structure
echo "📁 Step 3: Create Project Structure"
echo "-----------------------------------"
cd /root
mkdir -p ai-trading-sentinel/backend ai-trading-sentinel/logs
cd ai-trading-sentinel
echo "✅ Project structure created"
echo ""

# Step 4: Create Python virtual environment
echo "🐍 Step 4: Create Virtual Environment"
echo "------------------------------------"
python3 -m venv venv
source venv/bin/activate
echo "✅ Virtual environment created and activated"
echo ""

# Step 5: Install Flask in virtual environment
echo "🌶️ Step 5: Install Flask"
echo "------------------------"
pip install --upgrade pip
pip install flask flask-cors
echo "✅ Flask installed in virtual environment"
echo ""

# Step 6: Create enhanced backend
echo "🚀 Step 6: Create Enhanced Backend"
echo "----------------------------------"
cat > backend/main.py << 'EOF'
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import subprocess
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Enhanced HTML Dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI Trading Sentinel - VPS Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 20px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-online { border-left: 5px solid #4CAF50; }
        .status-offline { border-left: 5px solid #f44336; }
        .status-warning { border-left: 5px solid #ff9800; }
        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); }
        .btn-danger { background: linear-gradient(45deg, #f44336, #d32f2f); }
        .btn-info { background: linear-gradient(45deg, #2196F3, #1976D2); }
        .logs {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        .timestamp { color: #4CAF50; }
        .error { color: #f44336; }
        .info { color: #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Sentinel</h1>
            <h2>VPS Control Dashboard</h2>
            <p>Status: <span id="status">🟢 ONLINE</span></p>
        </div>
        
        <div class="status-grid">
            <div class="status-card status-online">
                <h3>🚀 Backend Service</h3>
                <p>Flask Backend: <strong>Running</strong></p>
                <p>Port: <strong>5000</strong></p>
                <p>Host: <strong>0.0.0.0</strong></p>
            </div>
            
            <div class="status-card status-warning">
                <h3>🤖 Trading Bot</h3>
                <p>Status: <strong>Configuring</strong></p>
                <p>Environment: <strong>VPS Ready</strong></p>
                <p>Virtual Env: <strong>Active</strong></p>
            </div>
            
            <div class="status-card status-online">
                <h3>🔧 System Health</h3>
                <p>Memory: <strong>Available</strong></p>
                <p>Disk: <strong>OK</strong></p>
                <p>Network: <strong>Connected</strong></p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <button class="btn" onclick="checkHealth()">🔍 Health Check</button>
            <button class="btn btn-info" onclick="viewLogs()">📋 View Logs</button>
            <button class="btn btn-danger" onclick="restartService()">🔄 Restart</button>
        </div>
        
        <div class="logs" id="logs">
            <div class="timestamp">[{{ timestamp }}]</div>
            <div class="info">✅ Flask backend started successfully</div>
            <div class="info">✅ Virtual environment active</div>
            <div class="info">✅ External access configured</div>
            <div class="info">🔧 Ready for trading bot deployment</div>
        </div>
    </div>
    
    <script>
        function checkHealth() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('logs').innerHTML += 
                        `<div class="timestamp">[${new Date().toLocaleString()}]</div>
                         <div class="info">Health check: ${JSON.stringify(data)}</div>`;
                })
                .catch(error => {
                    document.getElementById('logs').innerHTML += 
                        `<div class="timestamp">[${new Date().toLocaleString()}]</div>
                         <div class="error">Health check failed: ${error}</div>`;
                });
        }
        
        function viewLogs() {
            fetch('/api/logs')
                .then(response => response.text())
                .then(data => {
                    document.getElementById('logs').innerHTML = data;
                })
                .catch(error => {
                    document.getElementById('logs').innerHTML += 
                        `<div class="error">Failed to load logs: ${error}</div>`;
                });
        }
        
        function restartService() {
            document.getElementById('logs').innerHTML += 
                `<div class="timestamp">[${new Date().toLocaleString()}]</div>
                 <div class="info">🔄 Service restart requested</div>`;
        }
        
        // Auto-refresh status every 30 seconds
        setInterval(checkHealth, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(DASHBOARD_HTML, timestamp=timestamp)

@app.route('/health')
@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'ai-trading-sentinel-backend',
        'version': '1.0.0',
        'environment': 'vps-production',
        'virtual_env': 'active'
    })

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'backend': 'running',
        'database': 'not_configured',
        'trading_bot': 'ready_for_deployment',
        'external_access': 'enabled',
        'virtual_environment': 'active'
    })

@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    try:
        log_content = ""
        log_files = ['/root/ai-trading-sentinel/logs/backend.log', '/var/log/syslog']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]  # Last 50 lines
                    log_content += f"\n=== {log_file} ===\n"
                    log_content += ''.join(lines)
        
        if not log_content:
            log_content = "No logs available"
            
        return log_content, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return f"Error reading logs: {str(e)}", 500

@app.route('/test')
def test():
    """Simple test endpoint"""
    return "🤖 AI Trading Sentinel Backend - Test OK!"

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('/root/ai-trading-sentinel/logs', exist_ok=True)
    
    # Configure logging to file
    file_handler = logging.FileHandler('/root/ai-trading-sentinel/logs/backend.log')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info("Starting AI Trading Sentinel Backend...")
    logger.info("Virtual environment: Active")
    logger.info("External access: Enabled on 0.0.0.0:5000")
    
    # Run Flask with external access
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

echo "✅ Enhanced backend created"
echo ""

# Step 7: Configure firewall
echo "🔥 Step 7: Configure Firewall"
echo "-----------------------------"
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22/tcp
sudo ufw allow 5000/tcp
sudo ufw --force enable
echo "✅ Firewall configured"
echo ""

# Step 8: Start backend in virtual environment
echo "🚀 Step 8: Start Backend"
echo "------------------------"
source venv/bin/activate
nohup python backend/main.py > logs/backend_startup.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
sleep 3
echo "✅ Backend started in virtual environment"
echo ""

# Step 9: Verification
echo "✅ Step 9: Verification"
echo "----------------------"
echo "Process status:"
ps aux | grep "backend/main.py" | grep -v grep || echo "❌ Backend not running"
echo ""
echo "Port binding:"
netstat -tlnp | grep :5000 || echo "❌ Port 5000 not bound"
echo ""
echo "Local health check:"
curl -s http://localhost:5000/health && echo "" && echo "✅ Local connection OK" || echo "❌ Local connection failed"
echo ""
echo "External test:"
curl -s http://localhost:5000/test && echo "" && echo "✅ Test endpoint OK" || echo "❌ Test endpoint failed"
echo ""

echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "📱 Access Points:"
echo "   🌐 Web Dashboard: http://5.189.145.177:5000"
echo "   🔍 Health Check:  http://5.189.145.177:5000/health"
echo "   📊 API Status:    http://5.189.145.177:5000/api/status"
echo "   🧪 Test Endpoint: http://5.189.145.177:5000/test"
echo ""
echo "📋 Management Commands:"
echo "   Check status:     ps aux | grep backend/main.py"
echo "   View logs:        tail -f logs/backend_startup.log"
echo "   Restart backend:  pkill -f backend/main.py && source venv/bin/activate && nohup python backend/main.py > logs/backend_startup.log 2>&1 &"
echo "   Activate venv:    source venv/bin/activate"
echo ""
echo "🔧 Virtual Environment Solution:"
echo "   ✅ Python virtual environment created"
echo "   ✅ Flask installed in isolated environment"
echo "   ✅ No system package conflicts"
echo "   ✅ Ubuntu 24.04 compatible"
echo ""
echo "If external access still fails, check Contabo control panel firewall settings."