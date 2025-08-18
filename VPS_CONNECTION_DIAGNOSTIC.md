# 🚨 VPS Connection Diagnostic - ERR_CONNECTION_REFUSED Fix

## Issue: Web Dashboard Not Accessible
**Error:** `ERR_CONNECTION_REFUSED` on `http://5.189.145.177:5000`

## Emergency Diagnostic Script

Copy and paste this diagnostic block into your VPS SSH terminal:

```bash
#!/bin/bash
echo "🔍 VPS Connection Diagnostic - $(date)"
echo "=========================================="

# 1. Check Service Status
echo "\n📊 Service Status:"
systemctl status trae-bot.service --no-pager
echo "\n🔄 Service Active State:"
systemctl is-active trae-bot.service
systemctl is-enabled trae-bot.service

# 2. Check Process Status
echo "\n🔍 Process Check:"
ps aux | grep -E "(python|flask|main.py)" | grep -v grep

# 3. Check Port Bindings
echo "\n🌐 Port Status:"
netstat -tlnp | grep :5000 || echo "❌ Port 5000 not listening"
ss -tlnp | grep :5000 || echo "❌ Port 5000 not bound"

# 4. Check Firewall
echo "\n🔥 Firewall Status:"
ufw status || echo "UFW not installed"
iptables -L INPUT -n | grep 5000 || echo "No iptables rule for port 5000"

# 5. Check Backend Process
echo "\n🖥️ Backend Process:"
ps aux | grep "backend/main.py" | grep -v grep || echo "❌ Backend not running"

# 6. Check Logs
echo "\n📝 Recent Logs:"
tail -20 /root/ai-trading-sentinel/logs/trae.log 2>/dev/null || echo "❌ No log file"

# 7. Test Local Connection
echo "\n🔗 Local Connection Test:"
curl -s http://localhost:5000/health || echo "❌ Local connection failed"
curl -s http://127.0.0.1:5000/health || echo "❌ Loopback connection failed"

# 8. Check Directory Structure
echo "\n📁 Project Structure:"
ls -la /root/ai-trading-sentinel/ | head -10
ls -la /root/ai-trading-sentinel/backend/ 2>/dev/null || echo "❌ Backend directory missing"

echo "\n✅ Diagnostic Complete!"
```

## Quick Fix Commands

If the diagnostic reveals issues, try these fixes:

### Fix 1: Restart Services
```bash
# Stop everything
sudo systemctl stop trae-bot.service
pkill -f "python.*main.py"
pkill -f "flask"

# Start backend manually
cd /root/ai-trading-sentinel
python3 backend/main.py &

# Check if it's running
curl http://localhost:5000/health
```

### Fix 2: Open Firewall Port
```bash
# Ubuntu UFW
sudo ufw allow 5000/tcp
sudo ufw reload

# Or iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save
```

### Fix 3: Manual Backend Start
```bash
cd /root/ai-trading-sentinel

# Install missing dependencies
pip3 install flask flask-cors

# Start backend with debug
python3 -c "
import sys
sys.path.append('/root/ai-trading-sentinel')
from backend.main import app
app.run(host='0.0.0.0', port=5000, debug=True)
"
```

### Fix 4: Create Simple Test Server
```bash
cd /root/ai-trading-sentinel

# Create minimal test server
cat > test_server.py << 'EOF'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Test server running"})

@app.route('/')
def home():
    return "<h1>AI Trading Sentinel Test</h1><p>Server is running!</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Run test server
python3 test_server.py
```

## Expected Results After Fix

✅ **Service Status:** `active (running)`  
✅ **Port Binding:** `0.0.0.0:5000` listening  
✅ **Local Test:** `curl localhost:5000/health` returns JSON  
✅ **External Access:** `http://5.189.145.177:5000` loads dashboard  

## Mobile Management Commands

```bash
# Quick status check
systemctl status trae-bot.service

# Manual backend start
cd /root/ai-trading-sentinel && python3 backend/main.py &

# Check what's running on port 5000
netstat -tlnp | grep 5000

# Kill and restart
pkill -f flask && python3 backend/main.py &
```

## Success Indicators

1. 🌐 **Web Access:** `http://5.189.145.177:5000` loads without errors
2. 📊 **Health Check:** `/health` endpoint returns `{"status": "ok"}`
3. 🔄 **Service Active:** `systemctl status` shows `active (running)`
4. 🌍 **Port Open:** `netstat` shows `0.0.0.0:5000` listening

---

**Next Step:** Run the diagnostic script first, then apply the appropriate fix based on the results.