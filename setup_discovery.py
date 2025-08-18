#!/usr/bin/env python3
"""
TradeBot Sentinel - Trade Endpoint Discovery Setup
Automatically installs dependencies and initializes Playwright browsers.

Usage:
    python setup_discovery.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_directories():
    """Create required directories."""
    directories = [
        'logs/curls',
        'logs/json', 
        'logs/screenshots',
        'logs/endpoints'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Directory created: {directory}")
    
    return True

def setup_environment_template():
    """Create environment template file."""
    env_template = """
# TradeBot Sentinel - Environment Variables
# Copy this to .env and fill in your credentials

# Bulenox Trading Platform Credentials
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here

# Optional: Trading Configuration
DEFAULT_SYMBOL=/GC
DEFAULT_AMOUNT=1
TRADE_MODE=ORDER

# Optional: Discovery Configuration
HEADLESS_MODE=true
SCREENSHOT_ENABLED=true
VERBOSE_LOGGING=true
"""
    
    env_file = Path('.env.template')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ Environment template created: .env.template")
        print("   Please copy to .env and configure your credentials")
    else:
        print("ℹ️ Environment template already exists")
    
    return True

def main():
    """Main setup process."""
    print("🎯 TradeBot Sentinel - Trade Endpoint Discovery Setup")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install Python dependencies
    if not run_command(
        f"{sys.executable} -m pip install -r requirements_discovery.txt",
        "Installing Python dependencies"
    ):
        print("⚠️ Dependency installation failed, trying alternative...")
        if not run_command(
            f"{sys.executable} -m pip install playwright requests curlconverter pathlib2 psutil",
            "Installing core dependencies"
        ):
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Install Playwright browsers
    if not run_command(
        f"{sys.executable} -m playwright install chromium",
        "Installing Playwright Chromium browser"
    ):
        print("❌ Failed to install Playwright browsers")
        sys.exit(1)
    
    # Install system dependencies for Playwright
    if not run_command(
        f"{sys.executable} -m playwright install-deps",
        "Installing Playwright system dependencies"
    ):
        print("⚠️ System dependencies installation failed (may require admin rights)")
        print("   The script may still work, but some features might be limited")
    
    # Setup environment template
    if not setup_environment_template():
        sys.exit(1)
    
    # Final verification
    print("\n🔍 Verifying installation...")
    
    try:
        import playwright
        print("✅ Playwright imported successfully")
    except ImportError:
        print("❌ Playwright import failed")
        sys.exit(1)
    
    try:
        import requests
        print("✅ Requests imported successfully")
    except ImportError:
        print("❌ Requests import failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("="*60)
    print("📋 Next Steps:")
    print("1. Copy .env.template to .env")
    print("2. Configure your Bulenox credentials in .env")
    print("3. Run: python trade_endpoint_discovery.py --visible")
    print("4. Check logs/curls/ for captured endpoints")
    print("\n🚀 Ready for Trade Endpoint Discovery!")

if __name__ == '__main__':
    main()