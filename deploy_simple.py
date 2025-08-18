#!/usr/bin/env python3
"""
🤖 TradeBot Sentinel - Simple Contabo VPS Deployment

This script provides deployment instructions and creates necessary files
for manual deployment to Contabo VPS.

Usage:
    python deploy_simple.py
"""

import os
import json
from datetime import datetime
from pathlib import Path

def create_deployment_package():
    """Create deployment package with all necessary files"""
    print("🚀 Creating TradeBot Sentinel deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deployment_package")
    deploy_dir.mkdir(exist_ok=True)
    
    # Create .env file for VPS
    env_content = f'''
# ✅ TradeBot Sentinel - Contabo VPS Configuration
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# ✅ Bulenox Trading Credentials
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=XujhMzFf6K
BROKER_USERNAME=BX64883
BROKER_PASSWORD=XujhMzFf6K
BROKER_URL=https://bulenox.projectx.com/login
BULENOX_ACCOUNT_ID=BX64883

# ✅ VPS Chrome Settings
HEADLESS=true
USE_TEMP_PROFILE=true
SCREENSHOT_ON_FAILURE=true
CHROME_OPTS=--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu --window-size=1920,1080 --disable-extensions --disable-plugins

# ✅ API Settings
PORT=5000
DEBUG=false
FLASK_SECRET_KEY=aPpS3cuReKey!47829
ENCRYPTION_KEY=Q2xpZW50LXNpZ25lZC1lbmNyeXB0aW9uLWtleQ==
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
CORS_ORIGINS=*

# ✅ Logging & Environment
LOG_LEVEL=INFO
ENVIRONMENT=production

# ✅ TradeBot Sentinel Automation Settings
AUTOMATION_HEADLESS=true
AUTOMATION_TIMEOUT=30000
SCREENSHOT_ON_ERROR=true
RETRY_ATTEMPTS=3
RETRY_DELAY=2000
INTERCEPT_TRADE_REQUESTS=true
SAVE_CURL_COMMANDS=true
AUTO_CONVERT_TO_PYTHON=true
VERBOSE_LOGGING=true
LOG_NETWORK_REQUESTS=true
LOG_ELEMENT_INTERACTIONS=true

# ✅ VPS Specific Settings
DISPLAY=:99
XVFB_DISPLAY=:99
CHROME_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
'''
    
    with open(deploy_dir / ".env", "w", encoding='utf-8') as f:
        f.write(env_content)
    
    # Create setup script for VPS
    setup_script = '''
#!/bin/bash
# 🤖 TradeBot Sentinel - VPS Setup Script

set -e

echo "🚀 Setting up TradeBot Sentinel on Contabo VPS..."

# Update system
echo "📦 Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y wget curl unzip xvfb
sudo apt install -y fonts-liberation libasound2 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libu2f-udev libvulkan1

# Install Google Chrome
echo "🌐 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update -y
sudo apt install -y google-chrome-stable

# Install ChromeDriver
echo "🚗 Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1)
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
sudo unzip -o /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip

# Create project directory
echo "📁 Setting up project directory..."
mkdir -p /home/tradebot/ai-trading-sentinel
cd /home/tradebot/ai-trading-sentinel

# Create Python virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install playwright selenium requests flask python-dotenv curlconverter
pip install pandas numpy matplotlib seaborn
pip install asyncio aiohttp websockets
pip install schedule APScheduler
pip install cryptography jwt
pip install psutil

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Create log directories
echo "📁 Creating log directories..."
mkdir -p logs/curls logs/json logs/screenshots
mkdir -p data/backtest data/signals
chmod 755 logs logs/curls logs/json logs/screenshots
chmod 755 data data/backtest data/signals

# Test Chrome installation
echo "🔍 Testing Chrome installation..."
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 2

python3 -c "
import os
os.environ['DISPLAY'] = ':99'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

try:
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.google.com')
    title = driver.title
    driver.quit()
    print(f'✅ Chrome test successful. Page title: {title}')
except Exception as e:
    print(f'❌ Chrome test failed: {str(e)}')
    exit(1)
"

kill $XVFB_PID 2>/dev/null || true

echo "✅ TradeBot Sentinel setup completed successfully!"
echo "📁 Project directory: /home/tradebot/ai-trading-sentinel"
echo "🔧 Virtual environment: /home/tradebot/ai-trading-sentinel/venv"
echo "📋 Next steps:"
echo "  1. Upload your ai-trading-sentinel files to /home/tradebot/ai-trading-sentinel/"
echo "  2. Copy the .env file to the project directory"
echo "  3. Activate virtual environment: source venv/bin/activate"
echo "  4. Run the main script: python main.py"
'''
    
    with open(deploy_dir / "setup_vps.sh", "w", encoding='utf-8') as f:
        f.write(setup_script)
    
    # Make setup script executable
    os.chmod(deploy_dir / "setup_vps.sh", 0o755)
    
    # Create systemd service file
    service_content = '''
[Unit]
Description=TradeBot Sentinel - AI Trading Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/tradebot/ai-trading-sentinel
Environment=PATH=/home/tradebot/ai-trading-sentinel/venv/bin
Environment=DISPLAY=:99
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac &
ExecStart=/home/tradebot/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/tradebot/ai-trading-sentinel/logs/tradebot.log
StandardError=append:/home/tradebot/ai-trading-sentinel/logs/tradebot_error.log

[Install]
WantedBy=multi-user.target
'''
    
    with open(deploy_dir / "tradebot-sentinel.service", "w", encoding='utf-8') as f:
        f.write(service_content)
    
    # Create deployment instructions
    instructions = f'''
# 🤖 TradeBot Sentinel - Contabo VPS Deployment Instructions

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📋 Deployment Steps

### 1. 📦 Transfer Files to VPS

```bash
# Option A: Using SCP (if you have SSH access)
scp -r ai-trading-sentinel/ root@YOUR_VPS_IP:/home/tradebot/

# Option B: Using rsync (recommended)
rsync -avz --progress ai-trading-sentinel/ root@YOUR_VPS_IP:/home/tradebot/ai-trading-sentinel/

# Option C: Manual upload via FTP/SFTP client
# Upload the entire ai-trading-sentinel directory to /home/tradebot/
```

### 2. 🔧 Setup VPS Environment

```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Run the setup script
cd /home/tradebot/ai-trading-sentinel
chmod +x setup_vps.sh
./setup_vps.sh
```

### 3. ⚙️ Configure Environment

```bash
# Copy the .env file (already configured with Bulenox credentials)
cp deployment_package/.env /home/tradebot/ai-trading-sentinel/.env

# Verify configuration
cat /home/tradebot/ai-trading-sentinel/.env
```

### 4. 🚀 Install and Start Service

```bash
# Copy systemd service file
sudo cp deployment_package/tradebot-sentinel.service /etc/systemd/system/

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable tradebot-sentinel.service
sudo systemctl start tradebot-sentinel.service

# Check service status
sudo systemctl status tradebot-sentinel.service
```

### 5. 📊 Monitor and Verify

```bash
# View real-time logs
tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot.log

# Check error logs
tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot_error.log

# Verify directories
ls -la /home/tradebot/ai-trading-sentinel/logs/
ls -la /home/tradebot/ai-trading-sentinel/logs/curls/
ls -la /home/tradebot/ai-trading-sentinel/logs/json/
```

## ✅ Verification Checklist

- [ ] Files transferred to VPS
- [ ] .env file configured with Bulenox credentials:
  - BULENOX_USERNAME=BX64883
  - BULENOX_PASSWORD=XujhMzFf6K
- [ ] Dependencies installed from requirements.txt
- [ ] Headless Chrome working with persistent profiles
- [ ] Log directories exist and are writable:
  - /home/tradebot/ai-trading-sentinel/logs/
  - /home/tradebot/ai-trading-sentinel/logs/curls/
  - /home/tradebot/ai-trading-sentinel/logs/json/
- [ ] Systemd service running
- [ ] Automation ready for trade execution

## 🔧 Troubleshooting

### Chrome Issues
```bash
# Test Chrome manually
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://www.google.com
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R root:root /home/tradebot/ai-trading-sentinel
chmod -R 755 /home/tradebot/ai-trading-sentinel/logs
```

### Service Issues
```bash
# Restart service
sudo systemctl restart tradebot-sentinel.service

# View detailed logs
journalctl -u tradebot-sentinel.service -f
```

## 🎯 Ready for Automation!

Once deployment is complete, TradeBot Sentinel will be ready to:
- ✅ Login to Bulenox platform automatically
- ✅ Intercept and capture trade requests
- ✅ Generate cURL commands and Python code
- ✅ Execute trades via API
- ✅ Log all activities for monitoring

## 📞 Support

If you encounter any issues during deployment, check:
1. System logs: `journalctl -u tradebot-sentinel.service`
2. Application logs: `/home/tradebot/ai-trading-sentinel/logs/tradebot.log`
3. Chrome/Selenium logs in the application output

---

**TradeBot Sentinel** - Automated Trading Intelligence
'''
    
    with open(deploy_dir / "DEPLOYMENT_INSTRUCTIONS.md", "w", encoding='utf-8') as f:
        f.write(instructions)
    
    # Create quick deployment script
    quick_deploy = '''
#!/bin/bash
# 🚀 Quick Deployment Script for TradeBot Sentinel

set -e

VPS_IP="$1"
SSH_USER="${2:-root}"

if [ -z "$VPS_IP" ]; then
    echo "❌ Usage: $0 <VPS_IP> [SSH_USER]"
    echo "   Example: $0 192.168.1.100 root"
    exit 1
fi

echo "🚀 Deploying TradeBot Sentinel to $VPS_IP..."

# Transfer files
echo "📦 Transferring files..."
rsync -avz --progress --exclude='venv/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='.git/' ../ai-trading-sentinel/ $SSH_USER@$VPS_IP:/home/tradebot/ai-trading-sentinel/

# Transfer deployment files
echo "📋 Transferring deployment configuration..."
scp .env $SSH_USER@$VPS_IP:/home/tradebot/ai-trading-sentinel/
scp setup_vps.sh $SSH_USER@$VPS_IP:/home/tradebot/ai-trading-sentinel/
scp tradebot-sentinel.service $SSH_USER@$VPS_IP:/tmp/

# Execute setup on VPS
echo "⚙️ Setting up VPS environment..."
ssh $SSH_USER@$VPS_IP "cd /home/tradebot/ai-trading-sentinel && chmod +x setup_vps.sh && ./setup_vps.sh"

# Install systemd service
echo "🚀 Installing systemd service..."
ssh $SSH_USER@$VPS_IP "sudo cp /tmp/tradebot-sentinel.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable tradebot-sentinel.service"

echo "✅ Deployment completed successfully!"
echo "🎯 To start the service: ssh $SSH_USER@$VPS_IP 'sudo systemctl start tradebot-sentinel.service'"
echo "📊 To check status: ssh $SSH_USER@$VPS_IP 'sudo systemctl status tradebot-sentinel.service'"
echo "📋 To view logs: ssh $SSH_USER@$VPS_IP 'tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot.log'"
'''
    
    with open(deploy_dir / "quick_deploy.sh", "w", encoding='utf-8') as f:
        f.write(quick_deploy)
    
    os.chmod(deploy_dir / "quick_deploy.sh", 0o755)
    
    print(f"✅ Deployment package created in: {deploy_dir.absolute()}")
    print("\n📋 Package contents:")
    for file in deploy_dir.iterdir():
        print(f"  📄 {file.name}")
    
    return deploy_dir

