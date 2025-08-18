# 🚀 AI Trading Sentinel - Complete Cloud Deployment Script
# This script implements the full frontend cloud deployment process

Write-Host "🌐 AI Trading Sentinel - Cloud Deployment Executor" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Configuration
$VPS_IP = "161.97.112.146"
$VPS_USER = "root"
$FRONTEND_BUILD_PATH = "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend\dist"
$DEPLOYMENT_PACKAGE = "frontend-deployment.tar.gz"

# Step 1: Verify Frontend Build
Write-Host "\n📦 Step 1: Verifying Frontend Build..." -ForegroundColor Yellow
if (-not (Test-Path $FRONTEND_BUILD_PATH)) {
    Write-Host "❌ Frontend build not found. Building now..." -ForegroundColor Red
    Set-Location "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed!" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ Frontend build verified" -ForegroundColor Green

# Step 2: Create Deployment Package
Write-Host "\n📦 Step 2: Creating Deployment Package..." -ForegroundColor Yellow
Set-Location "C:\Users\Admin\Downloads\ai-trading-sentinel\frontend"
if (Test-Path $DEPLOYMENT_PACKAGE) {
    Remove-Item $DEPLOYMENT_PACKAGE -Force
}

# Create tar.gz package (requires tar on Windows 10+)
try {
    tar -czf $DEPLOYMENT_PACKAGE -C dist .
    Write-Host "✅ Deployment package created: $DEPLOYMENT_PACKAGE" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create deployment package" -ForegroundColor Red
    exit 1
}

# Step 3: Upload to VPS
Write-Host "\n🚀 Step 3: Uploading Frontend to VPS..." -ForegroundColor Yellow
Write-Host "Uploading to: $VPS_USER@$VPS_IP" -ForegroundColor Cyan

# Upload deployment package
scp $DEPLOYMENT_PACKAGE "$VPS_USER@$VPS_IP":/tmp/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upload deployment package" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Frontend package uploaded successfully" -ForegroundColor Green

# Step 4: Deploy on VPS
Write-Host "\n⚙️ Step 4: Configuring VPS Deployment..." -ForegroundColor Yellow

$DEPLOYMENT_SCRIPT = @'
#!/bin/bash
set -e

echo "🔧 Installing Nginx..."
sudo apt update
sudo apt install -y nginx

echo "📁 Setting up web directory..."
sudo mkdir -p /var/www/trae-frontend
sudo chown -R www-data:www-data /var/www/trae-frontend

echo "📦 Extracting frontend..."
cd /var/www/trae-frontend
sudo tar -xzf /tmp/frontend-deployment.tar.gz
sudo chown -R www-data:www-data /var/www/trae-frontend

echo "⚙️ Configuring Nginx..."
sudo tee /etc/nginx/sites-available/trae-frontend > /dev/null << EOF
server {
    listen 80;
    server_name $VPS_IP;
    root /var/www/trae-frontend;
    index index.html;

    # Frontend static files
    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket proxy for real-time updates
    location /ws {
        proxy_pass http://127.0.0.1:5000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host \$host;
        access_log off;
    }
}
EOF

echo "🔗 Enabling site..."
sudo ln -sf /etc/nginx/sites-available/trae-frontend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "🧪 Testing Nginx configuration..."
sudo nginx -t

echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "🔥 Configuring firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

echo "🧹 Cleaning up..."
rm -f /tmp/frontend-deployment.tar.gz

echo "✅ Frontend deployment completed!"
echo "🌐 Access your dashboard at: http://$VPS_IP"
'@

# Save deployment script to temp file
$TEMP_SCRIPT = "deploy_script.sh"
$DEPLOYMENT_SCRIPT | Out-File -FilePath $TEMP_SCRIPT -Encoding UTF8

# Upload and execute deployment script
scp $TEMP_SCRIPT "$VPS_USER@$VPS_IP":/tmp/
ssh "$VPS_USER@$VPS_IP" "chmod +x /tmp/$TEMP_SCRIPT && /tmp/$TEMP_SCRIPT"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ VPS deployment completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ VPS deployment failed" -ForegroundColor Red
    exit 1
}

# Step 5: Verify Deployment
Write-Host "\n🧪 Step 5: Verifying Deployment..." -ForegroundColor Yellow

# Test frontend access
try {
    $response = Invoke-WebRequest -Uri "http://$VPS_IP" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend accessible at http://$VPS_IP" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Frontend verification failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test API connectivity
try {
    $apiResponse = Invoke-WebRequest -Uri "http://$VPS_IP/api/health" -TimeoutSec 10
    if ($apiResponse.StatusCode -eq 200) {
        Write-Host "✅ API connectivity verified" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ API verification failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Cleanup
Remove-Item $TEMP_SCRIPT -Force -ErrorAction SilentlyContinue
Remove-Item $DEPLOYMENT_PACKAGE -Force -ErrorAction SilentlyContinue

Write-Host "\n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🌐 Dashboard URL: http://$VPS_IP" -ForegroundColor Cyan
Write-Host "🔧 API Endpoint: http://$VPS_IP/api/" -ForegroundColor Cyan
Write-Host "📊 Health Check: http://$VPS_IP/health" -ForegroundColor Cyan
Write-Host "\n🚀 Your AI Trading Sentinel is now accessible worldwide!" -ForegroundColor Green
Write-Host "Start trading from anywhere in the world! 🌍" -ForegroundColor Yellow