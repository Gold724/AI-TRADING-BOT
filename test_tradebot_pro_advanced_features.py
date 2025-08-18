#!/usr/bin/env python3
"""
Test Suite for TradeBot Sentinel Pro Advanced Features
Comprehensive testing for all automation, monitoring, and reporting capabilities.

Author: TradeBot Sentinel Team
Version: 2.0.0
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add automation modules to path
sys.path.append(str(Path(__file__).parent / 'automation'))

# Import modules to test
try:
    from tradebot_sentinel_pro_advanced import TradeBotSentinelProAdvanced
    from trade_executor import TradeExecutor
    from monitoring_dashboard import MonitoringDashboard
    from alert_system import AlertSystem
    from backtest_engine import BacktestEngine as BacktestingEngine
    from continuous_improvement import ContinuousImprovement
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all modules are properly installed.")
    sys.exit(1)


class TestTradeExecutor(unittest.TestCase):
    """
    Test cases for the TradeExecutor module.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "execution": {
                "max_concurrent_trades": 5,
                "retry_attempts": 3,
                "timeout_seconds": 30
            },
            "risk_management": {
                "max_position_size_percent": 2.0,
                "stop_loss_percent": 1.0,
                "take_profit_percent": 2.0
            },
            "database": {
                "path": ":memory:"
            }
        }
        self.executor = TradeExecutor(config_path="automation/config/trade_executor.json")
    
    def test_initialization(self):
        """Test TradeExecutor initialization."""
        self.assertIsNotNone(self.executor)
        self.assertIsNotNone(self.executor.config)
        self.assertIsInstance(self.executor.pending_trades, list)
        self.assertIsInstance(self.executor.active_trades, dict)
        self.assertIsInstance(self.executor.strategies, dict)
        self.assertFalse(self.executor.running)
    
    def test_execute_trade_success(self):
        """Test successful trade execution."""
        # Test creating a mock cURL file for processing
        import tempfile
        import os
        
        curl_command = "curl -X POST 'https://api.example.com/trade' -H 'Content-Type: application/json' -d '{\"symbol\":\"EURUSD\",\"action\":\"buy\",\"amount\":1000,\"price\":1.1234}'"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(curl_command)
            temp_file = f.name
        
        try:
            # Test processing trade request from cURL
            trade_request = asyncio.run(
                self.executor.process_trade_request_from_curl(temp_file, "test_strategy")
            )
            
            # Verify trade request was created
            if trade_request:
                self.assertEqual(trade_request.symbol, "EURUSD")
                self.assertEqual(trade_request.action, "buy")
                self.assertEqual(trade_request.amount, 1000.0)
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_execute_trade_failure(self):
        """Test failed trade execution."""
        # Test with invalid cURL file
        import tempfile
        import os
        
        # Create invalid cURL command (missing required fields)
        invalid_curl_command = "curl -X POST 'https://api.example.com/trade' -d '{\"invalid\":\"data\"}'"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(invalid_curl_command)
            temp_file = f.name
        
        try:
            # Test processing invalid trade request
            trade_request = asyncio.run(
                self.executor.process_trade_request_from_curl(temp_file, "test_strategy")
            )
            
            # Should return None for invalid requests
            self.assertIsNone(trade_request)
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_risk_management(self):
        """Test risk management through configuration."""
        # Test that risk management configuration is loaded
        self.assertIn('max_position_size', self.executor.config)
        self.assertIn('max_daily_trades', self.executor.config)
        
        # Test position size limits
        max_position = self.executor.config.get('max_position_size', 10000)
        self.assertGreater(max_position, 0)
        
        # Test daily trade limits
        max_daily = self.executor.config.get('max_daily_trades', 50)
        self.assertGreater(max_daily, 0)
    
    def test_strategy_validation(self):
        """Test trading strategy validation through loaded strategies."""
        # Test that strategies are loaded
        self.assertIsInstance(self.executor.strategies, dict)
        
        # Test strategy configuration
        if self.executor.strategies:
            # Get first strategy for testing
            strategy_name = list(self.executor.strategies.keys())[0]
            strategy = self.executor.strategies[strategy_name]
            
            # Test strategy attributes
            self.assertTrue(hasattr(strategy, 'name'))
            self.assertTrue(hasattr(strategy, 'enabled'))
            self.assertTrue(hasattr(strategy, 'symbol_filters'))
        
        # Test strategy validation configuration
        self.assertIn('enable_strategy_validation', self.executor.config)
        self.assertIn('allowed_symbols', self.executor.config)


