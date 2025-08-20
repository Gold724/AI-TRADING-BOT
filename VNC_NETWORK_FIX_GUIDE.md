# 🌐 VNC Network Diagnostic & Fix Guide

## Problem: URLs Not Accessible Externally
Despite local success, the URLs are not accessible from outside the VPS.

## 🚀 Quick Fix (One Command)

**Copy and paste this single command in VNC terminal:**

```bash
wget -O /tmp/network_fix.sh https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/VNC_NETWORK_DIAGNOSTIC.sh 2>/dev/null || curl -o /tmp/network_fix.sh https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/VNC_NETWORK_DIAGNOSTIC.sh 2>/dev/null || cp VNC_NETWORK_DIAGNOSTIC.sh /tmp/network_fix.sh; chmod +x /tmp/network_fix.sh && /tmp/network_fix.sh
```

## 🔧 Alternative: Manual Execution

If the above fails, run these commands one by one:

### 1. Make Script Executable
```bash
chmod +x VNC_NETWORK_DIAGNOSTIC.sh
```

### 2. Run Diagnostic
```bash
./VNC_NETWORK_DIAGNOSTIC.sh
```

## 🔍 Manual Network Checks

If you want to check manually:

### Check Services
```bash
sudo systemctl status nginx ai-trading-backend
```

### Check Ports
```bash
sudo netstat -tlnp | grep -E ":80|:5001"
```

### Check Firewall
```bash
sudo ufw status
```

### Test Local URLs
```bash
curl http://localhost/
curl http://localhost/api/status
```

## 🎯 Expected Results After Fix

### Services Should Show:
- ✅ nginx: active (running)
- ✅ ai-trading-backend: active (running)

### Ports Should Show:
- ✅ :80 → nginx
- ✅ :5001 → python (backend)

### URLs Should Return 200 OK:
- ✅ http://161.97.112.146/ (Frontend)
- ✅ http://161.97.112.146/api/status (Backend)
- ✅ http://161.97.112.146/api/health (Health)
- ✅ http://161.97.112.146/api/trading/status (Trading)
- ✅ http://161.97.112.146/api/broker/credentials (Credentials)

## 🚨 Common Issues & Solutions

### Issue 1: Firewall Blocking
**Solution:** Script enables UFW and opens ports 80, 443, 22

### Issue 2: Backend Binding to 127.0.0.1 Only
**Solution:** Script creates new backend that binds to 0.0.0.0:5001

### Issue 3: Nginx Not Configured for External Access
**Solution:** Script updates nginx to listen on all interfaces

### Issue 4: Services Not Starting
**Solution:** Script recreates systemd services with proper configuration

## 🔧 Bulenox Integration Maintained

The fix preserves all Bulenox configuration:
- **Username:** BX64883
- **Password:** XujhMzFf6K
- **Mode:** LIVE Trading
- **Risk Level:** Medium
- **Max Daily Trades:** 5

## 📞 Verification Commands

After running the fix, verify with:

```bash
# Check services
sudo systemctl status nginx ai-trading-backend

# Test URLs
curl http://161.97.112.146/
curl http://161.97.112.146/api/status

# Check logs if issues persist
sudo journalctl -u ai-trading-backend -f
sudo tail -f /var/log/nginx/error.log
```

---

**🎯 This diagnostic will identify and fix network access issues, ensuring external URL accessibility.**