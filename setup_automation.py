#!/usr/bin/env python3
"""
TradeBot Sentinel Automation Setup Script

This script sets up the automation environment by:
1. Installing required Python packages
2. Installing Playwright browsers
3. Setting up environment variables template
4. Validating the setup

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AutomationSetup')

def run_command(command, description):
    """Run a command and handle errors"""
    try:
        logger.info(f"🔄 {description}...")
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def install_requirements():
    """Install Python requirements"""
    requirements_file = Path(__file__).parent / "requirements_automation.txt"
    
    if not requirements_file.exists():
        logger.error(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    command = f"{sys.executable} -m pip install -r {requirements_file}"
    return run_command(command, "Installing Python requirements")

def install_playwright_browsers():
    """Install Playwright browsers"""
    command = f"{sys.executable} -m playwright install chromium"
    return run_command(command, "Installing Playwright Chromium browser")

def create_env_template():
    """Create environment variables template"""
    try:
        env_template = Path(__file__).parent / ".env.template"
        
        template_content = """# TradeBot Sentinel Automation Environment Variables
# Copy this file to .env and fill in your actual credentials

# Bulenox ProjectX Trading Platform Credentials
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here

# Optional: Trading Platform URL (if different from default)
# TRADING_PLATFORM_URL=https://your-platform.com

# Optional: Automation Settings
# AUTOMATION_HEADLESS=true
# AUTOMATION_TIMEOUT=30000
# SCREENSHOT_ON_ERROR=true
"""
        
        with open(env_template, 'w') as f:
            f.write(template_content)
        
        logger.info(f"✅ Environment template created: {env_template}")
        logger.info("📝 Please copy .env.template to .env and fill in your credentials")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create environment template: {e}")
        return False

def validate_setup():
    """Validate the automation setup"""
    try:
        logger.info("🔍 Validating setup...")
        
        # Check if playwright is installed
        import playwright
        logger.info("✅ Playwright imported successfully")
        
        # Check if curlconverter is available
        try:
            import curlconverter
            logger.info("✅ curlconverter imported successfully")
        except ImportError:
            logger.warning("⚠️ curlconverter not found, will be installed on first use")
        
        # Check if automation script exists
        automation_script = Path(__file__).parent / "tradebot_sentinel_automation.py"
        if automation_script.exists():
            logger.info("✅ Automation script found")
        else:
            logger.error("❌ Automation script not found")
            return False
        
        # Check environment variables
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            logger.info("✅ Environment file found")
        else:
            logger.warning("⚠️ .env file not found. Please create it from .env.template")
        
        logger.info("🎉 Setup validation completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup validation failed: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions"""
    instructions = """
🤖 TradeBot Sentinel Automation Setup Complete!

📋 Next Steps:
1. Copy .env.template to .env
2. Fill in your Bulenox ProjectX credentials in .env
3. Run the automation:
   
   # Headless mode (default)
   python tradebot_sentinel_automation.py
   
   # Visible mode (for debugging)
   python tradebot_sentinel_automation.py --visible

📁 Generated Files:
- tradebot_sentinel_automation.py (main automation script)
- requirements_automation.txt (Python dependencies)
- .env.template (environment variables template)
- tradebot_automation.log (automation logs)
- trade.sh (generated cURL commands)
- trade_request_full.py (generated Python requests code)

🔧 Environment Variables Required:
- BULENOX_USERNAME: Your trading platform username
- BULENOX_PASSWORD: Your trading platform password

⚠️ Security Note:
- Never commit .env file to version control
- Keep your credentials secure
- Use strong, unique passwords

📚 For more information, check the automation logs and screenshots.
"""
    
    print(instructions)

def main():
    """Main setup function"""
    logger.info("🚀 Starting TradeBot Sentinel Automation Setup...")
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Install Playwright browsers
    if not install_playwright_browsers():
        success = False
    
    # Create environment template
    if not create_env_template():
        success = False
    
    # Validate setup
    if not validate_setup():
        success = False
    
    if success:
        logger.info("🎉 TradeBot Sentinel Automation setup completed successfully!")
        print_usage_instructions()
        return 0
    else:
        logger.error("💥 Setup failed! Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())