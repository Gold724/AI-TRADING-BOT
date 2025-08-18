# =============================================================================
# VNC Frontend Deployment Script for AI Trading Sentinel (Windows)
# Automates: VNC connection, frontend upload, Nginx config, web testing
# Target: Contabo VPS 161.97.112.146
# =============================================================================

$VPS_IP = "161.97.112.146"
$VNC_PORT = "5901"
$WEB_PORT = "80"
$FRONTEND_ZIP = "frontend-cloud.zip"
$WEB_ROOT = "/var/www/html"

Write-Host "🚀 AI Trading Sentinel - VNC Frontend Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host "VPS Target: $VPS_IP" -ForegroundColor Yellow
Write-Host "VNC Access: $VPS_IP`:$VNC_PORT" -ForegroundColor Yellow
Write-Host "Web Access: http://$VPS_IP" -ForegroundColor Yellow
Write-Host ""

# Check if frontend-cloud.zip exists
if (-not (Test-Path $FRONTEND_ZIP)) {
    Write-Host "❌ Error: $FRONTEND_ZIP not found in current directory!" -ForegroundColor Red
    Write-Host "Please ensure frontend-cloud.zip is in: $(Get-Location)" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found $FRONTEND_ZIP ($(Get-Item $FRONTEND_ZIP | Select-Object -ExpandProperty Length) bytes)" -ForegroundColor Green
Write-Host ""

# Step 1: VNC Connection Instructions
Write-Host "📡 STEP 1: VNC Connection Setup" -ForegroundColor Cyan
Write-Host "------------------------------" -ForegroundColor Cyan
Write-Host "1. Download VNC Viewer from: https://www.realvnc.com/en/connect/download/viewer/" -ForegroundColor White
Write-Host "2. Install and launch VNC Viewer" -ForegroundColor White
Write-Host "3. Connect to: $VPS_IP`:$VNC_PORT" -ForegroundColor Yellow
Write-Host "4. Enter VNC password when prompted" -ForegroundColor White
Write-Host "5. You should see XFCE4 desktop environment" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Quick Connect: vnc://$VPS_IP`:$VNC_PORT" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Manual Action Required: Connect via VNC Viewer before proceeding" -ForegroundColor Red
Read-Host "Press ENTER when VNC connection is established"

# Step 2: Frontend Upload Instructions
Write-Host "📦 STEP 2: Frontend Upload via VNC" -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan
Write-Host "In your VNC session, open a terminal and execute:" -ForegroundColor White
Write-Host ""

$uploadCommands = @'
# Navigate to web root and clean up
sudo mkdir -p /var/www/html
cd /var/www/html
sudo rm -rf *

# Method 1: Upload via file manager (Recommended)
# - Open file manager in VNC
# - Navigate to a temp directory (e.g., /tmp)
# - Upload frontend-cloud.zip using VNC file transfer
# - Then move it: sudo mv /tmp/frontend-cloud.zip /var/www/html/

# Method 2: If you have HTTP server running locally
# python3 -m http.server 8000  # Run this on your Windows machine
# wget http://YOUR_LOCAL_IP:8000/frontend-cloud.zip

# Extract and configure
sudo unzip frontend-cloud.zip
sudo rm frontend-cloud.zip
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Verify extraction
ls -la /var/www/html
'@

Write-Host $uploadCommands -ForegroundColor Gray
Write-Host ""
Write-Host "💡 TIP: You can copy-paste these commands directly into VNC terminal" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Manual Action Required: Execute above commands in VNC terminal" -ForegroundColor Red
Read-Host "Press ENTER when frontend upload is complete"

# Step 3: Nginx Configuration
Write-Host "🔧 STEP 3: Nginx Configuration" -ForegroundColor Cyan
Write-Host "------------------------------" -ForegroundColor Cyan
Write-Host "Execute this complete Nginx setup in VNC terminal:" -ForegroundColor White
Write-Host ""

$nginxCommands = @'
# Create comprehensive Nginx configuration
sudo tee /etc/nginx/sites-available/trading-frontend << 'NGINX_EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    root /var/www/html;
    index index.html index.htm;

    # Frontend static files with SPA support
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # API proxy to Flask backend (port 5000)
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support for real-time trading updates
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Security headers for production
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Performance optimization
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Static file caching (except for API)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# Enable the trading frontend site
sudo ln -sf /etc/nginx/sites-available/trading-frontend /etc/nginx/sites-enabled/

# Remove default Nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration syntax
sudo nginx -t

# Restart and enable Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Verify Nginx is running
sudo systemctl status nginx --no-pager
'@

Write-Host $nginxCommands -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Manual Action Required: Execute above Nginx commands in VNC terminal" -ForegroundColor Red
Read-Host "Press ENTER when Nginx configuration is complete"

# Step 4: Web Access Testing
Write-Host "🌐 STEP 4: Web Access Testing" -ForegroundColor Cyan
Write-Host "-----------------------------" -ForegroundColor Cyan
Write-Host "Testing web access from Windows machine..." -ForegroundColor White
Write-Host ""

# Test web access from Windows
try {
    Write-Host "Testing HTTP connection to http://$VPS_IP..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "http://$VPS_IP" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✅ HTTP Status: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
    Write-Host "✅ Content Length: $($response.Content.Length) bytes" -ForegroundColor Green
    
    if ($response.Content -match "Trading|Dashboard|AI|Sentinel") {
        Write-Host "✅ Frontend content detected!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Frontend content not detected in response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ HTTP connection failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check VNC terminal for Nginx errors" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Additional tests to run in VNC terminal:" -ForegroundColor White

$testCommands = @'
# Test local access on VPS
curl -I http://localhost
curl -I http://161.97.112.146

# Check frontend content
curl -s http://localhost | head -20

# Test API endpoint (if backend is running)
curl -I http://localhost/api/health

# Check Nginx logs for errors
sudo tail -10 /var/log/nginx/error.log
sudo tail -10 /var/log/nginx/access.log

# Verify file permissions
ls -la /var/www/html/
'@

Write-Host $testCommands -ForegroundColor Gray
Write-Host ""

# Final verification
Write-Host "🎯 DEPLOYMENT VERIFICATION CHECKLIST" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host "1. ✅ VNC Server: Running on $VPS_IP`:$VNC_PORT" -ForegroundColor White
Write-Host "2. 🔄 Frontend Upload: Manual verification required" -ForegroundColor Yellow
Write-Host "3. 🔄 Nginx Config: Manual verification required" -ForegroundColor Yellow
Write-Host "4. 🔄 Web Access: Test at http://$VPS_IP" -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 GLOBAL ACCESS POINTS" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host "🎮 Trading Dashboard: http://$VPS_IP" -ForegroundColor Cyan
Write-Host "🔧 VNC Management: $VPS_IP`:$VNC_PORT" -ForegroundColor Cyan
Write-Host "🔌 Backend API: http://$VPS_IP/api/" -ForegroundColor Cyan
Write-Host "📡 WebSocket: ws://$VPS_IP/ws" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔒 SECURITY RECOMMENDATIONS" -ForegroundColor Yellow
Write-Host "===========================" -ForegroundColor Yellow
Write-Host "• Set up HTTPS with Let's Encrypt for production" -ForegroundColor White
Write-Host "• Configure firewall rules for specific ports only" -ForegroundColor White
Write-Host "• Use strong VNC passwords and consider SSH tunneling" -ForegroundColor White
Write-Host "• Monitor access logs regularly" -ForegroundColor White
Write-Host ""
Write-Host "🎉 AI Trading Sentinel VNC Deployment Guide Complete!" -ForegroundColor Green
Write-Host "Ready for 24/7 global trading operations! 🚀" -ForegroundColor Green

# Open browser to test
$openBrowser = Read-Host "Would you like to open http://$VPS_IP in your browser now? (y/n)"
if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
    Start-Process "http://$VPS_IP"
}

Write-Host "Deployment script completed! 🎯" -ForegroundColor Green