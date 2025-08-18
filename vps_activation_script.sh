#!/bin/bash
# AI Trading Sentinel - VPS Activation & Troubleshooting Script
# Run this script on the VPS via VNC to activate all services

set -e

VPS_IP="161.97.112.146"
LOG_FILE="/tmp/vps_activation.log"

echo "=================================================" | tee -a $LOG_FILE
echo "AI Trading Sentinel - VPS Activation Script" | tee -a $LOG_FILE
echo "Target VPS: $VPS_IP" | tee -a $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE
echo "=================================================" | tee -a $LOG_FILE

# Function to check service status
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✅ $service is running" | tee -a $LOG_FILE
        return 0
    else
        echo "❌ $service is not running" | tee -a $LOG_FILE
        return 1
    fi
}

# Function to check port
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln | grep -q ":$port "; then
        echo "✅ Port $port ($service) is listening" | tee -a $LOG_FILE
        return 0
    else
        echo "❌ Port $port ($service) is not listening" | tee -a $LOG_FILE
        return 1
    fi
}

echo "\n🔧 STEP 1: System Update & Dependencies" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE
apt update && apt upgrade -y | tee -a $LOG_FILE
apt install -y nginx python3 python3-pip python3-venv git curl wget unzip net-tools | tee -a $LOG_FILE

echo "\n🖥️  STEP 2: VNC Server Activation" | tee -a $LOG_FILE
echo "----------------------------------" | tee -a $LOG_FILE

# Check if VNC is installed
if ! command -v vncserver &> /dev/null; then
    echo "Installing VNC server..." | tee -a $LOG_FILE
    apt install -y tightvncserver xfce4 xfce4-goodies | tee -a $LOG_FILE
fi

# Kill any existing VNC sessions
vncserver -kill :1 2>/dev/null || true

# Start VNC server
echo "Starting VNC server on display :1..." | tee -a $LOG_FILE
vncserver :1 -geometry 1920x1080 -depth 24 | tee -a $LOG_FILE

# Enable VNC systemd service
if [ ! -f "/etc/systemd/system/vncserver@.service" ]; then
    echo "Creating VNC systemd service..." | tee -a $LOG_FILE
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
    
    systemctl daemon-reload
    systemctl enable vncserver@1.service
    systemctl start vncserver@1.service
fi

check_service "vncserver@1"
check_port "5901" "VNC"

echo "\n🌐 STEP 3: Nginx Web Server Setup" | tee -a $LOG_FILE
echo "----------------------------------" | tee -a $LOG_FILE

# Create web directory
mkdir -p /var/www/html
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html

# Create default index if not exists
if [ ! -f "/var/www/html/index.html" ]; then
    cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel - VPS Active</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .status { background: #2d5a27; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .btn { background: #4CAF50; color: white; padding: 15px 32px; text-decoration: none; display: inline-block; margin: 10px; border-radius: 5px; }
        .btn:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel</h1>
        <div class="status">
            <h2>✅ VPS is Active</h2>
            <p>Server IP: 161.97.112.146</p>
            <p>Status: Online and Ready</p>
            <p>Last Updated: $(date)</p>
        </div>
        <a href="/api/health" class="btn">API Health Check</a>
        <a href="/api/status" class="btn">Bot Status</a>
        <p><strong>VNC Access:</strong> vnc://161.97.112.146:5901</p>
    </div>
</body>
</html>
EOF
fi

# Configure Nginx
cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    root /var/www/html;
    index index.html index.htm;
    
    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }
    
    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:5000/ws;
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

# Test Nginx configuration
nginx -t | tee -a $LOG_FILE

# Restart and enable Nginx
systemctl restart nginx
systemctl enable nginx

check_service "nginx"
check_port "80" "HTTP"

echo "\n🔌 STEP 4: Flask Backend Setup" | tee -a $LOG_FILE
echo "------------------------------" | tee -a $LOG_FILE

# Create backend directory
mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Create simple Flask backend if not exists
if [ ! -f "backend_main.py" ]; then
    cat > backend_main.py << 'EOF'
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'AI Trading Sentinel Backend',
        'version': '1.0.0'
    })

