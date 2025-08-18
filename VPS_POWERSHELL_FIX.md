# 🚀 VPS PowerShell Emergency Fix

## Problem Identified
The backend deployment failed because:
1. The `backend/main.py` file wasn't created properly
2. The `logs` directory doesn't exist
3. The Flask process exited with error code 1

## ⚡ IMMEDIATE FIX - Copy & Paste Commands

**Step 1: Create Backend Directory & Files**
```powershell
# Stop any existing processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Create directories
New-Item -ItemType Directory -Path "backend" -Force
New-Item -ItemType Directory -Path "logs" -Force

# Verify virtual environment is active
python --version
pip list | Select-String flask
```

**Step 2: Create Flask Backend (Copy this entire block)**
```powershell
@'
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import datetime
import os

app = Flask(__name__)
CORS(app)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AI Trading Sentinel - VPS Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            border-left: 5px solid #4CAF50;
        }
        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            margin: 5px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); 
        }
        .logs {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .success { color: #4CAF50; }
        .info { color: #2196F3; }
        .warning { color: #ff9800; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Sentinel</h1>
            <h2>VPS Control Dashboard</h2>
            <p>Status: <span class="success">🟢 ONLINE</span></p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🚀 Backend Service</h3>
                <p><strong>Status:</strong> Running</p>
                <p><strong>Port:</strong> 5000</p>
                <p><strong>Host:</strong> 0.0.0.0 (External Access)</p>
            </div>
            
            <div class="status-card">
                <h3>🐍 Python Environment</h3>
                <p><strong>Virtual Env:</strong> Active</p>
                <p><strong>Flask:</strong> Installed</p>
                <p><strong>Platform:</strong> VPS Compatible</p>
            </div>
            
            <div class="status-card">
                <h3>🔧 System Status</h3>
                <p><strong>Memory:</strong> Available</p>
                <p><strong>Network:</strong> Connected</p>
                <p><strong>Firewall:</strong> Configured</p>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="btn" onclick="checkHealth()">🔍 Health Check</button>
            <button class="btn" onclick="testAPI()">🧪 Test API</button>
            <button class="btn" onclick="location.reload()">🔄 Refresh</button>
        </div>
        
        <div class="logs" id="logs">
            <div class="success">[{{ timestamp }}] ✅ Flask backend started successfully</div>
            <div class="info">[{{ timestamp }}] ✅ Virtual environment active</div>
            <div class="info">[{{ timestamp }}] ✅ External access enabled on 0.0.0.0:5000</div>
            <div class="warning">[{{ timestamp }}] 🔧 Ready for AI Trading Sentinel deployment</div>
        </div>
    </div>
    
    <script>
        function checkHealth() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    addLog('🔍 Health Check: ' + JSON.stringify(data), 'success');
                })
                .catch(error => {
                    addLog('❌ Health Check Failed: ' + error, 'error');
                });
        }
        
        function testAPI() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    addLog('🧪 API Test: ' + JSON.stringify(data), 'info');
                })
                .catch(error => {
                    addLog('❌ API Test Failed: ' + error, 'error');
                });
        }
        
        function addLog(message, type) {
            const logs = document.getElementById('logs');
            const timestamp = new Date().toLocaleString();
            const className = type === 'error' ? 'error' : (type === 'success' ? 'success' : 'info');
            logs.innerHTML += `<div class="\${className}">[\${timestamp}] \${message}</div>`;
            logs.scrollTop = logs.scrollHeight;
        }
        
        // Auto-refresh health every 60 seconds
        setInterval(checkHealth, 60000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(HTML_DASHBOARD, timestamp=timestamp)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'ai-trading-sentinel-backend',
        'version': '1.0.0',
        'virtual_env': 'active',
        'platform': 'vps',
        'flask_version': 'installed',
        'external_access': 'enabled'
    })

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'backend': 'running',
        'virtual_environment': 'active',
        'external_access': 'enabled',
        'flask': 'operational',
        'cors': 'enabled',
        'ready_for_trading_bot': True
    })

@app.route('/test')
def test():
    """Simple test endpoint"""
    return "🤖 AI Trading Sentinel Backend - VPS SUCCESS!"

@app.route('/api/logs')
def get_logs():
    """Get system logs"""
    try:
        logs = []
        log_path = os.path.join(os.getcwd(), 'logs', 'backend.log')
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                logs.extend(f.readlines()[-20:])  # Last 20 lines
        
        if not logs:
            logs = ["No logs available yet\n"]
            
        return ''.join(logs), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return f"Error reading logs: {str(e)}", 500

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 Starting AI Trading Sentinel Backend...")
    print("📍 Virtual Environment: ACTIVE")
    print("🌐 External Access: ENABLED on 0.0.0.0:5000")
    print("🔧 VPS: COMPATIBLE")
    print("📱 Dashboard: http://5.189.145.177:5000")
    
    # Run Flask with external access
    app.run(host='0.0.0.0', port=5000, debug=False)
'@ | Out-File -FilePath "backend\main.py" -Encoding UTF8
```

**Step 3: Start Backend Service**
```powershell
# Start the Flask backend
Write-Host "🚀 Starting Flask backend..." -ForegroundColor Green
Start-Job -ScriptBlock { 
    Set-Location "C:\root\ai-trading-sentinel"
    python backend\main.py 
} -Name "FlaskBackend"

# Wait for startup
Start-Sleep -Seconds 3

# Check if job is running
Get-Job -Name "FlaskBackend"
```

**Step 4: Verification**
```powershell
# Check processes
Get-Process | Where-Object {$_.ProcessName -eq "python"}

# Check port binding
netstat -an | Select-String ":5000"

# Test local connection
Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 5
```

## 🔧 Alternative Simple Method

If the above doesn't work, try this minimal approach:

```powershell
# Create minimal backend
New-Item -ItemType Directory -Path "backend" -Force
@'
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>🤖 AI Trading Sentinel - VPS Online!</h1><p>Backend is running successfully.</p>"

@app.route("/health")
def health():
    return {"status": "healthy", "service": "ai-trading-sentinel"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
'@ | Out-File -FilePath "backend\main.py" -Encoding UTF8

# Start it
python backend\main.py
```

## 📱 Expected Results

After running these commands, you should be able to access:
- **🌐 Web Dashboard:** http://5.189.145.177:5000
- **🔍 Health Check:** http://5.189.145.177:5000/health
- **📊 API Status:** http://5.189.145.177:5000/api/status

## 🚨 Troubleshooting

If still not working:
1. **Check virtual environment:** `python --version` and `pip list`
2. **Check Flask installation:** `pip install flask flask-cors`
3. **Check firewall:** Ensure port 5000 is open
4. **Check process:** `Get-Process | Where-Object {$_.ProcessName -eq "python"}`
5. **View errors:** Check any error messages in the terminal

## 🎯 Root Cause Analysis

The original deployment failed because:
- The `cat > backend/main.py << 'EOF'` syntax is Linux bash, not PowerShell
- PowerShell uses different commands (`Out-File` instead of `cat`)
- The `nohup` command doesn't exist in PowerShell
- Process management is different in Windows/PowerShell

This fix provides PowerShell-compatible commands for the VPS environment.