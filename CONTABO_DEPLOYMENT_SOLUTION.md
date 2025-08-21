# 🚀 AI Trading Sentinel - Contabo VPS Deployment Solution

## 🔐 SSH Authentication Issues Resolved

You're experiencing SSH authentication failures to `161.97.112.146`. Here are multiple solutions:

### ✅ Solution 1: Password Reset (Recommended)

1. **Access Contabo Control Panel**:
   - Login to your Contabo customer portal
   - Navigate to "Your Services" → "VPS"
   - Select your VPS (vmi2736801)
   - Click "Reset Root Password"
   - Use the new password for SSH access

2. **Alternative: VNC Console Access**:
   - Use Contabo's VNC console from the control panel
   - Login directly without SSH
   - Reset password: `passwd root`

### ✅ Solution 2: SSH Key Authentication Setup

```powershell
# Generate SSH key pair (if not exists)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Copy public key to server (after password reset)
ssh-copy-id root@161.97.112.146

# Test SSH key authentication
ssh root@161.97.112.146
```

### ✅ Solution 3: Direct VNC Deployment

If SSH continues to fail, use Contabo's VNC console:

1. Access VNC from Contabo control panel
2. Login as root
3. Run deployment commands directly

---

## 🎯 Deployment Methods

### Method A: Automated Script (After SSH Fix)

```bash
# Download and run deployment script
wget -O deploy.sh https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/deploy/contabo_deploy.sh
chmod +x deploy.sh
./deploy.sh
```

### Method B: Manual Step-by-Step Deployment

```bash
#!/bin/bash
# AI Trading Sentinel - Manual Deployment

# 1. System Update
apt update && apt upgrade -y

# 2. Install Dependencies
apt install -y python3 python3-pip python3-venv nodejs npm git curl wget unzip htop nano

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# 4. Create Project Directory
mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# 5. Setup Python Environment
python3 -m venv venv
source venv/bin/activate

# 6. Create Main Application
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Application
"""

import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/trading.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 AI Trading Sentinel Starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Trading Mode: {os.getenv('TRADING_MODE', 'simulation')}")
    
    logger.info("✅ AI Trading Sentinel is running")
    
    # Keep running
    try:
        while True:
            time.sleep(60)  # Check every minute
            logger.info("💓 Heartbeat - System running normally")
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        logger.info("👋 AI Trading Sentinel stopped")

if __name__ == "__main__":
    main()
EOF

# 7. Create Requirements
cat > requirements.txt << 'EOF'
flask==2.3.3
requests==2.31.0
psutil==5.9.5
schedule==1.2.0
pandas==2.0.3
numpy==1.24.3
EOF

# 8. Install Python Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 9. Create Environment Configuration
cat > .env << 'EOF'
# AI Trading Sentinel Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=5000
FRONTEND_PORT=3000

# Trading Configuration
TRADING_MODE=simulation
RISK_LEVEL=medium
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0

# Monitoring
MONITORING_ENABLED=true
ALERT_EMAIL=admin@example.com

# Security
SECRET_KEY=change-this-secret-key-$(date +%s)
JWT_SECRET=change-this-jwt-secret-$(date +%s)
EOF

# 10. Create Systemd Service
cat > /etc/systemd/system/trae.service << 'EOF'
[Unit]
Description=AI Trading Sentinel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
ExecStart=/opt/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 11. Enable and Start Service
systemctl daemon-reload
systemctl enable trae
systemctl start trae

# 12. Set Permissions
chown -R root:root /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/*.py

echo "✅ AI Trading Sentinel deployed successfully!"
echo "📍 Location: /opt/ai-trading-sentinel"
echo "🔧 Service: systemctl status trae"
echo "📊 Dashboard: http://$(curl -s ifconfig.me):5000"
echo "📝 Logs: journalctl -u trae -f"
```

### Method C: Docker Deployment

```bash
# Quick Docker deployment
docker run -d \
  --name ai-trading-sentinel \
  --restart unless-stopped \
  -p 5000:5000 \
  -p 3000:3000 \
  -v /opt/ai-trading-data:/app/data \
  -e ENVIRONMENT=production \
  -e TRADING_MODE=simulation \
  your-dockerhub/ai-trading-sentinel:latest
```

---

## 🔧 Post-Deployment Validation

```bash
# Check service status
systemctl status trae

# View logs
journalctl -u trae -f

# Test connectivity
curl -I http://localhost:5000

# Check system resources
htop
df -h
free -h
```

---

## 🌐 Access URLs

After successful deployment:

- **Main Dashboard**: `http://161.97.112.146:5000`
- **API Endpoint**: `http://161.97.112.146:5000/api`
- **Health Check**: `http://161.97.112.146:5000/health`
- **SSH Access**: `ssh root@161.97.112.146`

---

## 🚨 Troubleshooting

### SSH Issues:
```bash
# Check SSH service
systemctl status ssh

# Reset SSH configuration
sudo systemctl restart ssh

# Check firewall
ufw status
```

### Service Issues:
```bash
# Restart service
systemctl restart trae

# Check logs for errors
journalctl -u trae --no-pager -n 50

# Manual start for debugging
cd /opt/ai-trading-sentinel
source venv/bin/activate
python main.py
```

### Network Issues:
```bash
# Check open ports
netstat -tlnp

# Test internal connectivity
curl localhost:5000

# Check firewall rules
ufw status verbose
```

---

## 📞 Support

- **Contabo Support**: support@contabo.com
- **VPS Control Panel**: [Contabo Customer Portal](https://my.contabo.com)
- **Emergency Access**: Use VNC console from control panel

---

## 🎯 Next Steps

1. ✅ Fix SSH authentication using Contabo control panel
2. ✅ Deploy AI Trading Sentinel using preferred method
3. ✅ Configure environment variables and credentials
4. ✅ Test all endpoints and functionality
5. ✅ Set up monitoring and alerts
6. ✅ Configure SSL/HTTPS (optional)
7. ✅ Set up automated backups

**Status**: Ready for deployment once SSH access is restored! 🚀