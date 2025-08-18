#!/usr/bin/env python3
"""
validate_live_trading_contracts.py
Live Trading Validation for Playwright-based Bulenox Bot

Features:
- Contract-based trading validation
- Risk management verification
- Live platform connectivity testing
- Position sizing validation
- Trade execution monitoring
- Emergency stop mechanisms

Author: TRAE-SentinelOps
Version: 2.0.0 (Playwright Edition)
Date: 2025-01-17
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Import our Playwright implementation
try:
    from bulenox_ai_playwright_contracts import BulenoxPlaywrightTrader
except ImportError:
    print("❌ Error: bulenox_ai_playwright_contracts.py not found")
    print("Please ensure the Playwright implementation is available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LiveTradingValidator')

class LiveTradingValidator:
    """Comprehensive live trading validation system"""
    
    def __init__(self, test_mode: bool = True, max_contract_size: int = 5):
        self.test_mode = test_mode
        self.max_contract_size = max_contract_size
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'test_mode': test_mode,
            'tests_run': [],
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'critical_issues': [],
            'recommendations': []
        }
        
        # Trading parameters for validation
        self.test_symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        self.test_contract_sizes = [1, 2, 3, 5]  # Contract sizes to test
        
        # Risk management limits
        self.max_daily_trades = 10
        self.max_drawdown_percent = 5.0
        self.max_position_size = 10  # contracts
        
        # Initialize trader
        self.trader = None
        
    async def initialize_trader(self) -> bool:
        """Initialize Playwright trader instance"""
        logger.info("🎭 Initializing Playwright trader...")
        
        try:
            self.trader = BulenoxPlaywrightTrader(
                headless=True,
                test_mode=self.test_mode
            )
            
            # Test browser initialization
            await self.trader.initialize()
            
            logger.info("✅ Playwright trader initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize trader: {e}")
            self.validation_results['critical_issues'].append(f"Trader initialization failed: {e}")
            return False
            
    async def test_platform_connectivity(self) -> bool:
        """Test connectivity to Bulenox platform"""
        test_name = "Platform Connectivity"
        logger.info(f"🌐 Testing {test_name}...")
        
        try:
            # Test login
            login_success = await self.trader.login()
            
            if login_success:
                logger.info("✅ Platform login successful")
                
                # Test platform responsiveness
                await asyncio.sleep(2)
                
                # Check if we can access trading interface
                trading_ready = await self.trader.check_trading_ready()
                
                if trading_ready:
                    logger.info("✅ Trading interface accessible")
                    self._record_test_result(test_name, True, "Platform fully accessible")
                    return True
                else:
                    logger.warning("⚠️  Trading interface not ready")
                    self._record_test_result(test_name, False, "Trading interface not accessible")
                    return False
            else:
                logger.error("❌ Platform login failed")
                self._record_test_result(test_name, False, "Login failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connectivity test failed: {e}")
            self._record_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_contract_size_validation(self) -> bool:
        """Test contract size validation logic"""
        test_name = "Contract Size Validation"
        logger.info(f"📊 Testing {test_name}...")
        
        validation_tests = [
            # (input_quantity, expected_contracts, description)
            (0.5, 1, "Sub-contract rounds up to 1"),
            (1.0, 1, "Exact 1 contract"),
            (1.5, 2, "1.5 rounds up to 2 contracts"),
            (2.0, 2, "Exact 2 contracts"),
            (5.0, 5, "5 contracts"),
            (10.0, 10, "10 contracts (max test)"),
            (0, 1, "Zero quantity defaults to 1 contract"),
            (-1, 1, "Negative quantity defaults to 1 contract")
        ]
        
        all_passed = True
        
        for input_qty, expected_contracts, description in validation_tests:
            try:
                # Test contract validation function
                validated_contracts = self.trader.validate_contract_size(input_qty)
                
                if validated_contracts == expected_contracts:
                    logger.info(f"✅ {description}: {input_qty} → {validated_contracts} contracts")
                else:
                    logger.error(f"❌ {description}: Expected {expected_contracts}, got {validated_contracts}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ Contract validation error for {input_qty}: {e}")
                all_passed = False
                
        self._record_test_result(test_name, all_passed, 
                               f"Tested {len(validation_tests)} contract size scenarios")
        return all_passed
        
    async def test_risk_management(self) -> bool:
        """Test risk management controls"""
        test_name = "Risk Management"
        logger.info(f"🛡️  Testing {test_name}...")
        
        risk_tests = [
            # Test maximum position size
            (self.max_position_size + 1, False, "Reject oversized position"),
            (self.max_position_size, True, "Accept maximum position"),
            (self.max_position_size - 1, True, "Accept normal position"),
            
            # Test contract limits
            (50, False, "Reject excessive contracts"),
            (20, False, "Reject large contracts"),
            (10, True, "Accept reasonable contracts"),
            (5, True, "Accept small contracts"),
            (1, True, "Accept minimum contracts")
        ]
        
        all_passed = True
        
        for contract_size, should_pass, description in risk_tests:
            try:
                # Test risk validation
                risk_check = self.trader.validate_risk_limits(
                    symbol='EURUSD',
                    side='BUY',
                    contracts=contract_size
                )
                
                if risk_check == should_pass:
                    logger.info(f"✅ {description}: {contract_size} contracts → {'Accepted' if should_pass else 'Rejected'}")
                else:
                    logger.error(f"❌ {description}: Expected {'pass' if should_pass else 'fail'}, got {'pass' if risk_check else 'fail'}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ Risk management error for {contract_size} contracts: {e}")
                all_passed = False
                
        self._record_test_result(test_name, all_passed, 
                               f"Tested {len(risk_tests)} risk management scenarios")
        return all_passed
        
    async def test_simulated_trading(self) -> bool:
        """Test simulated trading execution"""
        test_name = "Simulated Trading"
        logger.info(f"📈 Testing {test_name}...")
        
        if not self.test_mode:
            logger.warning("⚠️  Skipping simulated trading - not in test mode")
            self._record_test_result(test_name, True, "Skipped - live mode")
            return True
            
        trading_scenarios = [
            ('EURUSD', 'BUY', 1, "Basic buy order"),
            ('EURUSD', 'SELL', 2, "Basic sell order"),
            ('GBPUSD', 'BUY', 3, "Multi-contract buy"),
            ('USDJPY', 'SELL', 1, "JPY pair sell")
        ]
        
        all_passed = True
        
        for symbol, side, contracts, description in trading_scenarios:
            try:
                logger.info(f"🔄 Testing: {description} - {contracts} contracts of {symbol} {side}")
                
                # Simulate trade placement
                trade_result = await self.trader.place_trade_simulation(
                    symbol=symbol,
                    side=side,
                    contracts=contracts
                )
                
                if trade_result and trade_result.get('success'):
                    logger.info(f"✅ {description}: Trade simulation successful")
                    
                    # Verify contract size in result
                    result_contracts = trade_result.get('contracts', 0)
                    if result_contracts == contracts:
                        logger.info(f"✅ Contract size verified: {result_contracts}")
                    else:
                        logger.error(f"❌ Contract size mismatch: Expected {contracts}, got {result_contracts}")
                        all_passed = False
                        
                else:
                    logger.error(f"❌ {description}: Trade simulation failed")
                    all_passed = False
                    
                # Wait between trades
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Trading simulation error for {description}: {e}")
                all_passed = False
                
        self._record_test_result(test_name, all_passed, 
                               f"Tested {len(trading_scenarios)} trading scenarios")
        return all_passed
        
    async def test_emergency_controls(self) -> bool:
        """Test emergency stop and control mechanisms"""
        test_name = "Emergency Controls"
        logger.info(f"🚨 Testing {test_name}...")
        
        try:
            # Test emergency stop
            logger.info("Testing emergency stop mechanism...")
            emergency_result = await self.trader.emergency_stop()
            
            if emergency_result:
                logger.info("✅ Emergency stop mechanism working")
                
                # Test system recovery
                await asyncio.sleep(2)
                recovery_result = await self.trader.recover_from_emergency()
                
                if recovery_result:
                    logger.info("✅ Emergency recovery successful")
                    self._record_test_result(test_name, True, "Emergency controls functional")
                    return True
                else:
                    logger.error("❌ Emergency recovery failed")
                    self._record_test_result(test_name, False, "Recovery failed")
                    return False
            else:
                logger.error("❌ Emergency stop failed")
                self._record_test_result(test_name, False, "Emergency stop failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Emergency controls test failed: {e}")
            self._record_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_session_management(self) -> bool:
        """Test session management and persistence"""
        test_name = "Session Management"
        logger.info(f"🔄 Testing {test_name}...")
        
        try:
            # Test session health
            session_health = await self.trader.check_session_health()
            
            if session_health:
                logger.info("✅ Session health check passed")
                
                # Test session persistence
                session_data = await self.trader.get_session_data()
                
                if session_data and 'login_time' in session_data:
                    logger.info("✅ Session persistence working")
                    
                    # Test session refresh
                    refresh_result = await self.trader.refresh_session()
                    
                    if refresh_result:
                        logger.info("✅ Session refresh successful")
                        self._record_test_result(test_name, True, "Session management functional")
                        return True
                    else:
                        logger.warning("⚠️  Session refresh failed")
                        self._record_test_result(test_name, False, "Session refresh failed")
                        return False
                else:
                    logger.error("❌ Session data not available")
                    self._record_test_result(test_name, False, "Session data unavailable")
                    return False
            else:
                logger.error("❌ Session health check failed")
                self._record_test_result(test_name, False, "Session unhealthy")
                return False
                
        except Exception as e:
            logger.error(f"❌ Session management test failed: {e}")
            self._record_test_result(test_name, False, f"Exception: {e}")
            return False
            
    def _record_test_result(self, test_name: str, passed: bool, details: str):
        """Record test result"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.validation_results['tests_run'].append(result)
        
        if passed:
            self.validation_results['passed'] += 1
        else:
            self.validation_results['failed'] += 1
            
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("🚀 Starting comprehensive live trading validation...")
        logger.info("=" * 60)
        
        # Initialize trader
        if not await self.initialize_trader():
            logger.error("❌ Cannot proceed - trader initialization failed")
            return self.validation_results
            
        # Run validation tests
        validation_tests = [
            ("Platform Connectivity", self.test_platform_connectivity),
            ("Contract Size Validation", self.test_contract_size_validation),
            ("Risk Management", self.test_risk_management),
            ("Simulated Trading", self.test_simulated_trading),
            ("Emergency Controls", self.test_emergency_controls),
            ("Session Management", self.test_session_management)
        ]
        
        for test_name, test_func in validation_tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ Test crashed: {test_name} - {e}")
                self._record_test_result(test_name, False, f"Test crashed: {e}")
                
        # Generate recommendations
        self._generate_recommendations()
        
        # Calculate success rate
        total_tests = self.validation_results['passed'] + self.validation_results['failed']
        success_rate = (self.validation_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        self.validation_results['success_rate'] = success_rate
        self.validation_results['total_tests'] = total_tests
        
        # Cleanup
        if self.trader:
            await self.trader.cleanup()
            
        logger.info("=" * 60)
        logger.info(f"🎯 Validation Complete: {success_rate:.1f}% success rate")
        logger.info(f"✅ Passed: {self.validation_results['passed']}")
        logger.info(f"❌ Failed: {self.validation_results['failed']}")
        
        return self.validation_results
        
    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check success rate
        total_tests = self.validation_results['passed'] + self.validation_results['failed']
        if total_tests > 0:
            success_rate = self.validation_results['passed'] / total_tests
            
            if success_rate < 0.8:
                recommendations.append("❌ CRITICAL: Success rate below 80% - review failed tests before live deployment")
            elif success_rate < 0.9:
                recommendations.append("⚠️  WARNING: Success rate below 90% - consider addressing failed tests")
            else:
                recommendations.append("✅ GOOD: High success rate - system appears ready for deployment")
                
        # Check for critical issues
        if self.validation_results['critical_issues']:
            recommendations.append("🚨 CRITICAL ISSUES FOUND - Must be resolved before live trading")
            
        # Contract-specific recommendations
        recommendations.extend([
            "📊 Ensure contract sizes are properly validated in live environment",
            "🛡️  Monitor risk management controls during initial live trading",
            "📈 Start with minimum contract sizes (1 contract) for initial validation",
            "🔄 Implement gradual scaling of position sizes after successful validation",
            "📋 Maintain detailed logs of all contract-based trades for audit"
        ])
        
        self.validation_results['recommendations'] = recommendations
        
    def save_results(self, filename: str = None):
        """Save validation results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"live_trading_validation_{timestamp}.json"
            
        try:
            with open(filename, 'w') as f:
                json.dump(self.validation_results, f, indent=2)
            logger.info(f"📄 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
            

async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Live Trading Validation for Bulenox Bot')
    parser.add_argument('--live-mode', action='store_true', help='Run in live trading mode (DANGEROUS)')
    parser.add_argument('--max-contracts', type=int, default=5, help='Maximum contract size for testing')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    # Safety check for live mode
    if args.live_mode:
        print("⚠️  WARNING: Live trading mode enabled!")
        print("This will execute real trades with real money.")
        confirmation = input("Type 'CONFIRM_LIVE_TRADING' to proceed: ")
        
        if confirmation != 'CONFIRM_LIVE_TRADING':
            print("❌ Live trading not confirmed. Exiting.")
            sys.exit(1)
            
    # Create validator
    validator = LiveTradingValidator(
        test_mode=not args.live_mode,
        max_contract_size=args.max_contracts
    )
    
    try:
        # Run validation
        results = await validator.run_comprehensive_validation()
        
        # Save results
        validator.save_results(args.output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        
        if results['critical_issues']:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in results['critical_issues']:
                print(f"  - {issue}")
                
        print("\n💡 RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"  - {rec}")
            
        # Exit code based on results
        if results['success_rate'] >= 90:
            print("\n🎉 Validation PASSED - System ready for deployment")
            sys.exit(0)
        elif results['success_rate'] >= 80:
            print("\n⚠️  Validation PARTIAL - Review issues before deployment")
            sys.exit(1)
        else:
            print("\n❌ Validation FAILED - Critical issues must be resolved")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n👋 Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Validation crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())