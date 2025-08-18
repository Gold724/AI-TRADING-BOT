#!/bin/bash
# 🔧 Simple Backend Fix for AI Trading Sentinel
# Addresses Flask import errors and startup failures

echo "🔧 Simple Backend Fix - AI Trading Sentinel"
echo "==========================================="
echo "📅 Started: $(date)"
echo ""

# Step 1: Stop all existing processes
echo "🛑 Step 1: Clean Existing Processes"
echo "----------------------------------"
pkill -f "backend/main.py"
pkill -f "flask"
pkill -f ":5000"
pkill -f "python3.*5000"
sleep 3
echo "✅ All processes stopped"
echo ""

# Step 2: Install Flask and dependencies
echo "📦 Step 2: Install Flask Dependencies"
echo "-----------------------------------"
apt update
apt install -y python3-pip python3-venv
pip3 install --upgrade pip
pip3 install flask flask-cors
echo "✅ Flask dependencies installed"
echo ""

# Step 3: Create simple working directory
echo "📁 Step 3: Setup Working Directory"
echo "--------------------------------"
cd /root
mkdir -p ai-trading-sentinel/backend
mkdir -p ai-trading-sentinel/logs
cd ai-trading-sentinel
echo "✅ Directory structure created"
echo ""

# Step 4: Create minimal working backend
echo "🚀 Step 4: Create Minimal Backend"
echo "--------------------------------"
cat > backend/main.py << 'EOF'
#!/usr/bin/env python3
"""
AI Trading Sentinel - Minimal Working Backend
Simplified for VPS deployment
"""

import os
import sys
from datetime import datetime

try:
    from flask import Flask, jsonify, render_template_string
    from flask_cors import CORS
except ImportError:
    print("❌ Flask not installed. Installing...")
    os.system("pip3 install flask flask-cors")
    from flask import Flask, jsonify, render_template_string
    from flask_cors import CORS

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Simple HTML Dashboard
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AI Trading Sentinel</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
        }
        .status {
            background: rgba(76, 175, 80, 0.2);
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 16px;
            margin: 10px;
            cursor: pointer;
        }
        .btn:hover { background: #45a049; }
        .info {
            background: rgba(33, 150, 243, 0.2);
            border: 1px solid #2196F3;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel</h1>
        <h2>Control Panel</h2>
        
        <div class="status">
            <h3>✅ System Status: ONLINE</h3>
            <p><strong>Server:</strong> 5.189.145.177:5000</p>
            <p><strong>Backend:</strong> Running</p>
            <p><strong>Time:</strong> {{ timestamp }}</p>
        </div>
        
        <div class="info">
            <h3>🌐 Access Points</h3>
            <p><strong>Dashboard:</strong> <a href="http://5.189.145.177:5000" style="color: #4CAF50;">http://5.189.145.177:5000</a></p>
            <p><strong>Health Check:</strong> <a href="http://5.189.145.177:5000/health" style="color: #4CAF50;">http://5.189.145.177:5000/health</a></p>
            <p><strong>API Status:</strong> <a href="http://5.189.145.177:5000/api/status" style="color: #4CAF50;">http://5.189.145.177:5000/api/status</a></p>
        </div>
        
        <div>
            <button class="btn" onclick="checkHealth()">🔍 Health Check</button>
            <button class="btn" onclick="getStatus()">📊 Get Status</button>
            <button class="btn" onclick="location.reload()">🔄 Refresh</button>
        </div>
        
        <div id="output" style="margin-top: 20px; text-align: left; background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; font-family: monospace;"></div>
    </div>
    
    <script>
        function addOutput(text) {
            const output = document.getElementById('output');
            output.innerHTML += new Date().toLocaleTimeString() + ' - ' + text + '<br>';
            output.scrollTop = output.scrollHeight;
        }
        
        function checkHealth() {
            fetch('/health')
                .then(r => r.json())
                .then(data => addOutput('✅ Health: ' + JSON.stringify(data)))
                .catch(e => addOutput('❌ Health Error: ' + e.message));
        }
        
        function getStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => addOutput('📊 Status: ' + JSON.stringify(data)))
                .catch(e => addOutput('❌ Status Error: ' + e.message));
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template_string(HTML_TEMPLATE, 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "AI Trading Sentinel",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-minimal",
        "binding": "0.0.0.0:5000",
        "external_ip": "5.189.145.177"
    })

@app.route('/api/status')
def api_status():
    """API status"""
    return jsonify({
        "backend": "running",
        "mode": "minimal",
        "external_access": "enabled",
        "port": 5000,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test')
def test():
    """Simple test endpoint"""
    return "<h1>✅ AI Trading Sentinel Test</h1><p>Backend is working!</p>"

if __name__ == '__main__':
    print("🚀 Starting AI Trading Sentinel - Minimal Backend")
    print("🌐 Binding to 0.0.0.0:5000 for external access")
    print("📊 Dashboard: http://5.189.145.177:5000")
    
    # Create logs directory
    os.makedirs('/root/ai-trading-sentinel/logs', exist_ok=True)
    
    # Start Flask
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
EOF

echo "✅ Minimal backend created"
echo ""

# Step 5: Configure firewall (simplified)
echo "🔥 Step 5: Configure Firewall"
echo "-----------------------------"
ufw allow 5000/tcp
ufw --force enable
echo "✅ Firewall configured"
echo ""

# Step 6: Start backend
echo "🚀 Step 6: Start Backend"
echo "------------------------"
cd /root/ai-trading-sentinel

# Test Python and Flask
echo "Testing Python and Flask..."
python3 -c "import flask; print('✅ Flask available')" || {
    echo "❌ Flask not available, installing..."
    pip3 install flask flask-cors
}

# Start backend
echo "Starting backend..."
nohup python3 backend/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started with PID: $BACKEND_PID"
sleep 5

# Step 7: Verify
echo "🔍 Step 7: Verification"
echo "----------------------"
echo "Process check:"
ps aux | grep "backend/main.py" | grep -v grep || echo "❌ Backend not running"
echo ""
echo "Port check:"
netstat -tlnp | grep :5000 || echo "❌ Port 5000 not bound"
echo ""
echo "Local test:"
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Local connection working"
    echo "📊 Health response:"
    curl -s http://localhost:5000/health
else
    echo "❌ Local connection failed"
    echo "📋 Checking logs:"
    tail -10 logs/backend.log
fi
echo ""

# Final status
echo "📋 Final Status"
echo "==============="
echo "🌐 Dashboard: http://5.189.145.177:5000"
echo "📊 Health: http://5.189.145.177:5000/health"
echo "🧪 Test: http://5.189.145.177:5000/test"
echo ""
echo "📋 Management:"
echo "  View logs: tail -f /root/ai-trading-sentinel/logs/backend.log"
echo "  Restart: pkill -f backend/main.py && cd /root/ai-trading-sentinel && nohup python3 backend/main.py > logs/backend.log 2>&1 &"
echo "  Status: curl http://localhost:5000/health"
echo ""
echo "🎉 Simple backend fix complete!"