#!/bin/bash
# AI Trading Sentinel - VPS Deployment Script
# Auto-generated deployment script for Contambo VPS

set -e

VPS_HOST="161.97.112.146"
VPS_USER="root"
VPS_DIR="/root/AI-TRADING-BOT"

echo "🚀 Deploying AI Trading Sentinel to VPS..."

# Create remote directory
ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"

# Copy trading scripts
echo "📦 Copying trading scripts..."
scp trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/

# Copy launchers
echo "🔧 Copying launcher scripts..."
scp launchers/* $VPS_USER@$VPS_HOST:$VPS_DIR/

# Copy utilities
echo "⚙️ Copying utility scripts..."
scp utilities/* $VPS_USER@$VPS_HOST:$VPS_DIR/

# Set permissions
echo "🔐 Setting file permissions..."
ssh $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"

# Install dependencies
echo "📚 Installing Python dependencies..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && pip3 install -r requirements.txt"

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 -m playwright install"

# Verify deployment
echo "✅ Verifying deployment..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 verify_setup.py"

echo "🎉 Deployment completed successfully!"
echo "📍 Files deployed to: $VPS_HOST:$VPS_DIR"
echo "🚀 Ready to run: python3 tradebot_sentinel_advanced_pro.py --headless"
