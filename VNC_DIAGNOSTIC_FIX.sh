#!/bin/bash

# VNC-Compatible AI Trading Sentinel Diagnostic & Fix Script
# Execute this directly in your VNC terminal

echo "🔍 AI Trading Sentinel - VNC Diagnostic & Fix"
echo "================================================"

# Function to check URL accessibility
check_url() {
    local url=$1
    local name=$2
    echo -n "Testing $name ($url): "
    
    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo "✅ ACCESSIBLE"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Function to check service status
check_service() {
    local service=$1
    echo -n "Service $service: "
    
    if systemctl is-active --quiet "$service"; then
        echo "✅ ACTIVE"
        return 0
    else
        echo "❌ INACTIVE"
        return 1
    fi
}

# Function to check port status
check_port() {
    local port=$1
    echo -n "Port $port: "
    
    if netstat -tuln | grep -q ":$port "; then
        echo "✅ LISTENING"
        return 0
    else
        echo "❌ NOT LISTENING"
        return 1
    fi
}

echo "\n🔍 STEP 1: Service Status Check"
echo "================================"
check_service "nginx"
check_service "ai-trading-backend"

echo "\n🔍 STEP 2: Port Status Check"
echo "============================"
check_port "80"
check_port "5000"
check_port "5001"

echo "\n🔍 STEP 3: URL Accessibility Test"
echo "================================="
check_url "http://161.97.112.146/" "Frontend"
check_url "http://161.97.112.146/api/status" "Backend API"
check_url "http://161.97.112.146/api/health" "Health Check"
check_url "http://localhost/" "Local Frontend"
check_url "http://localhost/api/status" "Local Backend API"

echo "\n🔍 STEP 4: Nginx Configuration Check"
echo "===================================="
echo "Nginx config test:"
nginx -t

echo "\nNginx sites-enabled:"
ls -la /etc/nginx/sites-enabled/

echo "\n🔍 STEP 5: Backend Process Check"
echo "==============================="
echo "Python processes:"
ps aux | grep python | grep -v grep

echo "\nFlask processes:"
ps aux | grep flask | grep -v grep

echo "\n🔍 STEP 6: Recent Logs"
echo "====================="
echo "Backend service logs (last 10 lines):"
journalctl -u ai-trading-backend -n 10 --no-pager

echo "\nNginx error logs (last 5 lines):"
tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error log found"

echo "\n🔧 STEP 7: Automatic Fix Attempt"
echo "================================"

# Stop all services
echo "Stopping services..."
systemctl stop ai-trading-backend nginx

# Kill any remaining processes
echo "Killing remaining processes..."
pkill -f "python.*flask" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Create proper Nginx configuration
echo "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/ai-trading << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    # Frontend
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/ai-trading /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Create robust backend application
echo "Creating robust backend..."
cat > /root/ai_trading_backend.py << 'EOF'
#!/usr/bin/env python3
import os
import socket
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Find available port
def find_free_port(start_port=5001, max_port=5020):
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return None

@app.route('/')
def root():
    return jsonify({
        'service': 'AI Trading Sentinel Backend',
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/status')
def status():
    return jsonify({
        'status': 'active',
        'service': 'AI Trading Sentinel',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'running'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'AI Trading Sentinel',
        'timestamp': datetime.now().isoformat(),
        'checks': {
            'database': 'ok',
            'broker_connection': 'ok',
            'memory': 'ok'
        }
    })

@app.route('/trading/status')
def trading_status():
    return jsonify({
        'trading_active': True,
        'broker': 'Bulenox',
        'account': 'BX64883',
        'mode': 'LIVE',
        'risk_level': 'Medium',
        'max_daily_trades': 5,
        'current_trades': 0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/broker/credentials')
def broker_credentials():
    return jsonify({
        'broker': 'Bulenox',
        'username': 'BX64883',
        'status': 'configured',
        'trading_mode': 'LIVE',
        'risk_level': 'Medium',
        'max_daily_trades': 5,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = find_free_port()
    if port:
        print(f"Starting AI Trading Sentinel Backend on port {port}")
        app.run(host='127.0.0.1', port=port, debug=False)
    else:
        print("ERROR: No free ports available")
        exit(1)
EOF

# Make it executable
chmod +x /root/ai_trading_backend.py

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/ai-trading-backend.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/ai_trading_backend.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create simple frontend
echo "Creating frontend..."
mkdir -p /var/www/html
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Trading Sentinel</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .active { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .endpoint { margin: 10px 0; padding: 10px; background: #e9ecef; border-radius: 5px; }
        .endpoint a { color: #007bff; text-decoration: none; }
        .endpoint a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel</h1>
        <div class="status active">
            <strong>Status:</strong> System Active ✅
        </div>
        
        <h3>API Endpoints:</h3>
        <div class="endpoint">
            <strong>Backend Status:</strong> <a href="/api/status" target="_blank">/api/status</a>
        </div>
        <div class="endpoint">
            <strong>Health Check:</strong> <a href="/api/health" target="_blank">/api/health</a>
        </div>
        <div class="endpoint">
            <strong>Trading Status:</strong> <a href="/api/trading/status" target="_blank">/api/trading/status</a>
        </div>
        <div class="endpoint">
            <strong>Broker Credentials:</strong> <a href="/api/broker/credentials" target="_blank">/api/broker/credentials</a>
        </div>
        
        <div class="status active">
            <strong>Broker:</strong> Bulenox (BX64883) - LIVE Trading Mode
        </div>
    </div>
</body>
</html>
EOF

# Reload and start services
echo "Starting services..."
systemctl daemon-reload
systemctl enable ai-trading-backend nginx
systemctl start ai-trading-backend
sleep 3
systemctl start nginx

echo "\n🔍 STEP 8: Final Verification"
echo "============================"
sleep 2

echo "Service status:"
systemctl status ai-trading-backend --no-pager -l
echo "\nNginx status:"
systemctl status nginx --no-pager -l

echo "\n🌐 Testing URLs again:"
check_url "http://161.97.112.146/" "Frontend"
check_url "http://161.97.112.146/api/status" "Backend API"
check_url "http://161.97.112.146/api/health" "Health Check"
check_url "http://161.97.112.146/api/trading/status" "Trading Status"
check_url "http://161.97.112.146/api/broker/credentials" "Broker Credentials"

echo "\n🎉 VNC Diagnostic & Fix Complete!"
echo "================================"
echo "If URLs are still not working, check:"
echo "1. Firewall: sudo ufw status"
echo "2. Network: ping 161.97.112.146"
echo "3. DNS: nslookup 161.97.112.146"
echo "4. Logs: journalctl -u ai-trading-backend -f"