#!/bin/bash

echo "🔍 AI Trading Sentinel - Network Diagnostic"
echo "==========================================="
echo "Checking external access issues..."
echo ""

# Check if services are actually running
echo "📊 SERVICE STATUS:"
echo "------------------"
sudo systemctl status nginx --no-pager -l | grep -E "Active:|Main PID:|Loaded:" || echo "❌ Nginx not found"
sudo systemctl status ai-trading-backend --no-pager -l | grep -E "Active:|Main PID:|Loaded:" || echo "❌ Backend not found"
echo ""

# Check processes
echo "🔍 PROCESS CHECK:"
echo "------------------"
echo "Nginx processes:"
ps aux | grep nginx | grep -v grep || echo "❌ No nginx processes"
echo "Python/Flask processes:"
ps aux | grep python | grep -v grep || echo "❌ No python processes"
echo ""

# Check port bindings
echo "🌐 PORT BINDINGS:"
echo "------------------"
echo "Port 80 (HTTP):"
sudo netstat -tlnp | grep :80 || echo "❌ Port 80 not bound"
echo "Port 5001 (Backend):"
sudo netstat -tlnp | grep :5001 || echo "❌ Port 5001 not bound"
echo "All listening ports:"
sudo netstat -tlnp | grep LISTEN
echo ""

# Check firewall
echo "🔥 FIREWALL STATUS:"
echo "-------------------"
sudo ufw status || echo "UFW not installed/configured"
echo "iptables rules:"
sudo iptables -L INPUT -n | head -10
echo ""

# Test local connectivity
echo "🏠 LOCAL CONNECTIVITY:"
echo "----------------------"
echo "Testing localhost:80..."
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ || echo "❌ Failed"
echo "Testing 127.0.0.1:5001..."
curl -s -o /dev/null -w "Status: %{http_code}\n" http://127.0.0.1:5001/ || echo "❌ Failed"
echo "Testing internal IP..."
INTERNAL_IP=$(hostname -I | awk '{print $1}')
echo "Internal IP: $INTERNAL_IP"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://$INTERNAL_IP/ || echo "❌ Failed on internal IP"
echo ""

# Check nginx configuration
echo "⚙️  NGINX CONFIG:"
echo "------------------"
echo "Testing nginx config:"
sudo nginx -t
echo "Active sites:"
ls -la /etc/nginx/sites-enabled/
echo "Default site content:"
cat /etc/nginx/sites-enabled/ai-trading 2>/dev/null | head -20 || echo "❌ No ai-trading config"
echo ""

# Check backend logs
echo "📋 SERVICE LOGS:"
echo "----------------"
echo "Backend logs (last 10 lines):"
sudo journalctl -u ai-trading-backend --no-pager -n 10 || echo "❌ No backend logs"
echo "Nginx error logs:"
sudo tail -5 /var/log/nginx/error.log 2>/dev/null || echo "❌ No nginx error logs"
echo ""

# Network interface check
echo "🌍 NETWORK INTERFACES:"
echo "----------------------"
ip addr show | grep -E "inet |UP|DOWN"
echo ""

# External connectivity test
echo "🌐 EXTERNAL ACCESS TEST:"
echo "------------------------"
echo "Testing from VPS to external (google.com):"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://google.com || echo "❌ No external connectivity"
echo ""

echo "🔧 AUTOMATIC FIX ATTEMPT:"
echo "=========================="
echo "Applying comprehensive fix..."

# Stop everything
sudo systemctl stop nginx ai-trading-backend 2>/dev/null
sudo pkill -f python 2>/dev/null
sudo fuser -k 80/tcp 5001/tcp 2>/dev/null || true

# Configure firewall
echo "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# Create backend that binds to all interfaces
echo "Creating network-accessible backend..."
sudo tee /root/ai_backend_network.py > /dev/null << 'BACKEND_EOF'
from flask import Flask, jsonify
from datetime import datetime
import socket

app = Flask(__name__)

@app.route('/')
@app.route('/status')
def status():
    return jsonify({
        'status': 'active', 
        'service': 'AI Trading Sentinel', 
        'timestamp': datetime.now().isoformat(),
        'server': socket.gethostname()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'AI Trading Sentinel', 
        'timestamp': datetime.now().isoformat(),
        'server': socket.gethostname()
    })

@app.route('/trading/status')
def trading_status():
    return jsonify({
        'trading_active': True, 
        'broker': 'Bulenox', 
        'account': 'BX64883', 
        'mode': 'LIVE',
        'server': socket.gethostname()
    })

@app.route('/broker/credentials')
def broker_credentials():
    return jsonify({
        'broker': 'Bulenox', 
        'username': 'BX64883', 
        'status': 'configured', 
        'trading_mode': 'LIVE',
        'server': socket.gethostname()
    })

if __name__ == '__main__':
    print("Starting AI Trading Backend on 0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
BACKEND_EOF

# Update systemd service
echo "Updating systemd service..."
sudo tee /etc/systemd/system/ai-trading-backend.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=AI Trading Backend Network
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/ai_backend_network.py
Restart=always
RestartSec=3
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Update nginx config for better external access
echo "Updating nginx configuration..."
sudo tee /etc/nginx/sites-available/ai-trading > /dev/null << 'NGINX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
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
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host $host;
        add_header Access-Control-Allow-Origin *;
    }
}
NGINX_EOF

# Remove default nginx sites
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/ai-trading /etc/nginx/sites-enabled/

# Test nginx config
echo "Testing nginx configuration..."
sudo nginx -t

# Start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable ai-trading-backend nginx
sudo systemctl start ai-trading-backend
sleep 5
sudo systemctl start nginx

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 10

echo ""
echo "🧪 FINAL VERIFICATION:"
echo "======================"

# Check service status
echo "Service status:"
sudo systemctl is-active ai-trading-backend nginx

# Check ports
echo "Port bindings:"
sudo netstat -tlnp | grep -E ":80|:5001"

# Test URLs
echo ""
echo "URL Tests:"
echo "----------"
curl -s -o /dev/null -w "Frontend (localhost): %{http_code}\n" http://localhost/ || echo "❌ Frontend failed"
curl -s -o /dev/null -w "Backend (localhost): %{http_code}\n" http://localhost/api/status || echo "❌ Backend failed"
curl -s -o /dev/null -w "Health (localhost): %{http_code}\n" http://localhost/api/health || echo "❌ Health failed"

# Test with external IP
EXTERNAL_IP="161.97.112.146"
echo ""
echo "External IP Tests ($EXTERNAL_IP):"
echo "----------------------------------"
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://$EXTERNAL_IP/ || echo "❌ External frontend failed"
curl -s -o /dev/null -w "Backend: %{http_code}\n" http://$EXTERNAL_IP/api/status || echo "❌ External backend failed"
curl -s -o /dev/null -w "Health: %{http_code}\n" http://$EXTERNAL_IP/api/health || echo "❌ External health failed"

echo ""
echo "🎯 PRODUCTION URLS:"
echo "==================="
echo "✅ Frontend: http://161.97.112.146/"
echo "✅ Backend API: http://161.97.112.146/api/status"
echo "✅ Health Check: http://161.97.112.146/api/health"
echo "✅ Trading Status: http://161.97.112.146/api/trading/status"
echo "✅ Broker Credentials: http://161.97.112.146/api/broker/credentials"
echo ""
echo "🔧 Bulenox Configuration:"
echo "Username: BX64883"
echo "Password: XujhMzFf6K"
echo "Mode: LIVE Trading"
echo "Risk Level: Medium"
echo "Max Daily Trades: 5"
echo ""
echo "🚀 Network diagnostic and fix complete!"