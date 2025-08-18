
#!/bin/bash
# 🤖 TradeBot Sentinel - VPS Setup Script

set -e

echo "🚀 Setting up TradeBot Sentinel on Contabo VPS..."

# Update system
echo "📦 Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y wget curl unzip xvfb
sudo apt install -y fonts-liberation libasound2 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libu2f-udev libvulkan1

# Install Google Chrome
echo "🌐 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update -y
sudo apt install -y google-chrome-stable

# Install ChromeDriver
echo "🚗 Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1)
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
sudo unzip -o /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip

# Create project directory
echo "📁 Setting up project directory..."
mkdir -p /home/tradebot/ai-trading-sentinel
cd /home/tradebot/ai-trading-sentinel

# Create Python virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install playwright selenium requests flask python-dotenv curlconverter
pip install pandas numpy matplotlib seaborn
pip install asyncio aiohttp websockets
pip install schedule APScheduler
pip install cryptography jwt
pip install psutil

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Create log directories
echo "📁 Creating log directories..."
mkdir -p logs/curls logs/json logs/screenshots
mkdir -p data/backtest data/signals
chmod 755 logs logs/curls logs/json logs/screenshots
chmod 755 data data/backtest data/signals

# Test Chrome installation
echo "🔍 Testing Chrome installation..."
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 2

python3 -c "
import os
os.environ['DISPLAY'] = ':99'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

try:
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.google.com')
    title = driver.title
    driver.quit()
    print(f'✅ Chrome test successful. Page title: {title}')
except Exception as e:
    print(f'❌ Chrome test failed: {str(e)}')
    exit(1)
"

kill $XVFB_PID 2>/dev/null || true

echo "✅ TradeBot Sentinel setup completed successfully!"
echo "📁 Project directory: /home/tradebot/ai-trading-sentinel"
echo "🔧 Virtual environment: /home/tradebot/ai-trading-sentinel/venv"
echo "📋 Next steps:"
echo "  1. Upload your ai-trading-sentinel files to /home/tradebot/ai-trading-sentinel/"
echo "  2. Copy the .env file to the project directory"
echo "  3. Activate virtual environment: source venv/bin/activate"
echo "  4. Run the main script: python main.py"
