# VNC Remote Desktop Deployment Guide
## AI Trading Sentinel - Global Access via VNC

🚀 **Complete VNC setup for remote desktop access to Contabo VPS**

---

## 🎯 VNC Deployment Strategy

### Why VNC Over SSH?
- **Visual Interface**: Direct desktop access for easier file management
- **No Authentication Issues**: Bypass SSH key/password complications
- **Drag & Drop**: Easy file transfers via desktop interface
- **Browser Access**: Manage trading bot through VPS browser directly
- **Real-time Monitoring**: Visual monitoring of bot execution

---

## 📋 VNC Server Setup Commands

### 1. Connect to VPS (One-time SSH)
```bash
ssh root@161.97.112.146
```

### 2. Install VNC Server & Desktop Environment
```bash
# Update system
apt update && apt upgrade -y

# Install desktop environment (lightweight XFCE)
apt install -y xfce4 xfce4-goodies

# Install VNC server
apt install -y tightvncserver

# Install additional tools
apt install -y firefox nginx unzip curl git python3-pip
```

### 3. Configure VNC Server
```bash
# Start VNC server (will prompt for password)
vncserver :1

# Stop VNC server to configure
vncserver -kill :1

# Create VNC startup script
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF

# Make executable
chmod +x ~/.vnc/xstartup

# Create systemd service for auto-start
cat > /etc/systemd/system/vncserver@.service << 'EOF'
[Unit]
Description=Start TightVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/root

PIDFile=/root/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1920x1080 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
EOF

# Enable and start VNC service
systemctl daemon-reload
systemctl enable vncserver@1.service
systemctl start vncserver@1.service
```

### 4. Configure Firewall for VNC
```bash
# Allow VNC port (5901 for display :1)
ufw allow 5901/tcp

# Allow HTTP/HTTPS for web access
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Flask backend
ufw allow 5000/tcp

# Enable firewall
ufw --force enable
```

---

## 🖥️ VNC Client Access

### Option 1: VNC Viewer (Recommended)
1. **Download VNC Viewer**: https://www.realvnc.com/en/connect/download/viewer/
2. **Connect**: `161.97.112.146:5901`
3. **Enter VNC Password**: (set during vncserver :1 setup)

### Option 2: Web Browser VNC
```bash
# Install noVNC for web access
cd /opt
git clone https://github.com/novnc/noVNC.git
cd noVNC

# Install websockify
pip3 install websockify

# Start web VNC proxy
./utils/launch.sh --vnc localhost:5901 --listen 6080
```
**Access**: http://161.97.112.146:6080/vnc.html

---

## 📁 Frontend Deployment via VNC

### 1. Transfer Files via VNC Desktop
1. **Connect to VNC Desktop**
2. **Open Firefox** on VPS desktop
3. **Download frontend-cloud.zip** from your GitHub or cloud storage
4. **Extract files** using desktop file manager

### 2. Deploy Frontend via VNC Terminal
```bash
# Open terminal in VNC desktop
# Navigate to extracted frontend
cd /root/frontend-deployment

# Extract frontend
unzip frontend-cloud.zip -d /var/www/html/

# Configure Nginx
cat > /etc/nginx/sites-available/trading-bot << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    root /var/www/html/dist;
    index index.html;

    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://localhost:5000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx
```

### 3. Start Flask Backend
```bash
# Navigate to backend directory
cd /root/ai-trading-sentinel/backend

# Install Python dependencies
pip3 install -r requirements.txt

# Start Flask backend
python3 main.py
```

---

## 🔧 VNC Management Commands

### VNC Server Control
```bash
# Start VNC server
systemctl start vncserver@1.service

# Stop VNC server
systemctl stop vncserver@1.service

# Restart VNC server
systemctl restart vncserver@1.service

# Check VNC status
systemctl status vncserver@1.service

# View VNC logs
journalctl -u vncserver@1.service -f
```

### Change VNC Password
```bash
vncpasswd
```

### Multiple VNC Sessions
```bash
# Start additional displays
vncserver :2  # Port 5902
vncserver :3  # Port 5903
```

---

## 🌐 Access Points After VNC Deployment

| Service | URL | Purpose |
|---------|-----|----------|
| **VNC Desktop** | `161.97.112.146:5901` | Remote desktop access |
| **Web VNC** | `http://161.97.112.146:6080/vnc.html` | Browser-based VNC |
| **Trading Dashboard** | `http://161.97.112.146` | React frontend |
| **Flask API** | `http://161.97.112.146/api/` | Backend API |
| **WebSocket** | `ws://161.97.112.146/ws` | Real-time updates |

---

## 🚀 Quick VNC Deployment Script

```bash
#!/bin/bash
# save as: vnc_deploy.sh

echo "🚀 AI Trading Sentinel - VNC Deployment"

# Install desktop and VNC
apt update && apt upgrade -y
apt install -y xfce4 xfce4-goodies tightvncserver firefox nginx unzip curl git python3-pip

# Configure VNC
vncserver :1
vncserver -kill :1

# Create xstartup
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF
chmod +x ~/.vnc/xstartup

# Create systemd service
cat > /etc/systemd/system/vncserver@.service << 'EOF'
[Unit]
Description=Start TightVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/root

PIDFile=/root/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1920x1080 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
EOF

# Enable VNC service
systemctl daemon-reload
systemctl enable vncserver@1.service
systemctl start vncserver@1.service

# Configure firewall
ufw allow 5901/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw --force enable

echo "✅ VNC Server deployed successfully!"
echo "🖥️  Connect to: 161.97.112.146:5901"
echo "🌐 Web VNC: Install noVNC for browser access"
```

---

## 🔒 Security Considerations

### VNC Security
- **Strong Password**: Use complex VNC password
- **Firewall Rules**: Restrict VNC access to specific IPs if needed
- **SSH Tunnel**: For extra security, tunnel VNC through SSH

### SSH Tunnel (Optional)
```bash
# From local machine
ssh -L 5901:localhost:5901 root@161.97.112.146
# Then connect VNC to localhost:5901
```

---

## 📊 Success Metrics

✅ **VNC Server Running**: `systemctl status vncserver@1.service`  
✅ **Desktop Accessible**: VNC client connects successfully  
✅ **Frontend Deployed**: Trading dashboard loads at http://161.97.112.146  
✅ **Backend Connected**: API endpoints respond correctly  
✅ **WebSocket Active**: Real-time updates working  

---

## 🎯 Next Steps

1. **Execute VNC Setup**: Run the deployment script on VPS
2. **Connect via VNC**: Use VNC Viewer to access desktop
3. **Deploy Frontend**: Transfer and configure files via desktop
4. **Start Trading Bot**: Launch bot through VNC desktop interface
5. **Monitor Globally**: Access trading dashboard from anywhere

**🚀 Ready for 24/7 Global Trading Access! 🚀**