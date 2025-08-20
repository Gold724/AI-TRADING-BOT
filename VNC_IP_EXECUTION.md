# 🌐 VNC IP Fix - Execution Guide

## Problem Identified ✅
The URLs weren't working because services were configured for SSH IP (161.97.112.146) instead of VNC IP (5.189.145.177:63162).

## Quick Fix (One Command)
```bash
wget -O - https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/VNC_IP_FIX.sh | bash
```

## Manual Execution in VNC Terminal

### Step 1: Make Script Executable
```bash
chmod +x VNC_IP_FIX.sh
```

### Step 2: Run the Fix
```bash
sudo ./VNC_IP_FIX.sh
```

## What This Fix Does

1. **🛑 Stops Services**: Cleans all running services
2. **🌐 Network Analysis**: Shows available network interfaces
3. **⚙️ Nginx Config**: Configures for BOTH VNC IP (5.189.145.177) AND SSH IP (161.97.112.146)
4. **🐍 Backend Update**: Creates VNC-aware Flask backend
5. **🔧 Systemd Service**: Updates service for VNC compatibility
6. **🌍 Frontend**: Creates VNC-aware frontend with network info
7. **🔥 Firewall**: Allows access from both IP addresses
8. **✅ Verification**: Tests all URLs with proper IPs

## Expected Results After Fix

### ✅ VNC IP URLs (Primary)
- **Frontend**: http://5.189.145.177/
- **Backend API**: http://5.189.145.177/api/status
- **Health Check**: http://5.189.145.177/api/health
- **Trading Status**: http://5.189.145.177/api/trading/status
- **Broker Credentials**: http://5.189.145.177/api/broker/credentials
- **Network Info**: http://5.189.145.177/api/network/info

### ✅ SSH IP URLs (Backup)
- **Frontend**: http://161.97.112.146/
- **Backend API**: http://161.97.112.146/api/status

## Manual Commands (If Script Fails)

### Stop Services
```bash
sudo systemctl stop ai-trading-backend nginx
sudo pkill -f "python.*flask"
```

### Check Network Interfaces
```bash
ip addr show
echo "VNC IP: 5.189.145.177"
echo "SSH IP: 161.97.112.146"
```

### Test URLs After Fix
```bash
curl http://5.189.145.177/
curl http://5.189.145.177/api/status
curl http://161.97.112.146/
```

### Check Service Status
```bash
sudo systemctl status ai-trading-backend-vnc nginx
sudo netstat -tlnp | grep -E ":80|:5001"
```

## Troubleshooting

### If URLs Still Don't Work:
1. **Check Firewall**: `sudo ufw status`
2. **Check Services**: `sudo systemctl status nginx ai-trading-backend-vnc`
3. **Check Ports**: `sudo netstat -tlnp | grep -E ":80|:5001"`
4. **Check Logs**: `sudo journalctl -u ai-trading-backend-vnc -f`

### Common Issues:
- **Port Conflicts**: Script kills conflicting processes
- **Firewall Blocking**: Script configures UFW for both IPs
- **Service Binding**: Backend now binds to 0.0.0.0:5001 (all interfaces)
- **Nginx Config**: Configured for both VNC and SSH IPs

## Bulenox Integration Maintained
- **Username**: BX64883
- **Password**: XujhMzFf6K
- **Mode**: LIVE Trading
- **Risk Level**: Medium
- **Max Daily Trades**: 5
- **VNC Compatible**: ✅

## Key Difference
**Before**: Services only accessible via SSH IP (161.97.112.146)
**After**: Services accessible via BOTH VNC IP (5.189.145.177) AND SSH IP (161.97.112.146)

This ensures your VNC connection can properly access all trading bot URLs!