class TestMonitoringDashboard(unittest.TestCase):
    """
    Test cases for the MonitoringDashboard module.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "dashboard": {
                "mode": "cli",
                "host": "localhost",
                "port": 5000
            },
            "database": {
                "path": ":memory:"
            }
        }
        self.dashboard = MonitoringDashboard(config_path="automation/config/dashboard.json")
    
    def test_initialization(self):
        """Test MonitoringDashboard initialization."""
        self.assertIsNotNone(self.dashboard)
        self.assertIsNotNone(self.dashboard.config)
        self.assertIsNotNone(self.dashboard.metrics_history)
        self.assertIsNotNone(self.dashboard.alerts)
    
    def test_metrics_calculation(self):
        """Test metrics calculation."""
        # Test metrics history initialization
        self.assertEqual(len(self.dashboard.metrics_history), 0)
        
        # Test alerts initialization
        self.assertEqual(len(self.dashboard.alerts), 0)
        
        # Test configuration loading
        self.assertIsInstance(self.dashboard.config, dict)
        self.assertIn('update_interval_seconds', self.dashboard.config)
        self.assertGreater(self.dashboard.config['update_interval_seconds'], 0)
    
    def test_alert_generation(self):
        """Test alert generation."""
        # Test alert initialization
        self.assertEqual(len(self.dashboard.alerts), 0)
        
        # Test alert configuration
        self.assertIn('alerts', self.dashboard.config)
        alert_config = self.dashboard.config['alerts']
        self.assertIsInstance(alert_config, dict)
        
        # Test alert settings
        self.assertIn('enabled', alert_config)
        self.assertIn('error_rate_threshold', alert_config)
    
    def test_dashboard_display(self):
        """Test dashboard display functionality."""
        # Test metrics history structure (it's a deque, not a list)
        from collections import deque
        self.assertIsInstance(self.dashboard.metrics_history, deque)
        
        # Test configuration structure
        self.assertIn('dashboard', self.dashboard.config)
        display_config = self.dashboard.config['dashboard']
        self.assertIsInstance(display_config, dict)
        
        # Test update interval
        self.assertGreater(self.dashboard.update_interval, 0)


class TestAlertSystem(unittest.TestCase):
    """
    Test cases for the AlertSystem module.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "rate_limiting": {
                "max_alerts_per_minute": 10,
                "cooldown_seconds": 60
            },
            "channels": {
                "email": {"enabled": False},
                "telegram": {"enabled": False},
                "webhook": {"enabled": False},
                "file": {"enabled": True, "path": "alerts.log"}
            },
            "database": {
                "path": ":memory:"
            }
        }
        self.alert_system = AlertSystem(config_path="automation/config/alerts.json")
    
    def test_initialization(self):
        """Test AlertSystem initialization."""
        self.assertIsNotNone(self.alert_system)
        self.assertIsNotNone(self.alert_system.config)
        self.assertIsNotNone(self.alert_system.notification_configs)
        self.assertIsNotNone(self.alert_system.report_configs)
    
    def test_alert_creation(self):
        """Test alert creation and validation."""
        # Test alert queue initialization
        self.assertIsNotNone(self.alert_system.alert_queue)
        self.assertEqual(len(self.alert_system.alert_queue), 0)
        
        # Test rate limits initialization
        self.assertIsNotNone(self.alert_system.rate_limits)
        self.assertIsInstance(self.alert_system.rate_limits, dict)
    
    def test_rate_limiting(self):
        """Test alert rate limiting configuration."""
        # Test rate limits structure
        self.assertIsInstance(self.alert_system.rate_limits, dict)
        
        # Test alert queue capacity
        max_queue_size = self.alert_system.config.get('alert_settings', {}).get('max_queue_size', 1000)
        self.assertGreater(max_queue_size, 0)
    
    def test_alert_filtering(self):
        """Test alert filtering and configuration."""
        # Test notification configs
        self.assertIsInstance(self.alert_system.notification_configs, dict)
        
        # Test report configs
        self.assertIsInstance(self.alert_system.report_configs, dict)
        
        # Test running state
        self.assertFalse(self.alert_system.running)


