# 🚀 VNC Deployment - Next Steps

## ✅ Current Status
- ✅ Email notifications configured and tested
- ✅ All deployment scripts ready
- ✅ .env file properly configured
- 🔄 **NEXT**: VNC deployment execution

---

## 🖥️ Step 1: Connect to VNC Console

### Connection Details
```
IP Address: 5.189.145.177
Port: 63162
Protocol: VNC
```

### Recommended VNC Clients
- **Windows**: TightVNC Viewer, RealVNC Viewer
- **Mac**: Screen Sharing, RealVNC Viewer
- **Mobile**: VNC Viewer (iOS/Android)

### Connection Steps
1. Open your VNC client
2. Enter: `5.189.145.177:63162`
3. Connect (no password required for Contabo VNC)
4. You should see Ubuntu desktop

---

## 🛠️ Step 2: Execute Deployment Scripts

### Open Terminal in VNC Desktop
```bash
# Navigate to project directory
cd /root/ai-trading-sentinel

# Make scripts executable
chmod +x *.sh

# Execute main deployment
./vnc_deployment_implementation.sh
```

### What This Script Does
- ✅ Updates system packages
- ✅ Installs Python dependencies
- ✅ Sets up Playwright browsers
- ✅ Creates systemd service
- ✅ Configures logging
- ✅ Sets up monitoring

---

## ⚙️ Step 3: Configure Environment (GUI)

### Use GUI Configuration Tool
```bash
# Run GUI configuration helper
./configure_env_gui.sh
```

### Manual Configuration (if needed)
```bash
# Open .env in text editor
gedit .env

# Verify configuration
cat .env | grep -E "(BULENOX_USERNAME|EMAIL_NOTIFICATIONS)"
```

---

## 🚀 Step 4: Start Trading Service

### Use Service Manager GUI
```bash
# Launch service management tool
./service_manager_vnc.sh
```

### Manual Service Commands
```bash
# Start the service
sudo systemctl start trae-bot

# Enable auto-start
sudo systemctl enable trae-bot

# Check status
sudo systemctl status trae-bot

# View logs
sudo journalctl -u trae-bot -f
```

---

## 🧪 Step 5: Verify Browser Testing

### Run Browser Test
```bash
# Test Playwright in VNC environment
python test_browser_vnc.py
```

### Expected Results
- ✅ VNC environment detected
- ✅ Playwright browsers installed
- ✅ Browser launches successfully
- ✅ Web navigation works
- ✅ Trading platform accessible

---

## 📊 Step 6: Monitor Operation

### Real-time Monitoring
```bash
# Watch service logs
sudo journalctl -u trae-bot -f

# Check system resources
htop

# Monitor network
netstat -tulpn | grep python
```

### GUI Monitoring Tools
- **System Monitor**: Check CPU/RAM usage
- **Log Viewer**: View application logs
- **Terminal**: Run monitoring commands

---

## 🔧 Troubleshooting Commands

### Service Issues
```bash
# Restart service
sudo systemctl restart trae-bot

# Check service logs
sudo journalctl -u trae-bot --no-pager

# Verify .env file
python -c "import os; print('BULENOX_USERNAME:', os.getenv('BULENOX_USERNAME', 'NOT SET'))"
```

### Browser Issues
```bash
# Reinstall Playwright browsers
python -m playwright install

# Test browser manually
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=False); browser.close(); p.stop()"
```

### Network Issues
```bash
# Test internet connectivity
ping -c 3 google.com

# Test trading platform
curl -I https://bulenox.projectx.com

# Check DNS
nslookup bulenox.projectx.com
```

---

## 📱 Mobile Management

### VNC Mobile Apps
- **iOS**: VNC Viewer (free)
- **Android**: VNC Viewer (free)

### Quick Mobile Commands
```bash
# Check bot status
sudo systemctl is-active trae-bot

# Quick restart
sudo systemctl restart trae-bot

# View recent logs
sudo journalctl -u trae-bot -n 20
```

---

## 🎯 Success Indicators

### ✅ Deployment Successful When:
- VNC desktop accessible
- All scripts execute without errors
- Service starts and stays running
- Browser test passes
- Email notifications working
- Trading platform login successful

### 📊 Monitoring Dashboard
```bash
# Create simple status check
echo "#!/bin/bash
echo '=== AI Trading Sentinel Status ==='
echo 'Service Status:' \$(sudo systemctl is-active trae-bot)
echo 'Last Email Test:' \$(python test_email_config_simple.py 2>&1 | tail -1)
echo 'Browser Test:' \$(python test_browser_vnc.py 2>&1 | grep -o 'SUCCESS\|FAILED' | tail -1)
echo 'Uptime:' \$(uptime -p)
echo 'Memory:' \$(free -h | grep Mem | awk '{print \$3"/"\$2}')
" > status_check.sh
chmod +x status_check.sh
```

---

## 🆘 Emergency Procedures

### If VNC Connection Fails
1. Try Contabo web console
2. Check VNC port (63162) accessibility
3. Restart VNC service via web console
4. Contact Contabo support

### If Service Won't Start
1. Check logs: `sudo journalctl -u trae-bot`
2. Verify .env file: `cat .env`
3. Test dependencies: `python -c "import playwright"`
4. Restart system: `sudo reboot`

### If Browser Fails
1. Reinstall browsers: `python -m playwright install`
2. Check display: `echo $DISPLAY`
3. Test X11: `xeyes` (should show eyes)
4. Restart VNC: `sudo systemctl restart vncserver`

---

**🎯 Ready to proceed with VNC deployment!**

**📋 Checklist:**
- [ ] Connect to VNC (5.189.145.177:63162)
- [ ] Run `./vnc_deployment_implementation.sh`
- [ ] Configure with `./configure_env_gui.sh`
- [ ] Start service with `./service_manager_vnc.sh`
- [ ] Test browser with `python test_browser_vnc.py`
- [ ] Monitor with `sudo journalctl -u trae-bot -f`

**🔄 Next Action**: Connect to VNC and execute deployment scripts!