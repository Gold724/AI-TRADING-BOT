#!/bin/bash

# 🚀 AI Trading Sentinel - Automatic GitHub-based Deployment
# This script deploys via GitHub to bypass direct SCP issues

set -e

VPS_IP="185.244.214.70"
REPO_URL="https://github.com/your-username/ai-trading-sentinel.git"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "🚀 AI Trading Sentinel - Automatic GitHub Deployment"
echo "=================================================="
echo "Target VPS: $VPS_IP"
echo "Timestamp: $(date)"
echo ""

# Step 1: Create deployment package
echo "[INFO] Step 1: Creating deployment package..."
mkdir -p deployment_package
cp frontend-deployment.tar.gz deployment_package/ 2>/dev/null || echo "Warning: frontend-deployment.tar.gz not found"
cp nginx-frontend.conf deployment_package/ 2>/dev/null || echo "Warning: nginx-frontend.conf not found"
cp monitoring_setup.sh deployment_package/ 2>/dev/null || echo "Warning: monitoring_setup.sh not found"
cp verify_deployment.sh deployment_package/ 2>/dev/null || echo "Warning: verify_deployment.sh not found"

# Create a simple deployment script for VPS
cat > deployment_package/deploy_on_vps.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying AI Trading Sentinel on VPS..."

# Check if files exist
if [ ! -f "frontend-deployment.tar.gz" ]; then
    echo "❌ frontend-deployment.tar.gz not found!"
    exit 1
fi

