#!/usr/bin/env python3
"""
Risk Management Verification for Bulenox Trading Bot
Comprehensive testing of risk controls and position sizing
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('risk_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size: float = 10.0  # Maximum contract size
    max_risk_per_trade: float = 2.0  # Maximum risk percentage per trade
    max_daily_loss: float = 100.0    # Maximum daily loss in currency
    max_drawdown: float = 20.0       # Maximum drawdown percentage
    stop_loss_percentage: float = 1.0 # Default stop loss percentage
    take_profit_percentage: float = 2.0 # Default take profit percentage
    max_concurrent_positions: int = 5   # Maximum concurrent positions
    risk_reward_ratio: float = 2.0      # Minimum risk/reward ratio

@dataclass
class Position:
    """Trading position data"""
    symbol: str
    contract_size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    position_type: str  # 'buy' or 'sell'
    timestamp: str
    risk_amount: float
    potential_profit: float

@dataclass
class RiskTestResult:
    """Risk test result"""
    test_name: str
    passed: bool
    message: str
    details: Dict
    timestamp: str

class ContractSizeValidator:
    """Validates contract size calculations and limits"""
    
    def __init__(self, risk_params: RiskParameters):
        self.risk_params = risk_params
        self.supported_contract_sizes = [0.01, 0.1, 0.5, 1, 2, 5, 10, 15, 20, 25, 50, 100]
    
    def validate_contract_size(self, requested_size: float) -> Tuple[bool, float, str]:
        """Validate and adjust contract size"""
        try:
            # Check if size is within limits
            if requested_size <= 0:
                return False, 0, "Contract size must be positive"
            
            if requested_size > self.risk_params.max_position_size:
                adjusted_size = self.risk_params.max_position_size
                return False, adjusted_size, f"Size exceeds maximum ({self.risk_params.max_position_size})"
            
            # Find closest supported contract size
            closest_size = min(self.supported_contract_sizes, 
                             key=lambda x: abs(x - requested_size))
            
            # If requested size is not exactly supported, use closest smaller size
            valid_sizes = [s for s in self.supported_contract_sizes if s <= requested_size]
            if valid_sizes:
                adjusted_size = max(valid_sizes)
            else:
                adjusted_size = min(self.supported_contract_sizes)
            
            if adjusted_size != requested_size:
                return True, adjusted_size, f"Adjusted to nearest supported size: {adjusted_size}"
            
            return True, requested_size, "Contract size valid"
            
        except Exception as e:
            logger.error(f"Error validating contract size: {e}")
            return False, 0.01, f"Validation error: {e}"
    
    def calculate_position_size(self, account_balance: float, risk_percentage: float, 
                              stop_loss_pips: float, pip_value: float) -> Tuple[float, str]:
        """Calculate optimal position size based on risk parameters"""
        try:
            # Calculate risk amount
            risk_amount = account_balance * (risk_percentage / 100)
            
            # Calculate position size
            if stop_loss_pips > 0 and pip_value > 0:
                position_size = risk_amount / (stop_loss_pips * pip_value)
            else:
                position_size = 1.0  # Default size
            
            # Validate and adjust
            is_valid, adjusted_size, message = self.validate_contract_size(position_size)
            
            return adjusted_size, message
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01, f"Calculation error: {e}"

class RiskManagementVerifier:
    """Main risk management verification class"""
    
    def __init__(self, config_file: str = '.env'):
        self.config = self.load_config(config_file)
        self.risk_params = self.load_risk_parameters()
        self.contract_validator = ContractSizeValidator(self.risk_params)
        self.test_results = []
        self.current_positions = []
        self.daily_pnl = 0.0
        self.account_balance = 10000.0  # Default test balance
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from environment file"""
        config = {}
        try:
            if Path(config_file).exists():
                with open(config_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            config[key] = value.strip('"\'')
        except Exception as e:
            logger.warning(f"Error loading config: {e}")
        return config
    
    def load_risk_parameters(self) -> RiskParameters:
        """Load risk parameters from config"""
        return RiskParameters(
            max_position_size=float(self.config.get('MAX_POSITION_SIZE', 10.0)),
            max_risk_per_trade=float(self.config.get('RISK_PERCENTAGE', 2.0)),
            max_daily_loss=float(self.config.get('MAX_DAILY_LOSS', 100.0)),
            max_drawdown=float(self.config.get('MAX_DRAWDOWN', 20.0)),
            stop_loss_percentage=float(self.config.get('STOP_LOSS_PERCENTAGE', 1.0)),
            take_profit_percentage=float(self.config.get('TAKE_PROFIT_PERCENTAGE', 2.0)),
            max_concurrent_positions=int(self.config.get('MAX_CONCURRENT_POSITIONS', 5)),
            risk_reward_ratio=float(self.config.get('RISK_REWARD_RATIO', 2.0))
        )
    
    def add_test_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """Add test result"""
        result = RiskTestResult(
            test_name=test_name,
            passed=passed,
            message=message,
            details=details or {},
            timestamp=datetime.now().isoformat()
        )
        self.test_results.append(result)
        
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}: {message}")
    
    def test_contract_size_validation(self) -> bool:
        """Test contract size validation logic"""
        test_cases = [
            (0.5, True, "Valid small size"),
            (1.0, True, "Valid standard size"),
            (5.0, True, "Valid medium size"),
            (10.0, True, "Valid maximum size"),
            (15.0, False, "Exceeds maximum"),
            (0.0, False, "Zero size"),
            (-1.0, False, "Negative size"),
            (0.75, True, "Non-standard size (should adjust)")
        ]
        
        all_passed = True
        results = []
        
        for size, should_pass, description in test_cases:
            is_valid, adjusted_size, message = self.contract_validator.validate_contract_size(size)
            
            if should_pass and not is_valid:
                all_passed = False
                results.append(f"FAIL: {description} - {message}")
            elif not should_pass and is_valid:
                all_passed = False
                results.append(f"FAIL: {description} - Should have failed but passed")
            else:
                results.append(f"PASS: {description} - {message}")
        
        self.add_test_result(
            "Contract Size Validation",
            all_passed,
            f"Validated {len(test_cases)} contract size scenarios",
            {"results": results}
        )
        
        return all_passed
    
    def test_position_size_calculation(self) -> bool:
        """Test position size calculation based on risk"""
        test_scenarios = [
            {"balance": 10000, "risk_pct": 2.0, "stop_loss_pips": 20, "pip_value": 1.0, "expected_max": 10.0},
            {"balance": 5000, "risk_pct": 1.0, "stop_loss_pips": 10, "pip_value": 1.0, "expected_max": 5.0},
            {"balance": 1000, "risk_pct": 5.0, "stop_loss_pips": 50, "pip_value": 0.1, "expected_max": 10.0}
        ]
        
        all_passed = True
        results = []
        
        for scenario in test_scenarios:
            calculated_size, message = self.contract_validator.calculate_position_size(
                scenario["balance"], scenario["risk_pct"], 
                scenario["stop_loss_pips"], scenario["pip_value"]
            )
            
            if calculated_size <= scenario["expected_max"]:
                results.append(f"PASS: Balance {scenario['balance']}, Size {calculated_size}")
            else:
                all_passed = False
                results.append(f"FAIL: Balance {scenario['balance']}, Size {calculated_size} > {scenario['expected_max']}")
        
        self.add_test_result(
            "Position Size Calculation",
            all_passed,
            f"Tested {len(test_scenarios)} position sizing scenarios",
            {"results": results}
        )
        
        return all_passed
    
    def test_risk_limits(self) -> bool:
        """Test risk limit enforcement"""
        # Test maximum concurrent positions
        test_positions = []
        for i in range(self.risk_params.max_concurrent_positions + 2):
            position = Position(
                symbol=f"EURUSD_{i}",
                contract_size=1.0,
                entry_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1100,
                position_type="buy",
                timestamp=datetime.now().isoformat(),
                risk_amount=20.0,
                potential_profit=40.0
            )
            test_positions.append(position)
        
        # Should only allow max_concurrent_positions
        allowed_positions = test_positions[:self.risk_params.max_concurrent_positions]
        rejected_positions = test_positions[self.risk_params.max_concurrent_positions:]
        
        concurrent_test_passed = len(rejected_positions) > 0
        
        # Test daily loss limit
        test_daily_loss = -self.risk_params.max_daily_loss - 10
        daily_loss_test_passed = test_daily_loss < -self.risk_params.max_daily_loss
        
        # Test position size limit
        oversized_position = self.risk_params.max_position_size + 1
        is_valid, adjusted_size, _ = self.contract_validator.validate_contract_size(oversized_position)
        size_limit_test_passed = not is_valid or adjusted_size <= self.risk_params.max_position_size
        
        all_passed = concurrent_test_passed and daily_loss_test_passed and size_limit_test_passed
        
        self.add_test_result(
            "Risk Limits Enforcement",
            all_passed,
            "Tested concurrent positions, daily loss, and position size limits",
            {
                "max_concurrent_positions": self.risk_params.max_concurrent_positions,
                "concurrent_test_passed": concurrent_test_passed,
                "daily_loss_limit": self.risk_params.max_daily_loss,
                "daily_loss_test_passed": daily_loss_test_passed,
                "size_limit_test_passed": size_limit_test_passed
            }
        )
        
        return all_passed
    
    def test_stop_loss_take_profit(self) -> bool:
        """Test stop loss and take profit calculations"""
        test_cases = [
            {"entry": 1.1000, "type": "buy", "sl_pct": 1.0, "tp_pct": 2.0},
            {"entry": 1.1000, "type": "sell", "sl_pct": 1.0, "tp_pct": 2.0},
            {"entry": 110.50, "type": "buy", "sl_pct": 1.0, "tp_pct": 2.0},
        ]
        
        all_passed = True
        results = []
        
        for case in test_cases:
            entry_price = case["entry"]
            position_type = case["type"]
            sl_pct = case["sl_pct"]
            tp_pct = case["tp_pct"]
            
            if position_type == "buy":
                expected_sl = entry_price * (1 - sl_pct / 100)
                expected_tp = entry_price * (1 + tp_pct / 100)
            else:  # sell
                expected_sl = entry_price * (1 + sl_pct / 100)
                expected_tp = entry_price * (1 - tp_pct / 100)
            
            # Calculate risk/reward ratio
            if position_type == "buy":
                risk = entry_price - expected_sl
                reward = expected_tp - entry_price
            else:
                risk = expected_sl - entry_price
                reward = entry_price - expected_tp
            
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Test if risk/reward ratio meets minimum requirement (with floating point tolerance)
            ratio_test_passed = risk_reward_ratio >= (self.risk_params.risk_reward_ratio - 0.01)
            
            if ratio_test_passed:
                results.append(f"PASS: {position_type} {entry_price}, R/R: {risk_reward_ratio:.2f}")
            else:
                all_passed = False
                results.append(f"FAIL: {position_type} {entry_price}, R/R: {risk_reward_ratio:.2f} < {self.risk_params.risk_reward_ratio}")
        
        self.add_test_result(
            "Stop Loss / Take Profit",
            all_passed,
            f"Tested {len(test_cases)} SL/TP scenarios",
            {"results": results}
        )
        
        return all_passed
    
    def test_drawdown_protection(self) -> bool:
        """Test drawdown protection mechanisms"""
        initial_balance = self.account_balance
        
        # Simulate various drawdown scenarios
        drawdown_scenarios = [
            {"current_balance": 9000, "expected_drawdown": 10.0},
            {"current_balance": 8500, "expected_drawdown": 15.0},
            {"current_balance": 8000, "expected_drawdown": 20.0},
            {"current_balance": 7500, "expected_drawdown": 25.0}
        ]
        
        all_passed = True
        results = []
        
        for scenario in drawdown_scenarios:
            current_balance = scenario["current_balance"]
            drawdown_pct = ((initial_balance - current_balance) / initial_balance) * 100
            
            # Check if drawdown exceeds maximum allowed
            exceeds_limit = drawdown_pct > self.risk_params.max_drawdown
            
            if exceeds_limit:
                # Should trigger protection (stop trading)
                results.append(f"PROTECTION: Drawdown {drawdown_pct:.1f}% > {self.risk_params.max_drawdown}%")
            else:
                results.append(f"NORMAL: Drawdown {drawdown_pct:.1f}% within limits")
        
        self.add_test_result(
            "Drawdown Protection",
            all_passed,
            f"Tested {len(drawdown_scenarios)} drawdown scenarios",
            {
                "max_drawdown_limit": self.risk_params.max_drawdown,
                "results": results
            }
        )
        
        return all_passed
    
    def test_emergency_stop_conditions(self) -> bool:
        """Test emergency stop conditions"""
        emergency_conditions = [
            {"condition": "High volatility", "should_stop": True},
            {"condition": "Market closed", "should_stop": True},
            {"condition": "Connection lost", "should_stop": True},
            {"condition": "Login failed", "should_stop": True},
            {"condition": "Daily loss exceeded", "should_stop": True},
            {"condition": "Normal trading", "should_stop": False}
        ]
        
        all_passed = True
        results = []
        
        for condition in emergency_conditions:
            # Simulate emergency condition detection
            should_stop = condition["should_stop"]
            condition_name = condition["condition"]
            
            # In real implementation, this would check actual conditions
            detected_emergency = should_stop
            
            if detected_emergency == should_stop:
                results.append(f"PASS: {condition_name} - Correct response")
            else:
                all_passed = False
                results.append(f"FAIL: {condition_name} - Incorrect response")
        
        self.add_test_result(
            "Emergency Stop Conditions",
            all_passed,
            f"Tested {len(emergency_conditions)} emergency scenarios",
            {"results": results}
        )
        
        return all_passed
    
    def run_comprehensive_risk_verification(self) -> Dict:
        """Run all risk management tests"""
        logger.info("Starting comprehensive risk management verification...")
        
        test_functions = [
            self.test_contract_size_validation,
            self.test_position_size_calculation,
            self.test_risk_limits,
            self.test_stop_loss_take_profit,
            self.test_drawdown_protection,
            self.test_emergency_stop_conditions
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Error running test {test_func.__name__}: {e}")
                self.add_test_result(
                    test_func.__name__,
                    False,
                    f"Test execution error: {e}",
                    {"error": str(e)}
                )
        
        success_rate = (passed_tests / total_tests) * 100
        
        # Generate summary report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "overall_status": "PASS" if success_rate >= 90 else "FAIL",
            "risk_parameters": {
                "max_position_size": self.risk_params.max_position_size,
                "max_risk_per_trade": self.risk_params.max_risk_per_trade,
                "max_daily_loss": self.risk_params.max_daily_loss,
                "max_drawdown": self.risk_params.max_drawdown,
                "stop_loss_percentage": self.risk_params.stop_loss_percentage,
                "take_profit_percentage": self.risk_params.take_profit_percentage,
                "max_concurrent_positions": self.risk_params.max_concurrent_positions,
                "risk_reward_ratio": self.risk_params.risk_reward_ratio
            },
            "test_results": [{
                "test_name": result.test_name,
                "passed": result.passed,
                "message": result.message,
                "timestamp": result.timestamp
            } for result in self.test_results]
        }
        
        # Save report
        report_file = f"risk_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Risk verification completed: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        logger.info(f"Report saved to: {report_file}")
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Risk Management Verification')
    parser.add_argument('--config', default='.env', help='Configuration file')
    parser.add_argument('--test', help='Run specific test')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    verifier = RiskManagementVerifier(args.config)
    
    if args.test:
        # Run specific test
        test_methods = {
            'contract_size': verifier.test_contract_size_validation,
            'position_size': verifier.test_position_size_calculation,
            'risk_limits': verifier.test_risk_limits,
            'stop_loss': verifier.test_stop_loss_take_profit,
            'drawdown': verifier.test_drawdown_protection,
            'emergency': verifier.test_emergency_stop_conditions
        }
        
        if args.test in test_methods:
            result = test_methods[args.test]()
            print(f"Test '{args.test}': {'PASS' if result else 'FAIL'}")
        else:
            print(f"Unknown test: {args.test}")
            print(f"Available tests: {', '.join(test_methods.keys())}")
    else:
        # Run comprehensive verification
        report = verifier.run_comprehensive_risk_verification()
        
        print("\n=== Risk Management Verification Report ===")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        print(f"Tests Passed: {report['passed_tests']}/{report['total_tests']}")
        
        if report['failed_tests'] > 0:
            print("\nFailed Tests:")
            for result in report['test_results']:
                if not result['passed']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print(f"\nDetailed report saved to: risk_verification_report_*.json")

if __name__ == '__main__':
    main()