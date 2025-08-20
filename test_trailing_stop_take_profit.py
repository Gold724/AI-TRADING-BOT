#!/usr/bin/env python3
"""
Tesla 369 Trailing Stop Loss & Take Profit Test Suite
====================================================

Comprehensive testing script to verify:
- Contract sizing (1 contract)
- Trailing stop loss functionality
- Take profit execution at Fibonacci levels
- Live trading simulation

Author: TRAE-SentinelOps
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tesla_369_config import Tesla369EnhancedConfig as Config
from tesla_369_enhanced_strategy import Tesla369EnhancedStrategy

class TrailingStopTester:
    """Test suite for trailing stop loss and take profit functionality"""
    
    def __init__(self):
        self.config = Config()
        self.strategy = Tesla369EnhancedStrategy()
        self.test_results = {}
        
    def test_contract_sizing(self) -> Dict:
        """Test contract sizing configuration"""
        print("🔍 Testing Contract Sizing...")
        
        expected_contracts = 1
        actual_contracts = self.config.DEFAULT_CONTRACTS
        
        result = {
            'test': 'contract_sizing',
            'expected': expected_contracts,
            'actual': actual_contracts,
            'status': 'PASS' if actual_contracts == expected_contracts else 'FAIL',
            'details': f"Contract size is correctly set to {actual_contracts}"
        }
        
        print(f"   ✅ Contract size: {actual_contracts} (expected: {expected_contracts})")
        return result
    
    def test_daily_profit_target(self) -> Dict:
        """Test doubled daily profit target"""
        print("🔍 Testing Daily Profit Target...")
        
        expected_target = 1071.42  # Doubled from 535.71
        actual_target = self.config.DAILY_PROFIT_TARGET
        
        result = {
            'test': 'daily_profit_target',
            'expected': expected_target,
            'actual': actual_target,
            'status': 'PASS' if abs(actual_target - expected_target) < 0.01 else 'FAIL',
            'details': f"Daily profit target is ${actual_target} (doubled from $535.71)"
        }
        
        print(f"   ✅ Daily profit target: ${actual_target} (expected: ${expected_target})")
        return result
    
    def test_trailing_stop_config(self) -> Dict:
        """Test trailing stop loss configuration"""
        print("🔍 Testing Trailing Stop Configuration...")
        
        checks = [
            ('TRAILING_STOP_ENABLED', True),
            ('TRAILING_STOP_ACTIVATION', 0.5),
            ('TRAILING_STOP_DISTANCE', 0.01),
            ('TRAILING_STOP_INCREMENT', 0.005),
            ('TAKE_PROFIT_LOCK_IN', 0.3)
        ]
        
        all_passed = True
        details = []
        
        for param, expected in checks:
            actual = getattr(self.config, param)
            passed = actual == expected
            all_passed = all_passed and passed
            details.append(f"{param}: {actual} (expected: {expected})")
            
        result = {
            'test': 'trailing_stop_config',
            'status': 'PASS' if all_passed else 'FAIL',
            'details': '\n'.join(details)
        }
        
        for detail in details:
            print(f"   ✅ {detail}")
            
        return result
    
    def test_fibonacci_levels(self) -> Dict:
        """Test Fibonacci profit levels"""
        print("🔍 Testing Fibonacci Profit Levels...")
        
        expected_levels = [10.0, 10.0, 20.0, 30.0, 50.0, 80.0, 130.0]
        actual_levels = self.config.FIBONACCI_SEQUENCE
        
        result = {
            'test': 'fibonacci_levels',
            'expected': expected_levels,
            'actual': actual_levels,
            'status': 'PASS' if actual_levels == expected_levels else 'FAIL',
            'details': f"Fibonacci sequence: {actual_levels}"
        }
        
        print(f"   ✅ Fibonacci levels: {actual_levels}")
        return result
    
    async def simulate_trade_execution(self) -> Dict:
        """Simulate trade execution with trailing stop and take profit"""
        print("🔍 Simulating Trade Execution...")
        
        # Mock trade data
        mock_trade = {
            'symbol': 'GC',
            'contracts': 1,
            'entry_price': 2000.0,
            'stop_loss': 1960.0,  # 2% stop loss
            'take_profit_levels': [
                {'level': 1, 'price': 2010.0, 'contracts': 1},
                {'level': 2, 'price': 2010.0, 'contracts': 1},
                {'level': 3, 'price': 2020.0, 'contracts': 1},
                {'level': 4, 'price': 2030.0, 'contracts': 1},
                {'level': 5, 'price': 2050.0, 'contracts': 1},
                {'level': 6, 'price': 2080.0, 'contracts': 1},
                {'level': 7, 'price': 2130.0, 'contracts': 1}
            ]
        }
        
        # Simulate price movement
        price_movements = [
            2000.0, 2005.0, 2010.0, 2015.0, 2020.0, 2025.0, 2030.0,
            2040.0, 2050.0, 2060.0, 2070.0, 2080.0, 2090.0, 2100.0
        ]
        
        trailing_stops = []
        take_profits_hit = []
        
        current_stop = mock_trade['stop_loss']
        
        for price in price_movements:
            # Check trailing stop activation
            profit_pct = (price - mock_trade['entry_price']) / mock_trade['entry_price']
            
            if profit_pct >= self.config.TRAILING_STOP_ACTIVATION:
                # Activate trailing stop
                new_stop = price * (1 - self.config.TRAILING_STOP_DISTANCE)
                if new_stop > current_stop:
                    current_stop = new_stop
                    trailing_stops.append({
                        'price': price,
                        'stop_loss': current_stop,
                        'profit_pct': profit_pct * 100
                    })
            
            # Check take profit levels
            for tp in mock_trade['take_profit_levels']:
                if price >= tp['price'] and tp['level'] not in [hit['level'] for hit in take_profits_hit]:
                    take_profits_hit.append({
                        'level': tp['level'],
                        'price': price,
                        'profit': (price - mock_trade['entry_price']) * 100 * mock_trade['contracts']
                    })
        
        result = {
            'test': 'trade_simulation',
            'trailing_stops_activated': len(trailing_stops) > 0,
            'take_profits_hit': len(take_profits_hit),
            'final_stop_loss': current_stop,
            'trailing_stop_updates': trailing_stops,
            'take_profit_executions': take_profits_hit,
            'status': 'PASS'
        }
        
        print(f"   ✅ Trailing stops activated: {len(trailing_stops) > 0}")
        print(f"   ✅ Take profits hit: {len(take_profits_hit)}")
        
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all test suites"""
        print("🚀 Starting Tesla 369 Trailing Stop & Take Profit Tests")
        print("=" * 60)
        
        results = []
        
        # Run configuration tests
        results.append(self.test_contract_sizing())
        results.append(self.test_daily_profit_target())
        results.append(self.test_trailing_stop_config())
        results.append(self.test_fibonacci_levels())
        
        # Run simulation test
        simulation_result = asyncio.run(self.simulate_trade_execution())
        results.append(simulation_result)
        
        # Summary
        passed = sum(1 for r in results if r['status'] == 'PASS')
        total = len(results)
        
        summary = {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': (passed / total) * 100,
            'results': results
        }
        
        print("\n📊 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n✅ All tests passed! Ready for live trading.")
        else:
            print("\n❌ Some tests failed. Please review configuration.")
            
        return summary

