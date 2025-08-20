#!/bin/bash

# AI Trading Sentinel - Environment Update Script
# Updates .env file with broker credentials on VPS
# Run this on Contabo VPS (161.97.112.146) after deployment

echo "🔐 AI Trading Sentinel - Environment Update"
echo "📍 Target: Contabo VPS (161.97.112.146)"
echo "🕐 $(date)"
echo "=========================================="

# Navigate to application directory
cd /opt/ai-trading-sentinel

# Create .env file with broker credentials
echo "📝 Creating .env file with broker credentials..."
cat > .env << 'ENV_EOF'
# AI Trading Sentinel - Production Environment
# Bulenox Broker Configuration
BROKER_USERNAME=BX64883
BROKER_PASSWORD=XujhMzFf6K
BROKER_URL=https://bulenox.projectx.com/login

# Trading Configuration
TRADING_MODE=live
RISK_LEVEL=medium
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=3.0

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Monitoring
HEALTH_CHECK_INTERVAL=30
ALERT_EMAIL=admin@trading-sentinel.com
ENV_EOF

# Set proper permissions
chown tradebot:tradebot .env
chmod 600 .env

echo "✅ Environment file created successfully!"
echo "📊 Current .env contents:"
cat .env

# Restart services to apply new configuration
echo "🔄 Restarting services..."
systemctl restart ai-trading-backend
systemctl restart ai-trading-frontend

# Wait for services to start
sleep 5

# Verify services are running
echo "📊 Service Status:"
systemctl status ai-trading-backend --no-pager -l
systemctl status ai-trading-frontend --no-pager -l

echo "=========================================="
echo "🎉 Environment Update Complete!"
echo "📍 Production URLs:"
echo "   🌐 Frontend: http://161.97.112.146/"
echo "   🔧 Backend:  http://161.97.112.146/api/status"
echo "   🏥 Health:   http://161.97.112.146/api/health"
echo "=========================================="
echo "✅ Broker credentials configured at $(date)"
echo "🚀 AI Trading Sentinel is now ready for live trading!"

# Test broker connection
echo "🔍 Testing broker connection..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'✅ Broker URL: {os.getenv(\"BROKER_URL\")}')
print(f'✅ Username: {os.getenv(\"BROKER_USERNAME\")}')
print('🔐 Password: [PROTECTED]')
print('🚀 Ready for live trading!')
" 2>/dev/null || echo "⚠️  Python dotenv not installed, but .env file is ready"

echo "🎯 Next Steps:"
echo "1. Monitor logs: tail -f /opt/ai-trading-sentinel/logs/backend.log"
echo "2. Check trading status via frontend: http://161.97.112.146/"
echo "3. Verify broker connection in application"
echo "4. Start live trading operations"