# VNC Access Guide - AI Trading Sentinel Deployment

## 🎯 Complete VNC Deployment Process

This guide provides step-by-step instructions for deploying the AI Trading Sentinel using VNC access to your Contabo VPS.

---

## 📋 Prerequisites

- Contabo VPS account with Ubuntu 24.04
- VPS IP: `185.215.180.149`
- VNC access enabled on your VPS
- Web browser (Chrome, Firefox, Safari, Edge)

---

## 🔐 Step 1: Access Contabo VNC Console

### Method 1: Web-Based VNC (Recommended)

1. **Open your web browser** and navigate to:
   ```
   https://my.contabo.com
   ```

2. **Login to your Contabo account** using your credentials

3. **Navigate to VPS Management:**
   - Click on "Your Services" in the top menu
   - Select "VPS" from the dropdown
   - Find your VPS (185.215.180.149)

4. **Access VNC Console:**
   - Click on your VPS entry
   - Look for "VNC Console" or "Console" button
   - Click "Open VNC Console" or "Launch Console"

5. **VNC Console Opens:**
   - A new browser tab/window will open
   - You should see the Ubuntu desktop environment
   - If you see a login screen, use your VPS credentials

### Method 2: Direct VNC Client (Alternative)

If web-based VNC doesn't work:

1. **Download VNC Viewer:**
   - Windows: RealVNC Viewer, TightVNC, or UltraVNC
   - Mac: RealVNC Viewer or Screen Sharing
   - Linux: Remmina or TigerVNC

2. **Connect using:**
   - Server: `185.215.180.149:5901` (or port provided by Contabo)
   - Username: `ubuntu` (or your VPS username)
   - Password: Your VPS password

---

## 🚀 Step 2: Execute VNC Deployment Script

### 2.1 Open Terminal in VNC Session

1. **Right-click on desktop** → Select "Open Terminal"
   - OR press `Ctrl + Alt + T`
   - OR click Activities → Search "Terminal"

2. **Verify you're in the correct environment:**
   ```bash
   whoami
   pwd
   ls -la
   ```

### 2.2 Download and Execute Deployment Script

1. **Download the deployment script:**
   ```bash
   cd /home/ubuntu
   wget https://raw.githubusercontent.com/your-username/ai-trading-sentinel/main/vnc_deployment_implementation.sh
   ```

   **OR if you have the script locally, create it:**
   ```bash
   nano vnc_deployment_implementation.sh
   # Copy the script content from vnc_deployment_implementation.sh
   # Save with Ctrl+X, Y, Enter
   ```

2. **Make script executable:**
   ```bash
   chmod +x vnc_deployment_implementation.sh
   ```

3. **Execute the deployment script:**
   ```bash
   ./vnc_deployment_implementation.sh
   ```

4. **Monitor the installation process:**
   - The script will update the system
   - Install Python, Node.js, and dependencies
   - Install Playwright browsers
   - Clone the repository
   - Create systemd service
   - Set up logging

---

## ⚙️ Step 3: Configure .env File Using gedit

### 3.1 Automatic .env Configuration

The deployment script will:
1. Create a template `.env` file
2. Automatically open `gedit` (GUI text editor)
3. Display instructions for configuration

### 3.2 Manual .env Configuration

**When gedit opens, update these values:**

