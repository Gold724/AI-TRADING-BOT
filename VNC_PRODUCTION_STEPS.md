# 🚀 AI Trading Sentinel - VNC Production Deployment

## Current Status: Services Running ✅

### Active Local Services
- **Frontend**: http://localhost:5173/ (Vite v4.5.14)
- **Backend**: http://localhost:5000/ (Flask API with health checks)
- **WebSocket**: ws://localhost:5000/ws

---

## 🎯 Next 4 Critical Production Steps

### Step 1: VNC Connection & Environment Setup
**Target**: Contabo VPS 161.97.112.146

```bash
# Connect via VNC Desktop (not SSH)
# Use TightVNC, RealVNC, or Windows Remote Desktop

# System preparation via VNC terminal
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3-pip nodejs npm git nginx
sudo apt install -y htop curl wget unzip firefox

# Install PM2 for process management
sudo npm install -g pm2

# Create dedicated user
sudo useradd -m -s /bin/bash tradebot
sudo usermod -aG sudo tradebot
sudo mkdir -p /home/tradebot/.ssh
```

**VNC Advantages**:
- Direct desktop access for file management
- Browser testing on server
- Visual service monitoring
- Easy file transfer via drag-and-drop

---

### Step 2: Application Deployment & Configuration

```bash
# Switch to application user
sudo su - tradebot
cd /home/tradebot

# Clone and setup application
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
cd ai-trading-sentinel

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend build
cd frontend
npm install
npm run build
cd ..

# Copy .env file via VNC file manager
# Drag .env from local machine to /home/tradebot/ai-trading-sentinel/
```

**Critical Files to Transfer via VNC**:
- `.env` (trading credentials)
- `secrets.json` (if exists)
- SSL certificates (for HTTPS)

---

### Step 3: Production Services & Nginx Setup

```bash
# Backend systemd service
sudo tee /etc/systemd/system/trading-backend.service > /dev/null <<'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=tradebot
Group=tradebot
WorkingDirectory=/home/tradebot/ai-trading-sentinel
Environment=PATH=/home/tradebot/ai-trading-sentinel/venv/bin
Environment=PYTHONPATH=/home/tradebot/ai-trading-sentinel
ExecStart=/home/tradebot/ai-trading-sentinel/venv/bin/python backend_main.py
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Nginx configuration
sudo tee /etc/nginx/sites-available/trading-app > /dev/null <<'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    client_max_body_size 50M;
    
    # Frontend static files
    location / {
        root /home/tradebot/ai-trading-sentinel/frontend/dist;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # API endpoints
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket connections
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable and start services
sudo ln -sf /etc/nginx/sites-available/trading-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable trading-backend nginx
sudo systemctl start trading-backend
sudo systemctl reload nginx
```

---

### Step 4: 24/7 Monitoring & Health Checks

```bash
# Advanced monitoring script
tee /home/tradebot/advanced_monitor.py > /dev/null <<'EOF'
#!/usr/bin/env python3
import requests
import psutil
import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    filename='/home/tradebot/monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_backend_health():
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=10)
        return response.status_code == 200
    except:
        return False

def check_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': disk.percent
    }

def restart_backend():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'trading-backend'], check=True)
        logging.info("Backend restarted successfully")
        return True
    except:
        logging.error("Failed to restart backend")
        return False

def main():
    consecutive_failures = 0
    
    while True:
        try:
            # Health checks
            backend_healthy = check_backend_health()
            resources = check_system_resources()
            
            if not backend_healthy:
                consecutive_failures += 1
                logging.warning(f"Backend unhealthy (failure #{consecutive_failures})")
                
                if consecutive_failures >= 3:
                    logging.error("Multiple backend failures, restarting...")
                    restart_backend()
                    consecutive_failures = 0
                    time.sleep(30)  # Wait for restart
            else:
                consecutive_failures = 0
            
            # Resource monitoring
            if resources['cpu'] > 90:
                logging.warning(f"High CPU usage: {resources['cpu']}%")
            if resources['memory'] > 90:
                logging.warning(f"High memory usage: {resources['memory']}%")
            if resources['disk'] > 90:
                logging.error(f"High disk usage: {resources['disk']}%")
            
            # Log status every 5 minutes
            if int(time.time()) % 300 == 0:
                logging.info(f"System OK - CPU: {resources['cpu']}%, Memory: {resources['memory']}%, Backend: {'OK' if backend_healthy else 'FAIL'}")
            
        except Exception as e:
            logging.error(f"Monitor error: {e}")
        
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    main()
EOF

chmod +x /home/tradebot/advanced_monitor.py

# Monitor service
sudo tee /etc/systemd/system/trading-monitor.service > /dev/null <<'EOF'
[Unit]
Description=AI Trading Sentinel Advanced Monitor
After=network.target trading-backend.service
Wants=trading-backend.service

[Service]
Type=simple
User=tradebot
Group=tradebot
WorkingDirectory=/home/tradebot
ExecStart=/home/tradebot/ai-trading-sentinel/venv/bin/python /home/tradebot/advanced_monitor.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Enable monitoring
sudo systemctl enable trading-monitor
sudo systemctl start trading-monitor

# Setup log rotation
sudo tee /etc/logrotate.d/trading-app > /dev/null <<'EOF'
/home/tradebot/monitor.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

---

## 🔧 VNC Management Commands

### Service Status (via VNC terminal)
```bash
# Check all services
sudo systemctl status trading-backend trading-monitor nginx

# View real-time logs
sudo journalctl -u trading-backend -f
tail -f /home/tradebot/monitor.log

# System resources
htop
df -h
free -h
```

### Emergency Controls
```bash
# EMERGENCY STOP (stops all trading)
sudo systemctl stop trading-backend
sudo pkill -f "python.*backend_main.py"

# Restart everything
sudo systemctl restart trading-backend nginx trading-monitor

# Check production URLs
curl http://161.97.112.146/api/status
curl http://localhost:5000/api/status
```

---

## 🛡️ Production Verification Checklist

- [ ] **VNC Connection**: Stable desktop access to 161.97.112.146
- [ ] **Services Running**: Backend, Nginx, Monitor all active
- [ ] **URLs Accessible**: 
  - [ ] http://161.97.112.146/ (Frontend)
  - [ ] http://161.97.112.146/api/status (API)
- [ ] **Environment**: `.env` file properly configured
- [ ] **Monitoring**: Logs being written to `/home/tradebot/monitor.log`
- [ ] **Auto-restart**: Services restart on failure
- [ ] **Resource Monitoring**: CPU/Memory/Disk alerts working
- [ ] **Demo Mode**: Verified before enabling live trading

---

## 📊 Expected Production URLs

After successful deployment:

- **Main Dashboard**: http://161.97.112.146/
- **API Health**: http://161.97.112.146/api/status
- **Trading Status**: http://161.97.112.146/api/trading/status
- **WebSocket**: ws://161.97.112.146/ws

**Next Phase**: SSL certificate installation for HTTPS access.

---

*This completes the 4-step VNC production deployment for 24/7 AI Trading Sentinel operations.*