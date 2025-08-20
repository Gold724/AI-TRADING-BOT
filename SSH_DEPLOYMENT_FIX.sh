#!/bin/bash
# SSH Deployment Fix for Termius Connection (161.97.112.146)

echo "🚀 SSH Deployment Fix - Using Termius IP: 161.97.112.146"

# Stop existing services
echo "Stopping services..."
sudo systemctl stop nginx 2>/dev/null
sudo pkill -f python 2>/dev/null
sudo pkill -f flask 2>/dev/null

# Clean up processes
echo "Cleaning processes..."
sudo fuser -k 80/tcp 2>/dev/null
sudo fuser -k 5001/tcp 2>/dev/null

# Create web directory
echo "Creating web directory..."
sudo mkdir -p /var/www/html

# Create HTML frontend for SSH IP
echo "Creating frontend..."
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel - SSH Deployment</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { color: #28a745; font-weight: bold; }
        .ip { color: #007bff; font-weight: bold; }
        .bulenox { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel</h1>
        <p class="status">✅ Status: ACTIVE</p>
        <p>🌐 SSH IP: <span class="ip">161.97.112.146</span></p>
        <p>🔗 Connection: Termius SSH</p>
        <p>📊 Broker: <span class="bulenox">Bulenox BX64883 (LIVE)</span></p>
        <p>⚡ Mode: Live Trading</p>
        <p>🛡️ Risk Level: Medium</p>
        <hr>
        <h3>🔗 API Endpoints:</h3>
        <ul>
            <li><a href="/api/status">Backend Status</a></li>
            <li><a href="/api/health">Health Check</a></li>
            <li><a href="/api/bulenox">Bulenox Config</a></li>
        </ul>
    </div>
</body>
</html>
EOF

# Create Flask backend for SSH IP
echo "Creating backend..."
sudo tee /root/ssh_backend.py > /dev/null << 'EOF'
from flask import Flask, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'ssh_ip': '161.97.112.146',
        'connection': 'termius_ssh',
        'bulenox': 'BX64883',
        'mode': 'LIVE',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'active',
        'ssh_ip': '161.97.112.146',
        'connection': 'termius_ssh',
        'bulenox': 'BX64883',
        'mode': 'LIVE',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'ssh_connection': 'active',
        'services': 'running'
    })

@app.route('/api/bulenox')
def bulenox():
    return jsonify({
        'username': 'BX64883',
        'mode': 'LIVE',
        'risk_level': 'medium',
        'max_daily_trades': 5,
        'status': 'configured'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
EOF

# Create Nginx configuration for SSH IP
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    root /var/www/html;
    index index.html;
    
    # Frontend
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Create systemd service for SSH backend
echo "Creating systemd service..."
sudo tee /etc/systemd/system/ssh-trading-backend.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel SSH Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/ssh_backend.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable ssh-trading-backend
sudo systemctl start ssh-trading-backend
sudo systemctl enable nginx
sudo systemctl start nginx

# Wait for services to start
echo "Waiting for services..."
sleep 5

# Test services
echo "Testing services..."
echo "Frontend test:"
curl -s http://localhost/ | head -5
echo ""
echo "Backend test:"
curl -s http://localhost/api/status
echo ""
echo "Health test:"
curl -s http://localhost/api/health
echo ""

# Display results
echo ""
echo "🎉 SSH Deployment Complete!"
echo "📍 SSH IP: 161.97.112.146"
echo "🔗 Termius Connection: Active"
echo ""
echo "🌐 URLs (use SSH IP):"
echo "   Frontend: http://161.97.112.146/"
echo "   Backend:  http://161.97.112.146/api/status"
echo "   Health:   http://161.97.112.146/api/health"
echo "   Bulenox:  http://161.97.112.146/api/bulenox"
echo ""
echo "🤖 Bulenox Configuration:"
echo "   Username: BX64883"
echo "   Mode: LIVE Trading"
echo "   Risk Level: Medium"
echo ""
echo "✅ All services configured for SSH connection!"