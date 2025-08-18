#!/usr/bin/env python3
"""
TradeBot Sentinel Pro Advanced - Complete Automation System
Builds on the fully validated TradeBot Sentinel Pro system with advanced automation,
monitoring, and reporting layers for live trading.

Features:
- Automated Trade Execution
- Real-Time Monitoring Dashboard
- Strategy Testing & Simulation
- Alerts & Reporting
- Continuous Improvement
- 100% Backward Compatibility

Author: TradeBot Sentinel Team
Version: 2.0.0
License: MIT
"""

import sys
import os
import asyncio
import argparse
import signal
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import core TradeBot Sentinel Pro
try:
    from tradebot_sentinel_pro import TradeBotSentinelPro
except ImportError as e:
    print(f"❌ Failed to import core TradeBot Sentinel Pro: {e}")
    print("Please ensure tradebot_sentinel_pro.py is in the same directory.")
    sys.exit(1)

# Import automation modules
try:
    from automation.trade_executor import TradeExecutor
    from automation.monitoring_dashboard import MonitoringDashboard
    from automation.alert_system import AlertSystem
    from automation.backtesting_engine import BacktestingEngine
    from automation.continuous_improvement import ContinuousImprovement
except ImportError as e:
    print(f"⚠️  Warning: Some automation modules not available: {e}")
    print("Running in basic mode with core functionality only.")
    # Set flags to disable advanced features
    ADVANCED_FEATURES_AVAILABLE = False
else:
    ADVANCED_FEATURES_AVAILABLE = True

# Import utilities
try:
    from utils.config_manager import ConfigManager
    from utils.database_manager import DatabaseManager
    from utils.logger_setup import setup_logger
    from utils.health_monitor import HealthMonitor
except ImportError as e:
    print(f"⚠️  Warning: Some utility modules not available: {e}")
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@dataclass
class SystemStatus:
    """System status tracking"""
    core_system: bool = False
    trade_executor: bool = False
    monitoring_dashboard: bool = False
    alert_system: bool = False
    backtesting_engine: bool = False
    continuous_improvement: bool = False
    database_connected: bool = False
    last_health_check: Optional[datetime] = None
    active_trades: int = 0
    total_requests_captured: int = 0
    system_uptime: Optional[datetime] = None


