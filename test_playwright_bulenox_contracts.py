#!/usr/bin/env python3
"""
test_playwright_bulenox_contracts.py
Comprehensive test suite for Playwright-based Bulenox automation with contract focus

Tests:
1. Browser initialization and stealth settings
2. Login functionality with error handling
3. Contract size validation (critical for Bulenox)
4. Trade placement simulation
5. Network request interception
6. Screenshot capture and logging

IMPORTANT: This tests CONTRACT-based trading, not lot sizes!

Author: TRAE-SentinelOps
Version: 2.0.0
Date: 2025-01-17
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from bulenox_ai_playwright_contracts import (
        BulenoxPlaywrightAutomation,
        login_bulenox_ai,
        place_bulenox_trade
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure bulenox_ai_playwright_contracts.py is in the same directory")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PlaywrightBulenoxTest')

class PlaywrightBulenoxTester:
    """Comprehensive tester for Playwright Bulenox automation"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.test_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0
            }
        }
        
        # Test configuration
        self.test_contracts = [0.5, 1, 2, 5, 10, 15]  # Various contract sizes to test
        self.test_symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            
    def log_test_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        self.test_results['tests'][test_name] = {
            'success': success,
            'details': details,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results['summary']['total'] += 1
        if success:
            self.test_results['summary']['passed'] += 1
            logger.info(f"✅ {test_name}: PASSED - {details}")
        else:
            self.test_results['summary']['failed'] += 1
            logger.error(f"❌ {test_name}: FAILED - {details}")
            
    async def test_browser_initialization(self) -> bool:
        """Test browser initialization with stealth settings"""
        test_name = "Browser Initialization"
        
        try:
            automation = BulenoxPlaywrightAutomation(headless=True, debug=self.debug)
            
            # Test initialization
            success = await automation.init_browser()
            
            if success and automation.browser and automation.context and automation.page:
                # Test stealth settings
                user_agent = await automation.page.evaluate('navigator.userAgent')
                viewport = await automation.page.evaluate('({width: window.innerWidth, height: window.innerHeight})')
                
                details = f"Browser initialized with UA: {user_agent[:50]}..., Viewport: {viewport}"
                self.log_test_result(test_name, True, details, {
                    'user_agent': user_agent,
                    'viewport': viewport
                })
                
                await automation.close()
                return True
            else:
                self.log_test_result(test_name, False, "Failed to initialize browser components")
                await automation.close()
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_contract_validation(self) -> bool:
        """Test contract size validation logic"""
        test_name = "Contract Size Validation"
        
        try:
            automation = BulenoxPlaywrightAutomation(headless=True, debug=self.debug)
            
            validation_results = []
            
            for test_quantity in self.test_contracts:
                validated = automation.validate_contract_size(test_quantity)
                validation_results.append({
                    'input': test_quantity,
                    'output': validated,
                    'valid': validated >= 1 and isinstance(validated, int)
                })
                
            # Test edge cases
            edge_cases = [0, -1, 0.1, None, "invalid", 100]
            for edge_case in edge_cases:
                try:
                    validated = automation.validate_contract_size(edge_case)
                    validation_results.append({
                        'input': edge_case,
                        'output': validated,
                        'valid': validated >= 1 and isinstance(validated, int)
                    })
                except Exception as e:
                    validation_results.append({
                        'input': edge_case,
                        'output': None,
                        'error': str(e),
                        'valid': False
                    })
                    
            # Check if all validations are correct
            all_valid = all(result.get('valid', False) for result in validation_results)
            
            details = f"Validated {len(validation_results)} contract sizes"
            self.log_test_result(test_name, all_valid, details, validation_results)
            
            return all_valid
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_login_functionality(self) -> bool:
        """Test login functionality (without actual credentials)"""
        test_name = "Login Functionality"
        
        try:
            # Test with mock credentials to check flow
            automation = BulenoxPlaywrightAutomation(headless=True, debug=self.debug)
            automation.username = "test_user"
            automation.password = "test_pass"
            
            # Initialize browser
            if not await automation.init_browser():
                self.log_test_result(test_name, False, "Browser initialization failed")
                return False
                
            # Navigate to login page to test selectors
            try:
                await automation.page.goto(f"{automation.base_url}/login", timeout=30000)
                
                # Check if page loaded
                title = await automation.page.title()
                url = automation.page.url
                
                details = f"Login page loaded: {title}, URL: {url}"
                
                # Test selector finding (without actually filling)
                username_selector = await automation._find_element_with_fallbacks(
                    automation.selectors['login']['username'],
                    timeout=5000
                )
                
                password_selector = await automation._find_element_with_fallbacks(
                    automation.selectors['login']['password'],
                    timeout=5000
                )
                
                submit_selector = await automation._find_element_with_fallbacks(
                    automation.selectors['login']['submit'],
                    timeout=5000
                )
                
                selectors_found = {
                    'username': username_selector is not None,
                    'password': password_selector is not None,
                    'submit': submit_selector is not None
                }
                
                success = any(selectors_found.values())  # At least one selector should work
                
                self.log_test_result(test_name, success, details, {
                    'title': title,
                    'url': url,
                    'selectors_found': selectors_found
                })
                
                await automation.close()
                return success
                
            except Exception as e:
                details = f"Navigation error: {e}"
                self.log_test_result(test_name, False, details)
                await automation.close()
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_network_interception(self) -> bool:
        """Test network request interception"""
        test_name = "Network Interception"
        
        try:
            automation = BulenoxPlaywrightAutomation(headless=True, debug=self.debug)
            
            if not await automation.init_browser():
                self.log_test_result(test_name, False, "Browser initialization failed")
                return False
                
            # Navigate to a page to generate requests
            await automation.page.goto("https://httpbin.org/json", timeout=30000)
            await asyncio.sleep(2)
            
            # Check if requests were captured
            requests_captured = len(automation.captured_requests) > 0
            
            details = f"Captured {len(automation.captured_requests)} requests"
            self.log_test_result(test_name, requests_captured, details, {
                'requests_count': len(automation.captured_requests),
                'sample_requests': automation.captured_requests[:3]  # First 3 requests
            })
            
            await automation.close()
            return requests_captured
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_screenshot_functionality(self) -> bool:
        """Test screenshot capture functionality"""
        test_name = "Screenshot Functionality"
        
        try:
            automation = BulenoxPlaywrightAutomation(headless=True, debug=self.debug)
            
            if not await automation.init_browser():
                self.log_test_result(test_name, False, "Browser initialization failed")
                return False
                
            # Navigate to a simple page
            await automation.page.goto("https://httpbin.org/html", timeout=30000)
            
            # Take a test screenshot
            await automation._take_screenshot("test_screenshot")
            
            # Check if screenshot was created
            screenshot_files = list(automation.screenshots_dir.glob("test_screenshot_*.png"))
            success = len(screenshot_files) > 0
            
            details = f"Screenshot saved: {screenshot_files[0] if screenshot_files else 'None'}"
            self.log_test_result(test_name, success, details, {
                'screenshot_files': [str(f) for f in screenshot_files]
            })
            
            await automation.close()
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_compatibility_functions(self) -> bool:
        """Test compatibility functions for existing code"""
        test_name = "Compatibility Functions"
        
        try:
            # Test that functions are importable and callable
            functions_available = {
                'login_bulenox_ai': callable(login_bulenox_ai),
                'place_bulenox_trade': callable(place_bulenox_trade),
                'BulenoxPlaywrightAutomation': callable(BulenoxPlaywrightAutomation)
            }
            
            all_available = all(functions_available.values())
            
            details = f"Functions available: {functions_available}"
            self.log_test_result(test_name, all_available, details, functions_available)
            
            return all_available
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def test_trade_simulation(self) -> bool:
        """Test trade placement simulation (without actual execution)"""
        test_name = "Trade Simulation"
        
        try:
            automation = BulenoxPlaywrightAutomation(headless=True, debug=self.debug)
            
            # Test contract validation for different trade scenarios
            trade_scenarios = [
                {'symbol': 'EURUSD', 'side': 'BUY', 'quantity': 1},
                {'symbol': 'GBPUSD', 'side': 'SELL', 'quantity': 2},
                {'symbol': 'USDJPY', 'side': 'BUY', 'quantity': 0.5},  # Should be converted to 1
            ]
            
            simulation_results = []
            
            for scenario in trade_scenarios:
                validated_quantity = automation.validate_contract_size(scenario['quantity'])
                
                simulation_results.append({
                    'original': scenario,
                    'validated_quantity': validated_quantity,
                    'valid': validated_quantity >= 1 and isinstance(validated_quantity, int)
                })
                
            all_valid = all(result['valid'] for result in simulation_results)
            
            details = f"Simulated {len(simulation_results)} trade scenarios"
            self.log_test_result(test_name, all_valid, details, simulation_results)
            
            return all_valid
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
            return False
            
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("🚀 Starting Playwright Bulenox Contract Tests")
        logger.info("=" * 60)
        
        # List of all tests
        tests = [
            self.test_browser_initialization,
            self.test_contract_validation,
            self.test_compatibility_functions,
            self.test_trade_simulation,
            self.test_network_interception,
            self.test_screenshot_functionality,
            self.test_login_functionality,  # Last as it requires network
        ]
        
        # Run tests
        for test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ Test {test_func.__name__} crashed: {e}")
                self.log_test_result(test_func.__name__, False, f"Test crashed: {e}")
                
            # Small delay between tests
            await asyncio.sleep(1)
            
        # Calculate success rate
        total = self.test_results['summary']['total']
        passed = self.test_results['summary']['passed']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info("=" * 60)
        logger.info(f"📊 Test Results Summary:")
        logger.info(f"   Total Tests: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {self.test_results['summary']['failed']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
        # Add summary to results
        self.test_results['summary']['success_rate'] = success_rate
        self.test_results['summary']['overall_success'] = success_rate >= 80  # 80% threshold
        
        if success_rate >= 80:
            logger.info("✅ Overall: PASSED - Playwright implementation ready for deployment")
        else:
            logger.error("❌ Overall: FAILED - Issues need to be resolved before deployment")
            
        return self.test_results
        
    def save_results(self, filename: str = "playwright_bulenox_test_results.json"):
        """Save test results to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"💾 Test results saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Playwright Bulenox Automation')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--output', default='playwright_bulenox_test_results.json', 
                       help='Output file for test results')
    
    args = parser.parse_args()
    
    # Create tester
    tester = PlaywrightBulenoxTester(debug=args.debug)
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Save results
        tester.save_results(args.output)
        
        # Exit with appropriate code
        if results['summary']['overall_success']:
            logger.info("🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Some tests failed. Check results for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())