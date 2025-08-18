# 🚀 Final VPS Deployment Commands - Copy & Paste Ready

## ✅ Current Status: Repository Successfully Cloned!

You're now in: `root@vmi2736801:~/AI-TRADING-BOT#`

## 📋 Step-by-Step Commands (Copy each block)

### 1. Create the Missing deploy_cloud.sh Script
```bash
cat > deploy_cloud.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 AI Trading Sentinel - VPS Deployment Starting..."

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

# Create systemd service file
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
ExecStart=/root/AI-TRADING-BOT/venv/bin/python main.py
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
```

### 2. Run the Deployment Script
```bash
./deploy_cloud.sh
```

### 3. Configure Your Broker Credentials
```bash
# Edit the .env file
nano .env
```

**In the nano editor, update these lines:**
```env
# Change these values to your actual Bulenox credentials:
BULENOX_USERNAME=your_actual_username
BULENOX_PASSWORD=your_actual_password

# Set trading mode (start with simulation)
SIMULATION_MODE=true
AUTO_EXECUTE=false

# Set position limits
MAX_POSITION_SIZE=1000
RISK_PERCENTAGE=2
```

**Save and exit nano:** Press `Ctrl+X`, then `Y`, then `Enter`

### 4. Test the Bot Manually (Recommended)
```bash
# Activate virtual environment
source venv/bin/activate

# Test run the bot
python main.py
```

**If the test run works, press `Ctrl+C` to stop it.**

### 5. Start the Systemd Service
```bash
# Start the trading service
systemctl start trae-bot

# Enable auto-start on boot
systemctl enable trae-bot

# Check service status
systemctl status trae-bot
```

### 6. Monitor the Bot
```bash
# View live logs
journalctl -u trae-bot -f

# Check last 50 log entries
journalctl -u trae-bot -n 50

# Check system resources
htop
```

## 🌐 Access Your Trading Dashboard

Once running, access your dashboard at:
- **Main Dashboard:** `http://161.97.112.146:8000`
- **API Endpoint:** `http://161.97.112.146:8000/api`

## 📱 Termius Mobile Commands

**Quick Status Check:**
```bash
systemctl status trae-bot
```

**Restart Bot:**
```bash
systemctl restart trae-bot
```

**View Recent Logs:**
```bash
journalctl -u trae-bot -n 20
```

## 🚨 Troubleshooting Commands

**If service fails to start:**
```bash
# Check detailed logs
journalctl -u trae-bot -n 100 --no-pager

# Test manual execution
cd /root/AI-TRADING-BOT
source venv/bin/activate
python main.py
```

**Check system resources:**
```bash
# Memory usage
free -h

# Disk space
df -h

# Network connections
netstat -tlnp | grep :8000
```

## 🔐 Security Status

✅ **Firewall configured** (SSH, 8000, 3000 ports open)  
✅ **Environment variables secured** in .env file  
✅ **Systemd service** for reliable 24/7 operation  
✅ **Auto-restart** on failures  

---

**🎯 Your AI Trading Sentinel will be running 24/7 on Contabo VPS!**

**Next:** Copy the first command block and paste it into your VPS terminal.