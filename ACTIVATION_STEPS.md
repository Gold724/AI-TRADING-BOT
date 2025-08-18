# 🚀 AI Trading Sentinel - VPS Activation Guide

## 📊 Current Status
✅ **Local File Server:** Running on http://10.144.230.55:8000/  
✅ **Frontend File:** frontend-cloud.zip ready for download  
✅ **VPS Target:** 161.97.112.146  

---

## 🎯 Step-by-Step Activation

### Step 1: Connect via VNC 🖥️

**VNC Connection Details:**
- **Server:** `161.97.112.146:5901`
- **URL:** `vnc://161.97.112.146:5901`
- **Port:** 5901

**Download VNC Viewer:**
1. Go to: https://www.realvnc.com/en/connect/download/viewer/
2. Download and install VNC Viewer
3. Connect to: `161.97.112.146:5901`

---

### Step 2: Upload & Run Activation Script 📜

**In VNC Terminal, execute these commands:**

```bash
# Download activation script
cd /tmp
wget http://10.144.230.55:8000/vps_activation_script.sh
chmod +x vps_activation_script.sh

# Run activation script
sudo ./vps_activation_script.sh
```

**What the script does:**
- ✅ Updates system packages
- ✅ Configures VNC server with systemd
- ✅ Sets up Nginx web server
- ✅ Deploys Flask backend API
- ✅ Configures firewall (UFW)
- ✅ Creates monitoring services

---

### Step 3: Upload Frontend Files 🌐

**After activation script completes, run these commands in VNC:**

```bash
# Navigate to web directory
cd /var/www/html

# Clear existing files
sudo rm -rf *

# Download frontend
sudo wget http://10.144.230.55:8000/frontend-cloud.zip

# Extract frontend
sudo unzip frontend-cloud.zip
sudo rm frontend-cloud.zip

# Set permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Verify files
ls -la /var/www/html

# Restart Nginx
sudo systemctl restart nginx
```

---

### Step 4: Verify Deployment ✅

**On Windows (this machine), run:**

```powershell
python verify_deployment.py
```

**Expected Results:**
- ✅ PING: VPS connectivity
- ✅ VNC: Port 5901 accessible
- ✅ WEB: Port 80 serving frontend
- ✅ API: Port 5000 backend health
- ✅ FRONTEND: React dashboard loaded

**Access URLs after activation:**
- **Trading Dashboard:** http://161.97.112.146
- **API Health:** http://161.97.112.146/api/health
- **Bot Status:** http://161.97.112.146/api/status

---

## 🔧 Troubleshooting Commands

**If services fail, use these VNC commands:**

```bash
# Check service status
sudo systemctl status nginx
sudo systemctl status ai-trading-backend
sudo systemctl status vncserver@1

# Restart services
sudo systemctl restart nginx
sudo systemctl restart ai-trading-backend

# Check logs
sudo journalctl -u nginx -f
sudo journalctl -u ai-trading-backend -f

# Check ports
sudo netstat -tuln | grep -E ':(80|5000|5901)'

# Check firewall
sudo ufw status
```

---

## 🎯 Success Indicators

**You'll know activation worked when:**
1. **VNC:** Desktop environment loads
2. **Web:** http://161.97.112.146 shows trading dashboard
3. **API:** http://161.97.112.146/api/health returns JSON
4. **Verification:** `python verify_deployment.py` shows 5/5 score

---

## 🚨 Current File Server Status

**Local Server:** http://10.144.230.55:8000/  
**Available Files:**
- ✅ vps_activation_script.sh
- ✅ frontend-cloud.zip
- ✅ All project files

**Keep this server running until activation completes!**

---

## 🔥 Quick Start Commands

**⚠️ IMPORTANT: These commands are for VNC Linux Terminal ONLY!**

**Copy these exact commands for VNC:**

```bash
# Step 2: Activation Script (VNC Linux Terminal)
cd /tmp && wget http://10.144.230.55:8000/vps_activation_script.sh && chmod +x vps_activation_script.sh && sudo ./vps_activation_script.sh

# Step 3: Frontend Upload (VNC Linux Terminal)
cd /var/www/html && sudo rm -rf * && sudo wget http://10.144.230.55:8000/frontend-cloud.zip && sudo unzip frontend-cloud.zip && sudo rm frontend-cloud.zip && sudo chown -R www-data:www-data /var/www/html && sudo systemctl restart nginx
```

**For Windows PowerShell (Step 4 only):**
```powershell
# Step 4: Verify Deployment (Windows)
python verify_deployment.py
```

**🚨 DO NOT run Linux commands in Windows PowerShell!**
**✅ Use VNC connection to access Linux terminal on the VPS!**

**Ready to activate! 🚀**