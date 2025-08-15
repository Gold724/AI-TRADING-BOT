#!/bin/bash
# trae.sh - Startup script for AI Trading Sentinel

# Display banner
echo "========================================="
echo "   AI Trading Sentinel - Bulenox Edition   "
echo "========================================="
echo "Version: v0.2-beta"
echo ""

# Check if running as root on Linux
if [ "$(uname)" = "Linux" ] && [ "$(id -u)" -ne 0 ]; then
    echo "⚠️  Warning: Not running as root. Some features may not work properly."
fi

# Create necessary directories
mkdir -p logs/screenshots

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating a template..."
    cat > .env << EOL
# Bulenox Credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password

# Chrome Profile Settings
BULENOX_PROFILE_PATH=/root/.config/google-chrome
BULENOX_PROFILE_NAME=Default

# API Security
API_KEY=your_secure_api_key

# Application Settings
DEBUG=False
AUTO_LOGIN=True
PORT=5000

# Optional: Dreamer Mode (simulation only)
DREAMER_MODE=False
EOL
    echo "✅ Created .env template. Please edit it with your credentials."
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3."
    exit 1
fi

# Start Xvfb for headless browser
if [ -n "$DISPLAY" ]; then
    echo "🖥️ Starting Xvfb display server..."
    Xvfb $DISPLAY -screen 0 1920x1080x24 &
    sleep 1
    echo "✅ Xvfb started on $DISPLAY"
fi

# Check for required packages
echo "🔍 Checking for required packages..."
python3 -m pip install -r requirements.txt

# Start the application
echo "🚀 Starting AI Trading Sentinel..."
python3 bulenox_trade_sentinel.py