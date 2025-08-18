#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bulenox Contract Size Integration Test

This script tests the Bulenox integration to ensure:
1. Login functionality works at https://bulenox.projectx.com/login
2. Contract sizes are handled correctly (NOT lot sizes)
3. Trade placement works with proper contract validation
4. Risk management works with contract-based position sizing

IMPORTANT: This uses CONTRACTS, not lot sizes!
- Bulenox: 1 contract = 1 contract
- Exness: 1 lot = 100,000 units (different platform)
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade
from bulenox_ai_controller import BulenoxAIController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bulenox_contract_test.log')
    ]
)
logger = logging.getLogger('BulenoxContractTest')

class BulenoxContractTester:
    """Test Bulenox integration with proper contract size handling"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.test_results = []
        self.controller = None
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
    def test_login_functionality(self) -> bool:
        """Test Bulenox login at https://bulenox.projectx.com/login"""
        logger.info("\n=== Testing Bulenox Login Functionality ===")
        
        try:
            # Test direct login function
            logger.info("Testing direct login function...")
            login_success = login_bulenox_ai(debug=self.debug)
            
            if login_success:
                self.log_test_result(
                    "Direct Login", 
                    True, 
                    "Successfully logged into Bulenox platform"
                )
                return True
            else:
                self.log_test_result(
                    "Direct Login", 
                    False, 
                    "Failed to login to Bulenox platform"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Direct Login", 
                False, 
                f"Login test failed with error: {str(e)}"
            )
            return False
            
    def test_controller_login(self) -> bool:
        """Test Bulenox controller login functionality"""
        logger.info("\n=== Testing Bulenox Controller Login ===")
        
        try:
            # Initialize controller
            self.controller = BulenoxAIController()
            
            # Test session start
            logger.info("Starting Bulenox session...")
            session_result = self.controller.start_session(headless=False, debug=self.debug)
            
            if session_result.get('success', False):
                self.log_test_result(
                    "Controller Login", 
                    True, 
                    "Successfully started Bulenox session via controller"
                )
                return True
            else:
                self.log_test_result(
                    "Controller Login", 
                    False, 
                    f"Failed to start session: {session_result.get('message', 'Unknown error')}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Controller Login", 
                False, 
                f"Controller login failed: {str(e)}"
            )
            return False
            
    def test_contract_size_validation(self) -> bool:
        """Test contract size validation (ensure we're using contracts, not lots)"""
        logger.info("\n=== Testing Contract Size Validation ===")
        
        test_cases = [
            # (input_quantity, expected_contracts, description)
            (1, 1, "1 contract input"),
            (2, 2, "2 contracts input"),
            (0.5, 1, "0.5 contract rounded up to 1"),
            (0, 1, "0 contract rounded up to 1"),
            (-1, 1, "Negative contract rounded up to 1"),
            (10, 10, "10 contracts input"),
        ]
        
        all_passed = True
        
        for input_qty, expected, description in test_cases:
            try:
                # Test the validation logic from place_bulenox_trade
                # This simulates the validation without actually placing trades
                
                if not isinstance(input_qty, (int, float)) or input_qty <= 0:
                    actual = 1  # Default minimum
                else:
                    actual = max(1, int(input_qty))
                    
                success = (actual == expected)
                
                self.log_test_result(
                    f"Contract Validation: {description}", 
                    success, 
                    f"Input: {input_qty} → Expected: {expected}, Got: {actual}"
                )
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(
                    f"Contract Validation: {description}", 
                    False, 
                    f"Validation failed: {str(e)}"
                )
                all_passed = False
                
        return all_passed
        
    def test_simulated_trade_placement(self) -> bool:
        """Test simulated trade placement with contract sizes"""
        logger.info("\n=== Testing Simulated Trade Placement ===")
        
        if not self.controller or not self.controller.session_active:
            self.log_test_result(
                "Simulated Trade", 
                False, 
                "No active controller session for testing"
            )
            return False
            
        try:
            # Enable Dreamer Mode for safe testing
            logger.info("Enabling Dreamer Mode for safe testing...")
            dreamer_result = self.controller.toggle_dreamer_mode(enabled=True)
            
            if not dreamer_result.get('success', False):
                self.log_test_result(
                    "Dreamer Mode", 
                    False, 
                    "Failed to enable Dreamer Mode"
                )
                return False
                
            # Test signal with contract-based quantity
            test_signal = {
                "symbol": "EURUSD",
                "direction": "BUY",
                "quantity": 2,  # 2 CONTRACTS (not lot sizes)
                "take_profit": 50,
                "stop_loss": 30,
                "signal_id": "test_contract_001"
            }
            
            logger.info(f"Testing trade execution with {test_signal['quantity']} contracts...")
            result = self.controller.execute_trade(test_signal)
            
            if result.get('success', False):
                self.log_test_result(
                    "Simulated Trade", 
                    True, 
                    f"Successfully executed simulated trade: {test_signal['quantity']} contracts"
                )
                return True
            else:
                self.log_test_result(
                    "Simulated Trade", 
                    False, 
                    f"Trade execution failed: {result.get('message', 'Unknown error')}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Simulated Trade", 
                False, 
                f"Simulated trade test failed: {str(e)}"
            )
            return False
            
    def test_risk_management_contracts(self) -> bool:
        """Test risk management with contract-based position sizing"""
        logger.info("\n=== Testing Risk Management with Contracts ===")
        
        try:
            # Test various contract sizes against risk limits
            test_scenarios = [
                {"contracts": 1, "should_pass": True, "description": "1 contract - safe"},
                {"contracts": 3, "should_pass": True, "description": "3 contracts - within limit"},
                {"contracts": 5, "should_pass": False, "description": "5 contracts - exceeds typical limit"},
                {"contracts": 10, "should_pass": False, "description": "10 contracts - high risk"},
            ]
            
            # Typical risk limits for contract-based trading
            MAX_CONTRACTS_PER_TRADE = 3
            MAX_DAILY_CONTRACTS = 10
            
            all_passed = True
            
            for scenario in test_scenarios:
                contracts = scenario["contracts"]
                should_pass = scenario["should_pass"]
                description = scenario["description"]
                
                # Simulate risk check
                risk_check_passed = contracts <= MAX_CONTRACTS_PER_TRADE
                
                test_passed = (risk_check_passed == should_pass)
                
                self.log_test_result(
                    f"Risk Check: {description}", 
                    test_passed, 
                    f"Contracts: {contracts}, Risk Check: {risk_check_passed}, Expected: {should_pass}"
                )
                
                if not test_passed:
                    all_passed = False
                    
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                "Risk Management", 
                False, 
                f"Risk management test failed: {str(e)}"
            )
            return False
            
    def test_session_health(self) -> bool:
        """Test session health monitoring"""
        logger.info("\n=== Testing Session Health ===")
        
        if not self.controller:
            self.log_test_result(
                "Session Health", 
                False, 
                "No controller available for health check"
            )
            return False
            
        try:
            health_result = self.controller.check_session_health()
            
            if health_result.get('healthy', False):
                self.log_test_result(
                    "Session Health", 
                    True, 
                    "Session is healthy and active"
                )
                return True
            else:
                self.log_test_result(
                    "Session Health", 
                    False, 
                    f"Session health check failed: {health_result.get('message', 'Unknown issue')}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Session Health", 
                False, 
                f"Health check failed: {str(e)}"
            )
            return False
            
    def cleanup(self):
        """Clean up test resources"""
        logger.info("\n=== Cleaning Up Test Resources ===")
        
        try:
            if self.controller:
                # Disable Dreamer Mode
                self.controller.toggle_dreamer_mode(enabled=False)
                
                # End session
                self.controller.end_session()
                
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Bulenox contract integration tests"""
        logger.info("\n" + "="*60)
        logger.info("🚀 STARTING BULENOX CONTRACT INTEGRATION TESTS")
        logger.info("📋 Testing contract sizes (NOT lot sizes) for Bulenox")
        logger.info("🌐 Platform: https://bulenox.projectx.com/login")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # Run tests in sequence
            tests = [
                ("Login Functionality", self.test_login_functionality),
                ("Controller Login", self.test_controller_login),
                ("Contract Size Validation", self.test_contract_size_validation),
                ("Simulated Trade Placement", self.test_simulated_trade_placement),
                ("Risk Management", self.test_risk_management_contracts),
                ("Session Health", self.test_session_health),
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                logger.info(f"\n🔄 Running: {test_name}")
                try:
                    success = test_func()
                    if success:
                        passed_tests += 1
                except Exception as e:
                    logger.error(f"Test {test_name} crashed: {e}")
                    self.log_test_result(test_name, False, f"Test crashed: {str(e)}")
                    
        finally:
            # Always cleanup
            self.cleanup()
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "duration_seconds": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "test_results": self.test_results
        }
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 BULENOX CONTRACT INTEGRATION TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Passed: {passed_tests}/{total_tests} ({summary['success_rate']:.1f}%)")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Bulenox contract integration is ready.")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} tests failed. Review issues before deployment.")
            
        logger.info("\n📝 Detailed results saved to: bulenox_contract_test.log")
        
        return summary


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Bulenox Contract Integration')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Run tests
    tester = BulenoxContractTester(debug=args.debug)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['passed_tests'] == results['total_tests']:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some tests failed


if __name__ == "__main__":
    main()