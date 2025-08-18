
#!/bin/bash
# 🚀 Quick Deployment Script for TradeBot Sentinel

set -e

VPS_IP="$1"
SSH_USER="${2:-root}"

if [ -z "$VPS_IP" ]; then
    echo "❌ Usage: $0 <VPS_IP> [SSH_USER]"
    echo "   Example: $0 192.168.1.100 root"
    exit 1
fi

echo "🚀 Deploying TradeBot Sentinel to $VPS_IP..."

# Transfer files
echo "📦 Transferring files..."
rsync -avz --progress --exclude='venv/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='.git/' ../ai-trading-sentinel/ $SSH_USER@$VPS_IP:/home/tradebot/ai-trading-sentinel/

# Transfer deployment files
echo "📋 Transferring deployment configuration..."
scp .env $SSH_USER@$VPS_IP:/home/tradebot/ai-trading-sentinel/
scp setup_vps.sh $SSH_USER@$VPS_IP:/home/tradebot/ai-trading-sentinel/
scp tradebot-sentinel.service $SSH_USER@$VPS_IP:/tmp/

# Execute setup on VPS
echo "⚙️ Setting up VPS environment..."
ssh $SSH_USER@$VPS_IP "cd /home/tradebot/ai-trading-sentinel && chmod +x setup_vps.sh && ./setup_vps.sh"

# Install systemd service
echo "🚀 Installing systemd service..."
ssh $SSH_USER@$VPS_IP "sudo cp /tmp/tradebot-sentinel.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable tradebot-sentinel.service"

echo "✅ Deployment completed successfully!"
echo "🎯 To start the service: ssh $SSH_USER@$VPS_IP 'sudo systemctl start tradebot-sentinel.service'"
echo "📊 To check status: ssh $SSH_USER@$VPS_IP 'sudo systemctl status tradebot-sentinel.service'"
echo "📋 To view logs: ssh $SSH_USER@$VPS_IP 'tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot.log'"
