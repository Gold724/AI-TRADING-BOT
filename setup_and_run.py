#!/usr/bin/env python3
"""
TradeBot Sentinel Setup and Run Script

This script helps users set up their environment and run the TradeBot Sentinel.
It checks for required dependencies, environment variables, and provides
guidance for first-time setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['playwright', 'requests', 'curlconverter']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def install_playwright_browsers():
    """Install Playwright browsers if needed"""
    try:
        print("🌐 Installing Playwright browsers...")
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        print("✅ Playwright browsers installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Playwright browsers")
        print("Please run manually: playwright install chromium")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    env_template = Path('.env.template')
    
    if not env_file.exists():
        if env_template.exists():
            print("❌ .env file not found")
            print("📋 Please copy .env.template to .env and fill in your credentials:")
            print("   cp .env.template .env")
            print("   # Then edit .env with your actual credentials")
        else:
            print("❌ Neither .env nor .env.template found")
            create_env_template()
        return False
    
    # Check if required variables are set
    required_vars = ['BULENOX_USERNAME', 'BULENOX_PASSWORD']
    missing_vars = []
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            for var in required_vars:
                if f"{var}=" not in content or f"{var}=your_" in content:
                    missing_vars.append(var)
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    if missing_vars:
        print(f"❌ Missing or incomplete environment variables: {', '.join(missing_vars)}")
        print("Please edit your .env file and set proper values")
        return False
    
    print("✅ Environment variables configured")
    return True

def create_env_template():
    """Create .env.template file"""
    template_content = """# TradeBot Sentinel Environment Configuration
# Copy this file to .env and fill in your actual credentials

# Bulenox ProjectX Trading Platform Credentials
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here

# Optional: Browser Configuration
# HEADLESS_MODE=true
# SCREENSHOT_ON_ERROR=true
# LOG_LEVEL=INFO

# Security Note:
# Never commit the actual .env file to version control
# Add .env to your .gitignore file
"""
    
    try:
        with open('.env.template', 'w') as f:
            f.write(template_content)
        print("✅ Created .env.template file")
    except Exception as e:
        print(f"❌ Failed to create .env.template: {e}")

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print("✅ Environment variables loaded")
            return True
        except Exception as e:
            print(f"❌ Error loading .env file: {e}")
    return False

def run_tradebot_sentinel():
    """Run the TradeBot Sentinel script"""
    print("\n🚀 Starting TradeBot Sentinel...")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([sys.executable, 'enhanced_tradebot_sentinel.py'])
    except KeyboardInterrupt:
        print("\n⏹️  TradeBot Sentinel stopped by user")
    except Exception as e:
        print(f"❌ Error running TradeBot Sentinel: {e}")

def main():
    """Main setup and run function"""
    print("🤖 TradeBot Sentinel Setup & Run")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check and install dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Install Playwright browsers
    if not install_playwright_browsers():
        print("⚠️  Warning: Playwright browsers may not be installed properly")
    
    # Check environment configuration
    if not check_env_file():
        print("\n⚠️  Please configure your environment variables before running")
        sys.exit(1)
    
    # Load environment variables
    load_env_file()
    
    print("\n✅ All checks passed!")
    print("=" * 40)
    
    # Run the TradeBot Sentinel
    run_tradebot_sentinel()

if __name__ == "__main__":
    main()