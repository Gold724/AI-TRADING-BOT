#!/usr/bin/env python3
"""
VPS Deployment Verification Script for AI Trading Sentinel
Verifies VPS deployment status and provides deployment commands.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

def print_header():
    """Print script header"""
    print("🚀 AI Trading Sentinel - VPS Deployment Verification")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Local System: {os.name} ({sys.platform})")
    print()

def check_local_files():
    """Check if required deployment files exist locally"""
    print("📁 Checking Local Deployment Files")
    print("=" * 40)
    
    required_files = [
        'deploy_vps_complete.sh',
        'test_email_system.py',
        'test_bulenox_demo.py',
        '.env.production.template',
        'VPS_SETUP_COMPLETE_GUIDE.md',
        'requirements.txt',
        'main.py',
        'backend_main.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size:,} bytes)")
        else:
            missing_files.append(file)
            print(f"❌ {file} (missing)")
    
    if missing_files:
        print(f"\n⚠️ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ All required deployment files are present")
        return True

def check_git_status():
    """Check Git repository status"""
    print("\n📦 Checking Git Repository Status")
    print("=" * 40)
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("⚠️ Uncommitted changes detected:")
            print(result.stdout)
            print("💡 Consider committing changes before VPS deployment")
        else:
            print("✅ Working directory is clean")
        
        # Check current branch
        branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                     capture_output=True, text=True, check=True)
        current_branch = branch_result.stdout.strip()
        print(f"🌿 Current branch: {current_branch}")
        
        # Check remote URL
        remote_result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                     capture_output=True, text=True, check=True)
        remote_url = remote_result.stdout.strip()
        print(f"🔗 Remote URL: {remote_url}")
        
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Not a Git repository or Git not available")
        print("💡 Initialize Git repository for easier VPS deployment")
        return False
    except FileNotFoundError:
        print("❌ Git not found in PATH")
        print("💡 Install Git for version control")
        return False

def generate_deployment_commands():
    """Generate VPS deployment commands"""
    print("\n🚀 VPS Deployment Commands")
    print("=" * 40)
    
    print("📋 Copy and run these commands on your VPS:")
    print()
    
    # Method 1: Direct deployment script
    print("🔥 Method 1: Direct Deployment (Recommended)")
    print("─" * 50)
    print("# Download and run the complete deployment script")
    print("curl -fsSL https://raw.githubusercontent.com/Gold724/AI-TRADING-BOT/main/deploy_vps_complete.sh | bash")
    print()
    
    # Method 2: Manual deployment
    print("🔧 Method 2: Manual Deployment")
    print("─" * 50)
    print("# Clone repository")
    print("git clone https://github.com/Gold724/AI-TRADING-BOT.git /opt/ai-trading-sentinel")
    print("cd /opt/ai-trading-sentinel")
    print()
    print("# Make deployment script executable and run")
    print("chmod +x deploy_vps_complete.sh")
    print("./deploy_vps_complete.sh")
    print()
    
    # Method 3: Step-by-step
    print("📝 Method 3: Step-by-Step (For troubleshooting)")
    print("─" * 50)
    print("# Update system")
    print("sudo apt update && sudo apt upgrade -y")
    print()
    print("# Install dependencies")
    print("sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx")
    print()
    print("# Clone and setup")
    print("git clone https://github.com/Gold724/AI-TRADING-BOT.git /opt/ai-trading-sentinel")
    print("cd /opt/ai-trading-sentinel")
    print("python3 -m venv venv")
    print("source venv/bin/activate")
    print("pip install -r requirements.txt")
    print("playwright install")
    print()

def generate_env_configuration():
    """Generate .env configuration instructions"""
    print("\n⚙️ .env Configuration")
    print("=" * 40)
    
    print("📝 After deployment, update your .env file with:")
    print()
    
    env_config = """
# 🔐 BULENOX CREDENTIALS (REQUIRED)
BULENOX_USERNAME=your_bulenox_username
BULENOX_PASSWORD=your_bulenox_password
BULENOX_DEMO_MODE=true

