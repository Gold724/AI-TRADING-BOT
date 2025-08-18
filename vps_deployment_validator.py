#!/usr/bin/env python3
"""
AI Trading Sentinel - VPS Deployment Validator
==============================================
Comprehensive deployment verification and file push utility for Contambo VPS
- Validates all core trading scripts exist locally
- Creates deployment package with proper permissions
- Generates deployment checklist and validation report
- Ensures environment readiness for live trading
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import shutil
import stat

class VPSDeploymentValidator:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.deployment_dir = self.base_dir / "vps_deployment"
        self.missing_files = []
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "missing_files": [],
            "deployment_status": "PENDING",
            "manual_steps": []
        }
        
        # Core files required for VPS deployment
        self.core_files = {
            "trading_scripts": [
                "tradebot_sentinel_playwright.py",
                "tradebot_sentinel_advanced_pro.py",
                "login_bulenox_playwright.py",
                "endpoint_validator.py"
            ],
            "launchers": [
                "live_trading_launcher.sh",
                "live_trading_launcher.ps1",
                "live_trading_launcher.bat"
            ],
            "utilities": [
                "curl_to_python.py",
                "requirements.txt",
                "verify_setup.py"
            ],
            "config_files": [
                ".env.example",
                "secrets.json"
            ]
        }
        
    def log(self, message, level="INFO"):
        """Enhanced logging with emoji indicators"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji_map = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEPLOY": "🚀"
        }
        emoji = emoji_map.get(level, "📝")
        print(f"[{timestamp}] {emoji} {message}")
        
    def validate_local_files(self):
        """Validate all required files exist locally"""
        self.log("Starting local file validation...", "INFO")
        
        all_files_valid = True
        
        for category, files in self.core_files.items():
            self.log(f"Checking {category}...", "INFO")
            category_results = {}
            
            for file_name in files:
                file_path = self.base_dir / file_name
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    category_results[file_name] = {
                        "exists": True,
                        "size": file_size,
                        "path": str(file_path)
                    }
                    self.log(f"  ✅ {file_name} ({file_size} bytes)", "SUCCESS")
                else:
                    category_results[file_name] = {
                        "exists": False,
                        "size": 0,
                        "path": str(file_path)
                    }
                    self.missing_files.append(file_name)
                    self.log(f"  ❌ {file_name} - MISSING", "ERROR")
                    all_files_valid = False
                    
            self.report["validation_results"][category] = category_results
            
        return all_files_valid
        
    def create_deployment_package(self):
        """Create deployment package with all required files"""
        self.log("Creating deployment package...", "DEPLOY")
        
        # Create deployment directory
        if self.deployment_dir.exists():
            shutil.rmtree(self.deployment_dir)
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Copy all valid files to deployment directory
        copied_files = []
        
        for category, files in self.core_files.items():
            category_dir = self.deployment_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for file_name in files:
                source_path = self.base_dir / file_name
                if source_path.exists():
                    dest_path = category_dir / file_name
                    shutil.copy2(source_path, dest_path)
                    
                    # Make scripts executable
                    if file_name.endswith(('.py', '.sh')):
                        dest_path.chmod(dest_path.stat().st_mode | stat.S_IEXEC)
                        
                    copied_files.append(str(dest_path))
                    self.log(f"  📦 Packaged: {file_name}", "SUCCESS")
                    
        # Create deployment script
        self.create_deployment_script()
        
        return copied_files
        
    def create_deployment_script(self):
        """Create VPS deployment script"""
        deployment_script = self.deployment_dir / "deploy_to_vps.sh"
        
        script_content = '''#!/bin/bash
# AI Trading Sentinel - VPS Deployment Script
# Auto-generated deployment script for Contambo VPS

set -e

VPS_HOST="your-vps-host"
VPS_USER="root"
VPS_DIR="/root/AI-TRADING-BOT"

echo "🚀 Deploying AI Trading Sentinel to VPS..."

# Create remote directory
ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"

# Copy trading scripts
echo "📦 Copying trading scripts..."
scp trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/

# Copy launchers
echo "🔧 Copying launcher scripts..."
scp launchers/* $VPS_USER@$VPS_HOST:$VPS_DIR/

# Copy utilities
echo "⚙️ Copying utility scripts..."
scp utilities/* $VPS_USER@$VPS_HOST:$VPS_DIR/

# Set permissions
echo "🔐 Setting file permissions..."
ssh $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"

# Install dependencies
echo "📚 Installing Python dependencies..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && pip3 install -r requirements.txt"

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 -m playwright install"

# Verify deployment
echo "✅ Verifying deployment..."
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 verify_setup.py"

echo "🎉 Deployment completed successfully!"
echo "📍 Files deployed to: $VPS_HOST:$VPS_DIR"
echo "🚀 Ready to run: python3 tradebot_sentinel_advanced_pro.py --headless"
'''
        
        with open(deployment_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        deployment_script.chmod(deployment_script.stat().st_mode | stat.S_IEXEC)
        
        self.log(f"Created deployment script: {deployment_script}", "SUCCESS")
        
    def create_vps_validation_script(self):
        """Create VPS environment validation script"""
        validation_script = self.deployment_dir / "vps_environment_check.py"
        
        script_content = '''#!/usr/bin/env python3
"""
VPS Environment Validation Script
Checks if all dependencies and files are properly installed
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires 3.8+")
        return False

def check_pip_packages():
    """Check required pip packages"""
    required_packages = [
        'playwright',
        'requests',
        'python-dotenv'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - Installed")
        except ImportError:
            print(f"❌ {package} - Missing")
            all_installed = False
    
    return all_installed

def check_playwright_browsers():
    """Check Playwright browser installation"""
    try:
        result = subprocess.run(['python3', '-m', 'playwright', 'install', '--dry-run'], 
                              capture_output=True, text=True)
        if 'chromium' in result.stdout.lower():
            print("✅ Playwright browsers - Installed")
            return True
        else:
            print("❌ Playwright browsers - Missing")
            return False
    except Exception as e:
        print(f"❌ Playwright check failed: {e}")
        return False

def check_core_files():
    """Check core trading files exist"""
    core_files = [
        'tradebot_sentinel_playwright.py',
        'tradebot_sentinel_advanced_pro.py',
        'login_bulenox_playwright.py',
        'endpoint_validator.py'
    ]
    
    all_exist = True
    for file_name in core_files:
        if Path(file_name).exists():
            print(f"✅ {file_name} - Found")
        else:
            print(f"❌ {file_name} - Missing")
            all_exist = False
    
    return all_exist

def main():
    print("🔍 VPS Environment Validation")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python),
        ("Pip Packages", check_pip_packages),
        ("Playwright Browsers", check_playwright_browsers),
        ("Core Files", check_core_files)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All checks passed! Environment is ready.")
        print("🚀 Run: python3 tradebot_sentinel_advanced_pro.py --headless")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(validation_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        validation_script.chmod(validation_script.stat().st_mode | stat.S_IEXEC)
        
        self.log(f"Created VPS validation script: {validation_script}", "SUCCESS")
        
    def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        self.log("Generating deployment report...", "INFO")
        
        # Update report status
        if not self.missing_files:
            self.report["deployment_status"] = "READY"
        else:
            self.report["deployment_status"] = "INCOMPLETE"
            
        # Add manual steps
        self.report["manual_steps"] = [
            "1. Update VPS_HOST and VPS_USER in deploy_to_vps.sh",
            "2. Ensure SSH key authentication is set up",
            "3. Set environment variables (BULENOX_USERNAME, BULENOX_PASSWORD)",
            "4. Run: ./deploy_to_vps.sh from deployment directory",
            "5. Verify with: python3 vps_environment_check.py on VPS"
        ]
        
        # Save report
        report_file = self.deployment_dir / "deployment_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2)
            
        # Create human-readable report
        readable_report = self.deployment_dir / "DEPLOYMENT_CHECKLIST.md"
        self.create_readable_report(readable_report)
        
        self.log(f"Report saved: {report_file}", "SUCCESS")
        self.log(f"Checklist created: {readable_report}", "SUCCESS")
        
    def create_readable_report(self, report_path):
        """Create human-readable deployment checklist"""
        content = f'''# AI Trading Sentinel - VPS Deployment Checklist

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status:** {self.report["deployment_status"]}

## 📋 File Validation Results

'''
        
        for category, files in self.report["validation_results"].items():
            content += f"### {category.title()}\n\n"
            for file_name, info in files.items():
                status = "✅" if info["exists"] else "❌"
                size_info = f" ({info['size']} bytes)" if info["exists"] else " - MISSING"
                content += f"- {status} `{file_name}`{size_info}\n"
            content += "\n"
            
        if self.missing_files:
            content += f"## ⚠️ Missing Files ({len(self.missing_files)})\n\n"
            for file_name in self.missing_files:
                content += f"- ❌ `{file_name}`\n"
            content += "\n"
            
        content += "## 🚀 Deployment Steps\n\n"
        for i, step in enumerate(self.report["manual_steps"], 1):
            content += f"{i}. {step[3:]}\n"  # Remove "1. " prefix
            
        content += '''\n## 🔍 VPS Verification Commands\n\n```bash
# Check if files exist
find /root/AI-TRADING-BOT -name "*.py" -type f

# Verify Python environment
python3 --version
pip3 list | grep -E "playwright|requests|dotenv"

# Test core script
cd /root/AI-TRADING-BOT
python3 tradebot_sentinel_advanced_pro.py --help

# Run environment check
python3 vps_environment_check.py
```

## 🎯 Ready to Launch

Once all files are deployed and verified:

```bash
# Start in monitor mode (60s test)
python3 tradebot_sentinel_advanced_pro.py --monitor

# Start headless live trading
python3 tradebot_sentinel_advanced_pro.py --headless

# Use launcher script
./live_trading_launcher.sh
```
'''
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
    def run_validation(self):
        """Run complete validation and deployment preparation"""
        self.log("🚀 Starting VPS Deployment Validation", "DEPLOY")
        self.log("=" * 50, "INFO")
        
        # Step 1: Validate local files
        files_valid = self.validate_local_files()
        
        # Step 2: Create deployment package
        if files_valid:
            self.log("All files validated successfully!", "SUCCESS")
        else:
            self.log(f"Warning: {len(self.missing_files)} files missing", "WARNING")
            
        copied_files = self.create_deployment_package()
        
        # Step 3: Create VPS validation script
        self.create_vps_validation_script()
        
        # Step 4: Generate reports
        self.generate_deployment_report()
        
        # Final summary
        self.log("=" * 50, "INFO")
        self.log(f"Deployment package created: {self.deployment_dir}", "SUCCESS")
        self.log(f"Files packaged: {len(copied_files)}", "INFO")
        
        if self.missing_files:
            self.log(f"Missing files: {', '.join(self.missing_files)}", "WARNING")
        else:
            self.log("🎉 All required files are ready for deployment!", "SUCCESS")
            
        self.log("Next steps:", "INFO")
        self.log("1. Review DEPLOYMENT_CHECKLIST.md", "INFO")
        self.log("2. Update deploy_to_vps.sh with your VPS details", "INFO")
        self.log("3. Run ./deploy_to_vps.sh to deploy", "INFO")
        
        return self.report["deployment_status"] == "READY"

def main():
    validator = VPSDeploymentValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())