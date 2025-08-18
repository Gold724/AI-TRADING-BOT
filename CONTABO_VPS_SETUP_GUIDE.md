# 🚀 Contabo VPS Deployment Guide - AI Trading Sentinel

## Step 1: VPS Deployment - Execute deploy_cloud.sh on Contabo VPS

### Prerequisites
- Contabo VPS with Ubuntu 22.04/24.04 LTS
- SSH access to your VPS
- Root or sudo privileges

### 🔐 Initial VPS Connection

```bash
# Connect to your Contabo VPS
ssh root@YOUR_VPS_IP

# Example:
ssh root@161.97.112.146
```

### 🛠️ Automated Deployment Process

#### Option A: Direct Cloud Deploy Script

```bash
# Set environment variables
export CONTABO_VPS_IP="YOUR_VPS_IP"
export CONTABO_SSH_KEY="/path/to/your/ssh/key"

# Run the cloud deployment script
./cloud_deploy.sh --provider contabo --enable-monitoring
```

#### Option B: Dedicated Contabo Script

```bash
# Make deployment script executable
chmod +x deploy_to_contabo.sh

# Run deployment
./deploy_to_contabo.sh
```

### 🔧 Manual VPS Setup Commands

If automated deployment fails, use these manual commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip git curl wget unzip tmux htop

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Playwright dependencies
sudo apt-get install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

### 📁 Project Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
cd ai-trading-sentinel

# Install Python dependencies
pip3 install -r requirements.txt

# Install Playwright browsers
python3 -m playwright install chromium

# Install frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

### ⚙️ Environment Configuration

```bash
# Create environment file
cp .env.example .env
nano .env
```

Add your configuration:
```env
# Bulenox Credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
BULENOX_URL=https://bulenox.projectx.com/login

# Trading Configuration
MAX_DAILY_TRADES=5
TRADE_INTERVAL_SECONDS=60
SIGNAL_SOURCE=webhook
RISK_PERCENTAGE=2.0
MAX_DRAWDOWN=10.0

# Monitoring
SLACK_WEBHOOK_URL=your_slack_webhook_url
EMAIL_ALERTS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
WEBSOCKET_PORT=8080

# Security
JWT_SECRET_KEY=your_jwt_secret_key
API_KEY=your_api_key
```

### 🔒 Security Setup

```bash
# Set proper file permissions
chmod 600 .env
chmod +x *.sh

# Create logs directory
mkdir -p logs
chmod 755 logs

# Setup firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp
sudo ufw --force enable
```

### 🚀 Service Configuration

```bash
# Create systemd service
sudo cp trae.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trae

# Start the service
sudo systemctl start trae
sudo systemctl status trae
```

### 📊 Monitoring Setup

```bash
# Test monitoring system
python3 simple_monitoring_test.py --test-mode

# Setup log rotation
sudo cp logrotate.conf /etc/logrotate.d/trading-bot

# Create monitoring cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/python3 /root/ai-trading-sentinel/health_check.py") | crontab -
```

### ✅ Deployment Verification

```bash
# Check service status
sudo systemctl status trae

# Check logs
tail -f logs/trading_bot.log

# Test API endpoint
curl http://localhost:5000/api/health

# Test frontend
curl http://localhost:80
```

### 🔄 Maintenance Commands

```bash
# Restart service
sudo systemctl restart trae

# View logs
journalctl -u trae -f

# Update code
git pull origin main
sudo systemctl restart trae

# Monitor system resources
htop
df -h
free -h
```

### 🚨 Troubleshooting

#### Common Issues:

1. **Service won't start:**
```bash
sudo journalctl -u trae --no-pager
```

2. **Playwright browser issues:**
```bash
python3 -m playwright install-deps
python3 -m playwright install chromium
```

3. **Permission errors:**
```bash
sudo chown -R $USER:$USER /path/to/ai-trading-sentinel
chmod +x *.py *.sh
```

4. **Port conflicts:**
```bash
sudo netstat -tulpn | grep :5000
sudo kill -9 PID_NUMBER
```

### 📈 Performance Optimization

```bash
# Increase file limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize Python
export PYTHONUNBUFFERED=1
export PYTHONOPTIMIZE=1

# Setup swap (if needed)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Next Steps

After successful VPS deployment:
1. ✅ **Credential Setup** - Configure broker API keys
2. ✅ **Paper Trading** - Start with simulated trading
3. ✅ **Live Monitoring** - Enable 24/7 alerts
4. ✅ **Scale Operations** - Add multiple accounts

**Status**: 🟢 VPS deployment infrastructure ready for production use.