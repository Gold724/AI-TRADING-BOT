# 🚨 VNC Connection Troubleshooting Guide

## ❌ Current Issue: "Timed out waiting for a response from the computer"

**This means the VNC connection to `161.97.112.146:5901` is failing.**

## 🔧 Troubleshooting Steps

### Step 1: Check VNC Viewer Installation

**Download VNC Viewer:** <mcreference link="https://www.realvnc.com/en/connect/download/viewer/" index="0">0</mcreference>

1. Go to: https://www.realvnc.com/en/connect/download/viewer/
2. Download **VNC Viewer for Windows**
3. Install and launch VNC Viewer

### Step 2: Alternative Connection Methods

**Try these connection formats:**

```
# Method 1: Full VNC URL
vnc://161.97.112.146:5901

# Method 2: IP:Port format
161.97.112.146:5901

# Method 3: IP only (default port)
161.97.112.146

# Method 4: Alternative port
161.97.112.146:5900
```

### Step 3: Network Diagnostics

**Test VPS connectivity:**

```powershell
# Ping test
ping 161.97.112.146

# Port connectivity test
Test-NetConnection -ComputerName 161.97.112.146 -Port 5901
Test-NetConnection -ComputerName 161.97.112.146 -Port 5900
Test-NetConnection -ComputerName 161.97.112.146 -Port 22
```

### Step 4: Firewall & Antivirus Check

1. **Temporarily disable Windows Firewall**
2. **Disable antivirus real-time protection**
3. **Try VNC connection again**
4. **Re-enable security after testing**

### Step 5: Alternative Remote Access

**If VNC fails, try SSH:**

```powershell
# Using Windows built-in SSH
ssh root@161.97.112.146

# Or using PuTTY
# Download: https://www.putty.org/
# Host: 161.97.112.146
# Port: 22
# Username: root
# Password: (same as VNC)
```

## 🔄 VPS Service Restart (If SSH Works)

**If you can SSH but VNC fails:**

```bash
# Restart VNC service
sudo systemctl restart vncserver@1
sudo systemctl status vncserver@1

# Check VNC process
ps aux | grep vnc

# Restart VNC manually
vncserver -kill :1
vncserver :1 -geometry 1024x768 -depth 24
```

## 🌐 Web-Based Alternative

**If both VNC and SSH fail, try web access:**

```
# Check if web services are running
http://161.97.112.146
http://161.97.112.146:80
http://161.97.112.146:8080
http://161.97.112.146:3000
```

## 📱 Mobile Hotspot Test

**Network isolation test:**

1. **Connect PC to mobile hotspot**
2. **Try VNC connection again**
3. **If it works → ISP/network blocking issue**
4. **If it fails → VPS configuration issue**

## 🆘 Emergency Activation (No VNC)

**If VNC is completely unavailable:**

### Option 1: SSH Terminal Activation

```bash
# Connect via SSH
ssh root@161.97.112.146

# Download activation script
cd /tmp
wget http://10.144.230.55:8000/vps_activation_script.sh
chmod +x vps_activation_script.sh
sudo ./vps_activation_script.sh

# Download frontend
cd /var/www/html
sudo rm -rf *
sudo wget http://10.144.230.55:8000/frontend-cloud.zip
sudo unzip frontend-cloud.zip
sudo rm frontend-cloud.zip
sudo chown -R www-data:www-data /var/www/html
sudo systemctl restart nginx
```

### Option 2: Web Panel Access

**Check if Contabo provides web console:**

1. **Login to Contabo customer panel**
2. **Look for "Console" or "VNC" option**
3. **Use browser-based terminal**

## ✅ Success Indicators

**VNC connection successful when:**

- ✅ VNC Viewer shows desktop
- ✅ Can open terminal (Ctrl+Alt+T)
- ✅ Can run commands

**Services working when:**

- ✅ http://161.97.112.146 shows website
- ✅ http://161.97.112.146/api/health returns OK
- ✅ `python verify_deployment.py` shows 5/5

## 📞 Next Steps

1. **Try alternative connection methods above**
2. **Run network diagnostics**
3. **If still failing, use SSH alternative**
4. **Report results for further assistance**

**Local file server still running at: http://10.144.230.55:8000/**