@app.route('/status', methods=['GET'])
def bot_status():
    return jsonify({
        'bot_active': True,
        'trading_enabled': False,
        'last_trade': None,
        'balance': 0.0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/trades', methods=['GET'])
def trade_history():
    return jsonify({
        'trades': [],
        'total_trades': 0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        'risk_level': 'medium',
        'max_position_size': 1000,
        'stop_loss': 2.0,
        'take_profit': 4.0,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
fi

# Create requirements.txt
cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-CORS==4.0.0
requests==2.31.0
EOF

# Install Python dependencies
pip3 install -r requirements.txt | tee -a $LOG_FILE

# Create systemd service for Flask backend
cat > /etc/systemd/system/ai-trading-backend.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel
ExecStart=/usr/bin/python3 backend_main.py
Restart=always
RestartSec=10
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-trading-backend.service
systemctl start ai-trading-backend.service

check_service "ai-trading-backend"
check_port "5000" "Flask Backend"

echo "\n🔥 STEP 5: Firewall Configuration" | tee -a $LOG_FILE
echo "----------------------------------" | tee -a $LOG_FILE

# Configure UFW firewall
ufw --force enable | tee -a $LOG_FILE
ufw allow ssh | tee -a $LOG_FILE
ufw allow 80/tcp | tee -a $LOG_FILE
ufw allow 5000/tcp | tee -a $LOG_FILE
ufw allow 5901/tcp | tee -a $LOG_FILE
ufw status | tee -a $LOG_FILE

echo "\n📁 STEP 6: Frontend Upload Instructions" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE
echo "To upload frontend-cloud.zip:" | tee -a $LOG_FILE
echo "1. On your Windows machine, run: python local_file_server.py" | tee -a $LOG_FILE
echo "2. In this VNC terminal, run:" | tee -a $LOG_FILE
echo "   cd /var/www/html" | tee -a $LOG_FILE
echo "   wget http://YOUR_WINDOWS_IP:8000/frontend-cloud.zip" | tee -a $LOG_FILE
echo "   unzip -o frontend-cloud.zip" | tee -a $LOG_FILE
echo "   rm frontend-cloud.zip" | tee -a $LOG_FILE
echo "   chown -R www-data:www-data /var/www/html" | tee -a $LOG_FILE
echo "   systemctl reload nginx" | tee -a $LOG_FILE

echo "\n✅ STEP 7: Final Verification" | tee -a $LOG_FILE
echo "------------------------------" | tee -a $LOG_FILE

echo "Service Status Summary:" | tee -a $LOG_FILE
check_service "vncserver@1" || echo "⚠️  VNC may need manual restart"
check_service "nginx" || echo "⚠️  Nginx needs attention"
check_service "ai-trading-backend" || echo "⚠️  Backend needs attention"

echo "\nPort Status Summary:" | tee -a $LOG_FILE
check_port "5901" "VNC" || echo "⚠️  VNC port not accessible"
check_port "80" "HTTP" || echo "⚠️  Web port not accessible"
check_port "5000" "Flask" || echo "⚠️  Backend port not accessible"

echo "\n🎯 ACTIVATION COMPLETE" | tee -a $LOG_FILE
echo "======================" | tee -a $LOG_FILE
echo "VPS IP: $VPS_IP" | tee -a $LOG_FILE
echo "VNC Access: vnc://$VPS_IP:5901" | tee -a $LOG_FILE
echo "Web Access: http://$VPS_IP" | tee -a $LOG_FILE
echo "API Health: http://$VPS_IP/api/health" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
echo "Log saved to: $LOG_FILE" | tee -a $LOG_FILE

echo "\n🔧 NEXT STEPS:" | tee -a $LOG_FILE
echo "1. Upload frontend files using the instructions above" | tee -a $LOG_FILE
echo "2. Test web access from your browser" | tee -a $LOG_FILE
echo "3. Run deployment verification script from Windows" | tee -a $LOG_FILE

echo "\n📋 Quick Commands:" | tee -a $LOG_FILE
echo "- Check all services: systemctl status vncserver@1 nginx ai-trading-backend" | tee -a $LOG_FILE
echo "- View logs: journalctl -u ai-trading-backend -f" | tee -a $LOG_FILE
echo "- Restart services: systemctl restart vncserver@1 nginx ai-trading-backend" | tee -a $LOG_FILE
echo "- Check ports: netstat -tuln | grep -E ':(80|5000|5901) '" | tee -a $LOG_FILE

echo "\n🚀 VPS ACTIVATION SCRIPT COMPLETED SUCCESSFULLY! 🚀" | tee -a $LOG_FILE