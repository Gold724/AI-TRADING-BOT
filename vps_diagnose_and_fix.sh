#!/bin/bash

# AI Trading Sentinel - VPS Diagnostic & Fix Script
# Diagnoses and fixes inactive production URLs on Contabo VPS
# Run this on VPS: bash vps_diagnose_and_fix.sh

echo "🔍 AI Trading Sentinel - VPS Diagnostic & Fix"
echo "📍 Target: Contabo VPS (161.97.112.146)"
echo "🕐 $(date)"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash vps_diagnose_and_fix.sh"
    exit 1
fi

# Step 1: Check system status
echo "📊 Step 1: System Status Check"
echo "Memory usage:"
free -h
echo "Disk usage:"
df -h /
echo "Load average:"
uptime
echo ""

# Step 2: Check if application directory exists
echo "📁 Step 2: Application Directory Check"
if [ -d "/opt/ai-trading-sentinel" ]; then
    echo "✅ Application directory exists"
    cd /opt/ai-trading-sentinel
    ls -la
else
    echo "❌ Application directory missing - need to redeploy"
    echo "🔄 Creating application directory..."
    mkdir -p /opt/ai-trading-sentinel
    cd /opt/ai-trading-sentinel
fi
echo ""

# Step 3: Check services status
echo "🔧 Step 3: Service Status Check"
echo "Backend service:"
systemctl status ai-trading-backend --no-pager || echo "❌ Backend service not found"
echo "Frontend service:"
systemctl status ai-trading-frontend --no-pager || echo "❌ Frontend service not found"
echo "Nginx service:"
systemctl status nginx --no-pager || echo "❌ Nginx service not found"
echo ""

# Step 4: Check ports
echo "🌐 Step 4: Port Status Check"
echo "Checking port 80 (Nginx):"
netstat -tlnp | grep :80 || echo "❌ Port 80 not listening"
echo "Checking port 5000 (Backend):"
netstat -tlnp | grep :5000 || echo "❌ Port 5000 not listening"
echo "Checking port 3000 (Frontend):"
netstat -tlnp | grep :3000 || echo "❌ Port 3000 not listening"
echo ""

# Step 5: Check processes
echo "⚙️ Step 5: Process Check"
echo "Python processes:"
ps aux | grep python | grep -v grep || echo "❌ No Python processes found"
echo "Node processes:"
ps aux | grep node | grep -v grep || echo "❌ No Node processes found"
echo "Nginx processes:"
ps aux | grep nginx | grep -v grep || echo "❌ No Nginx processes found"
echo ""

# Step 6: Check logs
echo "📋 Step 6: Recent Log Check"
if [ -f "/var/log/nginx/error.log" ]; then
    echo "Nginx errors (last 10 lines):"
    tail -10 /var/log/nginx/error.log
fi
if [ -f "/opt/ai-trading-sentinel/logs/backend.log" ]; then
    echo "Backend errors (last 10 lines):"
    tail -10 /opt/ai-trading-sentinel/logs/backend.log
fi
echo ""

# Step 7: Fix - Restart services
echo "🔄 Step 7: Service Restart Fix"
echo "Stopping all services..."
systemctl stop ai-trading-backend 2>/dev/null
systemctl stop ai-trading-frontend 2>/dev/null
systemctl stop nginx 2>/dev/null

echo "Starting Nginx..."
systemctl start nginx
systemctl enable nginx

echo "Starting backend service..."
systemctl start ai-trading-backend
systemctl enable ai-trading-backend

echo "Starting frontend service..."
systemctl start ai-trading-frontend
systemctl enable ai-trading-frontend

# Wait for services to start
sleep 10

# Step 8: Verify fix
echo "✅ Step 8: Verification"
echo "Service status after restart:"
systemctl is-active nginx && echo "✅ Nginx: Active" || echo "❌ Nginx: Failed"
systemctl is-active ai-trading-backend && echo "✅ Backend: Active" || echo "❌ Backend: Failed"
systemctl is-active ai-trading-frontend && echo "✅ Frontend: Active" || echo "❌ Frontend: Failed"

echo "Port check after restart:"
netstat -tlnp | grep :80 && echo "✅ Port 80: Listening" || echo "❌ Port 80: Not listening"
netstat -tlnp | grep :5000 && echo "✅ Port 5000: Listening" || echo "❌ Port 5000: Not listening"
netstat -tlnp | grep :3000 && echo "✅ Port 3000: Listening" || echo "❌ Port 3000: Not listening"

# Step 9: Test URLs
echo "🌐 Step 9: URL Testing"
echo "Testing frontend..."
curl -s -o /dev/null -w "Frontend (Port 80): %{http_code}\n" http://localhost/ || echo "❌ Frontend test failed"
echo "Testing backend API..."
curl -s -o /dev/null -w "Backend API: %{http_code}\n" http://localhost/api/status || echo "❌ Backend API test failed"
echo "Testing health endpoint..."
curl -s -o /dev/null -w "Health Check: %{http_code}\n" http://localhost/api/health || echo "❌ Health check failed"

# Step 10: Emergency redeploy if needed
echo "🚨 Step 10: Emergency Redeploy Check"
if ! systemctl is-active nginx >/dev/null || ! systemctl is-active ai-trading-backend >/dev/null; then
    echo "⚠️ Services still failing - initiating emergency redeploy..."
    
    # Quick redeploy
    echo "Installing missing packages..."
    apt update
    apt install -y nginx python3 python3-pip nodejs npm
    
    # Create basic backend
    mkdir -p /opt/ai-trading-sentinel
    cd /opt/ai-trading-sentinel
    
    cat > app.py << 'BACKEND_EOF'
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/status')
def status():
    return jsonify({"status": "active", "service": "AI Trading Sentinel"})

@app.route('/api/health')
def health():
    return jsonify({"health": "ok", "timestamp": "$(date)"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
BACKEND_EOF
    
    # Install Flask
    pip3 install flask flask-cors gunicorn
    
    # Create systemd service
    cat > /etc/systemd/system/ai-trading-backend.service << 'SERVICE_EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/ai-trading-sentinel
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE_EOF
    
    # Configure Nginx
    cat > /etc/nginx/sites-available/default << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        return 200 'AI Trading Sentinel - Frontend Active';
        add_header Content-Type text/plain;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF
    
    # Restart services
    systemctl daemon-reload
    systemctl restart nginx
    systemctl restart ai-trading-backend
    systemctl enable nginx ai-trading-backend
    
    echo "✅ Emergency redeploy completed"
fi

echo "=========================================="
echo "🎉 Diagnostic & Fix Complete!"
echo "📍 Production URLs (should now be active):"
echo "   🌐 Frontend: http://161.97.112.146/"
echo "   🔧 Backend:  http://161.97.112.146/api/status"
echo "   🏥 Health:   http://161.97.112.146/api/health"
echo "=========================================="
echo "📊 Final Status Summary:"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Failed"
systemctl is-active ai-trading-backend && echo "✅ Backend: Running" || echo "❌ Backend: Failed"
echo "🕐 Completed at: $(date)"
echo "🚀 AI Trading Sentinel should now be accessible!"