#!/bin/bash
# 🚀 Quick VPS Deployment Script for AI Trading Sentinel
# Copy and paste this entire script into your Contabo VPS terminal

set -e
echo "🚀 AI Trading Sentinel - Quick VPS Deployment Starting..."

# Step 1: Clean existing directory
echo "📁 Cleaning existing repository..."
rm -rf AI-TRADING-BOT

# Step 2: Fresh clone
echo "📥 Cloning fresh repository..."
git clone https://github.com/Gold724/AI-TRADING-BOT.git
cd AI-TRADING-BOT

# Step 3: Create missing deploy_cloud.sh
echo "📝 Creating deployment script..."
cat > deploy_cloud.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting AI Trading Sentinel Deployment..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3.10+
echo "🐍 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv git curl wget htop

# Install Node.js
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Install Playwright dependencies
echo "🎭 Installing Playwright dependencies..."
apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Create virtual environment
echo "🔧 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Setup environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'ENVEOF'
# Broker Configuration
BULENOX_URL=https://bulenox.com
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here

# Trading Configuration
AUTO_EXECUTE=false
SIMULATION_MODE=true
MAX_POSITION_SIZE=1000
RISK_PERCENTAGE=2

# Notification Settings
SLACK_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Browser Settings
HEADLESS=true
BROWSER_TIMEOUT=30000
ENVEOF
    fi
fi

# Create systemd service
echo "🔧 Setting up systemd service..."
cat > /etc/systemd/system/trae-bot.service << 'SERVICEEOF'
[Unit]
Description=AI Trading Sentinel Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AI-TRADING-BOT
Environment=PATH=/root/AI-TRADING-BOT/venv/bin
ExecStart=/root/AI-TRADING-BOT/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd
systemctl daemon-reload

echo "✅ Deployment completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Configure .env file: nano .env"
echo "   2. Add your Bulenox credentials"
echo "   3. Start service: systemctl start trae-bot"
echo "   4. Enable auto-start: systemctl enable trae-bot"
echo "   5. Check status: systemctl status trae-bot"
echo ""
echo "🌐 Web Dashboard will be available at: http://161.97.112.146:8000"
EOF

# Make deployment script executable
chmod +x deploy_cloud.sh

# Step 4: Run deployment
echo "🚀 Running deployment script..."
./deploy_cloud.sh

# Step 5: Configure environment (interactive)
echo ""
echo "⚙️ IMPORTANT: Configure your broker credentials"
echo "Edit the .env file with your Bulenox username and password:"
echo ""
echo "nano .env"
echo ""
echo "Change these lines:"
echo "BULENOX_USERNAME=your_username_here  # Replace with actual username"
echo "BULENOX_PASSWORD=your_password_here  # Replace with actual password"
echo ""
echo "Press ENTER when ready to continue..."
read -r

# Step 6: Start services
echo "🚀 Starting trading service..."
systemctl start trae-bot
systemctl enable trae-bot

# Step 7: Show status
echo ""
echo "📊 Service Status:"
systemctl status trae-bot --no-pager

echo ""
echo "✅ AI Trading Sentinel deployment completed!"
echo ""
echo "📱 Access Methods:"
echo "   • Web Dashboard: http://161.97.112.146:8000"
echo "   • SSH: ssh root@161.97.112.146"
echo "   • Termius Mobile: Add host 161.97.112.146"
echo ""
echo "🔧 Useful Commands:"
echo "   • Check status: systemctl status trae-bot"
echo "   • View logs: journalctl -u trae-bot -f"
echo "   • Restart: systemctl restart trae-bot"
echo ""
echo "🎯 Your trading bot is now running 24/7!"