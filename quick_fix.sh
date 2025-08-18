#!/bin/bash

# TRAE VPS Quick Fix - One Command Solution
# Copy and paste this entire block into your VPS terminal

echo "🚀 TRAE VPS Quick Fix Starting..."

# Navigate to project directory
cd ~/ai-trading-sentinel || { echo "❌ Project directory not found"; exit 1; }

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 5000
sudo ufw --force enable

# Create and activate virtual environment
echo "📦 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install flask flask-cors python-dotenv requests

# Kill any existing Python processes
echo "🛑 Stopping existing processes..."
sudo pkill -f "python.*main.py" || true

# Start backend in background
echo "🌐 Starting Flask backend..."
nohup python backend/main.py > backend.log 2>&1 &

# Wait for startup
sleep 5

# Test API
echo "🧪 Testing API..."
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Backend is running successfully!"
    echo "📡 External URL: http://$(curl -s ifconfig.me):5000"
    echo "🔍 Test deployment:"
    echo 'curl -X POST "http://5.189.145.177:5000/api/deploy" -H "Content-Type: application/json" -H "Authorization: Bearer trae_deploy_2024_secure_token_tesla369" -d '"'"'{"strategy":"Tesla_369","mode":"safe","config":{"max_contracts":1,"daily_profit_target":535.71,"tesla_mode":true}}'"'"''
else
    echo "❌ Backend failed to start. Check logs:"
    tail -20 backend.log
fi

echo "🎯 Quick fix complete!"