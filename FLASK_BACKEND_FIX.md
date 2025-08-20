# 🔧 FLASK BACKEND FIX - 502 Bad Gateway

## 🚨 ISSUE IDENTIFIED
- **Web Dashboard**: ✅ Working (HTTP 200 OK)
- **API Endpoint**: ❌ 502 Bad Gateway
- **Cause**: Flask backend service not running properly
- **Solution**: Restart Flask backend service

---

## 🔄 IMMEDIATE FIX (Run in VPS Console)

**Copy/paste these commands:**

```bash
# 1. Check Flask backend service status
sudo systemctl status trading-bot

# 2. Restart Flask backend service
sudo systemctl restart trading-bot

# 3. Check if it's running now
sudo systemctl status trading-bot

# 4. Check service logs for errors
sudo journalctl -u trading-bot -f --lines=20

# 5. Test Flask is responding locally
curl http://localhost:5000/api/status

# 6. Check Nginx proxy configuration
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 DETAILED DIAGNOSTICS

### Check Flask Process
```bash
# Look for Flask process
ps aux | grep flask
ps aux | grep python

# Check if port 5000 is listening
ss -tlnp | grep :5000
```

### Check Service Configuration
```bash
# View service file
sudo cat /etc/systemd/system/trading-bot.service

# Check working directory
ls -la /opt/ai-trading-sentinel/

# Test Python environment
cd /opt/ai-trading-sentinel
source venv/bin/activate
python -c "import flask; print('Flask OK')"
```

### Manual Flask Start (if service fails)
```bash
# Navigate to project directory
cd /opt/ai-trading-sentinel

# Activate virtual environment
source venv/bin/activate

# Start Flask manually for testing
export FLASK_APP=backend_main.py
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=5000
```

---

## 🛠️ COMMON FIXES

### Fix 1: Service File Issues
```bash
# Reload systemd if service file changed
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl restart trading-bot
```

### Fix 2: Permission Issues
```bash
# Fix ownership
sudo chown -R root:root /opt/ai-trading-sentinel
sudo chmod +x /opt/ai-trading-sentinel/backend_main.py
```

### Fix 3: Python Dependencies
```bash
# Reinstall requirements
cd /opt/ai-trading-sentinel
source venv/bin/activate
pip install -r requirements.txt
```

### Fix 4: Nginx Configuration
```bash
# Check Nginx config for API proxy
sudo cat /etc/nginx/sites-available/default | grep -A 10 "/api"

# Expected configuration:
# location /api {
#     proxy_pass http://127.0.0.1:5000;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
# }
```

---

## ✅ SUCCESS VERIFICATION

**Flask backend is working when:**

```bash
# 1. Service shows active
sudo systemctl status trading-bot
# Expected: "active (running)"

# 2. Port 5000 is listening
ss -tlnp | grep :5000
# Expected: LISTEN on 127.0.0.1:5000

# 3. Local API test works
curl http://localhost:5000/api/status
# Expected: JSON response

# 4. External API test works
curl http://161.97.112.146/api/status
# Expected: JSON response (no 502 error)
```

---

## 🚀 EXPECTED API RESPONSE

**When working correctly:**
```json
{
  "status": "running",
  "bot_active": true,
  "last_update": "2025-08-18T20:10:00Z",
  "version": "1.0.0"
}
```

---

## 📱 NEXT STEPS AFTER FIX

1. **Verify External API**: Test from your computer
2. **Test Termius**: Try SSH connection
3. **Check All Endpoints**: Test trading bot APIs
4. **Monitor Logs**: Watch for any errors
5. **Run Trading Tests**: Execute end-to-end workflow

---

**🎯 GOAL**: Get Flask backend service running so API returns JSON instead of 502 Bad Gateway**