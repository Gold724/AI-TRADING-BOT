# VNC Connection Guide for AI Trading Sentinel Deployment

## 🔗 VNC Connection Details

**VNC Server IP:** `5.189.145.177`  
**VNC Port:** `63162`  
**Connection String:** `5.189.145.177:63162`

## 📋 Step 1: Download VNC Client

### Recommended VNC Clients:
1. **UltraVNC** (Windows) - https://www.uvnc.com/downloads/ultravnc.html
2. **RealVNC Viewer** (Cross-platform) - https://www.realvnc.com/en/connect/download/viewer/
3. **TigerVNC** (Linux/macOS) - https://tigervnc.org/
4. **TightVNC** (Windows/Linux) - https://www.tightvnc.com/

### Quick Download (UltraVNC for Windows):
```bash
# Download UltraVNC Viewer (recommended)
wget https://www.uvnc.com/component/docman/doc_download/426-ultravnc-1-4-0-0-x64-setup
```

## 🚀 Step 2: Connect to VPS via VNC

### Method 1: UltraVNC (Windows)
1. **Launch UltraVNC Viewer**
2. **Enter Connection Details:**
   - Server: `5.189.145.177:63162`
   - Click "Connect"
3. **Enter VNC Password** (from Contabo Control Panel)
4. **Access Desktop Environment**

### Method 2: RealVNC Viewer (Cross-platform)
1. **Open RealVNC Viewer**
2. **New Connection:**
   - VNC Server: `5.189.145.177:63162`
   - Name: "Contabo-VPS-Trading-Bot"
3. **Connect and Enter Password**

### Method 3: Command Line (Linux/macOS)
```bash
# Using vncviewer
vncviewer 5.189.145.177:63162

# Using TigerVNC
tigervnc 5.189.145.177:63162
```

## 🖥️ Step 3: VNC Desktop Setup

### Once Connected:
1. **Open Terminal** (Ctrl+Alt+T or right-click desktop)
2. **Update System:**
```bash
sudo apt update && sudo apt upgrade -y
```

3. **Install Desktop Tools:**
```bash
sudo apt install -y gedit gnome-terminal firefox-esr
```

## 📦 Step 4: Execute Deployment Script

### Download and Run Deployment Script:
```bash
# Navigate to home directory
cd ~

# Download deployment script
wget -O vnc_deploy.sh https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/vnc_deployment_implementation.sh

# Make executable
chmod +x vnc_deploy.sh

# Execute deployment
./vnc_deploy.sh
```

### Alternative - Manual Script Creation:
```bash
# Create deployment script
gedit vnc_deploy.sh

# Copy content from vnc_deployment_implementation.sh
# Save and execute
chmod +x vnc_deploy.sh
./vnc_deploy.sh
```

## ⚙️ Step 5: Configure Environment

### Edit .env File with GUI:
```bash
# Navigate to project directory
cd ~/ai-trading-sentinel

# Open .env with gedit
gedit .env
```

### Required .env Configuration:
```env
# Broker Configuration
BROKER_USERNAME=your_username
BROKER_PASSWORD=your_password
BROKER_URL=https://your-broker-url.com

# Trading Parameters
TRADE_AMOUNT=100
MAX_DAILY_TRADES=10
RISK_PERCENTAGE=2

# Monitoring
SLACK_WEBHOOK_URL=your_slack_webhook
EMAIL_NOTIFICATIONS=true

# VPS Configuration
VPS_MODE=true
HEADLESS_BROWSER=true
VNC_DISPLAY=:1
```

## 🔄 Step 6: Start Trading Bot Service

### Enable and Start Service:
```bash
# Enable service for auto-start
sudo systemctl enable trae-bot.service

# Start the service
sudo systemctl start trae-bot.service

# Check status
sudo systemctl status trae-bot.service
```

### Monitor Service via GUI:
```bash
# Open system monitor
gnome-system-monitor

# Or use terminal monitoring
watch -n 2 'systemctl status trae-bot.service'
```

## 🧪 Step 7: Verify Playwright Browser

### Test Browser Functionality:
```bash
# Navigate to project directory
cd ~/ai-trading-sentinel

# Run browser test
python3 test_browser_vnc.py
```

### Visual Browser Test:
```bash
# Launch Firefox for visual verification
firefox &

# Test Playwright in GUI mode
python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://google.com')
        await page.screenshot(path='vnc_test.png')
        await browser.close()
        print('✅ Browser test successful!')

asyncio.run(test_browser())
"
```

## 📊 Step 8: Monitoring and Management

### Real-time Log Monitoring:
```bash
# Follow service logs
sudo journalctl -u trae-bot.service -f

# Monitor application logs
tail -f ~/ai-trading-sentinel/logs/trae.log
```

### GUI Monitoring Tools:
```bash
# System resource monitor
htop

# Network monitoring
iftop

# Disk usage
df -h
```

## 🔧 Troubleshooting

### VNC Connection Issues:
1. **Black Screen:** Click VNC window and press Enter
2. **Keyboard Layout:** Test characters before typing passwords
3. **Connection Timeout:** Check firewall settings
4. **Password Issues:** Reset VNC password in Contabo Control Panel

### Service Issues:
```bash
# Restart service
sudo systemctl restart trae-bot.service

# Check service logs
sudo journalctl -u trae-bot.service --no-pager

# Verify Python environment
which python3
pip3 list | grep playwright
```

### Browser Issues:
```bash
# Reinstall Playwright browsers
python3 -m playwright install

# Test display
echo $DISPLAY
export DISPLAY=:1
```

## 🔒 Security Best Practices

### VNC Security:
1. **Change VNC Password Regularly**
2. **Use VNC Only When Necessary**
3. **Prefer SSH for Regular Access**
4. **Log Out After Each Session**

### System Security:
```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5900:5999/tcp  # VNC ports
```

## ✅ Success Indicators

- [ ] VNC connection established successfully
- [ ] Desktop environment accessible
- [ ] Deployment script executed without errors
- [ ] .env file configured properly
- [ ] trae-bot.service running and enabled
- [ ] Playwright browsers installed and functional
- [ ] Trading bot logs showing activity
- [ ] Browser test screenshots generated

## 📞 Emergency Contacts

**Contabo Support:** https://contabo.com/support/  
**VNC Tutorial:** https://contabo.com/blog/vnc-connect-vps/  
**Project Repository:** https://github.com/your-repo/ai-trading-sentinel

---

**⚠️ Important Notes:**
- VNC is not encrypted - use only for deployment and troubleshooting
- Always log out of VNC sessions when finished
- Monitor system resources during trading operations
- Keep VNC password secure and change regularly

**🎯 Next Steps:**
1. Connect via VNC using provided credentials
2. Execute deployment script
3. Configure .env file
4. Start and verify trading bot service
5. Test Playwright browser functionality
6. Monitor 24/7 operation