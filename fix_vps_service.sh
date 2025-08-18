#!/bin/bash

# ⚡ VPS Service Fix Script - AI Trading Sentinel
# Fixes systemd service configuration and deployment issues

set -e

echo "🔧 AI Trading Sentinel - VPS Service Fix"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Step 1: Stop existing service
print_status "Stopping existing trae-bot service..."
systemctl stop trae-bot.service 2>/dev/null || true
systemctl disable trae-bot.service 2>/dev/null || true

# Step 2: Create project directory
print_status "Setting up project directory..."
mkdir -p /root/ai-trading-sentinel
cd /root/ai-trading-sentinel

# Step 3: Clone or update repository
if [ -d ".git" ]; then
    print_status "Updating existing repository..."
    git pull origin main
else
    print_status "Cloning repository..."
    git clone https://github.com/your-username/ai-trading-sentinel.git .
fi

# Step 4: Create virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 5: Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Install Playwright browsers
print_status "Installing Playwright browsers..."
playwright install
playwright install-deps

# Step 7: Create logs directory
print_status "Creating logs directory..."
mkdir -p logs
touch logs/trae.log
chmod 644 logs/trae.log

# Step 8: Copy and install systemd service
print_status "Installing systemd service..."
cp trae-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable trae-bot.service

# Step 9: Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'
# AI Trading Sentinel Configuration
BROKER_USERNAME=your_username
BROKER_PASSWORD=your_password
BROKER_URL=https://your-broker.com

# Email Notifications
EMAIL_NOTIFICATIONS=true
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Trading Configuration
TRADE_AMOUNT=100
RISK_PERCENTAGE=2
MAX_DAILY_TRADES=10

# Environment
ENVIRONMENT=production
DEBUG=false
EOF
    print_warning "Please edit .env file with your actual credentials"
fi

# Step 10: Set proper permissions
print_status "Setting file permissions..."
chown -R root:root /root/ai-trading-sentinel
chmod +x main.py
chmod 600 .env

# Step 11: Test service configuration
print_status "Testing service configuration..."
systemctl start trae-bot.service
sleep 5

if systemctl is-active --quiet trae-bot.service; then
    print_success "Service started successfully!"
    systemctl status trae-bot.service --no-pager -l
else
    print_error "Service failed to start. Checking logs..."
    journalctl -u trae-bot.service --no-pager -l -n 20
    exit 1
fi

# Step 12: Start Flask backend
print_status "Starting Flask backend..."
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
echo $! > backend.pid

# Step 13: Test web interface
print_status "Testing web interface..."
sleep 3
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    print_success "Web interface is accessible at http://localhost:5000"
else
    print_warning "Web interface may not be ready yet. Check logs/backend.log"
fi

print_success "VPS Service Fix Complete!"
echo ""
echo "📊 Service Status:"
systemctl status trae-bot.service --no-pager -l
echo ""
echo "🌐 Web Interface: http://$(curl -s ifconfig.me):5000"
echo "📋 Logs: tail -f /root/ai-trading-sentinel/logs/trae.log"
echo "🔧 Service Control: systemctl [start|stop|restart] trae-bot.service"
echo ""
print_success "AI Trading Sentinel is now deployed and running!"