#!/bin/bash

# TRAE VPS Diagnostic Script
# Quickly diagnose VPS deployment issues

echo "🔍 TRAE VPS Diagnostic Report"
echo "================================"

# Check if we're in the right directory
echo "📁 Current Directory: $(pwd)"
if [ -f "backend/main.py" ]; then
    echo "✅ Project files found"
else
    echo "❌ Project files not found - run from ai-trading-sentinel directory"
fi

# Check Python and virtual environment
echo "\n🐍 Python Environment:"
which python3
python3 --version

if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    source venv/bin/activate
    echo "📦 Installed packages:"
    pip list | grep -E "(flask|requests|python-dotenv)"
else
    echo "❌ Virtual environment not found"
fi

# Check if Flask backend is running
echo "\n🌐 Network Status:"
echo "Checking if port 5000 is in use:"
netstat -tlnp | grep :5000 || echo "❌ Port 5000 not in use"

# Check systemd service
echo "\n🔧 Service Status:"
if systemctl is-active --quiet trae-backend; then
    echo "✅ trae-backend service is running"
    systemctl status trae-backend --no-pager -l
else
    echo "❌ trae-backend service not running"
    echo "Recent service logs:"
    journalctl -u trae-backend --no-pager -n 10
fi

# Check firewall
echo "\n🔥 Firewall Status:"
sudo ufw status

# Test local API
echo "\n🧪 API Test:"
echo "Testing local API..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health || echo "❌ Local API test failed"

# Check external IP
echo "\n🌍 External Access:"
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "External IP: $EXTERNAL_IP"
echo "Test URL: http://$EXTERNAL_IP:5000/api/health"

echo "\n📋 Quick Fixes:"
echo "1. Start service: sudo systemctl start trae-backend"
echo "2. Check logs: sudo journalctl -u trae-backend -f"
echo "3. Restart service: sudo systemctl restart trae-backend"
echo "4. Manual start: cd ~/ai-trading-sentinel && source venv/bin/activate && python backend/main.py"