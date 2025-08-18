#!/bin/bash
set -e

echo 'Starting AI Trading Sentinel deployment...'

# Update system
echo 'Updating system packages...'
apt update
apt upgrade -y

# Install Docker
echo 'Installing Docker...'
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
echo 'Installing Docker Compose...'
curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-'$(uname -s)'-'$(uname -m) -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
echo 'Cloning repository...'
cd /opt
if [ -d 'ai-trading-sentinel' ]; then
    rm -rf ai-trading-sentinel
fi
git clone https://github.com/Gold724/AI-TRADING-BOT.git ai-trading-sentinel
cd ai-trading-sentinel

# Set up environment
echo 'Setting up environment...'
if [ -f .env.example ]; then
    cp .env.example .env
else
    echo '# AI Trading Sentinel Environment' > .env
fi
echo 'ENVIRONMENT=production' >> .env
echo 'HEADLESS=true' >> .env
echo 'AUTO_EXECUTION_ENABLED=true' >> .env

# Build and start containers
echo 'Building and starting containers...'
docker-compose up -d --build

# Set up firewall
echo 'Configuring firewall...'
ufw allow 22/tcp
ufw allow 3000/tcp
ufw allow 8080/tcp
ufw --force enable

# Create systemd service file
echo 'Creating systemd service...'
cat > /etc/systemd/system/ai-trading-sentinel.service << 'SERVICEEOF'
[Unit]
Description=AI Trading Sentinel
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ai-trading-sentinel
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl enable ai-trading-sentinel.service
systemctl start ai-trading-sentinel.service

echo 'AI Trading Sentinel deployed successfully!'
echo 'Access URLs:'
echo '  Dashboard: http://'$(curl -s ifconfig.me)':3000'
echo '  Trading Interface: http://'$(curl -s ifconfig.me)':8080'
echo '  SSH: ssh root@'$(curl -s ifconfig.me)
