#!/bin/bash
# AI Trading Sentinel - VPS Production Deployment Script
# Target: Contabo VPS (161.97.112.146)
# OS: Ubuntu 22.04/24.04 LTS
# Access: VNC Remote Desktop Connection

set -e

echo "🚀 AI Trading Sentinel - VPS Production Deployment"
echo "=================================================="
echo "📅 Started at: $(date)"
echo "🖥️  Target VPS: 161.97.112.146"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/ai-trading-sentinel"
SERVICE_USER="tradebot"
DOMAIN="161.97.112.146"
FRONTEND_PORT="3000"
BACKEND_PORT="5000"

echo -e "${BLUE}Step 1: System Preparation${NC}"
echo "================================"

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    curl \
    wget \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

echo -e "${GREEN}✅ System packages installed${NC}"

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.10+
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Docker (optional for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

echo -e "${GREEN}✅ Runtime environments installed${NC}"

echo -e "${BLUE}Step 2: User and Directory Setup${NC}"
echo "===================================="

# Create service user
sudo useradd -r -s /bin/bash -d /opt/ai-trading-sentinel $SERVICE_USER || true
sudo mkdir -p $PROJECT_DIR
sudo chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

echo -e "${GREEN}✅ Service user and directories created${NC}"

echo -e "${BLUE}Step 3: Application Deployment${NC}"
echo "=================================="

# Clone repository (assuming GitHub access is configured)
cd /opt
sudo -u $SERVICE_USER git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git || \
sudo -u $SERVICE_USER git pull origin main

cd $PROJECT_DIR

# Set up Python virtual environment
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt

# Install Playwright browsers
sudo -u $SERVICE_USER ./venv/bin/playwright install
sudo -u $SERVICE_USER ./venv/bin/playwright install-deps

echo -e "${GREEN}✅ Python environment configured${NC}"

# Install Node.js dependencies
cd $PROJECT_DIR/frontend
sudo -u $SERVICE_USER npm install
sudo -u $SERVICE_USER npm run build

echo -e "${GREEN}✅ Frontend built${NC}"

echo -e "${BLUE}Step 4: Environment Configuration${NC}"
echo "===================================="

# Copy environment file
sudo -u $SERVICE_USER cp .env.production.template .env

# Generate secure keys
sudo -u $SERVICE_USER python3 generate_keys.py

echo -e "${YELLOW}⚠️  IMPORTANT: Configure .env file with:${NC}"
echo "   - Bulenox credentials"
echo "   - Email settings"
echo "   - VPS IP address"
echo "   - Security keys"

echo -e "${GREEN}✅ Environment template created${NC}"

echo ""
echo -e "${BLUE}🎯 Next Manual Steps:${NC}"
echo "1. Configure .env file with production credentials"
echo "2. Set up Nginx reverse proxy"
echo "3. Configure systemd services"
echo "4. Enable SSL certificates"
echo ""
echo -e "${GREEN}Deployment script completed!${NC}"