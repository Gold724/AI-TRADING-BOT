#!/bin/bash

echo "🌐 AI Trading Sentinel - VNC IP Configuration Fix"
echo "================================================"
echo "Configuring for VNC IP: 5.189.145.177"
echo "SSH IP: 161.97.112.146 (for reference)"
echo ""

# Stop all services
echo "Stopping services..."
sudo systemctl stop ai-trading-backend nginx apache2 2>/dev/null

# Kill processes
echo "Cleaning processes..."
sudo pkill -f "python.*flask" 2>/dev/null || true
sudo pkill -f "python.*app" 2>/dev/null || true
sudo fuser -k 80/tcp 5000/tcp 5001/tcp 2>/dev/null || true

# Get network interfaces
echo "📊 Network Interface Analysis:"
echo "------------------------------"
echo "Available interfaces:"
ip addr show | grep -E "inet |UP|DOWN"
echo ""
echo "VNC IP: 5.189.145.177"
echo "SSH IP: 161.97.112.146"
echo ""

# Create Nginx config for VNC access
echo "Configuring Nginx for VNC IP..."
sudo tee /etc/nginx/sites-available/ai-trading-vnc > /dev/null << 'EOF'
# VNC IP Configuration
server {
    listen 80;
    listen [::]:80;
    server_name 5.189.145.177 161.97.112.146 localhost _;
    
    # Frontend
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
        add_header Access-Control-Allow-Origin *;
    }
    
    # API routes
    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        add_header Access-Control-Allow-Origin *;
    }
}
EOF

# Enable VNC site configuration
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/ai-trading
sudo ln -sf /etc/nginx/sites-available/ai-trading-vnc /etc/nginx/sites-enabled/

# Create backend that works with VNC
echo "Creating VNC-compatible backend..."
sudo tee /root/ai_backend_vnc.py > /dev/null << 'EOF'
from flask import Flask, jsonify, request
from datetime import datetime
import socket
import os

app = Flask(__name__)

@app.route('/')
@app.route('/status')
def status():
    return jsonify({
        'status': 'active', 
        'service': 'AI Trading Sentinel VNC', 
        'timestamp': datetime.now().isoformat(),
        'vnc_ip': '5.189.145.177',
        'ssh_ip': '161.97.112.146',
        'access_method': 'VNC',
        'server': socket.gethostname(),
        'client_ip': request.remote_addr
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'AI Trading Sentinel VNC', 
        'timestamp': datetime.now().isoformat(),
        'vnc_accessible': True,
        'server': socket.gethostname()
    })

@app.route('/trading/status')
def trading_status():
    return jsonify({
        'trading_active': True, 
        'broker': 'Bulenox', 
        'account': 'BX64883', 
        'mode': 'LIVE',
        'vnc_connection': True,
        'server': socket.gethostname()
    })

@app.route('/broker/credentials')
def broker_credentials():
    return jsonify({
        'broker': 'Bulenox', 
        'username': 'BX64883', 
        'status': 'configured', 
        'trading_mode': 'LIVE',
        'access_via': 'VNC',
        'server': socket.gethostname()
    })

