#!/bin/bash

# Deploy TradeBot Sentinel to VPS with Credentials
# Run this script in Termius or any SSH terminal connected to your VPS

set -e  # Exit on any error

echo "=== TradeBot Sentinel VPS Deployment ==="
echo "Starting deployment process..."

# VPS Configuration (Update these with your actual values)
VPS_HOST="your-vps-ip-or-domain.com"  # Replace with your actual VPS IP/domain
VPS_USER="root"                        # Replace with your VPS username
VPS_PORT="22"                          # Replace with your SSH port if different
DEPLOY_DIR="/root/AI-TRADING-BOT"

# Bulenox Credentials (Set these with your actual credentials)
export BULENOX_USERNAME="BX64883"  # Your actual Bulenox username
export BULENOX_PASSWORD="XujhMzFf6K"  # Your actual Bulenox password

echo "Deployment Configuration:"
echo "- VPS Host: $VPS_HOST"
echo "- VPS User: $VPS_USER"
echo "- Deploy Directory: $DEPLOY_DIR"
echo "- Bulenox Username: $BULENOX_USERNAME"
echo ""

# Function to run commands on VPS
run_remote() {
    echo "[REMOTE] $1"
    ssh -p $VPS_PORT $VPS_USER@$VPS_HOST "$1"
}

# Function to copy files to VPS
copy_to_vps() {
    echo "[COPY] $1 -> $VPS_HOST:$2"
    scp -P $VPS_PORT "$1" "$VPS_USER@$VPS_HOST:$2"
}

echo "Step 1: Creating deployment directory on VPS..."
run_remote "mkdir -p $DEPLOY_DIR"

echo "Step 2: Updating system packages..."
run_remote "apt update && apt upgrade -y"

echo "Step 3: Installing core dependencies..."
run_remote "apt install -y python3 python3-pip python3-venv curl wget git unzip"

echo "Step 4: Installing browser dependencies..."
run_remote "apt install -y libnss3 libatk1.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2"

echo "Step 5: Installing Node.js (for curlconverter)..."
run_remote "curl -fsSL https://deb.nodesource.com/setup_18.x | bash -"
run_remote "apt install -y nodejs"

echo "Step 6: Copying TradeBot Sentinel files..."
# Copy main script
copy_to_vps "login_bulenox_playwright.py" "$DEPLOY_DIR/"

# Copy requirements if exists
if [ -f "requirements.txt" ]; then
    copy_to_vps "requirements.txt" "$DEPLOY_DIR/"
fi

# Copy other essential files
for file in "*.py" "*.sh" "*.json"; do
    if ls $file 1> /dev/null 2>&1; then
        copy_to_vps "$file" "$DEPLOY_DIR/"
    fi
done

echo "Step 7: Setting up Python environment..."
run_remote "cd $DEPLOY_DIR && python3 -m venv venv"
run_remote "cd $DEPLOY_DIR && source venv/bin/activate && pip install --upgrade pip"

echo "Step 8: Installing Python dependencies..."
run_remote "cd $DEPLOY_DIR && source venv/bin/activate && pip install playwright requests curlconverter asyncio"

echo "Step 9: Installing Playwright browsers..."
run_remote "cd $DEPLOY_DIR && source venv/bin/activate && playwright install chromium"
run_remote "cd $DEPLOY_DIR && source venv/bin/activate && playwright install-deps"

echo "Step 10: Setting up environment variables..."
run_remote "cd $DEPLOY_DIR && echo 'export BULENOX_USERNAME=\"$BULENOX_USERNAME\"' > .env"
run_remote "cd $DEPLOY_DIR && echo 'export BULENOX_PASSWORD=\"$BULENOX_PASSWORD\"' >> .env"

echo "Step 11: Making scripts executable..."
run_remote "cd $DEPLOY_DIR && chmod +x *.py *.sh"

echo "Step 12: Testing the setup..."
run_remote "cd $DEPLOY_DIR && source venv/bin/activate && source .env && python3 --version"
run_remote "cd $DEPLOY_DIR && source venv/bin/activate && python3 -c 'import playwright; print(\"Playwright installed successfully\")'"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "To run TradeBot Sentinel on your VPS:"
echo "1. SSH into your VPS: ssh -p $VPS_PORT $VPS_USER@$VPS_HOST"
echo "2. Navigate to directory: cd $DEPLOY_DIR"
echo "3. Activate environment: source venv/bin/activate"
echo "4. Load credentials: source .env"
echo "5. Run the bot: python3 login_bulenox_playwright.py"
echo ""
echo "For visible mode (debugging): python3 login_bulenox_playwright.py --visible"
echo ""
echo "Log files will be created in: $DEPLOY_DIR/tradebot_sentinel.log"
echo "Screenshots will be saved in: $DEPLOY_DIR/screenshot_*.png"
echo "Trade requests will be saved as: $DEPLOY_DIR/trade.sh and $DEPLOY_DIR/trade_request_full.py"
echo ""
echo "=== IMPORTANT SECURITY NOTES ==="
echo "1. Replace placeholder credentials with your actual Bulenox login details"
echo "2. Ensure your VPS has proper firewall configuration"
echo "3. Consider using SSH key authentication instead of passwords"
echo "4. Regularly update your VPS system packages"
echo ""

# Instructions for Termius
echo "=== TERMIUS USAGE INSTRUCTIONS ==="
echo ""
echo "To run this script in Termius:"
echo "1. Open Termius and connect to your VPS"
echo "2. Upload this script to your VPS: scp deploy_with_credentials.sh user@vps:/tmp/"
echo "3. SSH into your VPS through Termius"
echo "4. Make script executable: chmod +x /tmp/deploy_with_credentials.sh"
echo "5. Edit credentials: nano /tmp/deploy_with_credentials.sh"
echo "6. Run the script: /tmp/deploy_with_credentials.sh"
echo ""
echo "Alternative - Direct execution in Termius:"
echo "1. Copy the commands from this script"
echo "2. Paste and run them one by one in your Termius terminal"
echo "3. This gives you more control over each step"
echo ""
echo "=== END OF DEPLOYMENT SCRIPT ==="