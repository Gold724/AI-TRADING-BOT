# 🚨 IMMEDIATE VNC DEPLOYMENT - Activate Production URLs

## Current Status

### ✅ Local Services (Active)
- **Frontend**: http://localhost:5173/ ✅
- **Backend**: http://localhost:5000/ ✅
- **Trading Status**: http://localhost:5000/api/trading/status ✅
- **WebSocket**: ws://localhost:5000/ws ✅

### ❌ Production URLs (Not Active - Need VNC Deployment)
- **Frontend**: http://161.97.112.146/ ❌
- **API Status**: http://161.97.112.146/api/status ❌
- **Trading Status**: http://161.97.112.146/api/trading/status ❌
- **WebSocket**: ws://161.97.112.146/ws ❌

---

## 🎯 IMMEDIATE ACTION REQUIRED

### Step 1: Connect to VPS via VNC
```
VPS Details:
- IP: 161.97.112.146
- Access: VNC Remote Desktop
- OS: Ubuntu 22.04/24.04
```

**VNC Connection Methods:**
1. **Windows Remote Desktop**: Use built-in RDP client
2. **TightVNC Viewer**: Download from tightvnc.com
3. **RealVNC Viewer**: Download from realvnc.com
4. **UltraVNC**: Download from uvnc.com

### Step 2: Execute Deployment Commands

Once connected via VNC desktop, open terminal and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.10 python3-pip nodejs npm git nginx curl wget htop

# Install PM2 globally
sudo npm install -g pm2

# Create application user
sudo useradd -m -s /bin/bash tradebot
sudo usermod -aG sudo tradebot

# Switch to tradebot user
sudo su - tradebot

# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
cd ai-trading-sentinel

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup frontend
cd frontend
npm install
npm run build
cd ..
```

### Step 3: Transfer .env File via VNC

**CRITICAL**: Copy your local `.env` file to the VPS:

1. **Via VNC File Manager**: Drag and drop from local machine
2. **Via VNC Desktop**: Copy content and paste into new file
3. **Location**: `/home/tradebot/ai-trading-sentinel/.env`

### Step 4: Configure Services

```bash
# Create backend systemd service
sudo tee /etc/systemd/system/trading-backend.service > /dev/null <<'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/home/tradebot/ai-trading-sentinel
Environment=PATH=/home/tradebot/ai-trading-sentinel/venv/bin
ExecStart=/home/tradebot/ai-trading-sentinel/venv/bin/python backend_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/trading-app > /dev/null <<'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    location / {
        root /home/tradebot/ai-trading-sentinel/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable services
sudo ln -sf /etc/nginx/sites-available/trading-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo systemctl enable trading-backend nginx
sudo systemctl start trading-backend
sudo systemctl restart nginx
```

### Step 5: Verify Deployment

```bash
# Check service status
sudo systemctl status trading-backend
sudo systemctl status nginx

# Test local endpoints
curl http://localhost:5000/api/status
curl http://127.0.0.1/api/status

# Check from VNC browser
# Open Firefox/Chrome on VPS desktop:
# - http://161.97.112.146/
# - http://161.97.112.146/api/status
```

---

## 🔧 Quick Troubleshooting

### If Backend Won't Start:
```bash
# Check logs
sudo journalctl -u trading-backend -f

# Check Python environment
source /home/tradebot/ai-trading-sentinel/venv/bin/activate
python backend_main.py  # Test manually
```

### If Nginx Issues:
```bash
# Test Nginx config
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### If URLs Still Not Working:
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443

# Check if services are listening
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :5000
```

---

## 🎯 Expected Results After Deployment

Once deployment is complete, these URLs should be active:

- ✅ **Frontend**: http://161.97.112.146/
- ✅ **API Status**: http://161.97.112.146/api/status
- ✅ **Trading Status**: http://161.97.112.146/api/trading/status
- ✅ **WebSocket**: ws://161.97.112.146/ws

---

## 📞 Emergency Commands

```bash
# Stop all services
sudo systemctl stop trading-backend nginx

# Restart all services
sudo systemctl restart trading-backend nginx

# Check system resources
htop
df -h
free -h
```

---

**⚠️ IMPORTANT**: The production URLs will only become active after executing these deployment steps on the actual VPS via VNC connection. The deployment scripts and configurations are ready - they just need to be executed on the target server.

**Next Step**: Connect to 161.97.112.146 via VNC and follow this deployment guide to activate all production URLs.