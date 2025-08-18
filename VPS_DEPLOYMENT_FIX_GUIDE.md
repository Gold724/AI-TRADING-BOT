# 🔧 VPS Deployment Fix Guide - TradeBot Sentinel

## Issue Description
The VPS is trying to run `login_bulenox_playwright.py` but the file is missing from the `/root/AI-TRADING-BOT` directory. This indicates an incomplete deployment.

## Error Analysis
```bash
python3: can't open file '/root/AI-TRADING-BOT/login_bulenox_playwright.py': [Errno 2] No such file or directory
root@vmi2736801:~/AI-TRADING-BOT# cd AI-TRADING-BOT 
-bash: cd: AI-TRADING-BOT: No such file or directory
```

## Quick Fix Solutions

### Solution 1: Automated Fix Script (Recommended)

#### For Linux/Mac Users:
```bash
# Make the script executable
chmod +x fix_vps_deployment.sh

# Run the fix script
./fix_vps_deployment.sh
```

#### For Windows Users:
```powershell
# Run the PowerShell fix script
.\fix_vps_deployment.ps1 -VpsHost "your-vps-ip"
```

### Solution 2: Manual File Copy

#### Step 1: Copy the main script
```bash
# Copy the main TradeBot Sentinel script
scp login_bulenox_playwright.py root@your-vps-ip:/root/AI-TRADING-BOT/

# Copy all trading scripts from deployment directory
scp vps_deployment/trading_scripts/* root@your-vps-ip:/root/AI-TRADING-BOT/
```

#### Step 2: Copy utilities and launchers
```bash
# Copy utility scripts
scp vps_deployment/utilities/* root@your-vps-ip:/root/AI-TRADING-BOT/

# Copy launcher scripts
scp vps_deployment/launchers/* root@your-vps-ip:/root/AI-TRADING-BOT/
```

#### Step 3: Set permissions
```bash
# SSH to VPS and set permissions
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT
chmod +x *.py *.sh
```

### Solution 3: Complete Re-deployment

#### Using the deployment script:
```bash
# Navigate to vps_deployment directory
cd vps_deployment

# Edit deploy_to_vps.sh with your VPS details
vim deploy_to_vps.sh
# Update VPS_HOST="your-vps-ip"

# Run deployment
./deploy_to_vps.sh
```

## Post-Fix Setup

Once files are copied, complete the setup on your VPS:

### 1. SSH to your VPS
```bash
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT
```

### 2. Install Python Dependencies
```bash
# Install required packages
pip3 install -r requirements.txt

# Install Playwright browsers
python3 -m playwright install

# Install additional dependencies if needed
pip3 install curlconverter
```

### 3. Set Environment Variables
```bash
# Create .env file
echo "BULENOX_USERNAME=your_username" > .env
echo "BULENOX_PASSWORD=your_password" >> .env

# Or export directly
export BULENOX_USERNAME="your_username"
export BULENOX_PASSWORD="your_password"
```

### 4. Test the Installation
```bash
# Test basic functionality
python3 login_bulenox_playwright.py --help

# Run verification script
python3 verify_setup.py
```

### 5. Run TradeBot Sentinel
```bash
# Run in headless mode (recommended for VPS)
python3 login_bulenox_playwright.py --headless --capture-all

# Or use the launcher script
./live_trading_launcher.sh
```

## Verification Checklist

After running the fix, verify these files exist on your VPS:

```bash
ls -la /root/AI-TRADING-BOT/
```

Required files:
- ✅ `login_bulenox_playwright.py` - Main TradeBot Sentinel script
- ✅ `tradebot_sentinel_advanced_pro.py` - Advanced trading script
- ✅ `requirements.txt` - Python dependencies
- ✅ `verify_setup.py` - Setup verification script
- ✅ `live_trading_launcher.sh` - Trading launcher
- ✅ `curl_to_python.py` - cURL conversion utility

## Troubleshooting Common Issues

### Issue: SSH Connection Failed
**Solution:**
- Verify VPS IP address is correct
- Check SSH key is properly configured
- Ensure VPS is running and accessible

### Issue: Permission Denied
**Solution:**
```bash
ssh root@your-vps-ip "chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh"
```

### Issue: Python Dependencies Missing
**Solution:**
```bash
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && pip3 install -r requirements.txt"
```

### Issue: Playwright Browsers Not Installed
**Solution:**
```bash
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && python3 -m playwright install"
```

## Advanced Configuration

### Environment Variables Setup
Create a comprehensive `.env` file on your VPS:

```bash
# SSH to VPS
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT

# Create .env file
cat > .env << EOF
# Bulenox Credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password

# Trading Configuration
HEADLESS_MODE=true
CAPTURE_MODE=true
SCREENSHOT_DIR=./screenshots

# Network Configuration
TIMEOUT=30000
RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=./tradebot_sentinel.log
EOF
```

### Systemd Service Setup (Optional)
Create a systemd service for automatic startup:

```bash
# Create service file
sudo tee /etc/systemd/system/tradebot-sentinel.service > /dev/null << EOF
[Unit]
Description=TradeBot Sentinel - AI Trading Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AI-TRADING-BOT
Environment=DISPLAY=:99
ExecStart=/usr/bin/python3 login_bulenox_playwright.py --headless --capture-all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tradebot-sentinel
sudo systemctl start tradebot-sentinel

# Check status
sudo systemctl status tradebot-sentinel
```

## Success Indicators

When everything is working correctly, you should see:

1. **File Verification:**
   ```bash
   ls -la /root/AI-TRADING-BOT/login_bulenox_playwright.py
   # Should show the file exists with execute permissions
   ```

2. **Script Execution:**
   ```bash
   python3 /root/AI-TRADING-BOT/login_bulenox_playwright.py --help
   # Should show help text without errors
   ```

3. **Dependencies Check:**
   ```bash
   python3 -c "import playwright; print('Playwright installed successfully')"
   ```

4. **Environment Variables:**
   ```bash
   echo $BULENOX_USERNAME
   # Should display your username
   ```

## Support

If you continue to experience issues:

1. Check the deployment logs
2. Verify network connectivity to your VPS
3. Ensure all required files are present
4. Test with a simple Python script first
5. Review the TradeBot Sentinel logs for detailed error information

---

**🎉 Once completed, your TradeBot Sentinel will be fully operational on your VPS!**