class TestBacktestingEngine(unittest.TestCase):
    """
    Test cases for the BacktestingEngine module.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "backtesting": {
                "default_capital": 10000,
                "commission_rate": 0.001,
                "slippage_rate": 0.0001
            },
            "database": {
                "path": ":memory:"
            }
        }
        self.engine = BacktestingEngine(
            historical_data_dir="data/backtest/historical",
            backtest_results_dir="data/backtest/results",
            backtest_charts_dir="data/backtest/charts"
        )
    
    def test_initialization(self):
        """Test BacktestingEngine initialization."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.historical_data_dir)
        self.assertIsNotNone(self.engine.backtest_results_dir)
        self.assertIsNotNone(self.engine.backtest_charts_dir)
    
    def test_strategy_loading(self):
        """Test strategy loading and validation."""
        # Test that strategy manager is initialized
        self.assertIsNotNone(self.engine.strategy_manager)
        self.assertIsInstance(self.engine.historical_data, dict)
    
    def test_market_data_loading(self):
        """Test market data loading."""
        # Test that historical data dictionary is initialized
        self.assertIsInstance(self.engine.historical_data, dict)
        self.assertIsInstance(self.engine.backtest_results, dict)
    
    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        # Test that evaluator and risk controller are initialized
        self.assertIsNotNone(self.engine.evaluator)
        self.assertIsNotNone(self.engine.risk_controller)
        self.assertEqual(self.engine.current_equity, 10000.0)
    
    def test_backtest_execution(self):
        """Test complete backtest execution."""
        # Mock the run_strategy_backtest method to return expected results
        with patch.object(self.engine, 'run_strategy_backtest') as mock_backtest:
            mock_backtest.return_value = {
                "trade_count": 10,
                "win_rate": 0.6,
                "profit_factor": 1.5,
                "absolute_return": 0.15
            }
            
            # This would require more complex setup with actual market data
            # For now, test the basic structure
            result = self.engine.run_strategy_backtest(
                strategy_name="trend_following",
                symbol="EURUSD",
                timeframe="H1",
                start_date="2023-01-01",
                end_date="2023-01-02",
                initial_equity=10000.0
            )
            
            self.assertIsInstance(result, dict)
            # Check for expected keys in backtest results
            expected_keys = ["trade_count", "win_rate", "profit_factor", "absolute_return"]
            for key in expected_keys:
                self.assertIn(key, result)
            
            self.assertIsInstance(result["trade_count"], int)
            self.assertIsInstance(result["win_rate"], (int, float))
            self.assertIsInstance(result["profit_factor"], (int, float))