class TradeBotSentinelProAdvanced:
    """
    Advanced TradeBot Sentinel Pro with complete automation layers.
    Maintains 100% backward compatibility with the original system.
    """
    
    def __init__(self, config_path: Optional[str] = None, mode: str = "automation"):
        """Initialize the advanced system"""
        self.mode = mode
        self.config_path = config_path or "config/main_config.json"
        self.project_root = project_root
        self.system_status = SystemStatus()
        self.system_status.system_uptime = datetime.now()
        
        # Initialize logger
        self.logger = self.setup_logging()
        self.logger.info(f"🚀 Initializing TradeBot Sentinel Pro Advanced v2.0.0")
        self.logger.info(f"📁 Project root: {self.project_root}")
        self.logger.info(f"⚙️  Mode: {mode}")
        self.logger.info(f"🔧 Config path: {self.config_path}")
        
        # Initialize configuration manager
        self.config_manager = self._initialize_config_manager()
        
        # Initialize database manager
        self.db_manager = self._initialize_database_manager()
        
        # Load configurations
        self.configs = self.load_configurations()
        self.config = self.configs  # Add config attribute for backward compatibility
        
        # Initialize running state
        self.running = False
        
        # Initialize core system (backward compatibility)
        self.core_system = self._initialize_core_system()
        
        # Initialize advanced modules (if available)
        self.trade_executor = None
        self.monitoring_dashboard = None
        self.alert_system = None
        self.backtesting_engine = None
        self.continuous_improvement = None
        self.health_monitor = None
        
        if ADVANCED_FEATURES_AVAILABLE:
            self.initialize_modules()
        
        # Thread management
        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="TradeBot")
        self.shutdown_event = threading.Event()
        self.background_tasks = []
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.info("✅ TradeBot Sentinel Pro Advanced initialized successfully")
    
    def setup_logging(self):
        """
        Setup comprehensive logging system.
        """
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("TradeBotSentinelProAdvanced")
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            log_dir / f"tradebot_advanced_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        return self.logger
    
    def _initialize_config_manager(self):
        """
        Initialize the configuration manager.
        
        Returns:
            Configuration manager instance or None if not available
        """
        try:
            # Try to import and initialize config manager
            from automation.config_manager import ConfigManager
            return ConfigManager(self.config_dir)
        except ImportError:
            self.logger.warning("ConfigManager not available, using basic configuration loading")
            return None
        except Exception as e:
            self.logger.error(f"Error initializing config manager: {e}")
            return None
    
    def _initialize_database_manager(self):
        """
        Initialize the database manager.
        
        Returns:
            Database manager instance or None if not available
        """
        try:
            # Try to import and initialize database manager
            from automation.database_manager import DatabaseManager
            return DatabaseManager(self.project_root / "data")
        except ImportError:
            self.logger.warning("DatabaseManager not available, using basic data storage")
            return None
        except Exception as e:
            self.logger.error(f"Error initializing database manager: {e}")
            return None
    
    def _initialize_core_system(self):
        """
        Initialize the core system.
        
        Returns:
            Core system instance or None if not available
        """
        try:
            # Try to import and initialize core system
            from tradebot_sentinel_pro import TradeBotSentinelPro
            return TradeBotSentinelPro()
        except ImportError:
            self.logger.warning("Core TradeBotSentinelPro not available")
            return None
        except Exception as e:
            self.logger.error(f"Error initializing core system: {e}")
            return None
    
    def _setup_signal_handlers(self):
        """
        Setup signal handlers for graceful shutdown.
        """
        try:
            import signal
            
            def signal_handler(signum, frame):
                self.logger.info(f"Received signal {signum}, shutting down gracefully...")
                self.running = False
                if hasattr(self, 'shutdown_event'):
                    self.shutdown_event.set()
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            self.logger.info("Signal handlers setup complete")
        except Exception as e:
            self.logger.error(f"Error setting up signal handlers: {e}")
    
    def load_configurations(self) -> Dict[str, Any]:
        """
        Load all configuration files.
        
        Returns:
            Dictionary containing all configurations
        """
        configs = {}
        config_dir = Path("automation/config")
        config_files = [
            "trade_executor.json",
            "dashboard.json",
            "alert_system.json",
            "backtesting_engine.json",
            "continuous_improvement.json"
        ]
        
        for config_file in config_files:
            config_path = config_dir / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_name = config_file.replace('.json', '')
                        if config_name == 'dashboard':
                            config_name = 'monitoring_dashboard'
                        configs[config_name] = json.load(f)
                        self.logger.info(f"Loaded configuration: {config_file}")
                except Exception as e:
                    self.logger.error(f"Error loading {config_file}: {e}")
                    configs[config_name] = {}
            else:
                self.logger.warning(f"Configuration file not found: {config_file}")
                config_name = config_file.replace('.json', '')
                if config_name == 'dashboard':
                    config_name = 'monitoring_dashboard'
                configs[config_name] = {}
        
        return configs
    
    def initialize_modules(self):
        """
        Initialize all automation modules.
        """
        try:
            # Initialize trade executor
            if self.configs.get('trade_executor', {}).get('enabled', True):
                if 'TradeExecutor' in globals():
                    self.trade_executor = TradeExecutor(
                        config_path="automation/config/trade_executor.json"
                    )
                    self.logger.info("Trade executor initialized")
                else:
                    self.logger.warning("TradeExecutor class not available")
            
            # Initialize monitoring dashboard
            if self.configs.get('monitoring_dashboard', {}).get('enabled', True):
                if 'MonitoringDashboard' in globals():
                    self.monitoring_dashboard = MonitoringDashboard(
                        config_path="automation/config/dashboard.json"
                    )
                    self.logger.info("Monitoring dashboard initialized")
                else:
                    self.logger.warning("MonitoringDashboard class not available")
            
            # Initialize alert system
            if self.configs.get('alert_system', {}).get('enabled', True):
                if 'AlertSystem' in globals():
                    self.alert_system = AlertSystem(
                        config_path="automation/config/alert_system.json"
                    )
                    self.logger.info("Alert system initialized")
                else:
                    self.logger.warning("AlertSystem class not available")
            
            # Initialize backtesting engine
            if self.configs.get('backtesting_engine', {}).get('enabled', True):
                if 'BacktestingEngine' in globals():
                    self.backtesting_engine = BacktestingEngine(
                        historical_data_dir="data/historical",
                        backtest_results_dir="data/backtest/results",
                        backtest_charts_dir="data/backtest/charts"
                    )
                    self.logger.info("Backtesting engine initialized")
                else:
                    self.logger.warning("BacktestingEngine class not available")
            
            # Initialize continuous improvement
            if self.configs.get('continuous_improvement', {}).get('enabled', True):
                if 'ContinuousImprovement' in globals():
                    self.continuous_improvement = ContinuousImprovement(
                        config_path="automation/config/continuous_improvement.json"
                    )
                    self.logger.info("Continuous improvement initialized")
                else:
                    self.logger.warning("ContinuousImprovement class not available")
            
        except Exception as e:
            self.logger.error(f"Error initializing modules: {e}")
            raise
    
    async def start_automation(self):
        """
        Start the advanced automation system.
        """
        if self.running:
            self.logger.warning("Automation system is already running")
            return
        
        self.running = True
        self.logger.info("Starting TradeBot Sentinel Pro Advanced automation system")
        
        try:
            # Send startup alert
            if self.alert_system:
                await self.alert_system.send_alert(
                    "system_startup",
                    "TradeBot Sentinel Pro Advanced",
                    "Automation system started successfully",
                    alert_type="info"
                )
            
            # Start all modules concurrently
            tasks = []
            
            # Start trade executor
            if self.trade_executor:
                tasks.append(asyncio.create_task(self.trade_executor.start()))
            
            # Start monitoring dashboard
            if self.monitoring_dashboard:
                tasks.append(asyncio.create_task(self.monitoring_dashboard.start()))
            
            # Start alert system
            if self.alert_system:
                tasks.append(asyncio.create_task(self.alert_system.start()))
            
            # Start continuous improvement
            if self.continuous_improvement:
                tasks.append(asyncio.create_task(self.continuous_improvement.start()))
            
            # Main automation loop
            tasks.append(asyncio.create_task(self.automation_loop()))
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error in automation system: {e}")
            if self.alert_system:
                await self.alert_system.send_alert(
                    "system_error",
                    "Critical System Error",
                    f"Automation system encountered an error: {str(e)}",
                    alert_type="critical"
                )
            raise
        finally:
            self.running = False
    
    async def automation_loop(self):
        """
        Main automation loop for coordinating all systems.
        """
        self.logger.info("Starting main automation loop")
        
        while self.running:
            try:
                # Check system health
                await self.check_system_health()
                
                # Process trade files if available
                await self.process_trade_files()
                
                # Update monitoring metrics
                await self.update_monitoring_metrics()
                
                # Check for alerts
                await self.check_alert_conditions()
                
                # Sleep for configured interval
                await asyncio.sleep(self.configs.get('trade_executor', {}).get('monitoring', {}).get('check_interval', 5))
                
            except Exception as e:
                self.logger.error(f"Error in automation loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def check_system_health(self):
        """
        Check the health of all system components.
        """
        health_status = {
            'core_bot': 'healthy',
            'trade_executor': 'healthy' if self.trade_executor else 'disabled',
            'monitoring_dashboard': 'healthy' if self.monitoring_dashboard else 'disabled',
            'alert_system': 'healthy' if self.alert_system else 'disabled',
            'backtesting_engine': 'healthy' if self.backtesting_engine else 'disabled',
            'continuous_improvement': 'healthy' if self.continuous_improvement else 'disabled'
        }
        
        # Check if any critical components are unhealthy
        critical_components = ['core_bot', 'trade_executor']
        unhealthy_critical = [comp for comp in critical_components if health_status.get(comp) == 'unhealthy']
        
        if unhealthy_critical and self.alert_system:
            await self.alert_system.send_alert(
                "system_health",
                "Critical System Health Alert",
                f"Critical components unhealthy: {', '.join(unhealthy_critical)}",
                alert_type="critical"
            )
    
    async def process_trade_files(self):
        """
        Process any available trade files for execution.
        """
        if not self.trade_executor:
            return
        
        trade_file_path = self.configs.get('trade_executor', {}).get('monitoring', {}).get('trade_file_path', 'trade.sh')
        
        if os.path.exists(trade_file_path):
            try:
                # Execute trade via trade executor
                result = await self.trade_executor.execute_trade_from_file(trade_file_path)
                
                if result and self.alert_system:
                    await self.alert_system.send_alert(
                        "trade_execution",
                        "Trade Executed",
                        f"Trade executed successfully: {result.get('symbol', 'Unknown')}",
                        alert_type="success"
                    )
                
            except Exception as e:
                self.logger.error(f"Error processing trade file: {e}")
                if self.alert_system:
                    await self.alert_system.send_alert(
                        "trade_error",
                        "Trade Execution Error",
                        f"Failed to execute trade: {str(e)}",
                        alert_type="failure"
                    )
    
    async def update_monitoring_metrics(self):
        """
        Update monitoring dashboard metrics.
        """
        if not self.monitoring_dashboard:
            return
        
        try:
            # Get latest metrics from trade executor
            if self.trade_executor:
                metrics = await self.trade_executor.get_metrics()
                await self.monitoring_dashboard.update_metrics(metrics)
        
        except Exception as e:
            self.logger.error(f"Error updating monitoring metrics: {e}")
    
    async def check_alert_conditions(self):
        """
        Check for alert conditions across all systems.
        """
        if not self.alert_system:
            return
        
        try:
            # Check trade executor alerts
            if self.trade_executor:
                alerts = await self.trade_executor.get_alerts()
                for alert in alerts:
                    await self.alert_system.process_alert(alert)
            
            # Check monitoring dashboard alerts
            if self.monitoring_dashboard:
                alerts = await self.monitoring_dashboard.get_alerts()
                for alert in alerts:
                    await self.alert_system.process_alert(alert)
        
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
    
    async def run_backtest(self, strategy_name: str, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Run a backtest for the specified strategy and parameters.
        
        Args:
            strategy_name: Name of the strategy to test
            symbol: Trading symbol
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
        
        Returns:
            Backtest results dictionary
        """
        if not self.backtesting_engine:
            raise ValueError("Backtesting engine not initialized")
        
        self.logger.info(f"Starting backtest: {strategy_name} on {symbol} from {start_date} to {end_date}")
        
        try:
            result = await self.backtesting_engine.run_backtest(
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if self.alert_system:
                await self.alert_system.send_alert(
                    "backtest_complete",
                    "Backtest Completed",
                    f"Backtest completed for {strategy_name} on {symbol}. Total return: {result.get('total_return', 0):.2%}",
                    alert_type="info"
                )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error running backtest: {e}")
            if self.alert_system:
                await self.alert_system.send_alert(
                    "backtest_error",
                    "Backtest Error",
                    f"Backtest failed for {strategy_name} on {symbol}: {str(e)}",
                    alert_type="failure"
                )
            raise
    
    async def capture_trade_session(self, duration_minutes: int = 60) -> str:
        """
        Capture a live trading session using the core bot.
        
        Args:
            duration_minutes: Duration to capture in minutes
        
        Returns:
            Path to the captured session data
        """
        self.logger.info(f"Starting trade session capture for {duration_minutes} minutes")
        
        try:
            # Use core bot to capture session
            session_data = await self.core_bot.capture_session(duration_minutes)
            
            # Process captured data with continuous improvement
            if self.continuous_improvement:
                await self.continuous_improvement.process_session_data(session_data)
            
            if self.alert_system:
                await self.alert_system.send_alert(
                    "session_capture",
                    "Trading Session Captured",
                    f"Successfully captured {duration_minutes} minute trading session",
                    alert_type="success"
                )
            
            return session_data
        
        except Exception as e:
            self.logger.error(f"Error capturing trade session: {e}")
            if self.alert_system:
                await self.alert_system.send_alert(
                    "session_error",
                    "Session Capture Error",
                    f"Failed to capture trading session: {str(e)}",
                    alert_type="failure"
                )
            raise
    
    def generate_report(self, report_type: str = "daily") -> Dict[str, Any]:
        """
        Generate comprehensive system report.
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
        
        Returns:
            Report data dictionary
        """
        self.logger.info(f"Generating {report_type} report")
        
        report = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "system_status": "operational",
            "modules": {
                "trade_executor": bool(self.trade_executor),
                "monitoring_dashboard": bool(self.monitoring_dashboard),
                "alert_system": bool(self.alert_system),
                "backtesting_engine": bool(self.backtesting_engine),
                "continuous_improvement": bool(self.continuous_improvement)
            }
        }
        
        try:
            # Add trade executor metrics
            if self.trade_executor:
                report["trade_metrics"] = self.trade_executor.get_summary_metrics()
            
            # Add monitoring metrics
            if self.monitoring_dashboard:
                report["monitoring_metrics"] = self.monitoring_dashboard.get_summary_metrics()
            
            # Add alert statistics
            if self.alert_system:
                report["alert_statistics"] = self.alert_system.get_alert_statistics()
            
            # Add backtest results
            if self.backtesting_engine:
                report["recent_backtests"] = self.backtesting_engine.get_recent_results()
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            report["error"] = str(e)
        
        return report
    
    async def stop_automation(self):
        """
        Stop the automation system gracefully.
        """
        self.logger.info("Stopping TradeBot Sentinel Pro Advanced automation system")
        
        self.running = False
        
        # Stop all modules
        if self.trade_executor:
            await self.trade_executor.stop()
        
        if self.monitoring_dashboard:
            await self.monitoring_dashboard.stop()
        
        if self.alert_system:
            await self.alert_system.stop()
        
        if self.continuous_improvement:
            await self.continuous_improvement.stop()
        
        # Send shutdown alert
        if self.alert_system:
            await self.alert_system.send_alert(
                "system_shutdown",
                "System Shutdown",
                "TradeBot Sentinel Pro Advanced automation system stopped",
                alert_type="info"
            )
        
        self.logger.info("Automation system stopped successfully")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.running:
            asyncio.run(self.stop_automation())


async def main():
    """
    Main entry point for the advanced TradeBot Sentinel Pro system.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="TradeBot Sentinel Pro Advanced Automation System")
    parser.add_argument("--config-dir", default="automation/config", help="Configuration directory")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--mode", choices=["automation", "backtest", "capture", "report"], 
                       default="automation", help="Operation mode")
    parser.add_argument("--strategy", help="Strategy name for backtesting")
    parser.add_argument("--symbol", help="Trading symbol")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--duration", type=int, default=60, help="Capture duration in minutes")
    parser.add_argument("--report-type", choices=["daily", "weekly", "monthly"], 
                       default="daily", help="Report type")
    
    args = parser.parse_args()
    
    # Initialize the advanced system
    bot = TradeBotSentinelProAdvanced(
        config_dir=args.config_dir,
        headless=args.headless
    )
    
    try:
        if args.mode == "automation":
            # Run full automation system
            print("🚀 Starting TradeBot Sentinel Pro Advanced Automation System")
            print("Press Ctrl+C to stop...")
            await bot.start_automation()
        
        elif args.mode == "backtest":
            # Run backtest
            if not all([args.strategy, args.symbol, args.start_date, args.end_date]):
                print("Error: Backtest mode requires --strategy, --symbol, --start-date, and --end-date")
                return
            
            result = await bot.run_backtest(
                strategy_name=args.strategy,
                symbol=args.symbol,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            print("\n📊 Backtest Results:")
            print(json.dumps(result, indent=2))
        
        elif args.mode == "capture":
            # Capture trading session
            session_data = await bot.capture_trade_session(args.duration)
            print(f"\n📸 Session captured: {session_data}")
        
        elif args.mode == "report":
            # Generate report
            report = bot.generate_report(args.report_type)
            print(f"\n📋 {args.report_type.title()} Report:")
            print(json.dumps(report, indent=2))
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopping automation system...")
        await bot.stop_automation()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await bot.stop_automation()
        raise


if __name__ == "__main__":
    # Ensure event loop compatibility on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())