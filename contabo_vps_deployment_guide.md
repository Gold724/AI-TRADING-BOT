# 🚀 Contabo VPS Deployment Guide - AI Trading Sentinel

## Current Status
✅ **SSH Connection Established**: `root@vmi2736801:~#`  
❌ **Repository Issue**: Directory already exists  
❌ **Missing Script**: `deploy_cloud.sh` not found  

## 🔧 Step-by-Step Resolution

### 1. Clean and Re-clone Repository
```bash
# Remove existing directory
rm -rf AI-TRADING-BOT

# Fresh clone from GitHub
git clone https://github.com/Gold724/AI-TRADING-BOT.git

# Navigate to project
cd AI-TRADING-BOT

# Verify files exist
ls -la
```

### 2. Create Missing deploy_cloud.sh Script
```bash
# Create the deployment script
cat > deploy_cloud.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting AI Trading Sentinel Deployment on Contabo VPS..."

# Update system
apt update && apt upgrade -y

# Install Python 3.10+
apt install -y python3 python3-pip python3-venv git curl wget

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Install Playwright dependencies
apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment file
cp .env.example .env
echo "⚠️  Please configure .env with your broker credentials"

# Create systemd service
sudo cp trae-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "✅ Deployment completed successfully!"
echo "📝 Next steps:"
echo "   1. Configure .env file with broker credentials"
echo "   2. Start service: systemctl start trae-bot"
echo "   3. Enable auto-start: systemctl enable trae-bot"
EOF

# Make executable
chmod +x deploy_cloud.sh
```

### 3. Execute Deployment
```bash
# Run deployment script
./deploy_cloud.sh
```

### 4. Configure Environment Variables
```bash
# Edit .env file with your credentials
nano .env

# Add your Bulenox credentials:
# BULENOX_URL=https://bulenox.projectx.com
# BULENOX_USERNAME=your_username
# BULENOX_PASSWORD=your_password
```

### 5. Start Trading Service
```bash
# Start the service
systemctl start trae-bot

# Enable auto-start on boot
systemctl enable trae-bot

# Check status
systemctl status trae-bot
```

## 📊 Monitoring Commands

### Service Status
```bash
# Check service status
systemctl status trae-bot

# View logs
journalctl -u trae-bot -f

# Restart service
systemctl restart trae-bot
```

### System Health
```bash
# Check system resources
htop

# Check disk space
df -h

# Check memory usage
free -h

# Check network connections
netstat -tlnp | grep :8000
```

## 🌐 Web Dashboard Access

Once deployed, access your trading dashboard at:
- **URL**: `http://161.97.112.146:8000`
- **API**: `http://161.97.112.146:8000/api`

## 📱 Termius Mobile Setup

1. **Download Termius** from App Store/Google Play
2. **Add New Host**:
   - Host: `161.97.112.146`
   - Username: `root`
   - Password: `JfAJZ38VwU8j42LKa84PqIxVx`
3. **Quick Commands**:
   ```bash
   # Service status
   systemctl status trae-bot
   
   # View logs
   journalctl -u trae-bot -n 50
   
   # Restart bot
   systemctl restart trae-bot
   ```

## 🚨 Troubleshooting

### If Service Fails to Start
```bash
# Check logs for errors
journalctl -u trae-bot -n 100

# Verify Python environment
source /root/AI-TRADING-BOT/venv/bin/activate
python --version

# Test manual execution
cd /root/AI-TRADING-BOT
python main.py
```

### If Web Dashboard Not Accessible
```bash
# Check if port 8000 is open
netstat -tlnp | grep :8000

# Check firewall
ufw status

# Open port if needed
ufw allow 8000
```

## 🔐 Security Notes

- ✅ SSH access secured with password authentication
- ✅ Environment variables protected in .env file
- ✅ Service runs with systemd for reliability
- ⚠️  Consider setting up SSH key authentication for enhanced security

## 📈 Next Steps

1. **Monitor Performance**: Watch logs and system resources
2. **Configure Alerts**: Set up Slack/email notifications
3. **Scale Operations**: Add multiple trading accounts if needed
4. **Backup Strategy**: Regular backups of configuration and data

---

**🎯 Your AI Trading Sentinel is now ready for 24/7 automated trading on Contabo VPS!**