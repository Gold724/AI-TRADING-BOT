# 🚀 AI Trading Sentinel - Complete VPS Setup Guide

## 📋 Prerequisites Checklist
- [ ] Contabo VPS running Ubuntu 22.04/24.04
- [ ] VNC access configured (not SSH)
- [ ] Bulenox trading account credentials
- [ ] GitHub repository access

## 🔧 Step 1: Deploy the Fixed Script

Run this command on your VPS to deploy with Node.js conflict fixes:

```bash
curl -fsSL https://raw.githubusercontent.com/your-username/AI-TRADING-BOT/main/deploy_vps_fixed.sh | bash
```

**What this script does:**
- ✅ Removes conflicting Node.js packages
- ✅ Installs Node.js 20.x LTS via NodeSource
- ✅ Installs Python 3.10+, PM2, Nginx
- ✅ Configures VNC for remote access
- ✅ Sets up the trading environment

## 🔐 Step 2: Configure Your .env File

### 2.1 Access Your VPS via VNC
```bash
# Start VNC server if not running
vncserver :1 -geometry 1920x1080 -depth 24
```

### 2.2 Navigate to Project Directory
```bash
cd /opt/ai-trading-sentinel
```

### 2.3 Create Production Environment File
```bash
# Copy the template
cp .env.production.template .env.production

# Edit with nano
nano .env.production
```

### 2.4 Add Your Bulenox Credentials
Replace these values in the `.env.production` file:

```bash
# ═══════════════════════════════════════
# 🏢 BROKER CREDENTIALS
# ═══════════════════════════════════════
BULENOX_USERNAME=your_actual_username
BULENOX_PASSWORD=your_actual_password
BULENOX_LOGIN_URL=https://bulenox.com/login

# ═══════════════════════════════════════
# 🌐 PRODUCTION SETTINGS
# ═══════════════════════════════════════
FLASK_ENV=production
FLASK_DEBUG=False
PYTHONPATH=/opt/ai-trading-sentinel

# ═══════════════════════════════════════
# 🔗 API ENDPOINTS (replace YOUR_VPS_IP)
# ═══════════════════════════════════════
VPS_IP=YOUR_ACTUAL_VPS_IP
API_URL=http://YOUR_ACTUAL_VPS_IP:5000
FRONTEND_URL=http://YOUR_ACTUAL_VPS_IP:3000
SENTINEL_URL=http://YOUR_ACTUAL_VPS_IP:8090

# ═══════════════════════════════════════
# 📊 TRADING CONFIGURATION (Contract-Based)
# ═══════════════════════════════════════
TRADING_MODE=DEMO  # Start with DEMO, change to LIVE when ready
RISK_LEVEL=MEDIUM

# Contract Sizing (Gold Futures)
MAX_CONTRACTS=3
DEFAULT_CONTRACTS=1
HIGH_CONFIDENCE_CONTRACTS=2

# Risk Management
MAX_DRAWDOWN=0.05
DAILY_PROFIT_TARGET=500
DAILY_MAX_DRAWDOWN=300
MAX_CONSECUTIVE_LOSSES=3

# Dynamic Stop Loss & Take Profit (Self-Adjusting)
ENABLE_DYNAMIC_SL_TP=true
ATR_MULTIPLIER_SL=2.0
ATR_MULTIPLIER_TP=3.0
TRAILING_STOP_ENABLED=true
VOLATILITY_ADJUSTMENT=true

# Gold Futures Specifications
CONTRACT_SIZE=100
TICK_SIZE=0.1
TICK_VALUE=10.0
MARGIN_REQUIREMENT=5000

# Session Trading Windows (UTC)
LONDON_SESSION_START=08:00
LONDON_SESSION_END=17:00
NY_SESSION_START=13:00
NY_SESSION_END=22:00
ASIAN_SESSION_START=00:00
ASIAN_SESSION_END=09:00

# ═══════════════════════════════════════
# 🔒 SECURITY
# ═══════════════════════════════════════
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# ═══════════════════════════════════════
# 📱 NOTIFICATIONS (optional)
# ═══════════════════════════════════════
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 2.5 Generate Security Keys
```bash
# Generate secure keys
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.production
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env.production
```

### 2.6 Save and Exit
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

## 🚀 Step 3: Start the Services

### 3.1 Restart All Services
```bash
# Restart PM2 processes
pm2 restart all

