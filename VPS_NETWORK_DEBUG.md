# 🌐 VPS NETWORK DEBUG GUIDE

## Current Status
- ✅ VPS Internal: `curl http://localhost/` works
- ❌ External Access: `http://161.97.112.146/` fails (ERR_CONNECTION_TIMED_OUT)
- ✅ SSH Connection: Termius connects to 161.97.112.146:22

## Root Cause Analysis
**The firewall is blocking HTTP traffic on port 80**

## 🔧 STEP 1: Check Current Firewall Status
```bash
sudo ufw status
sudo iptables -L
```

## 🔧 STEP 2: Open Required Ports
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
```

## 🔧 STEP 3: Verify Nginx is Running
```bash
sudo systemctl status nginx
sudo systemctl restart nginx
sudo netstat -tlnp | grep :80
```

## 🔧 STEP 4: Test Network Connectivity
```bash
# Test internal
curl -I http://localhost/

# Test external (from VPS)
curl -I http://161.97.112.146/

# Check if port 80 is listening
sudo ss -tlnp | grep :80
```

## Expected Output After Fix
```
# Firewall status
Status: active
To                         Action      From
--                         ------      ----
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
22/tcp                     ALLOW       Anywhere

# Nginx status
● nginx.service - A high performance web server
   Active: active (running)

# Port listening
tcp  0  0  0.0.0.0:80  0.0.0.0:*  LISTEN  1234/nginx
```

## 🚨 EMERGENCY ONE-LINER
```bash
sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw --force enable && sudo systemctl restart nginx
```

## Verification Steps
1. **Browser**: Open `http://161.97.112.146/`
2. **Expected**: "SSH Fixed: 161.97.112.146" page
3. **Bulenox**: Trading bot integration details

## Troubleshooting
If still failing:
```bash
# Check if Contabo has additional firewall
sudo iptables -F
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables-save
```

## Success Indicators
- ✅ `http://161.97.112.146/` loads in browser
- ✅ Shows "SSH Fixed" message
- ✅ No ERR_CONNECTION_TIMED_OUT
- ✅ Ready for full trading bot deployment

---
**TRAE-SentinelOps**: Network connectivity issue - firewall blocking port 80!