#!/bin/bash
# 🔧 BACKEND SERVICE FIX - Complete Solution
# Fixes Flask app reference and auth module import issues

set -e

echo "🔧 AI Trading Sentinel - Complete Backend Fix"
echo "============================================="

# Navigate to project directory
cd /root/ai-trading-sentinel

echo "\n📍 Step 1: Verifying Flask app location..."
if [ -f "backend/main.py" ] && grep -q "app = Flask" backend/main.py; then
    echo "✅ Flask app confirmed in backend/main.py"
else
    echo "❌ Flask app not found in backend/main.py"
    exit 1
fi

echo "\n📦 Step 2: Creating Python package structure..."
if [ ! -f "backend/__init__.py" ]; then
    echo "# Backend package initialization" > backend/__init__.py
    echo "✅ Created backend/__init__.py"
else
    echo "✅ backend/__init__.py already exists"
fi

echo "\n🔧 Step 3: Fixing auth import in backend/main.py..."
if grep -q "from auth import" backend/main.py; then
    sed -i 's/from auth import/from .auth import/g' backend/main.py
    echo "✅ Fixed auth import to use relative import"
else
    echo "✅ Auth import already correct"
fi

echo "\n🧪 Step 4: Testing module import..."
source venv/bin/activate
if python -c "from backend.main import app; print('✅ SUCCESS: backend.main:app accessible')" 2>/dev/null; then
    echo "Module import successful"
else
    echo "❌ Module import failed - checking details..."
    python -c "from backend.main import app; print('✅ SUCCESS: backend.main:app accessible')" || true
    echo "Continuing with service setup..."
fi

echo "\n🛑 Step 5: Stopping current service..."
sudo systemctl stop trading-bot.service 2>/dev/null || echo "Service not running"

echo "\n📝 Step 6: Creating corrected service file..."
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<SERVICEEOF
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
Environment=PYTHONPATH=/root/ai-trading-sentinel
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 backend.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "✅ Service file updated with backend.main:app"

echo "\n🔄 Step 7: Restarting services..."
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot.service

echo "\n⏱️ Waiting for service to start..."
sleep 5

echo "\n✅ Step 8: Verification..."
echo "Service status:"
sudo systemctl status trading-bot.service --no-pager -l

echo "\n🌐 Testing API endpoints..."
echo "Testing root endpoint:"
if curl -s http://localhost:8080/ > /dev/null; then
    echo "✅ Root endpoint responding"
    curl -s http://localhost:8080/ | head -3
else
    echo "❌ Root endpoint not responding"
fi

echo "\nTesting API health:"
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo "✅ API health endpoint responding"
    curl -s http://localhost:8080/api/health
else
    echo "❌ API health endpoint not responding"
fi

echo "\n🎉 Complete backend fix completed!"
echo "\n📊 Summary:"
echo "- Flask app: backend/main.py"
echo "- Service reference: backend.main:app"
echo "- Python package: backend/__init__.py created"
echo "- Auth import: Fixed to relative import"
echo "- Port: 8080"
echo "- Status: $(sudo systemctl is-active trading-bot.service)"

if sudo systemctl is-active trading-bot.service | grep -q "active"; then
    echo "\n✅ SUCCESS: Backend service is running!"
else
    echo "\n❌ ISSUE: Service not active - check logs:"
    echo "sudo journalctl -u trading-bot.service --no-pager -n 10"
fi
