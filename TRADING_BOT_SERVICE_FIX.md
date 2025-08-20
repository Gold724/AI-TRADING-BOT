# 🚨 TRADING-BOT SERVICE FIX - Critical Backend Failure

## 🔍 DIAGNOSIS

**Issue Identified**: `trading-bot.service` failing with exit code 1
```
Process: 4433 ExecStart=/opt/trading-bot/venv/bin/gunicorn --config gunicorn.conf.py app:app (code=exited, status=1/FAILURE)
Result: exit-code
Status: activating (auto-restart)
```

**Root Cause**: Gunicorn configuration or Flask app startup failure

---

## ⚡ IMMEDIATE FIX (Copy-paste in Termius)

### Step 1: Check Service Logs
```bash
# View detailed error logs
sudo journalctl -u trading-bot --no-pager -l -n 50

# Check if gunicorn.conf.py exists
ls -la /opt/trading-bot/gunicorn.conf.py

# Check Flask app file
ls -la /opt/trading-bot/app.py
ls -la /opt/trading-bot/backend_main.py
```

### Step 2: Manual Flask Startup (Bypass Gunicorn)
```bash
# Navigate to trading bot directory
cd /opt/trading-bot

# Activate virtual environment
source venv/bin/activate

# Check Python path and Flask app
python -c "import sys; print(sys.path)"
python -c "import app; print('Flask app imported successfully')"

# Manual Flask startup
python backend_main.py &

# Check if Flask is running
ps aux | grep python
netstat -tlnp | grep 5000
```

### Step 3: Test API After Manual Start
```bash
# Test local API
curl -s http://localhost:5000/api/status
curl -s http://localhost/api/status

# Should return JSON instead of 502
```

---

## 🔧 PERMANENT SERVICE FIX

### Option A: Fix Gunicorn Configuration
```bash
# Check current service file
sudo cat /etc/systemd/system/trading-bot.service

# Create/fix gunicorn.conf.py
cat > /opt/trading-bot/gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# Ensure app.py exists or create symlink
ln -sf backend_main.py app.py
```

### Option B: Simplify Service (Direct Python)
```bash
# Edit service file
sudo nano /etc/systemd/system/trading-bot.service

# Replace ExecStart line with:
# ExecStart=/opt/trading-bot/venv/bin/python /opt/trading-bot/backend_main.py

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart trading-bot
sudo systemctl status trading-bot --no-pager -l
```

---

## 🚨 EMERGENCY WORKAROUND

If service continues failing, run Flask manually:

```bash
# Kill any existing processes
sudo pkill -f "python.*backend_main"
sudo pkill -f gunicorn

# Start Flask in background
cd /opt/trading-bot
source venv/bin/activate
nohup python backend_main.py > flask.log 2>&1 &

# Verify it's running
ps aux | grep backend_main
curl -s http://localhost:5000/api/status
```

---

## ✅ SUCCESS VERIFICATION

### Service Status:
```
● trading-bot.service - AI Trading Sentinel Backend
   Active: active (running)
   Main PID: [number] (python or gunicorn)
```

### API Response:
```bash
curl http://localhost/api/status
# Should return: {"status": "running", "timestamp": "..."}
```

### External Test:
```powershell
# From Windows machine
Invoke-WebRequest http://161.97.112.146/api/status
# Should return: StatusCode: 200
```

---

## 📋 POST-FIX CHECKLIST

- [ ] `trading-bot.service` shows "active (running)"
- [ ] Flask process visible in `ps aux | grep python`
- [ ] Port 5000 listening: `netstat -tlnp | grep 5000`
- [ ] Local API works: `curl localhost:5000/api/status`
- [ ] Nginx proxy works: `curl localhost/api/status`
- [ ] External API works: Test from Windows
- [ ] No 502 errors in browser

---

**🎯 PRIORITY**: Fix this service failure to restore full trading bot functionality!