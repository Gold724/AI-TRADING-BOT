# 🚀 TRAE VPS Setup & Deployment Guide

## Current Issue: Flask Backend Not Accessible

**Problem**: `curl: (7) Failed to connect to 5.189.145.177 port 5000`

**Root Cause**: Backend not running or firewall blocking port 5000

---

## 🔧 Quick Fix Commands (Run on VPS)

### 1. Navigate to Project Directory
```bash
cd ~/ai-trading-sentinel
```

### 2. Run Diagnostic Script
```bash
chmod +x vps_diagnose.sh
./vps_diagnose.sh
```

### 3. Configure Firewall (Allow Port 5000)
```bash
sudo ufw allow 5000
sudo ufw status
```

### 4. Quick Start Backend
```bash
chmod +x start_backend.sh
./start_backend.sh
```

---

## 🏗️ Complete VPS Setup (First Time)

### 1. Run Full Deployment Script
```bash
chmod +x vps_deploy.sh
./vps_deploy.sh
```

### 2. Verify Service Status
```bash
sudo systemctl status trae-backend
```

### 3. Test API Endpoint
```bash
curl http://localhost:5000/api/health
curl http://5.189.145.177:5000/api/health
```

---

## 🔍 Troubleshooting Commands

### Check if Backend is Running
```bash
ps aux | grep python
netstat -tlnp | grep :5000
```

### View Service Logs
```bash
sudo journalctl -u trae-backend -f
```

### Restart Service
```bash
sudo systemctl restart trae-backend
sudo systemctl status trae-backend
```

### Manual Backend Start (Debug Mode)
```bash
cd ~/ai-trading-sentinel
source venv/bin/activate
cd backend
python main.py
```

---

## 🧪 Test Deployment API

Once backend is running, test the deployment endpoint:

```bash
curl -X POST "http://5.189.145.177:5000/api/deploy" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer trae_deploy_2024_secure_token_tesla369" \
  -d '{"strategy":"Tesla_369","mode":"safe","config":{"max_contracts":1,"daily_profit_target":535.71,"tesla_mode":true}}'
```

---

## 🔥 Expected Output

### Successful API Response:
```json
{
  "success": true,
  "message": "Tesla 3-6-9 strategy deployed successfully",
  "strategy": "Tesla_369",
  "mode": "safe"
}
```

### Health Check Response:
```json
{
  "status": "healthy",
  "service": "TRAE AI Trading Sentinel",
  "version": "2.0.0"
}
```

---

## 🚨 Emergency Commands

### Stop All Python Processes
```bash
sudo pkill -f python
```

### Disable Service
```bash
sudo systemctl stop trae-backend
sudo systemctl disable trae-backend
```

### Check System Resources
```bash
free -h
df -h
top
```

---

## 📋 Next Steps After Fix

1. ✅ Verify external API access
2. ✅ Test GitHub Actions deployment
3. ✅ Configure monitoring alerts
4. ✅ Setup SSL/HTTPS (optional)
5. ✅ Configure backup strategy

---

## 🔗 Useful URLs

- **API Health**: http://5.189.145.177:5000/api/health
- **Deployment**: http://5.189.145.177:5000/api/deploy
- **Dashboard**: http://5.189.145.177:5000/

---

**🎯 Priority**: Run `./vps_diagnose.sh` first to identify the exact issue!