# Step 1: Extract Frontend Files
echo "[INFO] Extracting frontend files..."
sudo mkdir -p /var/www/html/backup
sudo cp -r /var/www/html/* /var/www/html/backup/ 2>/dev/null || true
sudo tar -xzf frontend-deployment.tar.gz -C /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/
echo "✅ Frontend files extracted successfully"

# Step 2: Configure Nginx
echo "[INFO] Configuring Nginx..."
if [ -f "nginx-frontend.conf" ]; then
    sudo cp nginx-frontend.conf /etc/nginx/sites-available/ai-trading-sentinel
    sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl reload nginx
    echo "✅ Nginx configured successfully"
else
    echo "⚠️ nginx-frontend.conf not found, skipping Nginx config"
fi

# Step 3: Setup Monitoring
echo "[INFO] Setting up monitoring..."
if [ -f "monitoring_setup.sh" ]; then
    chmod +x monitoring_setup.sh
    sudo ./monitoring_setup.sh
    echo "✅ Monitoring setup completed"
else
    echo "⚠️ monitoring_setup.sh not found, skipping monitoring setup"
fi

# Step 4: Verify Deployment
echo "[INFO] Verifying deployment..."
if [ -f "verify_deployment.sh" ]; then
    chmod +x verify_deployment.sh
    ./verify_deployment.sh
else
    echo "⚠️ verify_deployment.sh not found, running basic verification"
    
    echo "=== Service Status ==="
    sudo systemctl status nginx || true
    sudo systemctl status ai-trading-backend || true
    
    echo "=== Port Status ==="
    sudo netstat -tlnp | grep -E ':(80|5000|8080)' || true
    
    echo "=== Test Endpoints ==="
    curl -s http://localhost/ | head -5 || echo "Frontend not accessible"
    curl -s http://localhost/api/health || echo "API not accessible"
    curl -s http://localhost:8080/ || echo "Monitoring not accessible"
fi

echo ""
echo "🎉 Deployment completed!"
echo "Access your application at:"
echo "- Frontend: http://185.244.214.70/"
echo "- API: http://185.244.214.70/api/"
echo "- Monitoring: http://185.244.214.70:8080/"
EOF

chmod +x deployment_package/deploy_on_vps.sh

echo "✅ Deployment package created"

# Step 2: Create VPS commands
echo "[INFO] Step 2: Creating VPS deployment commands..."

cat > vps_deployment_commands.txt << EOF
# 🚀 AI Trading Sentinel - VPS Deployment Commands
# Copy and paste these commands in your VPS terminal (Termius)

# Method 1: Direct download (if files are accessible via HTTP)
cd /root
wget -O frontend-deployment.tar.gz "https://github.com/your-username/ai-trading-sentinel/raw/main/frontend-deployment.tar.gz" || echo "Download failed"
wget -O nginx-frontend.conf "https://github.com/your-username/ai-trading-sentinel/raw/main/nginx-frontend.conf" || echo "Download failed"
wget -O monitoring_setup.sh "https://github.com/your-username/ai-trading-sentinel/raw/main/monitoring_setup.sh" || echo "Download failed"
wget -O verify_deployment.sh "https://github.com/your-username/ai-trading-sentinel/raw/main/verify_deployment.sh" || echo "Download failed"

# Method 2: Clone repository and run deployment
cd /root
git clone https://github.com/your-username/ai-trading-sentinel.git temp_deploy || git pull
cd temp_deploy
chmod +x deploy_on_vps.sh
sudo ./deploy_on_vps.sh

# Method 3: Manual deployment (if files are present)
cd /root

# Extract frontend
sudo mkdir -p /var/www/html/backup
sudo cp -r /var/www/html/* /var/www/html/backup/ 2>/dev/null || true
sudo tar -xzf frontend-deployment.tar.gz -C /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/

# Configure Nginx
sudo cp nginx-frontend.conf /etc/nginx/sites-available/ai-trading-sentinel
sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Setup monitoring
chmod +x monitoring_setup.sh
sudo ./monitoring_setup.sh

# Verify deployment
chmod +x verify_deployment.sh
./verify_deployment.sh

# Final status check
sudo systemctl status nginx ai-trading-backend monitoring-dashboard
sudo netstat -tlnp | grep -E ':(80|5000|8080)'
curl -s http://localhost/ | head -5
curl -s http://localhost/api/health
curl -s http://localhost:8080/

echo "🎉 Deployment completed!"
echo "Access URLs:"
echo "- Frontend: http://185.244.214.70/"
echo "- API: http://185.244.214.70/api/"
echo "- Monitoring: http://185.244.214.70:8080/"
EOF

echo "✅ VPS deployment commands created"

# Step 3: Create alternative deployment using curl
echo "[INFO] Step 3: Creating curl-based deployment..."

cat > curl_deployment.sh << 'EOF'
#!/bin/bash
# Alternative deployment using base64 encoding

echo "🚀 Creating base64 encoded deployment files..."

# Create base64 encoded files for easy transfer
if [ -f "frontend-deployment.tar.gz" ]; then
    echo "Creating base64 encoded frontend..."
    base64 frontend-deployment.tar.gz > frontend-deployment.tar.gz.b64
    echo "Frontend encoded: $(wc -c < frontend-deployment.tar.gz.b64) bytes"
fi

if [ -f "nginx-frontend.conf" ]; then
    echo "Creating base64 encoded nginx config..."
    base64 nginx-frontend.conf > nginx-frontend.conf.b64
    echo "Nginx config encoded: $(wc -c < nginx-frontend.conf.b64) bytes"
fi

if [ -f "monitoring_setup.sh" ]; then
    echo "Creating base64 encoded monitoring script..."
    base64 monitoring_setup.sh > monitoring_setup.sh.b64
    echo "Monitoring script encoded: $(wc -c < monitoring_setup.sh.b64) bytes"
fi

echo "✅ Base64 files created. You can copy these to VPS and decode them."
EOF

chmod +x curl_deployment.sh

echo ""
echo "🎉 Automatic deployment methods created!"
echo ""
echo "📁 Files created:"
echo "  - deployment_package/deploy_on_vps.sh"
echo "  - vps_deployment_commands.txt"
echo "  - curl_deployment.sh"
echo ""
echo "🚀 Next steps:"
echo "1. Try Method 1: Copy commands from vps_deployment_commands.txt to your VPS"
echo "2. Try Method 2: Use GitHub clone method (if repo is accessible)"
echo "3. Try Method 3: Use base64 encoding for file transfer"
echo ""
echo "💡 Recommended: Use Method 1 with the git clone approach"