def main():
    print("🤖 TradeBot Sentinel - Contabo VPS Deployment Preparation")
    print("="*60)
    
    # Create deployment package
    deploy_dir = create_deployment_package()
    
    print("\n🚀 DEPLOYMENT OPTIONS:")
    print("\n1. 🔧 Manual Deployment:")
    print(f"   - Read: {deploy_dir}/DEPLOYMENT_INSTRUCTIONS.md")
    print(f"   - Follow step-by-step instructions")
    
    print("\n2. ⚡ Quick Deployment (if you have SSH access):")
    print(f"   - Run: cd {deploy_dir} && ./quick_deploy.sh YOUR_VPS_IP")
    print(f"   - Example: cd {deploy_dir} && ./quick_deploy.sh 192.168.1.100")
    
    print("\n3. 📦 File Transfer Only:")
    print("   - Upload ai-trading-sentinel/ to your VPS")
    print(f"   - Copy {deploy_dir}/.env to your VPS project directory")
    print(f"   - Run {deploy_dir}/setup_vps.sh on your VPS")
    
    print("\n✅ CONFIGURED CREDENTIALS:")
    print("   - BULENOX_USERNAME=BX64883")
    print("   - BULENOX_PASSWORD=XujhMzFf6K")
    print("   - Headless Chrome enabled")
    print("   - All log directories configured")
    
    print("\n🎯 READY FOR AUTOMATION!")
    print("\nNext steps:")
    print("1. Choose your deployment method above")
    print("2. Follow the instructions in DEPLOYMENT_INSTRUCTIONS.md")
    print("3. Start the TradeBot Sentinel service")
    print("4. Monitor logs for successful automation")

if __name__ == "__main__":
    main()