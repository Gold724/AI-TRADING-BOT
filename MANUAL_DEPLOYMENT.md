# 🚀 AI Trading Sentinel - Manual Deployment Guide

## Current Situation
You're already connected to your Contabo VPS. Since SSH authentication is having issues with the target server (161.97.112.146), we'll deploy directly on your current server.

## Quick Deployment Steps

Since you're already on the Contabo server, run these commands directly:

### Step 1: Copy the deployment script
```bash
# You can copy the deploy_local.sh content or create it manually
cat > deploy_local.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 AI Trading Sentinel - Direct Deployment"
echo "========================================="
echo "Deploying on current server: $(hostname)"
echo "IP Address: $(curl -s ifconfig.me 2>/dev/null || echo 'localhost')"
echo ""

# Update system
echo "[1/10] Updating system..."
sudo apt update -y

# Install packages
echo "[2/10] Installing packages..."
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Create directory
echo "[3/10] Creating directory..."
sudo mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Create main app
echo "[4/10] Creating main application..."
sudo tee main.py > /dev/null << 'APPEOF'
#!/usr/bin/env python3
import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/trading.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 AI Trading Sentinel Starting...")
    logger.info(f"Server: {os.uname().nodename}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    
    try:
        while True:
            logger.info("💓 System running - Heartbeat OK")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        logger.info("👋 AI Trading Sentinel stopped")

if __name__ == "__main__":
    main()
APPEOF

# Create requirements
echo "[5/10] Creating requirements..."
sudo tee requirements.txt > /dev/null << 'REQEOF'
flask==2.3.3
requests==2.31.0
psutil==5.9.5
REQEOF

# Setup Python environment
echo "[6/10] Setting up Python environment..."
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt

# Create systemd service
echo "[7/10] Creating systemd service..."
sudo tee /etc/systemd/system/trae.service > /dev/null << 'SVCEOF'
[Unit]
Description=AI Trading Sentinel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel
ExecStart=/opt/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVCEOF

# Set permissions
echo "[8/10] Setting permissions..."
sudo chown -R root:root /opt/ai-trading-sentinel
sudo chmod +x /opt/ai-trading-sentinel/main.py

# Enable service
echo "[9/10] Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable trae
sudo systemctl start trae

# Final status
echo "[10/10] Checking status..."
echo ""
echo "✅ Deployment completed!"
echo "📍 Location: /opt/ai-trading-sentinel"
echo "🔧 Service: $(sudo systemctl is-active trae)"
echo "📊 Status: $(sudo systemctl status trae --no-pager -l)"
echo "📝 Logs: sudo journalctl -u trae -f"
echo ""
EOF
```

### Step 2: Run the deployment
```bash
chmod +x deploy_local.sh
./deploy_local.sh
```

### Step 3: Verify deployment
```bash
# Check service status
sudo systemctl status trae

# View logs
sudo journalctl -u trae -f

# Check if it's running
ps aux | grep python
```

## Alternative: Manual Step-by-Step

If you prefer manual installation:

```bash
# 1. Update system
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv git curl wget

# 2. Create directory
sudo mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# 3. Create virtual environment
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip

# 4. Install basic packages
sudo ./venv/bin/pip install flask requests psutil

# 5. Create a simple test app
sudo tee main.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 AI Trading Sentinel Starting...")
    while True:
        logger.info("💓 System running - Heartbeat OK")
        time.sleep(60)

if __name__ == "__main__":
    main()
EOF

# 6. Make executable
sudo chmod +x main.py

# 7. Test run
sudo ./venv/bin/python main.py
```

## Service Management Commands

```bash
# Start service
sudo systemctl start trae

# Stop service
sudo systemctl stop trae

# Restart service
sudo systemctl restart trae

# Check status
sudo systemctl status trae

# View logs
sudo journalctl -u trae -f

# Enable auto-start
sudo systemctl enable trae
```

## Troubleshooting

### If deployment fails:
```bash
# Check system info
uname -a
whoami
pwd

# Check Python
python3 --version
which python3

# Check permissions
ls -la /opt/
sudo ls -la /opt/ai-trading-sentinel/
```

### If service fails:
```bash
# Check service logs
sudo journalctl -u trae --no-pager

# Check if port is in use
sudo netstat -tlnp | grep :5000

# Manual test
cd /opt/ai-trading-sentinel
sudo ./venv/bin/python main.py
```

## Next Steps After Deployment

1. **Verify the service is running**: `sudo systemctl status trae`
2. **Check logs**: `sudo journalctl -u trae -f`
3. **Test connectivity**: The service should be logging heartbeat messages
4. **Configure firewall** (if needed): `sudo ufw allow 5000`
5. **Set up monitoring**: The logs will show system status

## Success Indicators

✅ Service shows "active (running)" status  
✅ Logs show "💓 System running - Heartbeat OK" every minute  
✅ No error messages in journalctl  
✅ Process visible in `ps aux | grep python`  

---

**Note**: This deployment creates a basic heartbeat service. Once confirmed working, we can enhance it with the full trading functionality.