#!/bin/bash
# 🚨 MODULE NOT FOUND FIX - Executable Script
# Diagnoses and fixes ModuleNotFoundError for backend_main

set -e

echo "🔍 AI Trading Sentinel - Module Fix Script"
echo "=========================================="

# Navigate to project directory
cd /root/ai-trading-sentinel

echo "\n📁 Step 1: Checking file existence..."
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la *.py | grep -E '(main|backend)' || echo "No main/backend Python files found"

echo "\n🔍 Step 2: Searching for backend_main.py..."
if [ -f "backend_main.py" ]; then
    echo "✅ backend_main.py found in root directory"
    ls -la backend_main.py
else
    echo "❌ backend_main.py NOT found in root directory"
    echo "Searching subdirectories..."
    find . -name "backend_main.py" -type f || echo "No backend_main.py found anywhere"
    echo "\nSearching for any main files..."
    find . -name "*main*.py" -type f || echo "No main files found"
fi

echo "\n🐍 Step 3: Testing Python environment..."
source venv/bin/activate
echo "Python path:"
python -c "import sys; print('\n'.join(sys.path))"

echo "\n🧪 Step 4: Testing module import..."
if python -c "import backend_main; print('✅ SUCCESS: backend_main module found')" 2>/dev/null; then
    echo "Module import successful"
else
    echo "❌ Module import failed"
    echo "Checking what Flask apps are available..."
    grep -r "app = Flask" . 2>/dev/null || echo "No Flask app definitions found"
    grep -r "Flask(__name__)" . 2>/dev/null || echo "No Flask(__name__) patterns found"
fi

echo "\n🔧 Step 5: Applying fix..."
if [ -f "backend_main.py" ]; then
    echo "✅ backend_main.py exists - fixing systemd service with PYTHONPATH"
    
    # Stop current service
    sudo systemctl stop trading-bot.service 2>/dev/null || echo "Service not running"
    
    # Create corrected service file
    sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
Environment=PYTHONPATH=/root/ai-trading-sentinel
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 backend_main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "✅ Service file updated with PYTHONPATH"
else
    echo "❌ backend_main.py missing - checking alternatives..."
    
    # Check for main.py with Flask app
    if [ -f "main.py" ] && grep -q "Flask" main.py; then
        echo "✅ Found Flask app in main.py - updating service"
        
        sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
Environment=PYTHONPATH=/root/ai-trading-sentinel
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        echo "✅ Service configured to use main:app"
    else
        echo "❌ No suitable Flask app found"
        echo "Available Python files:"
        ls -la *.py
        exit 1
    fi
fi

echo "\n🔄 Step 6: Restarting services..."
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot.service

echo "\n⏱️ Waiting for service to start..."
sleep 3

echo "\n✅ Step 7: Verification..."
echo "Service status:"
sudo systemctl status trading-bot.service --no-pager -l

echo "\n🌐 Testing API endpoint..."
if curl -s http://localhost:8080/api/status > /dev/null; then
    echo "✅ SUCCESS: API is responding!"
    curl http://localhost:8080/api/status
else
    echo "❌ API not responding - checking logs..."
    echo "Recent service logs:"
    sudo journalctl -u trading-bot.service --no-pager -n 20
fi

echo "\n🎉 Module fix script completed!"
echo "If issues persist, check the logs above for specific errors."