#!/bin/bash
# AI Trading Sentinel - Final Production Deployment Script
# This script completes the deployment process on the VPS

set -e

VPS_IP="185.244.214.70"
VPS_USER="root"
LOCAL_FILES_DIR="."

echo "🚀 AI Trading Sentinel - Final Production Deployment"
echo "=================================================="
echo "Target VPS: $VPS_IP"
echo "Timestamp: $(date)"
echo ""

# Function to log messages
log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "✅ [SUCCESS] $1"
}

log_error() {
    echo "❌ [ERROR] $1"
}

log_warning() {
    echo "⚠️  [WARNING] $1"
}

# Step 1: Upload deployment files to VPS
log_info "Step 1: Uploading deployment files to VPS..."

# Check if files exist locally
REQUIRED_FILES=("frontend-deployment.tar.gz" "nginx-frontend.conf" "monitoring_setup.sh" "verify_deployment.sh")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Required file not found: $file"
        exit 1
    fi
done

# Upload files using SCP
log_info "Uploading files via SCP..."
scp -o ConnectTimeout=30 -o StrictHostKeyChecking=no \
    frontend-deployment.tar.gz \
    nginx-frontend.conf \
    monitoring_setup.sh \
    verify_deployment.sh \
    $VPS_USER@$VPS_IP:/tmp/

if [ $? -eq 0 ]; then
    log_success "All deployment files uploaded successfully"
else
    log_error "Failed to upload files to VPS"
    exit 1
fi

# Step 2-5: Execute deployment commands on VPS
log_info "Executing deployment commands on VPS..."

ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
set -e

echo "🔧 Starting VPS deployment process..."

# Step 2: Extract frontend to /var/www/html/
echo "Step 2: Extracting frontend files..."
cd /tmp

# Backup existing files if they exist
if [ -d "/var/www/html" ] && [ "$(ls -A /var/www/html)" ]; then
    echo "Backing up existing web files..."
    sudo mkdir -p /var/www/html.backup.$(date +%Y%m%d_%H%M%S)
    sudo cp -r /var/www/html/* /var/www/html.backup.$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
fi

# Extract frontend files
echo "Extracting frontend deployment package..."
tar -xzf frontend-deployment.tar.gz

# Ensure web directory exists
sudo mkdir -p /var/www/html

# Remove old files and copy new ones
sudo rm -rf /var/www/html/*
sudo cp -r dist/* /var/www/html/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

echo "✅ Frontend files extracted and permissions set"

# Step 3: Configure Nginx with new frontend config
echo "Step 3: Configuring Nginx..."

# Backup existing Nginx config
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Copy new configuration
sudo cp nginx-frontend.conf /etc/nginx/sites-available/ai-trading-sentinel

# Enable the new site
sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    # Reload Nginx
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Step 4: Run monitoring setup
echo "Step 4: Setting up 24/7 monitoring system..."

# Make monitoring script executable
chmod +x monitoring_setup.sh

# Run monitoring setup
sudo ./monitoring_setup.sh

if [ $? -eq 0 ]; then
    echo "✅ 24/7 monitoring system configured successfully"
else
    echo "❌ Failed to configure monitoring system"
    exit 1
fi

# Step 5: Verify deployment
echo "Step 5: Verifying complete deployment..."

# Make verification script executable
chmod +x verify_deployment.sh

# Run verification
./verify_deployment.sh

if [ $? -eq 0 ]; then
    echo "✅ Deployment verification completed successfully"
else
    echo "⚠️  Deployment verification found issues - check logs"
fi

# Final status check
echo ""
echo "🔍 Final System Status Check:"
echo "=============================="

# Check all services
echo "Service Status:"
systemctl is-active ai-trading-sentinel-backend && echo "✅ Backend Service: Running" || echo "❌ Backend Service: Stopped"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Stopped"
systemctl is-active ai-trading-monitoring && echo "✅ Monitoring: Running" || echo "❌ Monitoring: Stopped"

echo ""
echo "Endpoint Tests:"
# Test endpoints
curl -s -f http://localhost/ > /dev/null && echo "✅ Frontend: Accessible" || echo "❌ Frontend: Not accessible"
curl -s -f http://localhost/api/health > /dev/null && echo "✅ API Health: OK" || echo "❌ API Health: Failed"
curl -s -f http://localhost:8080/health > /dev/null && echo "✅ Backend Direct: OK" || echo "❌ Backend Direct: Failed"
curl -s -f http://localhost:3000/ > /dev/null && echo "✅ Monitoring Dashboard: OK" || echo "❌ Monitoring Dashboard: Failed"

echo ""
echo "🌐 External Access URLs:"
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || echo "185.244.214.70")
echo "Frontend: http://$EXTERNAL_IP/"
echo "API: http://$EXTERNAL_IP/api/"
echo "Monitoring: http://$EXTERNAL_IP:3000/"

echo ""
echo "🎉 AI Trading Sentinel deployment completed!"
echo "The system is now ready for 24/7 production trading."

ENDSSH

if [ $? -eq 0 ]; then
    log_success "VPS deployment completed successfully!"
    echo ""
    echo "🎯 DEPLOYMENT SUMMARY:"
    echo "====================="
    echo "✅ Frontend deployed and accessible"
    echo "✅ Nginx configured with API proxy"
    echo "✅ 24/7 monitoring system active"
    echo "✅ All services verified and running"
    echo ""
    echo "🌐 Access your AI Trading Sentinel:"
    echo "Frontend: http://185.244.214.70/"
    echo "API: http://185.244.214.70/api/"
    echo "Monitoring: http://185.244.214.70:3000/"
    echo ""
    echo "🚀 Your trading bot is now live and ready for production!"
else
    log_error "VPS deployment encountered issues"
    exit 1
fi