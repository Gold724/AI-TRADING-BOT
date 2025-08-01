#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "📦 Updating system..."
apt update && apt upgrade -y

echo "🐍 Installing Python, pip, git, tmux..."
apt install -y python3 python3-pip git unzip curl tmux

echo "🌐 Installing Google Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb || apt --fix-broken install -y

echo "🧩 Installing ChromeDriver (matching version)..."
CHROME_VERSION=$(google-chrome --version | grep -oP '[0-9.]+' | head -1)
CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | grep -A 20 "$CHROME_VERSION" | grep "linux64" | grep -oP 'https://.*?zip' | head -1)

mkdir -p /usr/local/bin/chromedriver
cd /usr/local/bin/chromedriver
curl -Lo chromedriver.zip "$CHROMEDRIVER_VERSION"
unzip chromedriver.zip
chmod +x chromedriver
ln -s /usr/local/bin/chromedriver/chromedriver /usr/bin/chromedriver
cd ~

echo "✅ Chrome & ChromeDriver installed"

echo "📁 Setting up project directory..."
mkdir -p /root/ai-trading-sentinel

echo "📦 Installing additional Python packages..."
pip3 install selenium requests python-dotenv websocket-client slackclient flask flask-cors

echo "🔧 Setting up Chrome profile directory..."
mkdir -p /root/.config/google-chrome/Default

echo "⏱️ Installing tmux for persistent sessions..."
if ! command -v tmux &> /dev/null; then
    apt install -y tmux
fi

echo "✅ Setup complete!"
echo "The deployment script will handle the rest of the setup process."
echo "Your AI Trading Sentinel will be ready to run after deployment."
echo ""
echo "To manually start the system after deployment:"
echo "cd /root/ai-trading-sentinel"
echo "python3 heartbeat.py"
echo ""
echo "Or attach to the tmux session created during deployment:"
echo "tmux attach -t trading_sentinel"