#!/bin/bash
# 🚨 Emergency VPS Fix - Navigate to correct directory and deploy

set -e
echo "🚨 Emergency Fix: AI Trading Sentinel VPS Deployment"
echo "📍 Current directory: $(pwd)"
echo ""

# Navigate to the AI-TRADING-BOT directory
echo "📂 Navigating to AI-TRADING-BOT directory..."
cd /root/AI-TRADING-BOT
echo "✅ Now in: $(pwd)"
echo ""

# Stop the failing service first
echo "🛑 Stopping failing trae-bot service..."
systemctl stop trae-bot || true
echo ""

# Create the deploy_cloud.sh script in the correct directory
echo "📝 Creating deploy_cloud.sh script..."
cat > deploy_cloud.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 AI Trading Sentinel - VPS Deployment Starting..."
echo "📍 Working directory: $(pwd)"

# Update system packages
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3.10+ and essential tools
echo "🐍 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv git curl wget htop nano ufw

# Install Node.js 18.x
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Install Playwright system dependencies
echo "🎭 Installing Playwright dependencies..."
apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2 libgtk-3-0 libgdk-pixbuf2.0-0

# Create Python virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Setup environment configuration
echo "⚙️ Setting up environment configuration..."
cp .env.example .env

# Create systemd service file with correct paths
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/trae-bot.service << 'SERVICEEOF'
[Unit]
Description=AI Trading Sentinel Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AI-TRADING-BOT
Environment=PATH=/root/AI-TRADING-BOT/venv/bin
Environment=DISPLAY=:99
ExecStart=/root/AI-TRADING-BOT/venv/bin/python /root/AI-TRADING-BOT/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd daemon
systemctl daemon-reload

# Setup firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 8000
ufw allow 3000

echo "✅ Deployment base setup completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Configure .env file with your Bulenox credentials"
echo "   2. Test the bot manually first"
echo "   3. Start the systemd service"
echo "   4. Monitor logs and performance"
echo ""
echo "🌐 Web Dashboard will be available at: http://161.97.112.146:8000"
EOF

# Make the script executable
chmod +x deploy_cloud.sh

echo "✅ deploy_cloud.sh script created in correct directory!"
echo ""
echo "🚀 Now running the deployment..."
echo ""

# Run the deployment script
./deploy_cloud.sh

echo ""
echo "🎯 Deployment completed! Next steps:"
echo ""
echo "1️⃣ Configure your Bulenox credentials:"
echo "   nano .env"
echo ""
echo "2️⃣ Update these values in .env:"
echo "   BULENOX_USERNAME=your_actual_username"
echo "   BULENOX_PASSWORD=your_actual_password"
echo "   SIMULATION_MODE=true"
echo "   AUTO_EXECUTE=false"
echo ""
echo "3️⃣ Test the bot manually:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "4️⃣ Start the systemd service:"
echo "   systemctl start trae-bot"
echo "   systemctl enable trae-bot"
echo ""
echo "5️⃣ Monitor the service:"
echo "   systemctl status trae-bot"
echo "   journalctl -u trae-bot -f"
echo ""
echo "🌐 Dashboard: http://161.97.112.146:8000"
echo "📱 Mobile monitoring via Termius ready!"
echo ""
echo "🎉 AI Trading Sentinel deployment complete!"

echo ""
echo "🔧 Quick Commands for VPS Terminal:"
echo "================================="
echo "# Navigate to project directory:"
echo "cd /root/AI-TRADING-BOT"
echo ""
echo "# Activate virtual environment:"
echo "source venv/bin/activate"
echo ""
echo "# Test bot manually:"
echo "python main.py"
echo ""
echo "# Start service:"
echo "systemctl start trae-bot"
echo ""
echo "# Check service status:"
echo "systemctl status trae-bot"
echo ""
echo "# View logs:"
echo "journalctl -u trae-bot -f"
echo ""