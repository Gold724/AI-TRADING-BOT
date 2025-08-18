# 🚀 Quick Fix Commands - Copy & Paste

## Problem: Backend failing with Exit 1 errors
**Root Cause:** Missing Flask dependencies and import errors

## ⚡ Immediate Fix (Copy & Paste These Commands)

```bash
# Stop all processes
pkill -f "backend/main.py"
pkill -f "flask"
pkill -f ":5000"
sleep 3

# Install Flask
apt update
apt install -y python3-pip
pip3 install flask flask-cors

# Create working directory
cd /root
mkdir -p ai-trading-sentinel/backend
mkdir -p ai-trading-sentinel/logs
cd ai-trading-sentinel

# Create minimal working backend
cat > backend/main.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return f'''
    <html>
    <head><title>AI Trading Sentinel</title></head>
    <body style="font-family: Arial; background: #667eea; color: white; text-align: center; padding: 50px;">
        <h1>🤖 AI Trading Sentinel</h1>
        <h2>✅ Backend Online</h2>
        <p><strong>Server:</strong> 5.189.145.177:5000</p>
        <p><strong>Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <div style="margin: 30px;">
            <a href="/health" style="color: #4CAF50; margin: 10px;">Health Check</a> |
            <a href="/api/status" style="color: #4CAF50; margin: 10px;">API Status</a>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "AI Trading Sentinel",
        "timestamp": datetime.now().isoformat(),
        "external_ip": "5.189.145.177",
        "port": 5000
    })

@app.route('/api/status')
def status():
    return jsonify({
        "backend": "running",
        "external_access": "enabled",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 AI Trading Sentinel Backend Starting...")
    print("🌐 Access: http://5.189.145.177:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Configure firewall
ufw allow 5000/tcp
ufw --force enable

# Start backend
nohup python3 backend/main.py > logs/backend.log 2>&1 &
echo "✅ Backend started"
sleep 3

# Test
echo "🧪 Testing..."
ps aux | grep "backend/main.py" | grep -v grep
netstat -tlnp | grep :5000
curl -s http://localhost:5000/health

echo ""
echo "🎉 Quick Fix Complete!"
echo "🌐 Access: http://5.189.145.177:5000"
echo "📊 Health: http://5.189.145.177:5000/health"
```

## ✅ Expected Results

- ✅ Flask installed successfully
- ✅ Backend process running
- ✅ Port 5000 bound to 0.0.0.0:5000
- ✅ Local health check returns JSON
- ✅ External access working

## 🔍 Verification Commands

```bash
# Check process
ps aux | grep backend/main.py

# Check port
netstat -tlnp | grep :5000

# Test local
curl http://localhost:5000/health

# View logs
tail -f /root/ai-trading-sentinel/logs/backend.log
```

## 🚨 If Still Not Working

1. **Check Contabo Firewall:**
   - Login to Contabo control panel
   - Go to "Firewall" or "Security Groups"
   - Add rule: TCP 5000 from 0.0.0.0/0

2. **Manual Test:**
   ```bash
   # Simple HTTP server test
   cd /root/ai-trading-sentinel
   echo "<h1>Test</h1>" > test.html
   python3 -m http.server 5000 --bind 0.0.0.0
   ```

3. **Check VPS Provider Settings:**
   - Some VPS providers block ports by default
   - Contact Contabo support if needed

---

**This minimal backend eliminates complex dependencies and focuses on getting external access working first.**