# Restart Nginx
sudo systemctl restart nginx

# Check status
pm2 status
sudo systemctl status nginx
```

### 3.2 Verify Services are Running
```bash
# Check if all services are up
curl http://localhost:5000/health
curl http://localhost:3000
curl http://localhost:8090
```

## 🌐 Step 4: Access Your Trading Dashboard

### 4.1 Dashboard URLs
- **Main Dashboard**: `http://YOUR_VPS_IP:3000`
- **API Backend**: `http://YOUR_VPS_IP:5000`
- **Trading Sentinel**: `http://YOUR_VPS_IP:8090`

### 4.2 VNC Access
```bash
# Connect via VNC Viewer to:
YOUR_VPS_IP:5901
```

## 🧪 Step 5: Test Your Setup

### 5.1 Test Bulenox Connection
```bash
cd /opt/ai-trading-sentinel
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
print('✅ Bulenox Username:', os.getenv('BULENOX_USERNAME'))
print('✅ Trading Mode:', os.getenv('TRADING_MODE'))
print('✅ Max Contracts:', os.getenv('MAX_CONTRACTS'))
"
```

### 5.2 Test API Endpoints
```bash
# Test health endpoint
curl -X GET http://localhost:5000/health

# Test trading status
curl -X GET http://localhost:5000/api/trading/status
```

### 5.3 Run Demo Trade Test
```bash
# Test demo trading
python3 test_tradebot.py --mode=demo --contracts=1
```

## 🔍 Step 6: Monitor and Troubleshoot

### 6.1 Check Logs
```bash
# PM2 logs
pm2 logs

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Application logs
tail -f /opt/ai-trading-sentinel/logs/trading.log
```

### 6.2 Common Issues & Solutions

#### Issue: Node.js conflicts
```bash
# Run the fix script again
curl -fsSL https://raw.githubusercontent.com/your-username/AI-TRADING-BOT/main/deploy_vps_fixed.sh | bash
```

#### Issue: Permission errors
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/*.sh
```

#### Issue: Services not starting
```bash
# Restart everything
pm2 kill
pm2 start ecosystem.config.js
sudo systemctl restart nginx
```

## 🎯 Step 7: Go Live (When Ready)

### 7.1 Switch to Live Trading
```bash
# Edit .env.production
nano .env.production

# Change this line:
TRADING_MODE=LIVE  # Changed from DEMO
```

### 7.2 Restart Services
```bash
pm2 restart all
```

### 7.3 Monitor Live Trading
```bash
# Watch real-time logs
pm2 logs --lines 50

# Monitor via dashboard
# Visit: http://YOUR_VPS_IP:3000
```

## 🛡️ Security Best Practices

1. **Never commit .env.production to Git**
2. **Use strong passwords for VNC**
3. **Enable firewall for specific ports only**
4. **Regular backups of configuration**
5. **Monitor for unusual trading activity**

## 📞 Support Commands

### Quick Health Check
```bash
# One-liner health check
curl -s http://localhost:5000/health && echo "✅ Backend OK" || echo "❌ Backend Down"
```

### Emergency Stop
```bash
# Stop all trading immediately
pm2 stop all
```

### Restart Everything
```bash
# Full restart
pm2 restart all && sudo systemctl restart nginx
```

---

## 🎉 You're All Set!

Your AI Trading Sentinel is now deployed and configured with:
- ✅ Contract-based position sizing
- ✅ Dynamic, self-adjusting Stop Loss & Take Profit
- ✅ Real-time risk management
- ✅ 24/7 monitoring and alerts
- ✅ Professional trading dashboard

**Next Steps:**
1. Test in DEMO mode first
2. Monitor performance for 24-48 hours
3. Switch to LIVE when confident
4. Set up alerts and monitoring

**Dashboard Access:** `http://YOUR_VPS_IP:3000`
**VNC Access:** `YOUR_VPS_IP:5901`

Happy Trading! 🚀📈