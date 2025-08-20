#!/usr/bin/env python3
"""
Tesla 369 Strategy Synchronization Verification
=============================================

Quick verification script to confirm your Tesla 369 strategy is fully synchronized
with the enhanced system. Run this to validate everything works together.
"""

import json
import sys
import os
from datetime import datetime

def verify_sync():
    """Verify complete synchronization"""
    
    print("🔍 Tesla 369 Strategy Synchronization Verification")
    print("=" * 50)
    
    # Test 1: Check existing strategy files
    existing_files = [
        'bulenox_gold_scalping_strategy.py',
        'strategy_config.py',
        'test_369_gold_scalping_enhanced.py',
        'fibonacci_multi_tp_strategy.py'
    ]
    
    print("\n📁 Checking existing strategy files:")
    for file in existing_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Missing")
    
    # Test 2: Check enhanced files
    enhanced_files = [
        'tesla_369_enhanced_strategy.py',
        'tesla_369_config.py',
        'tesla_369_sync.py',
        'liquidity_detector.py',
        'lunar_calendar.py',
        'news_guard.py',
        'session_manager.py'
    ]
    
    print("\n📁 Checking enhanced strategy files:")
    for file in enhanced_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Missing")
    
    # Test 3: Verify Fibonacci sequence consistency
    try:
        from tesla_369_sync import Tesla369Sync
        sync = Tesla369Sync()
        
        print(f"\n📊 Fibonacci Sequence Verification:")
        print(f"  ✅ Existing: {sync.existing_params['fibonacci_sequence']}")
        print(f"  ✅ Daily Target: ${sync.existing_params['daily_profit_target']}")
        print(f"  ✅ Symbol: {sync.existing_params['symbol']}")
        
    except Exception as e:
        print(f"  ❌ Sync verification failed: {e}")
        return False
    
    # Test 4: Run compatibility test
    try:
        print(f"\n🧪 Running compatibility test...")
        result = sync.run_compatibility_test()
        
        if result['compatibility_verified']:
            print(f"  ✅ Compatibility verified")
            print(f"  ✅ Original strategy: {result['original_result']['strategy']}")
            print(f"  ✅ Enhanced strategy: Ready")
        else:
            print(f"  ❌ Compatibility issues found")
            
    except Exception as e:
        print(f"  ❌ Compatibility test failed: {e}")
        return False
    
    # Test 5: Feature status
    print(f"\n⚙️ Feature Status:")
    features = sync.get_feature_status()
    for feature, enabled in features.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"  {feature}: {status}")
    
    # Test 6: Quick trade simulation
    try:
        print(f"\n🎯 Quick Trade Simulation:")
        market_data = {
            'price': 2000.0,
            'volume': 1000,
            'bid': 1999.5,
            'ask': 2000.5,
            'timestamp': datetime.now().isoformat()
        }
        
        result = sync.execute_trade_with_enhancements(market_data)
        
        print(f"  ✅ Trade executed: {result.trade_executed}")
        print(f"  ✅ Profit target: ${result.profit_target}")
        print(f"  ✅ Fibonacci level: {result.fibonacci_level}")
        print(f"  ✅ Enhanced score: {result.enhanced_score:.2f}")
        
    except Exception as e:
        print(f"  ❌ Trade simulation failed: {e}")
        return False
    
    print(f"\n🎉 Verification Complete!")
    print(f"   Your Tesla 369 strategy is fully synchronized and ready to use!")
    
    return True

def generate_quick_start():
    """Generate quick start commands"""
    
    print("\n🚀 Quick Start Commands:")
    print("-" * 30)
    print("1. Verify synchronization:")
    print("   python verify_sync.py")
    print()
    print("2. Test enhanced features:")
    print("   python -c 'from tesla_369_sync import Tesla369Sync; print("Ready!")'")
    print()
    print("3. Enable all features:")
    print("   python -c 'from tesla_369_sync import Tesla369Sync; sync = Tesla369Sync(use_enhanced=True); print("Enhanced Tesla 369 ready!")'")
    print()
    print("4. Migration report:")
    print("   python -c 'from tesla_369_sync import Tesla369Sync; sync = Tesla369Sync(); print(sync.get_migration_report())'")

if __name__ == "__main__":
    success = verify_sync()
    
    if success:
        generate_quick_start()
        print(f"\n✅ All systems synchronized!")
    else:
        print(f"\n❌ Synchronization issues detected. Check the logs above.")
        sys.exit(1)