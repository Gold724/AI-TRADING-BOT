# VNC Deployment Checklist - AI Trading Sentinel

## 🎯 Objective
Activate production URLs on Contabo VPS (161.97.112.146) via VNC connection

## 📋 Current Status
- ✅ Local Services Running:
  - Frontend: http://localhost:5173/
  - Backend: http://localhost:5000/
- ❌ Production URLs (Not Active Yet):
  - Frontend: http://161.97.112.146:3000/
  - Backend: http://161.97.112.146:5000/
  - WebSocket: ws://161.97.112.146:5000/

## 🖥️ VNC Connection Steps

### Step 1: Connect to VPS via VNC
```bash
# VNC Connection Details
IP: 161.97.112.146
Port: 5901 (or as configured)
Password: [Your VNC Password]
```

### Step 2: Open Terminal on VPS
Once connected via VNC, open a terminal and execute the following commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm git nginx curl

# Install Node.js 18+ (if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installations
node --version
npm --version
python3 --version
```

### Step 3: Create Application User and Directory
```bash
# Create trading user
sudo useradd -m -s /bin/bash trading
sudo usermod -aG sudo trading

# Create application directory
sudo mkdir -p /opt/ai-trading-sentinel
sudo chown trading:trading /opt/ai-trading-sentinel

# Switch to trading user
sudo su - trading
cd /opt/ai-trading-sentinel
```

### Step 4: Clone Repository
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git .

# Or if you need to transfer files manually:
# Create the directory structure and copy files from local machine
```

### Step 5: Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional packages if needed
pip install flask flask-cors flask-socketio python-dotenv requests
```

### Step 6: Setup Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Build production frontend
npm run build

# Go back to root
cd ..
```

### Step 7: Configure Environment Variables
```bash
# Create .env file
cat > .env << 'EOF'
# Bulenox Configuration
BULENOX_EMAIL=your_email@example.com
BULENOX_PASSWORD=your_password
BULENOX_BASE_URL=https://bulenox.projectx.com

# Trading Configuration
TRADING_MODE=demo
RISK_PERCENTAGE=1.0
MAX_DAILY_TRADES=10
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=3.0

# Server Configuration
FLASK_ENV=production
FLASK_DEBUG=False
HOST=0.0.0.0
PORT=5000
FRONTEND_PORT=3000

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# Notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=alerts@example.com

# GitHub (for CI/CD)
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/ai-trading-sentinel
EOF

# Set proper permissions
chmod 600 .env
```

### Step 8: Create Systemd Services

#### Backend Service
```bash
sudo tee /etc/systemd/system/ai-trading-backend.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
ExecStart=/opt/ai-trading-sentinel/venv/bin/python backend_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Frontend Service (using serve)
```bash
# Install serve globally
sudo npm install -g serve

# Create frontend service
sudo tee /etc/systemd/system/ai-trading-frontend.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/ai-trading-sentinel/frontend
ExecStart=/usr/bin/serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Step 9: Configure Nginx (Optional - for production)
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/ai-trading-sentinel > /dev/null << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 10: Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable ai-trading-backend
sudo systemctl enable ai-trading-frontend
sudo systemctl start ai-trading-backend
sudo systemctl start ai-trading-frontend

# Check service status
sudo systemctl status ai-trading-backend
sudo systemctl status ai-trading-frontend
```

### Step 11: Configure Firewall
```bash
# Allow necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 3000  # Frontend
sudo ufw allow 5000  # Backend
sudo ufw allow 5901  # VNC
sudo ufw enable
```

### Step 12: Verify Deployment
```bash
# Check if services are running
sudo systemctl status ai-trading-backend
sudo systemctl status ai-trading-frontend

# Check if ports are listening
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :5000

# Test API endpoints
curl http://localhost:5000/api/status
curl http://localhost:3000

# Check logs
sudo journalctl -u ai-trading-backend -f
sudo journalctl -u ai-trading-frontend -f
```

## 🎯 Expected Results After Deployment

Once all steps are completed, these URLs should be active:

- ✅ **Frontend**: http://161.97.112.146:3000/
- ✅ **Backend API**: http://161.97.112.146:5000/api/status
- ✅ **WebSocket**: ws://161.97.112.146:5000/
- ✅ **Health Check**: http://161.97.112.146:5000/api/health

## 🔧 Troubleshooting

### If services fail to start:
```bash
# Check logs
sudo journalctl -u ai-trading-backend -n 50
sudo journalctl -u ai-trading-frontend -n 50

# Restart services
sudo systemctl restart ai-trading-backend
sudo systemctl restart ai-trading-frontend
```

### If ports are not accessible:
```bash
# Check firewall
sudo ufw status

# Check if services are binding to correct interfaces
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :3000
```

### Manual service start (for debugging):
```bash
# Start backend manually
cd /opt/ai-trading-sentinel
source venv/bin/activate
python backend_main.py

# Start frontend manually (in another terminal)
cd /opt/ai-trading-sentinel/frontend
serve -s dist -l 3000
```

## 📞 Support Commands

```bash
# View all services
sudo systemctl list-units --type=service | grep ai-trading

# Restart all services
sudo systemctl restart ai-trading-backend ai-trading-frontend

# View system resources
top
df -h
free -h
```

---

**Note**: Execute these commands step by step via VNC connection to activate the production URLs. Each step should complete successfully before proceeding to the next one.