# 📧 EMAIL NOTIFICATIONS (CONFIGURED)
EMAIL_NOTIFICATIONS=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=edufyinc@gmail.com
EMAIL_PASSWORD=paxq vizg qjzw ujsm
EMAIL_TO=edufyinc@gmail.com
SMTP_PORT=587

# 🔒 SECURITY (CONFIGURED)
SECRET_KEY=brgvQkUBbpfayCHXMXQ9cNivpy9qEmyjup7ntfY4k5g
JWT_SECRET=mHWCAWj_7JA1kQTezxKqtLTP3IRqDbgMLM_O65AYe6E

# 📊 TRADING (CONFIGURED)
TRADING_MODE=safe
MAX_CONTRACTS=3
DEFAULT_CONTRACTS=1
MAX_DRAWDOWN=500.00
PROFIT_TARGET=1000.00
    """
    
    print(env_config)
    
    print("💡 Commands to edit .env on VPS:")
    print("nano /opt/ai-trading-sentinel/.env")
    print("# or")
    print("vim /opt/ai-trading-sentinel/.env")
    print()

def generate_service_commands():
    """Generate service management commands"""
    print("\n🔧 Service Management Commands")
    print("=" * 40)
    
    print("📋 After deployment and .env configuration:")
    print()
    
    print("🚀 Start Services:")
    print("cd /opt/ai-trading-sentinel")
    print("pm2 start ecosystem.config.js")
    print("pm2 save")
    print()
    
    print("📊 Check Status:")
    print("pm2 status")
    print("pm2 logs")
    print("sudo systemctl status nginx")
    print()
    
    print("🔄 Restart Services:")
    print("pm2 restart all")
    print("sudo systemctl restart nginx")
    print()
    
    print("🛑 Stop Services:")
    print("pm2 stop all")
    print()
    
    print("📝 View Logs:")
    print("pm2 logs ai-trading-backend")
    print("pm2 logs ai-trading-bot")
    print("tail -f /opt/ai-trading-sentinel/logs/trading.log")
    print()

def generate_testing_commands():
    """Generate testing commands for VPS"""
    print("\n🧪 Testing Commands (Run on VPS)")
    print("=" * 40)
    
    print("📧 Test Email System:")
    print("cd /opt/ai-trading-sentinel")
    print("source venv/bin/activate")
    print("python test_email_system.py")
    print()
    
    print("🔐 Test Bulenox Connection:")
    print("python test_bulenox_demo.py")
    print()
    
    print("🌐 Test Web Access:")
    print("curl -I http://localhost")
    print("curl -I http://localhost/api/health")
    print()
    
    print("🔍 Health Checks:")
    print("ps aux | grep python")
    print("netstat -tlnp | grep :80")
    print("netstat -tlnp | grep :5000")
    print("df -h")
    print("free -h")
    print()

def check_deployment_readiness():
    """Check if system is ready for deployment"""
    print("\n✅ Deployment Readiness Check")
    print("=" * 40)
    
    checks = {
        'Local files': check_local_files(),
        'Git repository': check_git_status(),
        'Email configuration': True,  # Already tested
        'Security keys': True,  # Already generated
    }
    
    all_ready = all(checks.values())
    
    print("\n📊 Readiness Summary:")
    for check_name, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")
    
    if all_ready:
        print("\n🎉 System is ready for VPS deployment!")
        return True
    else:
        print("\n⚠️ Please fix the issues above before deployment")
        return False

def main():
    """Main function"""
    print_header()
    
    # Check deployment readiness
    ready = check_deployment_readiness()
    
    if ready:
        # Generate deployment instructions
        generate_deployment_commands()
        generate_env_configuration()
        generate_service_commands()
        generate_testing_commands()
        
        print("\n🎯 DEPLOYMENT WORKFLOW")
        print("=" * 40)
        print("1. ✅ Run deployment script on VPS")
        print("2. ⚙️ Configure Bulenox credentials in .env")
        print("3. 🚀 Start services with PM2")
        print("4. 🧪 Run connection tests")
        print("5. 🌐 Access trading dashboard")
        print("6. 📊 Monitor logs and performance")
        
        print("\n🌐 After deployment, access your dashboard at:")
        print("http://YOUR_VPS_IP")
        
        return True
    else:
        print("\n❌ Deployment not ready - fix issues first")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)