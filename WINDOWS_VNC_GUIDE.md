# 🚨 Windows VNC Connection Guide

## ❌ Error Explanation

You tried to run Linux bash commands in Windows PowerShell:
```
wget http://10.144.230.55:8000/vps_activation_script.sh && chmod +x vps_activation_script.sh
```

**This won't work!** `&&` and `wget` are Linux commands, not Windows PowerShell.

## ✅ Correct Solution: Use VNC

### Step 1: Download VNC Viewer
```
https://www.realvnc.com/en/connect/download/viewer/
```

### Step 2: Connect to VPS
- **VNC Server:** `161.97.112.146:5901`
- **Password:** `trading123`

### Step 3: Open Terminal in VNC
1. Right-click desktop → "Open Terminal"
2. Or press `Ctrl+Alt+T`

### Step 4: Run Linux Commands in VNC Terminal

**Copy-paste these commands ONE BY ONE:**

```bash
# Activation Script
cd /tmp
wget http://10.144.230.55:8000/vps_activation_script.sh
chmod +x vps_activation_script.sh
sudo ./vps_activation_script.sh
```

```bash
# Frontend Upload
cd /var/www/html
sudo rm -rf *
sudo wget http://10.144.230.55:8000/frontend-cloud.zip
sudo unzip frontend-cloud.zip
sudo rm frontend-cloud.zip
sudo chown -R www-data:www-data /var/www/html
sudo systemctl restart nginx
```

### Step 5: Verify (Back in Windows)

Return to Windows PowerShell and run:
```powershell
python verify_deployment.py
```

## 🎯 Expected Results

- **Trading Dashboard:** http://161.97.112.146
- **API Health:** http://161.97.112.146/api/health
- **Verification Score:** 5/5 ✅

## 🔧 Troubleshooting

**If VNC won't connect:**
```bash
# In VNC terminal, restart VNC service
sudo systemctl restart vncserver@1
```

**If commands fail:**
```bash
# Check internet connection
ping google.com

# Check file server
wget http://10.144.230.55:8000/
```

**Ready to connect via VNC! 🚀**