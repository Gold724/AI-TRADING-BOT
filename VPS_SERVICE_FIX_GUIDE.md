# 🔧 VPS Service Fix Guide - AI Trading Sentinel

## 🚨 Current Issue: Service Failing to Start

**Problem**: The `trae-bot.service` is failing with exit-code errors and the web interface at `http://5.189.145.177:5000` shows `ERR_CONNECTION_REFUSED`.

**Root Cause**: 
- Incorrect service configuration paths
- Missing project directory structure
- Service file conflicts (duplicate StandardOutput)
- Python environment issues

---

## 🎯 Quick Fix (VNC Console Method)

### Step 1: Connect to VNC Console
```
Contabo VNC Console:
IP: 5.189.145.177
Port: 63162
Credentials: Use your Contabo account
```

### Step 2: Open Terminal in VNC
1. Right-click desktop → Open Terminal
2. Switch to root user:
```bash
sudo su -
```

### Step 3: Run Diagnostic Script
```bash
cd /root
wget https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/diagnose_service_failure.sh
chmod +x diagnose_service_failure.sh
./diagnose_service_failure.sh
```

### Step 4: Run Fix Script
```bash
wget https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/fix_vps_service.sh
chmod +x fix_vps_service.sh
./fix_vps_service.sh
```

---

## 🛠️ Manual Fix Steps

### 1. Stop Failing Service
```bash
sudo systemctl stop trae-bot.service
sudo systemctl disable trae-bot.service
```

### 2. Create Correct Directory Structure
```bash
sudo mkdir -p /root/ai-trading-sentinel
cd /root/ai-trading-sentinel
```

### 3. Clone Repository (if not exists)
```bash
# If directory is empty
git clone https://github.com/your-username/ai-trading-sentinel.git .

# Or copy files from existing location
cp -r /root/AI-TRADING-BOT/* /root/ai-trading-sentinel/ 2>/dev/null || true
```

### 4. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install
playwright install-deps
```

### 5. Create Logs Directory
```bash
mkdir -p logs
touch logs/trae.log
chmod 644 logs/trae.log
```

### 6. Fix Service Configuration
```bash
# Copy corrected service file
sudo cp trae-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trae-bot.service
```

### 7. Configure Environment
```bash
# Edit .env file with correct credentials
nano .env
```

### 8. Test Service
```bash
sudo systemctl start trae-bot.service
sudo systemctl status trae-bot.service
```

### 9. Start Web Interface
```bash
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
echo $! > backend.pid
```

---

## 🔍 Troubleshooting Commands

### Check Service Status
```bash
# Service status
sudo systemctl status trae-bot.service -l

# Service logs
sudo journalctl -u trae-bot.service -f

# Recent logs
sudo journalctl -u trae-bot.service --no-pager -l -n 20
```

### Check Web Interface
```bash
# Test local connection
curl localhost:5000
curl localhost:5000/health

# Check port listening
sudo netstat -tlnp | grep 5000

# Check backend process
ps aux | grep python
```

### Check File Permissions
```bash
# Check project permissions
ls -la /root/ai-trading-sentinel/

# Check service file
ls -la /etc/systemd/system/trae-bot.service

# Check logs
ls -la /root/ai-trading-sentinel/logs/
```

---

## 🚀 Expected Results After Fix

### ✅ Service Status
```
● trae-bot.service - AI Trading Sentinel Bot
   Loaded: loaded (/etc/systemd/system/trae-bot.service; enabled)
   Active: active (running) since [timestamp]
```

### ✅ Web Interface
```bash
$ curl localhost:5000/health
{"status": "healthy", "service": "AI Trading Sentinel"}
```

### ✅ External Access
- Web Dashboard: `http://5.189.145.177:5000`
- API Health: `http://5.189.145.177:5000/health`
- Trading Status: `http://5.189.145.177:5000/api/status`

---

## 📱 Mobile Management

### Termius SSH Commands
```bash
# Quick status check
sudo systemctl status trae-bot.service

# Restart service
sudo systemctl restart trae-bot.service

# View logs
tail -f /root/ai-trading-sentinel/logs/trae.log

# Check web interface
curl localhost:5000/health
```

### Emergency Restart
```bash
# Full restart sequence
sudo systemctl stop trae-bot.service
sudo systemctl start trae-bot.service
cd /root/ai-trading-sentinel
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
```

---

## 🆘 Emergency Recovery

If all else fails, run the complete deployment:

```bash
# Emergency full deployment
cd /root
wget https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/emergency_deploy.sh
chmod +x emergency_deploy.sh
./emergency_deploy.sh
```

---

## 📞 Support Contacts

- **VNC Console**: Contabo Customer Portal
- **SSH Access**: `ssh root@5.189.145.177 -p 18177`
- **Web Interface**: `http://5.189.145.177:5000`
- **Logs Location**: `/root/ai-trading-sentinel/logs/`

---

## 🎯 Success Indicators

1. ✅ Service shows `Active: active (running)`
2. ✅ Web interface responds to `curl localhost:5000`
3. ✅ External access works: `http://5.189.145.177:5000`
4. ✅ No errors in `journalctl -u trae-bot.service`
5. ✅ Backend process running: `ps aux | grep python`

**Once all indicators are green, the AI Trading Sentinel is ready for 24/7 operation!**