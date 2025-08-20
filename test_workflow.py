#!/usr/bin/env python3
"""
Quick test script to verify GitHub Actions workflow configuration
"""

import os
import sys

def test_workflow_config():
    """Test that all required files exist for the workflow"""
    
    required_files = [
        '.github/workflows/ci_cd_pipeline.yml',
        'deploy_to_contabo.py',
        'requirements.txt',
        '.env.example'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        return False
    
    print("✅ All required workflow files exist")
    
    # Test imports
    try:
        import tradebot_sentinel_bulenox_automation
        print("✅ Main bot module import successful")
    except ImportError as e:
        print(f"❌ Failed to import main bot: {e}")
        return False
    
    try:
        import bulenox_gold_scalping_strategy
        print("✅ Strategy module import successful")
    except ImportError as e:
        print(f"❌ Failed to import strategy: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_workflow_config()
    sys.exit(0 if success else 1)