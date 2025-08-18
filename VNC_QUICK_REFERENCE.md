# 🚀 VNC Deployment - Quick Reference

## 🎯 Your Mission: Deploy AI Trading Sentinel via VNC

### 📍 Current Status
✅ **Email Setup**: COMPLETE (Gmail notifications working)  
🔄 **Next Phase**: VNC deployment execution

---

## 🖥️ VNC Connection (Step 1)

```
🌐 IP: 5.189.145.177
🔌 Port: 63162
🔑 Password: None (Contabo VNC)
```

**Quick Connect**: Open VNC client → Enter `5.189.145.177:63162` → Connect

---

## ⚡ Deployment Commands (Step 2)

```bash
# In VNC desktop terminal:
cd /root/ai-trading-sentinel
chmod +x *.sh
./vnc_deployment_implementation.sh
```

---

## ⚙️ Service Management (Step 3)

```bash
# GUI method (recommended):
./service_manager_vnc.sh

# Manual method:
sudo systemctl start trae-bot
sudo systemctl enable trae-bot
sudo systemctl status trae-bot
```

---

## 🧪 Testing (Step 4)

```bash
# Test browser functionality:
python test_browser_vnc.py

# Test email notifications:
python test_email_config_simple.py

# Monitor live logs:
sudo journalctl -u trae-bot -f
```

---

## 🎯 Success Indicators

✅ **VNC Connected**: Ubuntu desktop visible  
✅ **Scripts Run**: No errors during deployment  
✅ **Service Active**: `systemctl status trae-bot` shows "active (running)"  
✅ **Browser Works**: Playwright test passes  
✅ **Emails Work**: Test email received  
✅ **Trading Ready**: Bot logs show login attempts  

---

## 🆘 Quick Fixes

### Service Won't Start
```bash
sudo journalctl -u trae-bot --no-pager
# Check logs for errors
```

### Browser Issues
```bash
python -m playwright install
# Reinstall browsers
```

### Connection Lost
```bash
# Reconnect VNC: 5.189.145.177:63162
# Or use Contabo web console
```

---

## 📱 Mobile Access

**VNC Apps**: VNC Viewer (iOS/Android)  
**Connection**: Same IP:Port (5.189.145.177:63162)  
**Quick Status**: `sudo systemctl is-active trae-bot`

---

## 🔄 What Happens Next

1. **Connect VNC** → See Ubuntu desktop
2. **Run Scripts** → System gets configured
3. **Start Service** → Bot begins running
4. **Monitor Logs** → Watch trading activity
5. **Receive Emails** → Get notifications
6. **24/7 Operation** → Automated trading

---

**🎯 Ready? Connect to VNC and let's deploy!**