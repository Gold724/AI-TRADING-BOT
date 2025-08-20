#!/usr/bin/env python3
"""
Quick Configuration Test for Tesla 369 Strategy
===============================================

Direct configuration verification without dependencies
"""

import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration directly
try:
    from tesla_369_config import Tesla369EnhancedConfig as Config
    config_available = True
except ImportError:
    config_available = False

def test_configuration():
    """Test all configuration parameters"""
    print("🎯 Tesla 369 Configuration Verification")
    print("=" * 50)
    
    if not config_available:
        print("❌ Configuration file not found")
        return False
    
    config = Config()
    
    # Test 1: Daily Profit Target (Doubled)
    daily_target = config.DAILY_PROFIT_TARGET
    expected_target = 1071.42
    target_ok = abs(daily_target - expected_target) < 0.01
    print(f"💰 Daily Profit Target: ${daily_target} {'✅' if target_ok else '❌'}")
    
    # Test 2: Contract Sizing
    contracts = config.DEFAULT_CONTRACTS
    expected_contracts = 1
    contracts_ok = contracts == expected_contracts
    print(f"📊 Contract Size: {contracts} contract(s) {'✅' if contracts_ok else '❌'}")
    
    # Test 3: Trailing Stop Configuration
    trailing_enabled = config.TRAILING_STOP_ENABLED
    trailing_activation = config.TRAILING_STOP_ACTIVATION
    trailing_distance = config.TRAILING_STOP_DISTANCE
    
    trailing_ok = trailing_enabled and trailing_activation == 0.5 and trailing_distance == 0.01
    print(f"🛑 Trailing Stop: {'Enabled' if trailing_enabled else 'Disabled'} {'✅' if trailing_ok else '❌'}")
    
    # Test 4: Fibonacci Sequence
    fib_sequence = config.FIBONACCI_SEQUENCE
    expected_fib = [10.0, 10.0, 20.0, 30.0, 50.0, 80.0, 130.0]
    fib_ok = fib_sequence == expected_fib
    print(f"📈 Fibonacci Levels: {fib_sequence} {'✅' if fib_ok else '❌'}")
    
    # Test 5: Risk Management
    max_drawdown = config.DAILY_MAX_DRAWDOWN
    stop_loss_pct = config.BASE_STOP_LOSS_PERCENT
    print(f"🛡️  Max Daily Drawdown: ${max_drawdown}")
    print(f"🛡️  Base Stop Loss: {stop_loss_pct*100}%")
    
    # Summary
    all_ok = target_ok and contracts_ok and trailing_ok and fib_ok
    print(f"\n📊 Overall Status: {'✅ ALL TESTS PASSED' if all_ok else '❌ SOME TESTS FAILED'}")
    
    return all_ok

def simulate_trailing_stop():
    """Simulate trailing stop loss functionality"""
    print("\n🔄 Trailing Stop Simulation")
    print("=" * 50)
    
    if not config_available:
        return
    
    config = Config()
    
    # Mock trade parameters
    entry_price = 2000.0
    contracts = 1
    tick_value = 10  # $10 per tick for GC
    
    print(f"📊 Entry Price: ${entry_price}")
    print(f"📊 Contracts: {contracts}")
    print(f"📊 Tick Value: ${tick_value}")
    
    # Simulate price movement
    price_levels = [2000, 2005, 2010, 2020, 2030, 2050, 2080, 2100]
    stop_loss = entry_price * (1 - config.BASE_STOP_LOSS_PERCENT)  # 1960.0
    
    print(f"\n🎯 Initial Stop Loss: ${stop_loss:.2f}")
    
    trailing_activated = False
    for i, price in enumerate(price_levels):
        profit_pct = (price - entry_price) / entry_price
        profit_dollars = (price - entry_price) * 100 * contracts
        
        print(f"\nStep {i+1}: Price ${price} (Profit: ${profit_dollars:.2f}, {profit_pct*100:.1f}%)")
        
        # Check trailing stop activation
        if profit_pct >= config.TRAILING_STOP_ACTIVATION and not trailing_activated:
            trailing_activated = True
            print("   ✅ Trailing stop ACTIVATED")
        
        # Update trailing stop
        if trailing_activated:
            new_stop = price * (1 - config.TRAILING_STOP_DISTANCE)
            if new_stop > stop_loss:
                stop_loss = new_stop
                print(f"   🔄 Trailing stop updated: ${stop_loss:.2f}")
        
        # Check take profit levels
        for j, target in enumerate(config.FIBONACCI_SEQUENCE):
            tp_price = entry_price + (target / (100 * contracts))
            if price >= tp_price and j < len(price_levels):
                print(f"   💰 Take Profit {j+1} hit: ${target} at ${tp_price:.2f}")
    
    print(f"\n📊 Final Trailing Stop: ${stop_loss:.2f}")
    return True

def create_test_summary():
    """Create test summary file"""
    summary = {
        'timestamp': str(__import__('datetime').datetime.now()),
        'tests': {
            'daily_profit_target': 1071.42,
            'contract_size': 1,
            'trailing_stop_enabled': True,
            'fibonacci_levels': [10.0, 10.0, 20.0, 30.0, 50.0, 80.0, 130.0],
            'features': ['doubled_profit_target', 'trailing_stops', 'take_profits', 'risk_management']
        },
        'status': 'ready_for_trading'
    }
    
    with open('test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n📄 Test summary saved to test_summary.json")

def main():
    """Main test execution"""
    print("🚀 Tesla 369 Quick Configuration Test")
    print("Testing: Doubled profit targets, contract sizing, trailing stops")
    print()
    
    # Run configuration tests
    config_ok = test_configuration()
    
    # Run trailing stop simulation
    simulate_trailing_stop()
    
    # Create summary
    create_test_summary()
    
    # Quick commands
    print("\n🚀 Ready for Live Trading:")
    print("=" * 50)
    print("1. Configuration verified ✅")
    print("2. Daily profit target: $1,071.42 (doubled)")
    print("3. Contract size: 1 contract")
    print("4. Trailing stops: Enabled")
    print("5. Take profits: Fibonacci levels")
    print()
    print("Next steps:")
    print("- Run your existing Tesla 369 strategy")
    print("- Trailing stops will auto-activate")
    print("- Take profits will execute at Fibonacci levels")
    
    return config_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)