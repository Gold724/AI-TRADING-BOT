#!/bin/bash
# Fix Ubuntu Dependencies for TradeBot Sentinel VPS Setup
# Addresses package installation errors for libx264 and libicu73

echo "🔧 Fixing Ubuntu Dependencies for TradeBot Sentinel"
echo "================================================"

# Update package lists
echo "📦 Updating package lists..."
apt update -y

# Install core dependencies (excluding problematic packages)
echo "📦 Installing core dependencies..."
apt install -y \
    libnss3 \
    libatk1.0-0t64 \
    libatk-bridge2.0-0t64 \
    libcups2t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libgtk-3-0t64 \
    libasound2t64 \
    libffi8 \
    fonts-liberation \
    wget \
    curl \
    unzip \
    xvfb

# Handle libx264 alternative
echo "📦 Installing media libraries..."
apt install -y libx264-164 || apt install -y libx264-dev || echo "⚠️ libx264 not available, skipping"

# Handle libicu alternative (check available version)
echo "📦 Installing ICU libraries..."
apt install -y libicu74 || apt install -y libicu72 || apt install -y libicu-dev || echo "⚠️ libicu not available, skipping"

# Install additional Playwright dependencies
echo "📦 Installing additional browser dependencies..."
apt install -y \
    libxss1 \
    libgconf-2-4 \
    libxtst6 \
    libxrandr2 \
    libasound2-dev \
    libpangocairo-1.0-0 \
    libatk1.0-dev \
    libcairo-gobject2 \
    libgtk-3-dev \
    libgdk-pixbuf2.0-dev

# Install Python and pip if not available
echo "🐍 Ensuring Python environment..."
apt install -y python3 python3-pip python3-venv

# Install Node.js for additional tools (optional)
echo "📦 Installing Node.js..."
apt install -y nodejs npm || echo "⚠️ Node.js installation failed, continuing"

echo ""
echo "✅ Ubuntu dependencies installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Install Python requirements: pip3 install -r requirements.txt"
echo "2. Install Playwright browsers: python3 -m playwright install"
echo "3. Install Playwright system dependencies: python3 -m playwright install-deps"
echo "4. Set environment variables:"
echo "   export BULENOX_USERNAME='your_username'"
echo "   export BULENOX_PASSWORD='your_password'"
echo "5. Test TradeBot Sentinel: python3 login_bulenox_playwright.py --headless"
echo ""
echo "🎉 TradeBot Sentinel VPS is ready for deployment!"