# 🔍 CONTABO VPS NETWORK DEBUG - AI Trading Sentinel

**Status**: External connectivity still failing after firewall reset
**Issue**: Connection timeout to http://161.97.112.146/ despite internal services running

## 🚨 CRITICAL DIAGNOSIS COMMANDS (Type in Termius)

### 1. Check Network Interface Status
```bash
ip addr show
ip route show
ping -c 3 8.8.8.8
```

### 2. Verify Services and Ports
```bash
sudo netstat -tlnp | grep -E ':80|:443|:5000'
sudo systemctl status nginx trading-bot --no-pager
curl -I http://localhost/
```

### 3. Check Contabo-Specific Network Settings
```bash
# Check if interface is properly configured
sudo ip link show
sudo ip addr show eth0
sudo ip addr show ens3

# Check routing table
ip route show default
cat /etc/resolv.conf
```

### 4. Advanced Network Diagnostics
```bash
# Check if external traffic can reach the server
sudo tcpdump -i any port 80 &
# (Let it run for 30 seconds while testing from external)
sudo pkill tcpdump

# Check iptables rules
sudo iptables -L -n -v
sudo iptables -t nat -L -n -v
```

### 5. Contabo Control Panel Check
**IMPORTANT**: Login to Contabo customer portal and verify:

1. **VPS Status**: Ensure VPS is "Running" 
2. **Network Settings**: Check firewall rules in control panel
3. **IP Configuration**: Verify 161.97.112.146 is correctly assigned
4. **DDoS Protection**: Check if enabled and blocking HTTP traffic
5. **Port Restrictions**: Ensure no provider-level port blocking

### 6. Emergency Network Reset
```bash
# Complete network stack reset
sudo systemctl stop networking
sudo systemctl stop systemd-networkd
sudo ip addr flush dev eth0
sudo ip addr flush dev ens3
sudo systemctl start systemd-networkd
sudo systemctl start networking
sleep 5
sudo systemctl restart nginx trading-bot
```

### 7. Alternative Port Testing
```bash
# Test on different port to isolate issue
sudo ufw allow 8080
sudo sed -i 's/listen 80/listen 8080/' /etc/nginx/sites-available/trading-bot
sudo systemctl restart nginx
curl -I http://localhost:8080/
```

## 🏢 CONTABO-SPECIFIC FIXES

### Check Provider Firewall
```bash
# Some VPS providers have upstream firewalls
# Contact Contabo support if these don't work:
sudo ufw disable
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT  
sudo iptables -P OUTPUT ACCEPT
sudo iptables -F
sudo systemctl restart nginx
```

### Network Interface Reset (Contabo Ubuntu)
```bash
# Reset network interface (common Contabo issue)
sudo ip link set dev eth0 down
sudo ip link set dev eth0 up
sudo dhclient eth0
sudo systemctl restart networking
```

## 🧪 VERIFICATION TESTS

### Internal Tests (Run on VPS)
```bash
# Test each layer
curl http://127.0.0.1:5000/api/health    # Direct Flask
curl http://localhost/api/health          # Through Nginx
wget -O- http://localhost/ | head -10     # Full page test
```

### External Tests (Run from different location)
```bash
# Test from external server/service
nmap -p 80,443 161.97.112.146
telnet 161.97.112.146 80
```

## 🎯 EXPECTED RESULTS

✅ **ip addr show**: Should show eth0 or ens3 with 161.97.112.146  
✅ **ping 8.8.8.8**: Should succeed (internet connectivity)  
✅ **netstat -tlnp | grep :80**: Should show nginx listening  
✅ **curl localhost**: Should return HTML dashboard  
✅ **External access**: Should load http://161.97.112.146/  

## 🚨 IF STILL FAILING

### Contact Contabo Support
- **Issue**: External HTTP traffic not reaching VPS despite firewall configuration
- **VPS IP**: 161.97.112.146
- **Services**: nginx (port 80), trading-bot (port 5000)
- **Symptoms**: Internal curl works, external connection timeout

### Emergency Workaround
```bash
# Direct Flask access (bypass Nginx completely)
sudo ufw allow 5000
sudo systemctl stop nginx
cd /opt/trading-bot
source venv/bin/activate
python3 app.py &
# Test: http://161.97.112.146:5000/
```

## 📞 NEXT STEPS

1. **Run diagnostics above**
2. **Check Contabo control panel**
3. **Contact Contabo support if needed**
4. **Consider alternative port (8080, 5000)**
5. **Verify no upstream provider firewall**

---

**Success Indicator**: `curl http://161.97.112.146/` returns HTML dashboard