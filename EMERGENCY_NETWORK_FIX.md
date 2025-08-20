# 🚨 EMERGENCY NETWORK FIX - AI Trading Sentinel

**Issue**: External access to http://161.97.112.146/ fails despite services running internally

## 🔥 IMMEDIATE FIX (Type in Termius)

```bash
sudo iptables -F && sudo iptables -X && sudo iptables -t nat -F && sudo iptables -t nat -X && sudo ufw --force reset && sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw --force enable && sudo systemctl restart nginx && sudo systemctl restart trading-bot && curl -I http://localhost/
```

## 🔍 STEP-BY-STEP DIAGNOSIS

### 1. Check Current Status
```bash
sudo systemctl status nginx trading-bot
sudo netstat -tlnp | grep :80
sudo ufw status
```

### 2. Reset Firewall Completely
```bash
sudo iptables -F
sudo iptables -X
sudo iptables -t nat -F
sudo iptables -t nat -X
sudo ufw --force reset
```

### 3. Configure Basic Firewall
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

### 4. Restart Services
```bash
sudo systemctl restart nginx
sudo systemctl restart trading-bot
sudo systemctl restart networking
```

### 5. Test Internal Connectivity
```bash
curl -I http://localhost/
curl http://localhost/api/health
```

### 6. Check Network Interface
```bash
ip addr show
ip route show
ping -c 3 8.8.8.8
```

## 🏢 CONTABO VPS SPECIFIC FIXES

### Check Contabo Control Panel
1. Login to Contabo customer portal
2. Go to "My Services" → Your VPS
3. Check "Network" settings
4. Ensure no firewall rules blocking HTTP traffic
5. Verify IP address matches: **161.97.112.146**

### Network Interface Reset
```bash
sudo ip link set dev eth0 down
sudo ip link set dev eth0 up
sudo systemctl restart systemd-networkd
```

## 🧪 VERIFICATION TESTS

### Internal Tests (Run on VPS)
```bash
# Test Flask app directly
curl http://127.0.0.1:5000/api/health

# Test Nginx proxy
curl http://localhost/api/health

# Test external IP internally
curl -I http://161.97.112.146/
```

### External Tests (Run from local machine)
```bash
# Test connectivity
ping 161.97.112.146
telnet 161.97.112.146 80
curl -v http://161.97.112.146/
```

## 🎯 SUCCESS INDICATORS

✅ **Internal curl works**: `curl http://localhost/` returns HTML  
✅ **Services running**: `systemctl is-active nginx trading-bot` both return "active"  
✅ **Port 80 listening**: `netstat -tlnp | grep :80` shows nginx  
✅ **Firewall allows HTTP**: `ufw status` shows "80/tcp ALLOW"  
✅ **External access works**: Browser loads http://161.97.112.146/  

## 🚨 IF STILL FAILING

### Alternative Port Test
```bash
# Try different port
sudo ufw allow 8080
sudo sed -i 's/listen 80/listen 8080/' /etc/nginx/sites-available/trading-bot
sudo systemctl restart nginx
curl http://161.97.112.146:8080/
```

### Check Provider Firewall
- Contact Contabo support
- Check if DDoS protection is blocking traffic
- Verify no upstream firewall rules

### Emergency Fallback
```bash
# Direct Flask access (bypass Nginx)
sudo ufw allow 5000
curl http://161.97.112.146:5000/
```

## 📞 SUPPORT CONTACTS

- **Contabo Support**: https://my.contabo.com/support
- **VPS IP**: 161.97.112.146
- **Bulenox ID**: BX64883
- **Services**: nginx, trading-bot (systemd)

---

**Next Steps After Fix**:
1. ✅ Verify dashboard loads: http://161.97.112.146/
2. ✅ Test API endpoints: /api/health, /api/status
3. ✅ Proceed with live trading integration testing