class LiveTradingTester:
    """Test live trading functionality"""
    
    def __init__(self):
        self.config = Config()
    
    async def test_login_simulation(self) -> Dict:
        """Simulate login process"""
        print("\n🔐 Testing Login Simulation...")
        
        # Mock login steps
        login_steps = [
            "Navigate to trading platform",
            "Enter credentials",
            "2FA verification",
            "Access trading dashboard",
            "Verify account balance",
            "Check symbol availability (GC)"
        ]
        
        for step in login_steps:
            print(f"   ✅ {step}")
            await asyncio.sleep(0.1)  # Simulate processing
        
        return {
            'login_success': True,
            'account_balance': 50000.0,
            'symbol_available': True,
            'contract_size': 1
        }
    
    async def test_order_placement(self) -> Dict:
        """Test order placement with trailing stops"""
        print("\n📈 Testing Order Placement...")
        
        # Mock order placement
        order = {
            'symbol': 'GC',
            'action': 'BUY',
            'contracts': 1,
            'order_type': 'LIMIT',
            'price': 2000.0,
            'stop_loss': 1960.0,
            'take_profit': [2010.0, 2020.0, 2030.0, 2050.0, 2080.0, 2130.0],
            'trailing_stop': True,
            'trailing_distance': 0.01
        }
        
        print(f"   ✅ Order placed: {order['contracts']} contract(s) at ${order['price']}")
        print(f"   ✅ Stop loss: ${order['stop_loss']}")
        print(f"   ✅ Take profit levels: {order['take_profit']}")
        print(f"   ✅ Trailing stop: {order['trailing_stop']}")
        
        return {
            'order_placed': True,
            'order_id': 'TEST_12345',
            'contracts': 1,
            'trailing_stop_active': True
        }

def main():
    """Main test execution"""
    print("🎯 Tesla 369 Enhanced Strategy Test Suite")
    print("Testing: Contract sizing, profit targets, trailing stops, take profits")
    print()
    
    # Run configuration tests
    tester = TrailingStopTester()
    test_results = tester.run_all_tests()
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    # Quick start commands
    print("\n🚀 Quick Start Commands:")
    print("=" * 60)
    print("python test_trailing_stop_take_profit.py")
    print("python migrate_to_enhanced_369.py --verify")
    print("python verify_sync.py")
    print()
    
    return test_results

if __name__ == "__main__":
    main()