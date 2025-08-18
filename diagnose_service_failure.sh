#!/bin/bash

# 🔍 Service Failure Diagnostic Script
# Identifies root causes of trae-bot service failures

set -e

echo "🔍 AI Trading Sentinel - Service Diagnostic"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_check() {
    echo -e "${GREEN}✓${NC} $1"
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: Service Status
print_header "Service Status Check"
echo "Current service status:"
systemctl status trae-bot.service --no-pager -l || true
echo ""
echo "Recent service logs:"
journalctl -u trae-bot.service --no-pager -l -n 10 || true

# Check 2: Directory Structure
print_header "Directory Structure Check"
if [ -d "/root/ai-trading-sentinel" ]; then
    print_check "Project directory exists: /root/ai-trading-sentinel"
    cd /root/ai-trading-sentinel
    
    if [ -f "main.py" ]; then
        print_check "main.py found"
    else
        print_fail "main.py not found"
    fi
    
    if [ -d "venv" ]; then
        print_check "Virtual environment exists"
        if [ -f "venv/bin/python" ]; then
            print_check "Python executable found in venv"
        else
            print_fail "Python executable missing in venv"
        fi
    else
        print_fail "Virtual environment missing"
    fi
    
    if [ -f ".env" ]; then
        print_check ".env file exists"
    else
        print_warning ".env file missing"
    fi
    
    if [ -d "logs" ]; then
        print_check "Logs directory exists"
    else
        print_fail "Logs directory missing"
    fi
else
    print_fail "Project directory missing: /root/ai-trading-sentinel"
fi

# Check 3: Python Dependencies
print_header "Python Dependencies Check"
if [ -d "/root/ai-trading-sentinel/venv" ]; then
    cd /root/ai-trading-sentinel
    source venv/bin/activate
    echo "Python version:"
    python --version
    echo ""
    echo "Checking key dependencies:"
    
    python -c "import flask; print('✓ Flask installed')" 2>/dev/null || echo "✗ Flask missing"
    python -c "import playwright; print('✓ Playwright installed')" 2>/dev/null || echo "✗ Playwright missing"
    python -c "import requests; print('✓ Requests installed')" 2>/dev/null || echo "✗ Requests missing"
    
    echo ""
    echo "Testing main.py syntax:"
    python -m py_compile main.py && print_check "main.py syntax OK" || print_fail "main.py syntax error"
else
    print_fail "Cannot check dependencies - venv missing"
fi

# Check 4: Port Availability
print_header "Port Availability Check"
echo "Checking port 5000:"
if netstat -tlnp | grep :5000 > /dev/null; then
    print_warning "Port 5000 is already in use:"
    netstat -tlnp | grep :5000
else
    print_check "Port 5000 is available"
fi

# Check 5: System Resources
print_header "System Resources Check"
echo "Memory usage:"
free -h
echo ""
echo "Disk usage:"
df -h /root
echo ""
echo "CPU load:"
uptime

# Check 6: Network Connectivity
print_header "Network Connectivity Check"
echo "Testing internet connectivity:"
if ping -c 1 google.com > /dev/null 2>&1; then
    print_check "Internet connectivity OK"
else
    print_fail "No internet connectivity"
fi

echo "Testing localhost connectivity:"
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    print_check "Web service responding on localhost:5000"
else
    print_warning "Web service not responding on localhost:5000"
fi

# Check 7: Firewall Status
print_header "Firewall Status Check"
echo "UFW status:"
ufw status || echo "UFW not installed or not configured"
echo ""
echo "iptables rules:"
iptables -L INPUT -n | head -10 || echo "Cannot check iptables"

# Check 8: Service File Validation
print_header "Service File Validation"
if [ -f "/etc/systemd/system/trae-bot.service" ]; then
    print_check "Service file exists"
    echo "Service file contents:"
    cat /etc/systemd/system/trae-bot.service
else
    print_fail "Service file missing: /etc/systemd/system/trae-bot.service"
fi

print_header "Diagnostic Summary"
echo "🔍 Diagnostic complete. Review the checks above to identify issues."
echo ""
echo "📋 Common fixes:"
echo "   1. Run: chmod +x /root/ai-trading-sentinel/fix_vps_service.sh"
echo "   2. Run: /root/ai-trading-sentinel/fix_vps_service.sh"
echo "   3. Check logs: journalctl -u trae-bot.service -f"
echo "   4. Manual start: cd /root/ai-trading-sentinel && source venv/bin/activate && python main.py"
echo ""
echo "🆘 For immediate help, run the fix script or check the troubleshooting guide."