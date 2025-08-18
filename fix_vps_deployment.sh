#!/bin/bash
# Fix VPS Deployment - Copy Missing TradeBot Sentinel Files
# Run this script to fix missing files on your VPS

set -e

# VPS Configuration (update these values)
VPS_HOST="${VPS_HOST:-your-vps-ip}"
VPS_USER="${VPS_USER:-root}"
VPS_DIR="/root/AI-TRADING-BOT"

echo "🔧 Fixing VPS Deployment - TradeBot Sentinel"
echo "================================================"
echo "VPS Host: $VPS_HOST"
echo "VPS User: $VPS_USER"
echo "VPS Directory: $VPS_DIR"
echo ""

# Check if we can connect to VPS
echo "🔍 Testing VPS connection..."
if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_HOST "echo 'Connection successful'"; then
    echo "❌ Cannot connect to VPS. Please check:"
    echo "   - VPS_HOST is correct"
    echo "   - SSH key is properly configured"
    echo "   - VPS is running and accessible"
    exit 1
fi

echo "✅ VPS connection successful"
echo ""

# Create directory structure
echo "📁 Creating directory structure..."
ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"

# Copy the main TradeBot Sentinel script
echo "📦 Copying TradeBot Sentinel scripts..."
if [ -f "login_bulenox_playwright.py" ]; then
    scp login_bulenox_playwright.py $VPS_USER@$VPS_HOST:$VPS_DIR/
    echo "✅ Copied login_bulenox_playwright.py"
else
    echo "⚠️ login_bulenox_playwright.py not found in current directory"
fi

# Copy from vps_deployment directory
if [ -d "vps_deployment/trading_scripts" ]; then
    echo "📦 Copying from vps_deployment/trading_scripts..."
    scp vps_deployment/trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/
    echo "✅ Copied trading scripts"
fi

if [ -d "vps_deployment/utilities" ]; then
    echo "📦 Copying utilities..."
    scp vps_deployment/utilities/* $VPS_USER@$VPS_HOST:$VPS_DIR/
    echo "✅ Copied utilities"
fi

if [ -d "vps_deployment/launchers" ]; then
    echo "📦 Copying launchers..."
    scp vps_deployment/launchers/* $VPS_USER@$VPS_HOST:$VPS_DIR/
    echo "✅ Copied launchers"
fi

# Copy requirements.txt
if [ -f "requirements.txt" ]; then
    scp requirements.txt $VPS_USER@$VPS_HOST:$VPS_DIR/
    echo "✅ Copied requirements.txt"
elif [ -f "vps_deployment/utilities/requirements.txt" ]; then
    scp vps_deployment/utilities/requirements.txt $VPS_USER@$VPS_HOST:$VPS_DIR/
    echo "✅ Copied requirements.txt from utilities"
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
ssh $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh 2>/dev/null || true"

# Verify files exist
echo "🔍 Verifying deployed files..."
ssh $VPS_USER@$VPS_HOST "ls -la $VPS_DIR/"

echo ""
echo "✅ VPS deployment fix completed!"
echo ""
echo "📋 Next steps:"
echo "1. SSH to your VPS: ssh $VPS_USER@$VPS_HOST"
echo "2. Navigate to directory: cd $VPS_DIR"
echo "3. Install dependencies: pip3 install -r requirements.txt"
echo "4. Install Playwright: python3 -m playwright install"
echo "5. Set environment variables:"
echo "   export BULENOX_USERNAME='your_username'"
echo "   export BULENOX_PASSWORD='your_password'"
echo "6. Run TradeBot Sentinel: python3 login_bulenox_playwright.py --headless"
echo ""
echo "🎉 TradeBot Sentinel is ready for deployment!"