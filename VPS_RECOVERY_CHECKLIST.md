# ✅ VPS RECOVERY CHECKLIST - AI Trading Sentinel

## 🚨 CRITICAL SITUATION
- **Problem**: Termius cannot connect to Contabo VPS
- **Cause**: Complete network isolation (100% ping loss)
- **Solution**: Use Contabo control panel console access

---

## 📋 STEP-BY-STEP RECOVERY

### ☐ Step 1: Access Contabo Panel (2 minutes)
1. ☐ Open browser
2. ☐ Go to: **https://my.contabo.com/**
3. ☐ Login with your credentials
4. ☐ Click "Your Services" → "VPS Management"
5. ☐ Find VPS: **161.97.112.146**

### ☐ Step 2: Check VPS Status (1 minute)
6. ☐ Look at VPS status indicator
7. ☐ If "Stopped" → Click "Start" button
8. ☐ If "Running" → Continue to Step 3
9. ☐ If "Maintenance" → Wait and check back

### ☐ Step 3: Open VPS Console (1 minute)
10. ☐ Click "Console" or "VNC Console" button
11. ☐ Wait for console window to load
12. ☐ You should see a login prompt
13. ☐ Login with: `root` (or your username)

### ☐ Step 4: Test Network (2 minutes)
14. ☐ Type: `ping -c 4 8.8.8.8`
15. ☐ If ping works → Network is OK, skip to Step 6
16. ☐ If ping fails → Continue to Step 5

### ☐ Step 5: Emergency Network Reset (3 minutes)
17. ☐ Copy/paste this command:
```bash
sudo systemctl restart networking && sudo dhclient eth0
```
18. ☐ Wait 30 seconds
19. ☐ Test again: `ping -c 4 8.8.8.8`
20. ☐ If still fails → Try firewall reset:
```bash
sudo iptables -F && sudo ufw --force reset && sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw --force enable
```

### ☐ Step 6: Restart Services (2 minutes)
21. ☐ Restart SSH: `sudo systemctl restart ssh`
22. ☐ Restart web server: `sudo systemctl restart nginx`
23. ☐ Restart trading bot: `sudo systemctl restart trading-bot`
24. ☐ Check SSH is running: `sudo systemctl status ssh`

### ☐ Step 7: Test External Access (2 minutes)
25. ☐ From your computer, try: `ping 161.97.112.146`
26. ☐ Try Termius connection again
27. ☐ Try web dashboard: **http://161.97.112.146/**

---

## 🆘 IF STEPS FAIL

### ☐ Console Access Failed
- ☐ Try VPS restart from Contabo panel
- ☐ Wait 10 minutes and try console again
- ☐ Contact Contabo support immediately

### ☐ Network Still Down
- ☐ Check Contabo panel "Network" settings
- ☐ Disable DDoS protection if enabled
- ☐ Submit urgent support ticket

### ☐ Services Won't Start
- ☐ Check disk space: `df -h`
- ☐ Check system logs: `sudo journalctl -xe`
- ☐ Reboot VPS: `sudo reboot`

---

## 📞 EMERGENCY SUPPORT

**If nothing works:**
1. ☐ Go to: https://my.contabo.com/support
2. ☐ Create urgent ticket with subject: "VPS Network Isolation - 161.97.112.146"
3. ☐ Include: "Cannot ping, SSH, or access web services. Need immediate network fix."

---

## ✅ SUCCESS CONFIRMATION

**You've recovered when:**
- ☐ Ping works: `ping 161.97.112.146`
- ☐ Termius connects successfully
- ☐ Web dashboard loads: http://161.97.112.146/
- ☐ API responds: http://161.97.112.146/api/status

---

**🎯 MOST IMPORTANT**: Get to the VPS console first - this bypasses all network issues!

**⏱️ ESTIMATED TIME**: 10-15 minutes if everything goes smoothly

**🔗 QUICK LINK**: https://my.contabo.com/ (bookmark this!)