#!/bin/bash
# AI Trading Sentinel - Local Development Deployment
# This script runs without sudo privileges for local testing

set -e

echo "🚀 AI Trading Sentinel - Local Deployment"
echo "==========================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run from project root."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Set up environment variables
echo "⚙️ Setting up environment..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📋 Created .env from .env.example"
    else
        cat > .env << EOF
# AI Trading Sentinel Environment
ENVIRONMENT=development
HEADLESS=false
AUTO_EXECUTION_ENABLED=false
DEBUG=true
LOG_LEVEL=INFO

# Browser Settings
BROWSER_TIMEOUT=30
PAGE_LOAD_TIMEOUT=30

# Trading Settings
RISK_MANAGEMENT=true
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENTAGE=2.0

# Logging
LOG_FILE=logs/trading.log
LOG_ROTATION=daily
EOF
        echo "📋 Created default .env file"
    fi
else
    echo "✅ .env file already exists"
fi

# Create logs directory
mkdir -p logs
mkdir -p data/accounts
mkdir -p data/signals

# Test browser setup
echo "🌐 Testing browser configuration..."
python3 -c "from browser_config import setup_browser; print('✅ Browser setup OK')" || echo "⚠️ Browser setup needs attention"

# Run basic health check
echo "🏥 Running health check..."
python3 -c "import main; print('✅ Main module imports OK')" || echo "⚠️ Main module has issues"

echo ""
echo "✅ Local deployment complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file with your broker credentials"
echo "2. Test browser: python3 test_browser.py"
echo "3. Run bot: python3 main.py"
echo "4. Monitor logs: tail -f logs/trading.log"
echo ""
echo "🔧 Development Commands:"
echo "• Start bot: python3 main.py"
echo "• Run tests: python3 -m pytest test/"
echo "• Check health: python3 health_check.py"
echo "• View logs: tail -f logs/trading.log"
echo ""
echo "🌐 For cloud deployment, use: ./deploy_cloud.sh"