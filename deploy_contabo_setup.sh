#!/bin/bash

# Contabo VPS Setup Script for AI Trading Sentinel
# This script sets up the environment on a fresh Ubuntu 22.04 installation

set -e

# Color codes for terminal output
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}=== AI Trading Sentinel - Contabo VPS Setup ===${NC}"
echo -e "${YELLOW}This script will set up your Ubuntu 22.04 server for running the trading bot${NC}"
echo

# Update system packages
echo -e "${GREEN}[1/8] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo -e "${GREEN}[2/8] Installing Python and dependencies...${NC}"
sudo apt install -y python3 python3-pip python3-venv git

# Install Chrome and ChromeDriver
echo -e "${GREEN}[3/8] Installing Chrome and ChromeDriver...${NC}"
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
echo -e "${YELLOW}Detected Chrome version: $CHROME_VERSION${NC}"
wget -q "https://chromedriver.storage.googleapis.com/$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

# Create project directory
echo -e "${GREEN}[4/8] Setting up project directory...${NC}"
mkdir -p ~/ai-trading-sentinel
cd ~/ai-trading-sentinel

# Create Python virtual environment
echo -e "${GREEN}[5/8] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install project requirements
echo -e "${GREEN}[6/8] Installing project requirements...${NC}"
pip install --upgrade pip
pip install flask selenium requests paramiko python-dotenv

# Setup environment variables
echo -e "${GREEN}[7/8] Setting up environment variables...${NC}"
if [ -f .env ]; then
    echo -e "${YELLOW}Found existing .env file. Keeping it.${NC}"
else
    echo -e "${YELLOW}Creating .env file from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit the .env file with your actual credentials${NC}"
    echo -e "${YELLOW}Run: nano .env${NC}"
fi

# Create systemd service for auto-start
echo -e "${GREEN}[8/8] Creating systemd service for auto-start...${NC}"
cat > ~/ai-trading-sentinel.service << EOL
[Unit]
Description=AI Trading Sentinel Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/ai-trading-sentinel
Environment="PATH=/home/$USER/ai-trading-sentinel/venv/bin"
ExecStart=/home/$USER/ai-trading-sentinel/venv/bin/python cloud_main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=ai-trading-sentinel

[Install]
WantedBy=multi-user.target
EOL

sudo mv ~/ai-trading-sentinel.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "${YELLOW}To start the trading bot service:${NC}"
echo -e "  sudo systemctl start ai-trading-sentinel"
echo -e "${YELLOW}To enable auto-start on boot:${NC}"
echo -e "  sudo systemctl enable ai-trading-sentinel"
echo -e "${YELLOW}To check status:${NC}"
echo -e "  sudo systemctl status ai-trading-sentinel"
echo -e "${YELLOW}To view logs:${NC}"
echo -e "  sudo journalctl -u ai-trading-sentinel -f"
echo
echo -e "${GREEN}Your AI Trading Sentinel is ready to deploy!${NC}"