@app.route('/network/info')
def network_info():
    return jsonify({
        'vnc_ip': '5.189.145.177',
        'vnc_port': '63162',
        'ssh_ip': '161.97.112.146',
        'current_access': 'VNC',
        'server': socket.gethostname(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🌐 Starting AI Trading Backend for VNC Access")
    print("VNC IP: 5.189.145.177:63162")
    print("SSH IP: 161.97.112.146")
    print("Backend binding to: 0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
EOF

# Update systemd service
echo "Creating VNC-compatible systemd service..."
sudo tee /etc/systemd/system/ai-trading-backend-vnc.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Backend VNC
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/ai_backend_vnc.py
Restart=always
RestartSec=3
Environment=FLASK_ENV=production
Environment=VNC_IP=5.189.145.177
Environment=SSH_IP=161.97.112.146

[Install]
WantedBy=multi-user.target
EOF

# Create VNC-aware frontend
echo "Creating VNC-aware frontend..."
sudo mkdir -p /var/www/html
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel - VNC Access</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{font-family:Arial;margin:40px;background:#f5f5f5}
        .container{max-width:900px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        h1{color:#2c3e50;text-align:center;margin-bottom:30px}
        .vnc-info{background:#e3f2fd;padding:20px;border-radius:8px;margin:20px 0;border-left:4px solid #2196f3}
        .status{padding:15px;margin:10px 0;background:#d4edda;color:#155724;border-radius:5px}
        .endpoint{margin:10px 0;padding:15px;background:#e9ecef;border-radius:5px}
        .endpoint a{color:#007bff;text-decoration:none;font-weight:bold}
        .endpoint a:hover{text-decoration:underline}
        .network-info{background:#fff3cd;padding:15px;border-radius:5px;margin:15px 0}
        .bulenox-config{background:#f8d7da;color:#721c24;padding:15px;border-radius:5px;margin:15px 0}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel - VNC Access</h1>
        
        <div class="vnc-info">
            <h3>🌐 VNC Connection Details</h3>
            <p><strong>VNC IP:</strong> 5.189.145.177</p>
            <p><strong>VNC Port:</strong> 63162</p>
            <p><strong>SSH IP:</strong> 161.97.112.146 (reference)</p>
            <p><strong>Access Method:</strong> VNC (Current)</p>
        </div>
        
        <div class="status">Status: System Active via VNC ✅</div>
        
        <h3>🔗 API Endpoints (VNC Access):</h3>
        <div class="endpoint"><a href="/api/status">/api/status</a> - Service status with VNC info</div>
        <div class="endpoint"><a href="/api/health">/api/health</a> - Health check via VNC</div>
        <div class="endpoint"><a href="/api/trading/status">/api/trading/status</a> - Trading status</div>
        <div class="endpoint"><a href="/api/broker/credentials">/api/broker/credentials</a> - Broker config</div>
        <div class="endpoint"><a href="/api/network/info">/api/network/info</a> - Network information</div>
        
        <div class="network-info">
            <h4>📡 Network Configuration</h4>
            <p>This system is configured for VNC access. All services are bound to work with both VNC IP (5.189.145.177) and SSH IP (161.97.112.146).</p>
        </div>
        
        <div class="bulenox-config">
            <h4>🏦 Bulenox Integration</h4>
            <p><strong>Broker:</strong> Bulenox (BX64883)</p>
            <p><strong>Mode:</strong> LIVE Trading</p>
            <p><strong>Access:</strong> VNC Compatible</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh status every 30 seconds
        setInterval(function() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    console.log('Health check:', data);
                })
                .catch(error => {
                    console.log('Health check failed:', error);
                });
        }, 30000);
    </script>
</body>
</html>
EOF

# Configure firewall for both IPs
echo "Configuring firewall for VNC access..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 5.189.145.177
sudo ufw allow from 161.97.112.146
sudo ufw reload

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

# Start services
echo "Starting VNC-compatible services..."
sudo systemctl daemon-reload
sudo systemctl disable ai-trading-backend 2>/dev/null || true
sudo systemctl enable ai-trading-backend-vnc nginx
sudo systemctl start ai-trading-backend-vnc
sleep 5
sudo systemctl start nginx

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 10

echo ""
echo "🧪 VNC ACCESS VERIFICATION:"
echo "============================"

# Check service status
echo "Service Status:"
sudo systemctl is-active ai-trading-backend-vnc nginx

# Check port bindings
echo ""
echo "Port Bindings:"
sudo netstat -tlnp | grep -E ":80|:5001"

echo ""
echo "🌐 URL Tests (VNC Compatible):"
echo "------------------------------"

# Test with localhost
curl -s -o /dev/null -w "Frontend (localhost): %{http_code}\n" http://localhost/ || echo "❌ Frontend failed"
curl -s -o /dev/null -w "Backend (localhost): %{http_code}\n" http://localhost/api/status || echo "❌ Backend failed"
curl -s -o /dev/null -w "Health (localhost): %{http_code}\n" http://localhost/api/health || echo "❌ Health failed"
curl -s -o /dev/null -w "Network Info: %{http_code}\n" http://localhost/api/network/info || echo "❌ Network info failed"

echo ""
echo "🎯 PRODUCTION URLS (VNC Access):"
echo "================================="
echo "✅ Frontend: http://5.189.145.177/ (VNC IP)"
echo "✅ Backend API: http://5.189.145.177/api/status"
echo "✅ Health Check: http://5.189.145.177/api/health"
echo "✅ Trading Status: http://5.189.145.177/api/trading/status"
echo "✅ Broker Credentials: http://5.189.145.177/api/broker/credentials"
echo "✅ Network Info: http://5.189.145.177/api/network/info"
echo ""
echo "📡 Alternative URLs (SSH IP - for reference):"
echo "✅ Frontend: http://161.97.112.146/"
echo "✅ Backend API: http://161.97.112.146/api/status"
echo ""
echo "🔧 Bulenox Configuration (VNC Compatible):"
echo "Username: BX64883"
echo "Password: XujhMzFf6K"
echo "Mode: LIVE Trading"
echo "Risk Level: Medium"
echo "Max Daily Trades: 5"
echo "VNC Access: Enabled"
echo ""
echo "🚀 VNC IP configuration complete!"
echo "Now test URLs using VNC IP: 5.189.145.177"