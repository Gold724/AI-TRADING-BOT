# integration_test.py

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt

# Import all Phase 3 components
try:
    from memory_engine import MemoryEngine
    from emergency_protocol import EmergencyProtocol
    from backtest_engine import BacktestEngine
    from metrics_dashboard import launch_dashboard
    from prompt_optimizer import PromptOptimizer
    from signal_router import SignalRouter
    from live_trading import LiveTrading, Order, OrderType, OrderDirection
    
    # Import Phase 2 components
    from strategy_manager import StrategyManager
    from risk_control import RiskController
    from news_guard import NewsGuard
    from trade_evaluator import TradePerformanceEvaluator
    from sentinel_decider import SentinelDecider
    
    ALL_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    ALL_IMPORTS_SUCCESSFUL = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("integration_test")

class IntegrationTest:
    """Integration test for all Phase 3 components"""
    
    def __init__(self, config_path: str = "config/integration_test_config.json"):
        """Initialize the integration test
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.test_results = {}
        self.components = {}
        
        # Create test data directory if it doesn't exist
        os.makedirs("data/test", exist_ok=True)
        
        logger.info("Initialized integration test")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict: Configuration
        """
        try:
            # Create default config if file doesn't exist
            if not os.path.exists(config_path):
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                default_config = {
                    "test_mode": True,
                    "test_symbols": ["EURUSD", "GBPUSD", "USDJPY"],
                    "test_strategies": ["trend_following", "mean_reversion"],
                    "backtest": {
                        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d"),
                        "initial_balance": 10000
                    },
                    "live_trading": {
                        "broker": "mock",
                        "account_id": "test",
                        "initial_balance": 10000
                    },
                    "risk": {
                        "max_risk_per_trade": 1.0,
                        "max_open_trades": 3
                    }
                }
                
                with open(config_path, "w") as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
            
            # Load config from file
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return default config
            return {
                "test_mode": True,
                "test_symbols": ["EURUSD", "GBPUSD", "USDJPY"],
                "test_strategies": ["trend_following", "mean_reversion"]
            }
    
    def initialize_components(self) -> bool:
        """Initialize all components
        
        Returns:
            bool: True if all components initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing components...")
            
            # Initialize Phase 2 components
            self.components["strategy_manager"] = StrategyManager()
            self.components["risk_controller"] = RiskController()
            self.components["news_guard"] = NewsGuard()
            self.components["trade_evaluator"] = TradePerformanceEvaluator()
            self.components["sentinel_decider"] = SentinelDecider()
            
            # Initialize Phase 3 components
            self.components["memory_engine"] = MemoryEngine()
            self.components["emergency_protocol"] = EmergencyProtocol()
            self.components["backtest_engine"] = BacktestEngine()
            self.components["prompt_optimizer"] = PromptOptimizer()
            self.components["signal_router"] = SignalRouter()
            self.components["live_trading"] = LiveTrading()
            
            logger.info("All components initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            return False
    
    def test_memory_engine(self) -> Dict:
        """Test the memory engine component
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing memory engine...")
            memory_engine = self.components["memory_engine"]
            
            # Test updating market memory
            test_data = {
                "symbol": "EURUSD",
                "strategy": "trend_following",
                "entry_time": datetime.now().isoformat(),
                "exit_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "direction": "BUY",
                "entry_price": 1.1000,
                "exit_price": 1.1050,
                "profit": 50,
                "profit_pips": 50,
                "win": True,
                "market_condition": "trending",
                "volatility": "medium",
                "news_impact": "low"
            }
            
            memory_engine.update_market_memory(test_data)
            memory_engine.update_strategy_memory(test_data)
            memory_engine.update_condition_memory(test_data)
            
            # Test retrieving best strategy
            best_strategy = memory_engine.get_best_strategy_for_condition("trending")
            best_symbol = memory_engine.get_best_symbol_for_strategy("trend_following")
            next_condition = memory_engine.predict_next_market_condition("trending")
            optimal_params = memory_engine.get_optimal_trade_parameters("EURUSD", "trending")
            
            results = {
                "best_strategy": best_strategy,
                "best_symbol": best_symbol,
                "next_condition": next_condition,
                "optimal_params": optimal_params,
                "status": "success"
            }
            
            logger.info(f"Memory engine test results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error testing memory engine: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_emergency_protocol(self) -> Dict:
        """Test the emergency protocol component
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing emergency protocol...")
            emergency_protocol = self.components["emergency_protocol"]
            
            # Test activating and deactivating emergency
            emergency_protocol.activate_emergency("test", "caution", "Test emergency")
            is_active = emergency_protocol.is_emergency_active()
            status, message = emergency_protocol.get_emergency_status()
            
            # Test trading allowed
            trading_allowed = emergency_protocol.is_trading_allowed()
            
            # Deactivate emergency
            emergency_protocol.deactivate_emergency("test")
            is_active_after = emergency_protocol.is_emergency_active()
            
            results = {
                "is_active": is_active,
                "status": status,
                "message": message,
                "trading_allowed": trading_allowed,
                "is_active_after": is_active_after,
                "status": "success"
            }
            
            logger.info(f"Emergency protocol test results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error testing emergency protocol: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_backtest_engine(self) -> Dict:
        """Test the backtest engine component
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing backtest engine...")
            backtest_engine = self.components["backtest_engine"]
            
            # Create test data if it doesn't exist
            self._create_test_data()
            
            # Run backtest
            backtest_config = {
                "strategy": "trend_following",
                "symbol": "EURUSD",
                "timeframe": "1h",
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "initial_balance": 10000,
                "risk_per_trade": 1.0
            }
            
            results = backtest_engine.run_backtest(backtest_config)
            
            # Generate charts
            chart_path = backtest_engine.generate_equity_curve()
            
            # Run Monte Carlo simulation
            monte_carlo_results = backtest_engine.run_monte_carlo_simulation(results, num_simulations=100)
            
            backtest_results = {
                "total_trades": results.get("total_trades", 0),
                "win_rate": results.get("win_rate", 0),
                "profit_factor": results.get("profit_factor", 0),
                "net_profit": results.get("net_profit", 0),
                "max_drawdown": results.get("max_drawdown", 0),
                "sharpe_ratio": results.get("sharpe_ratio", 0),
                "chart_path": chart_path,
                "monte_carlo": {
                    "worst_case": monte_carlo_results.get("worst_case", 0),
                    "best_case": monte_carlo_results.get("best_case", 0),
                    "median_case": monte_carlo_results.get("median_case", 0)
                },
                "status": "success"
            }
            
            logger.info(f"Backtest engine test results: {backtest_results}")
            return backtest_results
        except Exception as e:
            logger.error(f"Error testing backtest engine: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_prompt_optimizer(self) -> Dict:
        """Test the prompt optimizer component
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing prompt optimizer...")
            prompt_optimizer = self.components["prompt_optimizer"]
            
            # Generate test prompt
            context = {
                "strategy": "trend_following",
                "symbol": "EURUSD",
                "market_condition": "trending",
                "volatility": "medium",
                "news_impact": "low",
                "recent_performance": "positive",
                "psychological_state": "neutral"
            }
            
            prompt = prompt_optimizer.generate_prompt(context)
            
            # Record prompt result
            result = {
                "prompt_id": "test_prompt_1",
                "context": context,
                "prompt": prompt,
                "response": "Take Trade with 85% confidence",
                "trade_result": {
                    "win": True,
                    "profit": 50,
                    "profit_pips": 50
                }
            }
            
            prompt_optimizer.record_prompt_result(result)
            
            # Get performance metrics
            performance = prompt_optimizer.get_prompt_performance("test_prompt_1")
            
            # Optimize prompt
            optimized_prompt = prompt_optimizer.optimize_prompt(context)
            
            results = {
                "original_prompt": prompt,
                "optimized_prompt": optimized_prompt,
                "performance": performance,
                "status": "success"
            }
            
            logger.info(f"Prompt optimizer test results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error testing prompt optimizer: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_signal_router(self) -> Dict:
        """Test the signal router component
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing signal router...")
            signal_router = self.components["signal_router"]
            
            # Create test signal
            test_signal = {
                "source": "tradingview",
                "symbol": "EURUSD",
                "direction": "BUY",
                "entry_price": 1.1000,
                "stop_loss": 1.0950,
                "take_profit": 1.1100,
                "strategy": "trend_following",
                "timestamp": datetime.now().isoformat()
            }
            
            # Process signal
            signal_id = signal_router.add_signal(test_signal)
            processed_signal = signal_router.process_signal(signal_id)
            
            # Get next signal
            next_signal = signal_router.get_next_signal()
            
            # Get signal history
            signal_history = signal_router.get_signal_history(limit=5)
            
            results = {
                "signal_id": signal_id,
                "processed_signal": processed_signal,
                "next_signal": next_signal,
                "signal_history_count": len(signal_history),
                "status": "success"
            }
            
            logger.info(f"Signal router test results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error testing signal router: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_live_trading(self) -> Dict:
        """Test the live trading component
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing live trading...")
            live_trading = self.components["live_trading"]
            
            # Connect to broker (mock)
            connected = live_trading.connect()
            
            if not connected:
                return {"status": "error", "message": "Failed to connect to broker"}
            
            # Get account info
            account_info = live_trading.get_account_info()
            
            # Create test order
            test_order = Order(
                symbol="EURUSD",
                order_type=OrderType.MARKET,
                direction=OrderDirection.BUY,
                volume=0.01,
                entry_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1100,
                comment="Integration test",
                strategy="trend_following"
            )
            
            # Place order
            success, order_id, error = live_trading.place_order(test_order)
            
            if not success:
                live_trading.disconnect()
                return {"status": "error", "message": f"Failed to place order: {error}"}
            
            # Get positions
            positions = live_trading.get_positions()
            
            # Close order
            close_success, close_error = live_trading.close_order(order_id)
            
            # Get trading stats
            stats = live_trading.get_trading_stats()
            
            # Disconnect
            live_trading.disconnect()
            
            results = {
                "connected": connected,
                "account_info": account_info,
                "order_placed": success,
                "order_id": order_id,
                "positions_count": len(positions),
                "order_closed": close_success,
                "trading_stats": stats,
                "status": "success"
            }
            
            logger.info(f"Live trading test results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error testing live trading: {e}")
            try:
                live_trading.disconnect()
            except:
                pass
            return {"status": "error", "message": str(e)}
    
    def test_integration(self) -> Dict:
        """Test the integration of all components
        
        Returns:
            Dict: Test results
        """
        try:
            logger.info("Testing integration of all components...")
            
            # 1. Create a signal with the signal router
            signal_router = self.components["signal_router"]
            test_signal = {
                "source": "tradingview",
                "symbol": "EURUSD",
                "direction": "BUY",
                "entry_price": 1.1000,
                "stop_loss": 1.0950,
                "take_profit": 1.1100,
                "strategy": "trend_following",
                "timestamp": datetime.now().isoformat()
            }
            signal_id = signal_router.add_signal(test_signal)
            
            # 2. Process the signal with the sentinel decider
            sentinel_decider = self.components["sentinel_decider"]
            memory_engine = self.components["memory_engine"]
            
            # Get market condition from memory engine
            market_condition = memory_engine.predict_next_market_condition("neutral")
            
            # Get optimal parameters
            optimal_params = memory_engine.get_optimal_trade_parameters("EURUSD", market_condition)
            
            # Create context for sentinel decider
            context = {
                "symbol": "EURUSD",
                "strategy": "trend_following",
                "direction": "BUY",
                "entry_price": 1.1000,
                "stop_loss": 1.0950,
                "take_profit": 1.1100,
                "market_condition": market_condition,
                "optimal_params": optimal_params
            }
            
            # Get decision from sentinel
            decision = sentinel_decider.get_decision(context)
            
            # 3. Check emergency protocol
            emergency_protocol = self.components["emergency_protocol"]
            trading_allowed = emergency_protocol.is_trading_allowed()
            
            # 4. If trading is allowed and decision is positive, place order
            if trading_allowed and decision.get("recommendation") == "Take Trade":
                live_trading = self.components["live_trading"]
                
                # Connect to broker
                connected = live_trading.connect()
                
                if connected:
                    # Create order
                    order = Order(
                        symbol="EURUSD",
                        order_type=OrderType.MARKET,
                        direction=OrderDirection.BUY,
                        volume=0.01,
                        entry_price=1.1000,
                        stop_loss=1.0950,
                        take_profit=1.1100,
                        comment="Integration test",
                        strategy="trend_following"
                    )
                    
                    # Place order
                    success, order_id, error = live_trading.place_order(order)
                    
                    # Close order after a short delay
                    if success:
                        time.sleep(2)  # Wait for 2 seconds
                        live_trading.close_order(order_id)
                    
                    # Disconnect
                    live_trading.disconnect()
            
            # 5. Update memory with the result
            memory_engine.update_market_memory({
                "symbol": "EURUSD",
                "strategy": "trend_following",
                "entry_time": datetime.now().isoformat(),
                "exit_time": (datetime.now() + timedelta(seconds=2)).isoformat(),
                "direction": "BUY",
                "entry_price": 1.1000,
                "exit_price": 1.1010,
                "profit": 10,
                "profit_pips": 10,
                "win": True,
                "market_condition": market_condition,
                "volatility": "medium",
                "news_impact": "low"
            })
            
            results = {
                "signal_id": signal_id,
                "market_condition": market_condition,
                "optimal_params": optimal_params,
                "decision": decision,
                "trading_allowed": trading_allowed,
                "status": "success"
            }
            
            logger.info(f"Integration test results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in integration test: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_test_data(self):
        """Create test data for backtesting"""
        try:
            # Create historical data directory if it doesn't exist
            os.makedirs(os.path.join("data", "historical"), exist_ok=True)
            
            # Create test data for EURUSD
            data_path = os.path.join("data", "historical", "EURUSD_1h.csv")
            
            # Check if file already exists
            if os.path.exists(data_path):
                return
            
            # Generate synthetic data
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            
            dates = [start_date + timedelta(hours=i) for i in range(int((end_date - start_date).total_seconds() / 3600) + 1)]
            
            # Generate random price data with a slight upward trend
            base_price = 1.1000
            prices = []
            
            for i in range(len(dates)):
                # Add random walk with slight upward bias
                random_change = (random.random() - 0.48) * 0.001  # Slight upward bias
                base_price += random_change
                
                # Add some volatility
                open_price = base_price
                high_price = base_price + random.random() * 0.0015
                low_price = base_price - random.random() * 0.0015
                close_price = base_price + (random.random() - 0.5) * 0.0010
                
                prices.append({
                    "datetime": dates[i].strftime("%Y-%m-%d %H:%M:%S"),
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": random.randint(100, 1000)
                })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(prices)
            df.to_csv(data_path, index=False)
            
            logger.info(f"Created test data at {data_path}")
        except Exception as e:
            logger.error(f"Error creating test data: {e}")
    
    def run_all_tests(self) -> Dict:
        """Run all tests
        
        Returns:
            Dict: Test results
        """
        if not ALL_IMPORTS_SUCCESSFUL:
            logger.error("Cannot run tests due to import errors")
            return {"status": "error", "message": "Import errors"}
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components")
            return {"status": "error", "message": "Component initialization failed"}
        
        # Run individual component tests
        self.test_results["memory_engine"] = self.test_memory_engine()
        self.test_results["emergency_protocol"] = self.test_emergency_protocol()
        self.test_results["backtest_engine"] = self.test_backtest_engine()
        self.test_results["prompt_optimizer"] = self.test_prompt_optimizer()
        self.test_results["signal_router"] = self.test_signal_router()
        self.test_results["live_trading"] = self.test_live_trading()
        
        # Run integration test
        self.test_results["integration"] = self.test_integration()
        
        # Calculate overall success rate
        success_count = sum(1 for test in self.test_results.values() if test.get("status") == "success")
        total_tests = len(self.test_results)
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate summary
        summary = {
            "total_tests": total_tests,
            "success_count": success_count,
            "success_rate": success_rate,
            "failed_tests": [name for name, result in self.test_results.items() if result.get("status") != "success"],
            "status": "success" if success_rate == 100 else "partial" if success_rate > 0 else "error"
        }
        
        self.test_results["summary"] = summary
        
        # Save results to file
        self._save_results()
        
        logger.info(f"All tests completed. Success rate: {success_rate:.2f}%")
        return summary
    
    def _save_results(self):
        """Save test results to file"""
        try:
            results_path = os.path.join("data", "test", f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(results_path, "w") as f:
                json.dump(self.test_results, f, indent=4)
                
            logger.info(f"Test results saved to {results_path}")
        except Exception as e:
            logger.error(f"Error saving test results: {e}")
    
    def generate_report(self):
        """Generate a report of the test results"""
        try:
            if not self.test_results:
                logger.warning("No test results to generate report from")
                return
                
            summary = self.test_results.get("summary", {})
            
            # Create a simple report
            report = f"# Integration Test Report\n\n"
            report += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report += f"**Success Rate:** {summary.get('success_rate', 0):.2f}%\n\n"
            report += f"**Total Tests:** {summary.get('total_tests', 0)}\n\n"
            report += f"**Successful Tests:** {summary.get('success_count', 0)}\n\n"
            
            if summary.get("failed_tests"):
                report += f"**Failed Tests:** {', '.join(summary.get('failed_tests', []))}\n\n"
            
            # Add individual test results
            report += "## Component Test Results\n\n"
            
            for name, result in self.test_results.items():
                if name == "summary":
                    continue
                    
                report += f"### {name.replace('_', ' ').title()}\n\n"
                report += f"**Status:** {result.get('status', 'unknown')}\n\n"
                
                if result.get("status") == "error":
                    report += f"**Error:** {result.get('message', 'Unknown error')}\n\n"
                elif name == "backtest_engine" and result.get("status") == "success":
                    report += f"**Total Trades:** {result.get('total_trades', 0)}\n\n"
                    report += f"**Win Rate:** {result.get('win_rate', 0):.2f}%\n\n"
                    report += f"**Profit Factor:** {result.get('profit_factor', 0):.2f}\n\n"
                    report += f"**Net Profit:** ${result.get('net_profit', 0):.2f}\n\n"
                    report += f"**Max Drawdown:** ${result.get('max_drawdown', 0):.2f}\n\n"
                    report += f"**Sharpe Ratio:** {result.get('sharpe_ratio', 0):.2f}\n\n"
            
            # Save report to file
            report_path = os.path.join("data", "test", f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            
            with open(report_path, "w") as f:
                f.write(report)
                
            logger.info(f"Test report saved to {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None

# Main function to run the integration test
def main():
    """Main function to run the integration test"""
    logger.info("Starting integration test")
    
    # Create integration test instance
    integration_test = IntegrationTest()
    
    # Run all tests
    summary = integration_test.run_all_tests()
    
    # Generate report
    report_path = integration_test.generate_report()
    
    if report_path:
        logger.info(f"Integration test completed. Report saved to {report_path}")
    else:
        logger.info(f"Integration test completed. Summary: {summary}")
    
    return summary

# Run the integration test if this script is executed directly
if __name__ == "__main__":
    main()