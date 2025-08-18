# Ubuntu 24.04 Virtual Environment Fix - Copy & Paste Commands

## Issue: Externally-Managed Environment
Ubuntu 24.04 blocks system-wide pip installations. Solution: Use Python virtual environment.

## 🚀 IMMEDIATE FIX - Copy & Paste These Commands:

```bash
# Stop existing processes
pkill -f "backend/main.py"
pkill -f "flask"
pkill -f ":5000"

# Install system dependencies
sudo apt update
sudo apt install -y python3-full python3-venv python3-pip

# Create project structure
cd /root
mkdir -p ai-trading-sentinel/backend ai-trading-sentinel/logs
cd ai-trading-sentinel

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask in virtual environment
pip install --upgrade pip
pip install flask flask-cors

# Create minimal backend
cat > backend/main.py << 'EOF'
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import datetime
import os

app = Flask(__name__)
CORS(app)

HTML_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AI Trading Sentinel - VPS Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #16213e; padding: 30px; border-radius: 10px; }
        .status { background: #0f3460; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .online { border-left: 5px solid #4CAF50; }
        .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer; }
        .btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel</h1>
        <h2>VPS Control Dashboard</h2>
        
        <div class="status online">
            <h3>🚀 Backend Service</h3>
            <p>Status: <strong>Running</strong></p>
            <p>Port: <strong>5000</strong></p>
            <p>Virtual Environment: <strong>Active</strong></p>
        </div>
        
        <div class="status online">
            <h3>🔧 System Status</h3>
            <p>Ubuntu: <strong>24.04</strong></p>
            <p>Python: <strong>Virtual Environment</strong></p>
            <p>Flask: <strong>Installed</strong></p>
        </div>
        
        <button class="btn" onclick="checkHealth()">🔍 Health Check</button>
        <button class="btn" onclick="location.reload()">🔄 Refresh</button>
        
        <div id="logs" style="background: #000; padding: 15px; margin-top: 20px; border-radius: 5px; font-family: monospace;">
            <div style="color: #4CAF50;">[{{ timestamp }}] ✅ Flask backend started successfully</div>
            <div style="color: #2196F3;">[{{ timestamp }}] ✅ Virtual environment active</div>
            <div style="color: #2196F3;">[{{ timestamp }}] ✅ External access configured</div>
            <div style="color: #ff9800;">[{{ timestamp }}] 🔧 Ready for trading bot deployment</div>
        </div>
    </div>
    
    <script>
        function checkHealth() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('logs').innerHTML += 
                        '<div style="color: #4CAF50;">[' + new Date().toLocaleString() + '] Health: ' + JSON.stringify(data) + '</div>';
                })
                .catch(error => {
                    document.getElementById('logs').innerHTML += 
                        '<div style="color: #f44336;">[' + new Date().toLocaleString() + '] Error: ' + error + '</div>';
                });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(HTML_DASHBOARD, timestamp=timestamp)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'ai-trading-sentinel-backend',
        'virtual_env': 'active',
        'ubuntu': '24.04'
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'backend': 'running',
        'virtual_environment': 'active',
        'external_access': 'enabled'
    })

@app.route('/test')
def test():
    return "🤖 AI Trading Sentinel Backend - Virtual Environment OK!"

if __name__ == '__main__':
    os.makedirs('/root/ai-trading-sentinel/logs', exist_ok=True)
    print("🚀 Starting AI Trading Sentinel Backend...")
    print("📍 Virtual Environment: Active")
    print("🌐 External Access: Enabled on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Configure firewall
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22/tcp
sudo ufw allow 5000/tcp
sudo ufw --force enable

# Start backend in virtual environment
source venv/bin/activate
nohup python backend/main.py > logs/backend_startup.log 2>&1 &

# Wait and verify
sleep 3
echo "🔍 Verification:"
ps aux | grep "backend/main.py" | grep -v grep
netstat -tlnp | grep :5000
curl -s http://localhost:5000/health

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "📱 Access: http://5.189.145.177:5000"
echo "🔍 Health: http://5.189.145.177:5000/health"
echo "🧪 Test: http://5.189.145.177:5000/test"
```

## ✅ What This Fixes:

1. **Virtual Environment**: Creates isolated Python environment
2. **Flask Installation**: Installs Flask without system conflicts
3. **Ubuntu 24.04 Compatibility**: Works with externally-managed environment
4. **External Access**: Binds to 0.0.0.0 for VPS access
5. **Firewall Configuration**: Opens port 5000 for external access

## 🔧 Management Commands:

```bash
# Check status
ps aux | grep backend/main.py
netstat -tlnp | grep :5000

# View logs
tail -f logs/backend_startup.log

# Restart backend
pkill -f backend/main.py
cd /root/ai-trading-sentinel
source venv/bin/activate
nohup python backend/main.py > logs/backend_startup.log 2>&1 &

# Activate virtual environment
cd /root/ai-trading-sentinel
source venv/bin/activate
```

## 🚨 If External Access Still Fails:

1. **Check Contabo Control Panel**: Firewall settings
2. **Check Network Security Groups**: Allow port 5000
3. **Verify VPS IP**: Confirm 5.189.145.177 is correct
4. **Test Local First**: `curl http://localhost:5000/health`

## 📋 Expected Results:

- ✅ Virtual environment created and activated
- ✅ Flask installed without conflicts
- ✅ Backend running on 0.0.0.0:5000
- ✅ Firewall configured for external access
- ✅ Web dashboard accessible externally
- ✅ Health endpoints responding

**This solution eliminates the externally-managed environment issue by using Python virtual environments as recommended by Ubuntu 24.04.**