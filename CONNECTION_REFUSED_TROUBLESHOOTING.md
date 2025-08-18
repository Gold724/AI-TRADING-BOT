# 🚨 Connection Refused - Troubleshooting Guide

## ❌ **Current Issue: ERR_CONNECTION_REFUSED**

```
http://5.189.145.177:5000 - Connection Refused
```

**This means**: The VPS is not running the TRAE web service on port 5000.

---

## 🔍 **Diagnosis Steps**

### Step 1: Check VPS Status
```bash
# Connect via SSH first
ssh root@5.189.145.177 -p 18177

# If SSH fails, use VNC Console:
# Go to Contabo Panel → VNC Console
```

### Step 2: Check Service Status
```bash
# Check if trae-bot service is running
sudo systemctl status trae-bot

# Expected output if working:
# ● trae-bot.service - TRAE Trading Bot
#    Loaded: loaded
#    Active: active (running)
```

### Step 3: Check Port 5000
```bash
# Check if anything is listening on port 5000
sudo netstat -tlnp | grep 5000

# Or use ss command
sudo ss -tlnp | grep 5000

# Expected output:
tcp 0 0 0.0.0.0:5000 0.0.0.0:* LISTEN 1234/python
```

### Step 4: Check Firewall
```bash
# Check firewall status
sudo ufw status

# If port 5000 is blocked, allow it:
sudo ufw allow 5000
```

---

## 🛠️ **Common Fixes**

### Fix 1: Service Not Started
```bash
# Start the service
sudo systemctl start trae-bot

# Enable auto-start on boot
sudo systemctl enable trae-bot

# Check status
sudo systemctl status trae-bot
```

### Fix 2: Service Failed to Start
```bash
# Check detailed logs
sudo journalctl -u trae-bot -f

# Look for error messages like:
# - Missing dependencies
# - Port already in use
# - Configuration errors
```

### Fix 3: Manual Start (Emergency)
```bash
# Navigate to project directory
cd /root/ai-trading-sentinel

# Start manually to see errors
python main.py

# Or start backend specifically
cd backend
python main.py
```

### Fix 4: Port Already in Use
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill the process (replace PID)
sudo kill -9 <PID>

# Restart trae-bot
sudo systemctl restart trae-bot
```

---

## 🚀 **Complete Deployment Check**

### VNC Console Deployment
```bash
# 1. Access via Contabo VNC Console
# 2. Open terminal in desktop
# 3. Navigate to project
cd /root/ai-trading-sentinel

# 4. Run deployment script
./vnc_deployment_implementation.sh

# 5. Configure environment
./configure_env_gui.sh

# 6. Start service
./service_manager_vnc.sh
```

### Manual Service Setup
```bash
# Create systemd service file
sudo nano /etc/systemd/system/trae-bot.service

# Content:
[Unit]
Description=TRAE Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Reload and start
sudo systemctl daemon-reload
sudo systemctl enable trae-bot
sudo systemctl start trae-bot
```

---

## 🔧 **Alternative Access Methods**

### Method 1: Direct Backend Start
```bash
# SSH into VPS
ssh root@5.189.145.177 -p 18177

# Navigate to backend
cd /root/ai-trading-sentinel/backend

# Install dependencies
pip install -r ../requirements.txt

# Start Flask app
python main.py
```

### Method 2: Docker Deployment
```bash
# Build and run with Docker
docker build -t trae-bot .
docker run -d -p 5000:5000 --name trae-bot trae-bot

# Check container status
docker ps
docker logs trae-bot
```

### Method 3: Screen Session
```bash
# Start in screen session (persistent)
screen -S trae-bot
cd /root/ai-trading-sentinel
python main.py

# Detach: Ctrl+A, then D
# Reattach: screen -r trae-bot
```

---

## 📊 **Verification Commands**

### Test Local Connection
```bash
# From VPS terminal
curl localhost:5000

# Should return HTML or JSON response
```

### Test External Connection
```bash
# From your local computer
curl http://5.189.145.177:5000

# Or use telnet to test port
telnet 5.189.145.177 5000
```

### Check All Services
```bash
# Check all running services
sudo systemctl list-units --type=service --state=running | grep trae

# Check network connections
sudo netstat -tlnp | grep python
```

---

## 🚨 **Emergency Recovery**

### If SSH is Also Down
1. **Contabo VNC Console**
   - Login to Contabo panel
   - Click "VNC Console"
   - Access desktop directly

2. **Reboot VPS**
   - Contabo panel → Reboot
   - Wait 2-3 minutes
   - Try connections again

3. **Reinstall Services**
   ```bash
   # Via VNC Console
   cd /root/ai-trading-sentinel
   ./vnc_deployment_implementation.sh
   ```

---

## ✅ **Success Indicators**

### Web Service Running
```bash
# These should all work:
curl localhost:5000                    # ✅ Returns HTML
sudo systemctl status trae-bot         # ✅ Active (running)
sudo netstat -tlnp | grep 5000         # ✅ Shows python process
```

### External Access Working
- Browser: `http://5.189.145.177:5000` loads dashboard
- No "Connection Refused" errors
- Can see trading interface

---

## 📱 **Quick Mobile Fix**

### Via Termius App
1. Connect to VPS
2. Run: `sudo systemctl restart trae-bot`
3. Check: `sudo systemctl status trae-bot`
4. Test: `curl localhost:5000`
5. If working, try browser again

---

## 🎯 **Next Steps After Fix**

1. **Verify Dashboard**: http://5.189.145.177:5000
2. **Test Trading Functions**: Login, place test trade
3. **Check Email Notifications**: Ensure alerts work
4. **Monitor Logs**: `sudo journalctl -u trae-bot -f`
5. **Set Auto-Start**: `sudo systemctl enable trae-bot`

**Remember**: The VPS needs to be fully deployed and configured before the web service will work. Use VNC Console for initial setup if SSH access fails!