# TradeBot Sentinel - Termius VPS Deployment Guide

## Prerequisites
- Termius app installed on your device
- VPS server with Ubuntu/Debian
- SSH access to your VPS
- Bulenox trading account credentials

## Method 1: Upload and Run Script (Recommended)

### Step 1: Edit Credentials
1. Open `deploy_with_credentials.sh` in a text editor
2. Replace the following placeholders with your actual values:
   ```bash
   VPS_HOST="your-actual-vps-ip"           # e.g., "192.168.1.100" or "myserver.com"
   VPS_USER="your-username"                # e.g., "root" or "ubuntu"
   VPS_PORT="22"                           # Change if using custom SSH port
   BULENOX_USERNAME="your_bulenox_username" # Your actual Bulenox login
   BULENOX_PASSWORD="your_bulenox_password" # Your actual Bulenox password
   ```

### Step 2: Upload Script to VPS
1. Open Termius
2. Connect to your VPS
3. Upload the script using Termius file transfer:
   - Tap the "Files" tab in Termius
   - Navigate to your local `deploy_with_credentials.sh`
   - Upload to `/tmp/` directory on your VPS

### Step 3: Execute Deployment
1. In Termius terminal, run:
   ```bash
   chmod +x /tmp/deploy_with_credentials.sh
   /tmp/deploy_with_credentials.sh
   ```

2. The script will automatically:
   - Install all dependencies
   - Set up Python environment
   - Install Playwright and browsers
   - Copy TradeBot Sentinel files
   - Configure environment variables

## Method 2: Manual Command Execution

If you prefer to run commands manually in Termius:

### Step 1: System Setup
```bash
# Create directory
mkdir -p /root/AI-TRADING-BOT
cd /root/AI-TRADING-BOT

# Update system
apt update && apt upgrade -y

# Install core dependencies
apt install -y python3 python3-pip python3-venv curl wget git unzip

# Install browser dependencies
apt install -y libnss3 libatk1.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

### Step 2: Node.js Installation
```bash
# Install Node.js for curlconverter
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
```

### Step 3: Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install playwright requests curlconverter asyncio

# Install Playwright browsers
playwright install chromium
playwright install-deps
```

### Step 4: Upload TradeBot Files
1. Use Termius file transfer to upload:
   - `login_bulenox_playwright.py`
   - Any other `.py` files
   - `requirements.txt` (if exists)

### Step 5: Configure Environment
```bash
# Set up environment variables (replace with actual credentials)
echo 'export BULENOX_USERNAME="your_actual_username"' > .env
echo 'export BULENOX_PASSWORD="your_actual_password"' >> .env

# Make scripts executable
chmod +x *.py *.sh
```

## Running TradeBot Sentinel

### Start the Bot
```bash
cd /root/AI-TRADING-BOT
source venv/bin/activate
source .env
python3 login_bulenox_playwright.py
```

### Debug Mode (Visible Browser)
```bash
python3 login_bulenox_playwright.py --visible
```

### Check Logs
```bash
# View real-time logs
tail -f tradebot_sentinel.log

# View all logs
cat tradebot_sentinel.log
```

## File Locations After Deployment

- **Main Script**: `/root/AI-TRADING-BOT/login_bulenox_playwright.py`
- **Environment**: `/root/AI-TRADING-BOT/.env`
- **Logs**: `/root/AI-TRADING-BOT/tradebot_sentinel.log`
- **Screenshots**: `/root/AI-TRADING-BOT/screenshot_*.png`
- **Trade Requests**: `/root/AI-TRADING-BOT/trade.sh` and `/root/AI-TRADING-BOT/trade_request_full.py`

## Troubleshooting

### Common Issues
1. **Permission Denied**: Run `chmod +x script_name.sh`
2. **Python Module Not Found**: Ensure virtual environment is activated
3. **Browser Launch Failed**: Run `playwright install-deps`
4. **Connection Timeout**: Check VPS firewall settings

### Termius-Specific Tips
1. **File Transfer**: Use Termius built-in SFTP for easy file uploads
2. **Multiple Sessions**: Open multiple terminal tabs for monitoring
3. **Persistent Sessions**: Use `screen` or `tmux` for long-running processes
4. **Port Forwarding**: Set up if you need to access web interfaces

### Running in Background
```bash
# Using screen (recommended)
screen -S tradebot
cd /root/AI-TRADING-BOT
source venv/bin/activate && source .env
python3 login_bulenox_playwright.py
# Press Ctrl+A, then D to detach

# Reattach to screen
screen -r tradebot
```

## Security Recommendations

1. **SSH Keys**: Use SSH key authentication instead of passwords
2. **Firewall**: Configure UFW or iptables
3. **Updates**: Regularly update system packages
4. **Monitoring**: Set up log monitoring and alerts
5. **Backups**: Regular backup of configuration and trade data

## Support

If you encounter issues:
1. Check the log files for error messages
2. Verify all credentials are correct
3. Ensure VPS has sufficient resources (RAM, CPU)
4. Test network connectivity to Bulenox platform

---

**Note**: Always test the deployment in a safe environment before using with real trading accounts.