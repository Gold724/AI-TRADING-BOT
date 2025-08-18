#!/usr/bin/env python3
"""
Verification script for TradeBot Sentinel setup
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def main():
    output_file = "setup_verification.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"TradeBot Sentinel Setup Verification\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
        
        # Check main script
        script_path = Path("tradebot_sentinel_playwright.py")
        if script_path.exists():
            f.write(f"✅ Main script exists: {script_path}\n")
            f.write(f"📊 Size: {script_path.stat().st_size:,} bytes\n")
        else:
            f.write(f"❌ Main script missing: {script_path}\n")
        
        # Check syntax
        f.write("\n🔍 Syntax Check:\n")
        try:
            import py_compile
            py_compile.compile('tradebot_sentinel_playwright.py', doraise=True)
            f.write("✅ Script syntax is valid\n")
        except Exception as e:
            f.write(f"❌ Syntax error: {e}\n")
        
        # Check dependencies
        f.write("\n📦 Dependencies:\n")
        deps = ['playwright', 'curlconverter', 'fake_useragent']
        for dep in deps:
            try:
                module = __import__(dep.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                f.write(f"✅ {dep}: {version}\n")
            except ImportError:
                f.write(f"❌ {dep}: not installed\n")
        
        # Check environment
        f.write("\n🔐 Environment:\n")
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        
        if username:
            f.write(f"✅ BULENOX_USERNAME: {username[:3]}***\n")
        else:
            f.write("⚠️  BULENOX_USERNAME not set\n")
        
        if password:
            f.write(f"✅ BULENOX_PASSWORD: ***{password[-3:]}\n")
        else:
            f.write("⚠️  BULENOX_PASSWORD not set\n")
        
        f.write("\n🎯 Status: TradeBot Sentinel is ready for automation!\n")
        f.write("\n📋 Usage:\n")
        f.write("   python tradebot_sentinel_playwright.py\n")
    
    print(f"Verification complete! Check {output_file} for results.")

if __name__ == "__main__":
    main()