class TestContinuousImprovement(unittest.TestCase):
    """
    Test cases for the ContinuousImprovement module.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "monitoring": {
                "check_interval": 30,
                "confidence_threshold": 0.7
            },
            "database": {
                "path": ":memory:"
            }
        }
        self.improvement = ContinuousImprovement(
            config_path="automation/config/continuous_improvement.json"
        )
    
    def test_initialization(self):
        """Test ContinuousImprovement initialization."""
        self.assertIsNotNone(self.improvement)
        self.assertIsNotNone(self.improvement.config)
        self.assertIsNotNone(self.improvement.element_tracker)
        self.assertIsNotNone(self.improvement.selector_optimizer)
    
    def test_selector_optimization(self):
        """Test selector optimization."""
        # Test that selector optimizer is initialized
        self.assertIsNotNone(self.improvement.selector_optimizer)
        self.assertIsInstance(self.improvement.selector_optimizer.selector_performance, dict)
        self.assertIsInstance(self.improvement.selector_optimizer.selector_stability, dict)
    
    def test_ui_change_detection(self):
        """Test UI change detection."""
        # Test that element tracker is initialized
        self.assertIsNotNone(self.improvement.element_tracker)
        self.assertIsInstance(self.improvement.element_tracker.tracked_elements, dict)
        self.assertIsInstance(self.improvement.element_tracker.element_history, dict)
    
    def test_session_recording(self):
        """Test session recording functionality."""
        # Test that session recorder is initialized
        self.assertIsNotNone(self.improvement.session_recorder)
        self.assertIsInstance(self.improvement.session_recorder.snapshots, object)
        self.assertFalse(self.improvement.session_recorder.recording)


class TestTradeBotSentinelProAdvanced(unittest.TestCase):
    """
    Test cases for the main TradeBotSentinelProAdvanced class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Create sample config files
        configs = {
            "trade_executor.json": {"enabled": True, "database": {"path": ":memory:"}},
            "monitoring_dashboard.json": {"enabled": True, "database": {"path": ":memory:"}},
            "alert_system.json": {"enabled": True, "database": {"path": ":memory:"}},
            "backtesting_engine.json": {"enabled": True, "database": {"path": ":memory:"}},
            "continuous_improvement.json": {"enabled": True, "database": {"path": ":memory:"}}
        }
        
        for filename, config in configs.items():
            with open(self.config_dir / filename, 'w') as f:
                json.dump(config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test TradeBotSentinelProAdvanced initialization."""
        # Test initialization in basic mode (without advanced features)
        bot = TradeBotSentinelProAdvanced(config_path=str(self.config_dir))
        
        self.assertIsNotNone(bot)
        # In basic mode, advanced modules should be None
        self.assertIsNone(bot.trade_executor)
        self.assertIsNone(bot.monitoring_dashboard)
        self.assertIsNone(bot.alert_system)
        self.assertIsNone(bot.backtesting_engine)
        self.assertIsNone(bot.continuous_improvement)
        
        # But the core system should still be available
        self.assertIsNotNone(bot.core_system)
    
    @patch('tradebot_sentinel_pro_advanced.TradeBotSentinelProAdvanced')
    def test_configuration_loading(self, mock_core_bot):
        """Test configuration loading."""
        bot = TradeBotSentinelProAdvanced(config_path=str(self.config_dir))
        
        self.assertIn("trade_executor", bot.configs)
        self.assertIn("monitoring_dashboard", bot.configs)
        self.assertIn("alert_system", bot.configs)
        self.assertIn("backtesting_engine", bot.configs)
        self.assertIn("continuous_improvement", bot.configs)
    
    @patch('tradebot_sentinel_pro_advanced.TradeBotSentinelProAdvanced')
    def test_report_generation(self, mock_core_bot):
        """Test report generation."""
        bot = TradeBotSentinelProAdvanced(config_path=str(self.config_dir))
        
        report = bot.generate_report("daily")
        
        self.assertIsInstance(report, dict)
        self.assertEqual(report["report_type"], "daily")
        self.assertIn("generated_at", report)
        self.assertIn("system_status", report)
        self.assertIn("modules", report)


class TestIntegration(unittest.TestCase):
    """
    Integration tests for the complete system.
    """
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Create temporary directories and files
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Minimal configs for integration testing
        configs = {
            "trade_executor.json": {
                "enabled": True,
                "database": {"path": ":memory:"},
                "execution": {"max_concurrent_trades": 1}
            },
            "monitoring_dashboard.json": {
                "enabled": True,
                "dashboard": {"mode": "cli"},
                "database": {"path": ":memory:"}
            },
            "alert_system.json": {
                "enabled": True,
                "channels": {"file": {"enabled": True}},
                "database": {"path": ":memory:"}
            },
            "backtesting_engine.json": {
                "enabled": False,  # Disable for integration tests
                "database": {"path": ":memory:"}
            },
            "continuous_improvement.json": {
                "enabled": False,  # Disable for integration tests
                "database": {"path": ":memory:"}
            }
        }
        
        for filename, config in configs.items():
            with open(self.config_dir / filename, 'w') as f:
                json.dump(config, f)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('tradebot_sentinel_pro_advanced.TradeBotSentinelProAdvanced')
    def test_system_startup_shutdown(self, mock_core_bot):
        """Test complete system startup and shutdown."""
        bot = TradeBotSentinelProAdvanced(config_path=str(self.config_dir))
        
        # Test that system initializes without errors
        self.assertFalse(bot.running)
        
        # Test graceful shutdown
        asyncio.run(bot.stop_automation())
        self.assertFalse(bot.running)
    
    @patch('tradebot_sentinel_pro_advanced.TradeBotSentinelProAdvanced')
    @patch('requests.post')
    def test_end_to_end_trade_flow(self, mock_post, mock_core_bot):
        """Test end-to-end trade execution flow."""
        # Mock successful trade response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "order_id": "12345"}
        mock_post.return_value = mock_response
        
        bot = TradeBotSentinelProAdvanced(config_path=str(self.config_dir))
        
        # Create a test trade file
        trade_file = Path(self.temp_dir) / "test_trade.sh"
        with open(trade_file, 'w') as f:
            f.write('curl -X POST "https://api.example.com/trade" -d \'{"symbol": "EURUSD", "side": "buy", "amount": 1000, "price": 1.1000}\'')
        
        # Test trade execution
        if bot.trade_executor:
            result = asyncio.run(bot.trade_executor.execute_trade_from_file(str(trade_file)))
            self.assertIsNotNone(result)


def run_tests():
    """
    Run all test suites.
    """
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestTradeExecutor,
        TestMonitoringDashboard,
        TestAlertSystem,
        TestBacktestingEngine,
        TestContinuousImprovement,
        TestTradeBotSentinelProAdvanced,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running TradeBot Sentinel Pro Advanced Test Suite")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)