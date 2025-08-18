# 🤖 Automated VPS Deployment Scripts Guide

## 📋 Overview

The `vps_deployment/` directory contains fully automated scripts to deploy your AI Trading Sentinel to any VPS (including Contambo VPS) with minimal manual intervention.

## 🚀 Quick Start (3 Steps)

### Step 1: Configure Your VPS Details
```bash
# Edit the deployment script
vim deploy_to_vps.sh

# Update these variables:
VPS_HOST="your-contambo-vps-ip"    # Replace with your actual VPS IP
VPS_USER="root"                    # Or your VPS username
VPS_DIR="/root/AI-TRADING-BOT"     # Target directory on VPS
```

### Step 2: Run Automated Deployment
```bash
# Make script executable and run
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh
```

### Step 3: Verify Deployment
```bash
# SSH to your VPS and validate
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT
python3 vps_environment_check.py
```

## 📁 Script Breakdown

### 🎯 `deploy_to_vps.sh` - Main Deployment Script

**What it does:**
- Creates remote directory structure
- Copies all trading scripts, launchers, and utilities
- Sets proper file permissions
- Installs Python dependencies automatically
- Installs Playwright browsers
- Runs verification checks

**Key Features:**
- ✅ **Fully Automated** - No manual file copying
- ✅ **Error Handling** - Stops on any failure (`set -e`)
- ✅ **Progress Indicators** - Shows what's happening
- ✅ **Verification** - Confirms successful deployment

### 🔍 `vps_environment_check.py` - Environment Validator

**What it checks:**
- Python version (requires 3.8+)
- Required packages (playwright, requests, python-dotenv)
- Playwright browser installation
- Core trading files existence
- File permissions and executability

**Usage:**
```bash
# Run on VPS after deployment
python3 vps_environment_check.py
```

## 🛠️ Customization Options

### Different VPS Configurations

**For non-root users:**
```bash
# In deploy_to_vps.sh
VPS_USER="your-username"
VPS_DIR="/home/your-username/AI-TRADING-BOT"
```

**For custom SSH ports:**
```bash
# Add port specification
ssh -p 2222 $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"
scp -P 2222 trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/
```

**For SSH key authentication:**
```bash
# Add key specification
ssh -i ~/.ssh/your-key $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"
scp -i ~/.ssh/your-key trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/
```

## 🔧 Manual Deployment (Fallback)

If automated deployment fails, use these manual steps:

### 1. Create Directory
```bash
ssh root@your-vps-ip "mkdir -p /root/AI-TRADING-BOT"
```

### 2. Copy Files by Category
```bash
# From vps_deployment directory
scp trading_scripts/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp launchers/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp utilities/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp config_files/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp vps_environment_check.py root@your-vps-ip:/root/AI-TRADING-BOT/
```

### 3. Set Permissions
```bash
ssh root@your-vps-ip "chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh"
```

### 4. Install Dependencies
```bash
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && pip3 install -r requirements.txt"
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && python3 -m playwright install"
```

## ⚙️ Post-Deployment Configuration

### Set Trading Credentials
```bash
# SSH to VPS and create .env file
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT
echo "BULENOX_USERNAME=your_username" > .env
echo "BULENOX_PASSWORD=your_password" >> .env
chmod 600 .env
```

### Test Core Functionality
```bash
# Test headless trading bot
python3 tradebot_sentinel_advanced_pro.py --headless

# Test full workflow
./live_trading_launcher.sh
```

## 🚨 Troubleshooting

### Common Issues & Solutions

**SSH Connection Failed:**
```bash
# Test SSH connection first
ssh root@your-vps-ip "echo 'Connection OK'"

# Check SSH key authentication
ssh-copy-id root@your-vps-ip
```

**Permission Denied:**
```bash
# Fix file permissions
ssh root@your-vps-ip "chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh"
```

**Python Dependencies Missing:**
```bash
# Reinstall dependencies
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && pip3 install --upgrade pip"
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && pip3 install -r requirements.txt"
```

**Playwright Browser Issues:**
```bash
# Install system dependencies
ssh root@your-vps-ip "python3 -m playwright install-deps"
ssh root@your-vps-ip "python3 -m playwright install"
```

## 📊 Deployment Verification

### Success Indicators
- ✅ All files copied without errors
- ✅ Dependencies installed successfully
- ✅ Playwright browsers installed
- ✅ Environment check passes
- ✅ Core script runs without errors

### Health Check Commands
```bash
# Check file structure
ssh root@your-vps-ip "ls -la /root/AI-TRADING-BOT/"

# Verify Python environment
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && python3 vps_environment_check.py"

# Test trading script
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && python3 tradebot_sentinel_advanced_pro.py --help"
```

## 🎯 Production Launch

Once deployment is verified:

### Option 1: Interactive Mode
```bash
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT
./live_trading_launcher.sh
```

### Option 2: Background Process
```bash
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && nohup ./live_trading_launcher.sh > trading.log 2>&1 &"
```

### Option 3: System Service (Advanced)
```bash
# Create systemd service
sudo tee /etc/systemd/system/ai-trading.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AI-TRADING-BOT
ExecStart=/root/AI-TRADING-BOT/live_trading_launcher.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable ai-trading.service
sudo systemctl start ai-trading.service
```

## 📝 Deployment Logs

The scripts generate comprehensive logs:

- **Deployment Log:** Console output during deployment
- **Environment Check:** Results from `vps_environment_check.py`
- **Trading Logs:** Generated in `/root/AI-TRADING-BOT/logs/`

## 🔄 Updates & Maintenance

### Updating Scripts
```bash
# Re-run deployment to update files
./deploy_to_vps.sh

# Or update specific files
scp trading_scripts/tradebot_sentinel_advanced_pro.py root@your-vps-ip:/root/AI-TRADING-BOT/
```

### Health Monitoring
```bash
# Regular health check
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && python3 vps_environment_check.py"

# Check trading logs
ssh root@your-vps-ip "tail -f /root/AI-TRADING-BOT/logs/trading.log"
```

## 🎉 Summary

These automated scripts provide:

- ✅ **One-Command Deployment** - Complete setup in minutes
- ✅ **Error Prevention** - Automated validation and verification
- ✅ **Cross-Platform** - Works on any Linux VPS
- ✅ **Production Ready** - Includes all necessary components
- ✅ **Maintenance Friendly** - Easy updates and monitoring

**Next Steps:**
1. Configure `deploy_to_vps.sh` with your VPS details
2. Run `./deploy_to_vps.sh` to deploy
3. Set your trading credentials in `.env`
4. Launch with `./live_trading_launcher.sh`

Your AI Trading Sentinel will be operational and ready for automated trading!