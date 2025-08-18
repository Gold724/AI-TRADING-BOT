#!/usr/bin/env python3
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
        print(f"
🔍 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print("
" + "=" * 40)
    if all_passed:
        print("🎉 All checks passed! Environment is ready.")
        print("🚀 Run: python3 tradebot_sentinel_advanced_pro.py --headless")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
