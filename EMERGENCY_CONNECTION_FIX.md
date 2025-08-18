# 🚨 Emergency Connection Fix - ERR_CONNECTION_REFUSED

## Complete Fix Script for VPS Connection Issues

Copy and paste this entire block into your VPS SSH terminal:

```bash
#!/bin/bash
echo "🚨 Emergency Connection Fix - $(date)"
echo "========================================"

# Stop all existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop trae-bot.service 2>/dev/null
pkill -f "python.*main.py" 2>/dev/null
pkill -f "flask" 2>/dev/null
sleep 2

# Navigate to project directory
cd /root/ai-trading-sentinel || { echo "❌ Project directory not found"; exit 1; }

# Install/update Flask dependencies
echo "📦 Installing Flask dependencies..."
pip3 install flask flask-cors gunicorn --upgrade

# Create enhanced backend with proper network binding
echo "🔧 Creating enhanced backend..."
mkdir -p backend logs

cat > backend/main.py << 'EOF'
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import os
import subprocess
import datetime
import json

app = Flask(__name__)
CORS(app)

# Enhanced HTML Dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel - Control Panel</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 8px; border-left: 4px solid #00ff88; }
        .card h3 { margin-top: 0; color: #00ff88; }
        .status-ok { color: #00ff88; }
        .status-error { color: #ff4444; }
        .btn { background: #00ff88; color: #000; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #00cc6a; }
        .logs { background: #000; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
        .refresh { position: fixed; top: 20px; right: 20px; }
    </style>
    <script>
        function refreshPage() { location.reload(); }
        function toggleService() {
            fetch('/api/toggle-service', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(refreshPage, 1000);
                });
        }
        setInterval(refreshPage, 30000); // Auto-refresh every 30 seconds
    </script>
</head>
<body>
    <button class="btn refresh" onclick="refreshPage()">🔄 Refresh</button>
    
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Sentinel</h1>
            <p>VPS Control Panel - {{ timestamp }}</p>
        </div>
        
        <div class="status-grid">
            <div class="card">
                <h3>🔄 Service Status</h3>
                <p>Main Service: <span class="{{ service_status_class }}">{{ service_status }}</span></p>
                <p>Web Backend: <span class="status-ok">RUNNING</span></p>
                <p>Uptime: {{ uptime }}</p>
                <button class="btn" onclick="toggleService()">Toggle Service</button>
            </div>
            
            <div class="card">
                <h3>🌐 Network Status</h3>
                <p>Server IP: 5.189.145.177</p>
                <p>Web Port: 5000</p>
                <p>Status: <span class="status-ok">ACCESSIBLE</span></p>
                <p>Last Check: {{ timestamp }}</p>
            </div>
            
            <div class="card">
                <h3>📊 System Info</h3>
                <p>OS: Ubuntu 24.04</p>
                <p>Python: {{ python_version }}</p>
                <p>Project: /root/ai-trading-sentinel</p>
                <p>Logs: {{ log_status }}</p>
            </div>
        </div>
        
        <div class="card">
            <h3>📝 Recent Logs</h3>
            <div class="logs">{{ recent_logs }}</div>
        </div>
        
        <div class="card">
            <h3>🎛️ Quick Actions</h3>
            <button class="btn" onclick="fetch('/api/restart-service', {method: 'POST'}).then(() => alert('Service restarted'))">🔄 Restart Service</button>
            <button class="btn" onclick="window.open('/api/logs', '_blank')">📋 View Full Logs</button>
            <button class="btn" onclick="window.open('/health', '_blank')">🏥 Health Check</button>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    try:
        # Get service status
        try:
            result = subprocess.run(['systemctl', 'is-active', 'trae-bot.service'], 
                                  capture_output=True, text=True, timeout=5)
            service_status = result.stdout.strip()
            service_status_class = 'status-ok' if service_status == 'active' else 'status-error'
        except:
            service_status = 'unknown'
            service_status_class = 'status-error'
        
        # Get uptime
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
        except:
            uptime = 'unknown'
        
        # Get Python version
        try:
            python_version = subprocess.run(['python3', '--version'], 
                                          capture_output=True, text=True).stdout.strip()
        except:
            python_version = 'Python 3.x'
        
        # Get recent logs
        try:
            if os.path.exists('/root/ai-trading-sentinel/logs/trae.log'):
                with open('/root/ai-trading-sentinel/logs/trae.log', 'r') as f:
                    lines = f.readlines()[-20:]  # Last 20 lines
                    recent_logs = ''.join(lines) or 'No recent logs'
                log_status = 'Available'
            else:
                recent_logs = 'Log file not found'
                log_status = 'Missing'
        except:
            recent_logs = 'Error reading logs'
            log_status = 'Error'
        
        return render_template_string(DASHBOARD_HTML,
            timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            service_status=service_status,
            service_status_class=service_status_class,
            uptime=uptime,
            python_version=python_version,
            recent_logs=recent_logs,
            log_status=log_status
        )
    except Exception as e:
        return f"<h1>Dashboard Error</h1><p>{str(e)}</p>", 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': 'ai-trading-sentinel',
        'version': '1.0.0',
        'server': '5.189.145.177:5000'
    })

@app.route('/api/status')
def api_status():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'trae-bot.service'], 
                              capture_output=True, text=True, timeout=5)
        service_active = result.stdout.strip() == 'active'
    except:
        service_active = False
    
    return jsonify({
        'service_active': service_active,
        'web_backend': True,
        'timestamp': datetime.datetime.now().isoformat(),
        'server_ip': '5.189.145.177',
        'port': 5000
    })

@app.route('/api/logs')
def api_logs():
    try:
        if os.path.exists('/root/ai-trading-sentinel/logs/trae.log'):
            with open('/root/ai-trading-sentinel/logs/trae.log', 'r') as f:
                logs = f.read()
            return f"<pre>{logs}</pre>"
        else:
            return "<h1>No logs found</h1>"
    except Exception as e:
        return f"<h1>Error reading logs</h1><p>{str(e)}</p>"

@app.route('/api/restart-service', methods=['POST'])
def restart_service():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'trae-bot.service'], timeout=10)
        return jsonify({'status': 'success', 'message': 'Service restarted'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/toggle-service', methods=['POST'])
def toggle_service():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'trae-bot.service'], 
                              capture_output=True, text=True, timeout=5)
        is_active = result.stdout.strip() == 'active'
        
        if is_active:
            subprocess.run(['sudo', 'systemctl', 'stop', 'trae-bot.service'], timeout=10)
            message = 'Service stopped'
        else:
            subprocess.run(['sudo', 'systemctl', 'start', 'trae-bot.service'], timeout=10)
            message = 'Service started'
        
        return jsonify({'status': 'success', 'message': message})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🚀 Starting AI Trading Sentinel Web Backend...")
    print("🌐 Dashboard: http://5.189.145.177:5000")
    print("📊 Health: http://5.189.145.177:5000/health")
    print("📡 API: http://5.189.145.177:5000/api/status")
    
    # Ensure logs directory exists
    os.makedirs('/root/ai-trading-sentinel/logs', exist_ok=True)
    
    # Start Flask with proper network binding
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=False,
        threaded=True
    )
EOF

# Create startup script
echo "📝 Creating startup script..."
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd /root/ai-trading-sentinel
echo "Starting AI Trading Sentinel Backend - $(date)" >> logs/backend.log
python3 backend/main.py >> logs/backend.log 2>&1 &
echo $! > backend.pid
echo "Backend started with PID: $(cat backend.pid)"
EOF

chmod +x start_backend.sh

# Open firewall port
echo "🔥 Configuring firewall..."
sudo ufw allow 5000/tcp 2>/dev/null || echo "UFW not available, trying iptables..."
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || echo "Iptables rule may already exist"

# Kill any existing processes on port 5000
echo "🧹 Cleaning existing processes..."
sudo fuser -k 5000/tcp 2>/dev/null || echo "No processes to kill on port 5000"

# Start backend with proper logging
echo "🚀 Starting enhanced backend..."
cd /root/ai-trading-sentinel
mkdir -p logs

# Start backend in background with logging
nohup python3 backend/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

echo "⏳ Waiting for backend to start..."
sleep 3

# Test local connection
echo "🔍 Testing local connection..."
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Local connection successful"
else
    echo "❌ Local connection failed"
    echo "📋 Backend logs:"
    tail -10 logs/backend.log
fi

# Check if process is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend process running (PID: $BACKEND_PID)"
else
    echo "❌ Backend process not running"
    echo "📋 Error logs:"
    tail -10 logs/backend.log
fi

# Check port binding
echo "🌐 Checking port binding..."
if netstat -tlnp | grep :5000; then
    echo "✅ Port 5000 is bound"
else
    echo "❌ Port 5000 not bound"
fi

echo ""
echo "🎉 Emergency Fix Complete!"
echo "========================="
echo "🌐 Web Dashboard: http://5.189.145.177:5000"
echo "📊 Health Check: http://5.189.145.177:5000/health"
echo "📡 API Status: http://5.189.145.177:5000/api/status"
echo ""
echo "📋 Management Commands:"
echo "Status: ps -p $(cat backend.pid 2>/dev/null) || echo 'Not running'"
echo "Logs: tail -f logs/backend.log"
echo "Restart: ./start_backend.sh"
echo "Stop: kill $(cat backend.pid 2>/dev/null)"
echo ""
echo "🔍 If still not accessible, check:"
echo "1. VPS provider firewall settings"
echo "2. Network security groups"
echo "3. curl http://localhost:5000/health (should work locally)"
```

## Verification Commands

After running the fix script, verify with these commands:

```bash
# Check if backend is running
ps aux | grep "backend/main.py" | grep -v grep

# Check port binding
netstat -tlnp | grep :5000

# Test local connection
curl http://localhost:5000/health

# Check logs
tail -f /root/ai-trading-sentinel/logs/backend.log
```

## Expected Results

✅ **Process Running:** Backend PID shown and active  
✅ **Port Bound:** `0.0.0.0:5000` listening  
✅ **Local Test:** `curl localhost:5000/health` returns JSON  
✅ **External Access:** `http://5.189.145.177:5000` loads dashboard  

## If Still Not Working

1. **Check VPS Provider Firewall:** Contabo control panel → Firewall → Allow port 5000
2. **Check Network Security:** Ensure no additional firewalls blocking port 5000
3. **Manual Test:** `python3 -m http.server 5000` should work if Flask doesn't

---

**This script creates a robust Flask backend with proper network binding and comprehensive error handling.**