```env
# Broker Configuration
BROKER_URL=https://app.bulenox.com
BROKER_USERNAME=your_actual_username
BROKER_PASSWORD=your_actual_password
BROKER_API_KEY=your_actual_api_key

# Trading Configuration
TRADING_MODE=live
RISK_LEVEL=medium
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=5.0

# Notification Configuration
SLACK_WEBHOOK_URL=your_slack_webhook_url
EMAIL_NOTIFICATIONS=true
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 3.3 Save Configuration

1. **Replace placeholder values** with your actual credentials
2. **Save the file:** Press `Ctrl + S`
3. **Close gedit:** Press `Alt + F4` or click the X button

---

## 🔄 Step 4: Start trae-bot Service and Monitor

### 4.1 Service Management

The deployment script automatically:
1. Creates the systemd service
2. Enables auto-start on boot
3. Starts the service
4. Opens monitoring tools

### 4.2 Manual Service Commands

**Check service status:**
```bash
sudo systemctl status trae-bot
```

**Start service:**
```bash
sudo systemctl start trae-bot
```

**Stop service:**
```bash
sudo systemctl stop trae-bot
```

**Restart service:**
```bash
sudo systemctl restart trae-bot
```

**View logs:**
```bash
sudo journalctl -u trae-bot -f
```

### 4.3 Monitoring Tools

The script opens these monitoring tools automatically:

1. **Log Monitor Terminal:**
   - Shows real-time service logs
   - Command: `sudo journalctl -u trae-bot -f`

2. **System Monitor (htop):**
   - Shows CPU, memory, and process usage
   - Command: `htop`

3. **Bot Log File:**
   ```bash
   tail -f /var/log/trae/trae.log
   ```

---

## 🌐 Step 5: Verify Playwright Browser Functionality

### 5.1 Automatic Browser Test

The deployment script includes an automatic browser test that:
1. Launches Playwright browser in visible mode
2. Navigates to test websites
3. Tests form interactions
4. Takes a screenshot
5. Verifies browser functionality

### 5.2 Manual Browser Test

**Run the browser test manually:**
```bash
cd /home/ubuntu/ai-trading-sentinel
python3 browser_test.py
```

**Expected output:**
```
Testing Playwright browser in VNC environment...
Navigating to test page...
Screenshot saved as browser_test.png
Testing form interactions...
Form filled successfully
Browser will stay open for 10 seconds for visual verification...
✓ Browser test completed successfully!
```

### 5.3 Visual Verification

1. **Browser should open visibly** in the VNC session
2. **You should see** the browser navigating to websites
3. **Screenshot file** `browser_test.png` should be created
4. **No error messages** should appear

---

## ✅ Success Indicators

### Service Status
```bash
$ sudo systemctl status trae-bot
● trae-bot.service - AI Trading Sentinel Bot
   Loaded: loaded (/etc/systemd/system/trae-bot.service; enabled; vendor preset: enabled)
   Active: active (running) since [timestamp]
```

### Log Output
```bash
$ tail -f /var/log/trae/trae.log
2024-01-20 10:30:00 - INFO - Starting AI Trading Sentinel...
2024-01-20 10:30:01 - INFO - Browser started successfully
2024-01-20 10:30:05 - INFO - Successfully logged in to broker
2024-01-20 10:30:06 - INFO - Bot is running... Press Ctrl+C to stop
```

### Browser Test Success
- Browser opens visibly in VNC
- No error messages
- Screenshot file created
- Form interactions work

---

## 🔧 Troubleshooting

### VNC Access Issues

**Problem:** Cannot access VNC console
**Solutions:**
1. Try different browser (Chrome, Firefox)
2. Disable browser extensions
3. Check if VNC is enabled in Contabo panel
4. Contact Contabo support

### Service Issues

**Problem:** Service fails to start
**Solutions:**
```bash
# Check detailed logs
sudo journalctl -u trae-bot -n 50

# Check service file
sudo systemctl cat trae-bot

# Restart service
sudo systemctl restart trae-bot
```

### Browser Issues

**Problem:** Playwright browser fails
**Solutions:**
```bash
# Reinstall Playwright
python3 -m playwright install
python3 -m playwright install-deps

# Check display environment
echo $DISPLAY
export DISPLAY=:1

# Test browser manually
python3 browser_test.py
```

### Environment Issues

**Problem:** .env file not loaded
**Solutions:**
```bash
# Check .env file exists
ls -la /home/ubuntu/ai-trading-sentinel/.env

# Verify .env content
cat /home/ubuntu/ai-trading-sentinel/.env

# Test environment loading
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('BROKER_USERNAME'))"
```

---

## 📞 Emergency Contacts

### Contabo Support
- **Website:** https://contabo.com/support
- **Email:** support@contabo.com
- **Phone:** Available in customer portal

### VNC Alternatives
- **SSH (if fixed):** `ssh -p 18177 ubuntu@185.215.180.149`
- **Contabo Web Console:** Available in customer portal
- **Mobile Apps:** Contabo mobile app

---

## 🎉 Deployment Complete!

**Your AI Trading Sentinel is now:**
- ✅ Running 24/7 on VPS
- ✅ Accessible via VNC
- ✅ Monitored with logs
- ✅ Auto-starting on boot
- ✅ Browser-enabled for trading

**Next Steps:**
1. Monitor logs regularly
2. Check trading performance
3. Update credentials as needed
4. Scale to multiple accounts if desired

**Happy Trading! 🚀📈**