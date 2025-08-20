#!/bin/bash

echo "🔧 AI Trading Sentinel - Network Connectivity Fix"
echo "Server: 161.97.112.146 | Bulenox: BX64883"
echo "================================================"

# 1. Check current network status
echo "📡 Checking network status..."
echo "Current IP addresses:"
ip addr show | grep inet
echo ""

# 2. Check firewall status
echo "🔥 Checking firewall status..."
sudo ufw status verbose
echo ""

# 3. Check if ports are listening
echo "👂 Checking listening ports..."
sudo netstat -tlnp | grep -E ':80|:443|:5000'
echo ""

# 4. Check service status
echo "⚙️ Checking service status..."
sudo systemctl status nginx --no-pager -l
echo ""
sudo systemctl status trading-bot --no-pager -l
echo ""

# 5. Fix firewall rules
echo "🛠️ Applying firewall fixes..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5000
sudo ufw --force enable
echo "✅ Firewall rules updated"
echo ""

# 6. Check iptables rules
echo "🔍 Checking iptables rules..."
sudo iptables -L -n
echo ""

# 7. Test internal connectivity
echo "🧪 Testing internal connectivity..."
curl -s http://localhost/ | head -5
echo ""
curl -s http://localhost/api/health | python3 -m json.tool 2>/dev/null || echo "API not responding"
echo ""

# 8. Restart services
echo "🔄 Restarting services..."
sudo systemctl restart nginx
sudo systemctl restart trading-bot
sleep 3
echo "✅ Services restarted"
echo ""

# 9. Final status check
echo "📊 Final status check..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: RUNNING"
else
    echo "❌ Nginx: FAILED"
fi

if systemctl is-active --quiet trading-bot; then
    echo "✅ Trading Bot: RUNNING"
else
    echo "❌ Trading Bot: FAILED"
fi

# 10. Test external connectivity
echo ""
echo "🌐 Testing external connectivity..."
echo "From VPS, testing external access:"
curl -s -I http://161.97.112.146/ | head -3 || echo "❌ External access failed"
echo ""

# 11. Network diagnostic
echo "🔍 Network diagnostic..."
echo "Default gateway:"
ip route | grep default
echo ""
echo "DNS servers:"
cat /etc/resolv.conf | grep nameserver
echo ""

# 12. Provider-specific fixes
echo "🏢 Applying Contabo VPS specific fixes..."
# Ensure network interface is up
sudo ip link set dev eth0 up 2>/dev/null || true
sudo ip link set dev ens3 up 2>/dev/null || true

# Flush and reset network
sudo systemctl restart networking 2>/dev/null || true
sudo systemctl restart systemd-networkd 2>/dev/null || true

echo "✅ Network fixes applied"
echo ""

echo "🎯 Summary:"
echo "Dashboard: http://161.97.112.146/"
echo "API Health: http://161.97.112.146/api/health"
echo "Bot Status: http://161.97.112.146/api/status"
echo "Bulenox: http://161.97.112.146/api/bulenox"
echo ""
echo "🔧 If still not accessible, run:"
echo "  sudo iptables -F"
echo "  sudo iptables -X"
echo "  sudo iptables -t nat -F"
echo "  sudo iptables -t nat -X"
echo "  sudo systemctl restart nginx"
echo ""
echo "📞 Emergency contact: Check Contabo control panel for network settings"