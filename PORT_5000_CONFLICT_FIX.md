# 🚨 PORT 5000 CONFLICT - Emergency Fix Guide

## ⚠️ CRITICAL ISSUE IDENTIFIED
**Root Cause:** Port 5000 is already in use by another process, preventing Gunicorn from starting.

**Error Pattern:**
```
[ERROR] Connection in use: ('127.0.0.1', 5000)
[ERROR] connection to ('127.0.0.1', 5000) failed: [Errno 98] Address already in use
```

## 🔧 IMMEDIATE FIX (Via Termius)

### Step 1: Kill Existing Process on Port 5000
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill the process (replace PID with actual process ID)
sudo kill -9 <PID>

# Alternative: Kill all processes on port 5000
sudo fuser -k 5000/tcp
```

### Step 2: Verify Port is Free
```bash
# Check if port 5000 is now available
sudo netstat -tlnp | grep :5000

# Should return empty if port is free
```

### Step 3: Restart Trading Bot Service
```bash
# Stop the service first
sudo systemctl stop trading-bot.service

# Wait 3 seconds
sleep 3

# Start the service
sudo systemctl start trading-bot.service

# Check status
sudo systemctl status trading-bot.service
```

### Step 4: Verify API Endpoint
```bash
# Test local API
curl -s http://localhost:5000/api/status

# Should return JSON response, not 502 error
```

## 🔍 TROUBLESHOOTING

### If Port Still in Use:
```bash
# More aggressive process killing
sudo pkill -f gunicorn
sudo pkill -f flask
sudo pkill -f python.*main.py

# Check for zombie processes
ps aux | grep -E '(gunicorn|flask|python)'
```

### If Service Still Fails:
```bash
# Check service logs
sudo journalctl -u trading-bot.service -f --no-pager -n 20

# Manual start for debugging
cd /opt/ai-trading-sentinel
sudo -u ubuntu python3 main.py
```

## ✅ SUCCESS INDICATORS
1. `sudo systemctl status trading-bot.service` shows **active (running)**
2. `curl http://localhost:5000/api/status` returns JSON (not 502)
3. No "Address already in use" errors in logs
4. External API test: `curl http://YOUR_VPS_IP/api/status` works

## 🚀 POST-FIX VERIFICATION
```bash
# Complete health check
sudo systemctl status nginx trading-bot.service
curl -s http://localhost:5000/api/status | jq .
ps aux | grep -E '(gunicorn|nginx)'
```

## 📋 ROOT CAUSE ANALYSIS
- **Issue:** Previous Flask/Gunicorn process didn't terminate cleanly
- **Impact:** New service instances can't bind to port 5000
- **Solution:** Force kill existing processes + clean restart
- **Prevention:** Improve service stop/restart procedures

---
**Priority:** 🔥 CRITICAL - API completely down until fixed
**ETA:** 2-3 minutes via Termius
**Next:** Verify external access + setup monitoring