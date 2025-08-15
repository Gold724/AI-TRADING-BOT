# deploy.py

import os
import sys
import json
import time
import logging
import argparse
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("deploy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deploy")

# Import components
try:
    from integration_test import IntegrationTest
    from monitoring_system import MonitoringSystem
    from capital_allocator import CapitalAllocator
    from model_refinement import ModelRefinement
    from metrics_dashboard import run_dashboard
    from live_trading import LiveTrading
    from emergency_protocol import EmergencyProtocol
    from signal_router import SignalRouter
    from memory_engine import MemoryEngine
    from strategy_manager import StrategyManager
    from risk_control import RiskController
    
    ALL_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    ALL_IMPORTS_SUCCESSFUL = False

class TradingSystemDeployer:
    """Deployer for the TRAE AI Trading System
    
    This class manages the deployment of all components of the TRAE AI Trading System,
    including integration testing, monitoring, capital allocation, and model refinement.
    """
    
    def __init__(self, config_path: str = "config/deploy_config.json"):
        """Initialize the deployer
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.components = {}
        self.component_threads = {}
        self.running = False
        self.dashboard_process = None
        
        logger.info("Trading system deployer initialized")
    
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
                    "environment": "development",  # development, staging, production
                    "run_integration_test": True,
                    "components": {
                        "monitoring_system": True,
                        "capital_allocator": True,
                        "model_refinement": True,
                        "metrics_dashboard": True,
                        "live_trading": True,
                        "emergency_protocol": True,
                        "signal_router": True
                    },
                    "broker": {
                        "name": "mock",  # mock, exness, bulenox
                        "api_key": "",
                        "api_secret": "",
                        "account_id": ""
                    },
                    "dashboard": {
                        "port": 8501,
                        "host": "localhost"
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
                "environment": "development",
                "run_integration_test": True,
                "components": {
                    "monitoring_system": True,
                    "capital_allocator": True,
                    "model_refinement": True,
                    "metrics_dashboard": True,
                    "live_trading": True,
                    "emergency_protocol": True,
                    "signal_router": True
                }
            }
    
    def run_integration_test(self) -> bool:
        """Run integration test
        
        Returns:
            bool: True if test passed, False otherwise
        """
        try:
            logger.info("Running integration test...")
            
            # Create integration test instance
            integration_test = IntegrationTest()
            
            # Run test
            result = integration_test.run_all_tests()
            
            if result["success"]:
                logger.info("Integration test passed!")
                return True
            else:
                logger.error(f"Integration test failed: {result['message']}")
                return False
        except Exception as e:
            logger.error(f"Error running integration test: {e}")
            return False
    
    def initialize_components(self) -> bool:
        """Initialize all components
        
        Returns:
            bool: True if all components initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing components...")
            
            # Get enabled components
            enabled_components = self.config.get("components", {})
            
            # Initialize core components first
            if enabled_components.get("emergency_protocol", True):
                self.components["emergency_protocol"] = EmergencyProtocol()
                logger.info("Initialized emergency protocol")
            
            if enabled_components.get("live_trading", True):
                # Get broker config
                broker_config = self.config.get("broker", {})
                
                # Initialize live trading with broker config
                self.components["live_trading"] = LiveTrading(
                    broker_name=broker_config.get("name", "mock"),
                    api_key=broker_config.get("api_key", ""),
                    api_secret=broker_config.get("api_secret", ""),
                    account_id=broker_config.get("account_id", "")
                )
                logger.info(f"Initialized live trading with {broker_config.get('name', 'mock')} broker")
            
            # Initialize other components
            if enabled_components.get("monitoring_system", True):
                self.components["monitoring_system"] = MonitoringSystem()
                logger.info("Initialized monitoring system")
            
            if enabled_components.get("capital_allocator", True):
                self.components["capital_allocator"] = CapitalAllocator()
                logger.info("Initialized capital allocator")
            
            if enabled_components.get("model_refinement", True):
                self.components["model_refinement"] = ModelRefinement()
                logger.info("Initialized model refinement")
            
            if enabled_components.get("signal_router", True):
                self.components["signal_router"] = SignalRouter()
                logger.info("Initialized signal router")
            
            logger.info("All components initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            return False
    
    def start_components(self):
        """Start all components"""
        try:
            logger.info("Starting components...")
            
            # Get enabled components
            enabled_components = self.config.get("components", {})
            
            # Start emergency protocol first
            if "emergency_protocol" in self.components:
                # No explicit start method for emergency protocol
                logger.info("Emergency protocol ready")
            
            # Start live trading
            if "live_trading" in self.components:
                live_trading = self.components["live_trading"]
                if live_trading.connect():
                    logger.info("Live trading connected")
                else:
                    logger.error("Failed to connect live trading")
                    return False
            
            # Start monitoring system
            if "monitoring_system" in self.components:
                monitoring_system = self.components["monitoring_system"]
                
                # Start in a separate thread
                monitoring_thread = threading.Thread(
                    target=monitoring_system.start_monitoring,
                    daemon=True
                )
                monitoring_thread.start()
                
                self.component_threads["monitoring_system"] = monitoring_thread
                logger.info("Monitoring system started")
            
            # Start capital allocator
            if "capital_allocator" in self.components:
                capital_allocator = self.components["capital_allocator"]
                
                # Start in a separate thread
                allocator_thread = threading.Thread(
                    target=capital_allocator.start_allocator,
                    daemon=True
                )
                allocator_thread.start()
                
                self.component_threads["capital_allocator"] = allocator_thread
                logger.info("Capital allocator started")
            
            # Start model refinement
            if "model_refinement" in self.components:
                model_refinement = self.components["model_refinement"]
                
                # Start in a separate thread
                refinement_thread = threading.Thread(
                    target=model_refinement.start_refinement,
                    daemon=True
                )
                refinement_thread.start()
                
                self.component_threads["model_refinement"] = refinement_thread
                logger.info("Model refinement started")
            
            # Start signal router
            if "signal_router" in self.components:
                signal_router = self.components["signal_router"]
                
                # Start in a separate thread
                router_thread = threading.Thread(
                    target=signal_router.start,
                    daemon=True
                )
                router_thread.start()
                
                self.component_threads["signal_router"] = router_thread
                logger.info("Signal router started")
            
            # Start metrics dashboard
            if enabled_components.get("metrics_dashboard", True):
                # Get dashboard config
                dashboard_config = self.config.get("dashboard", {})
                port = dashboard_config.get("port", 8501)
                host = dashboard_config.get("host", "localhost")
                
                # Start dashboard in a separate process
                dashboard_thread = threading.Thread(
                    target=self._start_dashboard,
                    args=(host, port),
                    daemon=True
                )
                dashboard_thread.start()
                
                self.component_threads["metrics_dashboard"] = dashboard_thread
                logger.info(f"Metrics dashboard started at http://{host}:{port}")
            
            self.running = True
            logger.info("All components started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting components: {e}")
            return False
    
    def _start_dashboard(self, host: str, port: int):
        """Start the metrics dashboard
        
        Args:
            host: Dashboard host
            port: Dashboard port
        """
        try:
            import subprocess
            
            # Start dashboard using subprocess
            cmd = [
                sys.executable,
                "metrics_dashboard.py",
                "--server.port", str(port),
                "--server.address", host
            ]
            
            self.dashboard_process = subprocess.Popen(cmd)
            logger.info(f"Dashboard process started with PID {self.dashboard_process.pid}")
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
    
    def stop_components(self):
        """Stop all components"""
        try:
            logger.info("Stopping components...")
            
            # Stop signal router
            if "signal_router" in self.components:
                signal_router = self.components["signal_router"]
                signal_router.stop()
                logger.info("Signal router stopped")
            
            # Stop model refinement
            if "model_refinement" in self.components:
                model_refinement = self.components["model_refinement"]
                model_refinement.stop_refinement()
                logger.info("Model refinement stopped")
            
            # Stop capital allocator
            if "capital_allocator" in self.components:
                capital_allocator = self.components["capital_allocator"]
                capital_allocator.stop_allocator()
                logger.info("Capital allocator stopped")
            
            # Stop monitoring system
            if "monitoring_system" in self.components:
                monitoring_system = self.components["monitoring_system"]
                monitoring_system.stop_monitoring()
                logger.info("Monitoring system stopped")
            
            # Stop live trading
            if "live_trading" in self.components:
                live_trading = self.components["live_trading"]
                live_trading.disconnect()
                logger.info("Live trading disconnected")
            
            # Stop dashboard process
            if self.dashboard_process:
                self.dashboard_process.terminate()
                self.dashboard_process.wait()
                logger.info("Dashboard process terminated")
            
            # Wait for threads to finish
            for component, thread in self.component_threads.items():
                if thread.is_alive():
                    thread.join(timeout=5)
                    logger.info(f"{component} thread joined")
            
            self.running = False
            logger.info("All components stopped")
        except Exception as e:
            logger.error(f"Error stopping components: {e}")
    
    def deploy(self) -> bool:
        """Deploy the trading system
        
        Returns:
            bool: True if deployment successful, False otherwise
        """
        try:
            logger.info(f"Deploying trading system in {self.config.get('environment', 'development')} environment")
            
            # Run integration test if enabled
            if self.config.get("run_integration_test", True):
                if not self.run_integration_test():
                    logger.error("Integration test failed, aborting deployment")
                    return False
            
            # Initialize components
            if not self.initialize_components():
                logger.error("Failed to initialize components, aborting deployment")
                return False
            
            # Start components
            if not self.start_components():
                logger.error("Failed to start components, aborting deployment")
                return False
            
            logger.info("Trading system deployed successfully")
            return True
        except Exception as e:
            logger.error(f"Error deploying trading system: {e}")
            return False
    
    def run(self):
        """Run the trading system"""
        try:
            # Deploy the system
            if not self.deploy():
                logger.error("Deployment failed, exiting")
                return
            
            logger.info("Trading system running, press Ctrl+C to stop")
            
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt, stopping trading system")
            self.stop_components()
        except Exception as e:
            logger.error(f"Error running trading system: {e}")
            self.stop_components()

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="TRAE AI Trading System Deployer")
    parser.add_argument(
        "--config",
        type=str,
        default="config/deploy_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--environment",
        type=str,
        choices=["development", "staging", "production"],
        help="Deployment environment"
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip integration test"
    )
    parser.add_argument(
        "--broker",
        type=str,
        choices=["mock", "exness", "bulenox"],
        help="Broker to use"
    )
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = TradingSystemDeployer(config_path=args.config)
    
    # Override config with command line arguments
    if args.environment:
        deployer.config["environment"] = args.environment
    
    if args.skip_test:
        deployer.config["run_integration_test"] = False
    
    if args.broker:
        deployer.config["broker"]["name"] = args.broker
    
    # Run the system
    deployer.run()

if __name__ == "__main__":
    main()