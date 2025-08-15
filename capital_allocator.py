# capital_allocator.py

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Try to import components
try:
    from live_trading import LiveTrading
    from risk_control import RiskController
    from strategy_manager import StrategyManager
    from emergency_protocol import EmergencyProtocol
    from memory_engine import MemoryEngine
    from backtest_engine import BacktestEngine
    
    ALL_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    ALL_IMPORTS_SUCCESSFUL = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("capital_allocator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("capital_allocator")

class CapitalAllocator:
    """Capital allocation manager for the trading system
    
    This class manages the gradual allocation of capital to trading strategies
    based on their performance and risk metrics. It implements a phased approach
    to capital allocation, starting with small amounts and gradually increasing
    as strategies prove reliable.
    """
    
    def __init__(self, config_path: str = "config/capital_allocator_config.json"):
        """Initialize the capital allocator
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.components = {}
        self.allocation_history = []
        self.strategy_performance = {}
        self.running = False
        self.allocator_thread = None
        self.last_allocation_time = datetime.now()
        
        # Create data directory
        os.makedirs("data/capital_allocator", exist_ok=True)
        
        logger.info("Capital allocator initialized")
    
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
                    "allocation_interval": 86400,  # seconds (1 day)
                    "initial_allocation": 0.05,  # 5% of total capital
                    "max_allocation": 0.8,  # 80% of total capital
                    "allocation_increment": 0.05,  # 5% increment
                    "performance_thresholds": {
                        "min_win_rate": 0.55,  # 55%
                        "min_profit_factor": 1.5,
                        "max_drawdown": 0.15,  # 15%
                        "min_sharpe_ratio": 1.0,
                        "min_trades": 20
                    },
                    "allocation_phases": [
                        {
                            "name": "Phase 1 - Initial Testing",
                            "duration_days": 7,
                            "max_allocation_percent": 10,
                            "max_strategies": 3
                        },
                        {
                            "name": "Phase 2 - Limited Deployment",
                            "duration_days": 14,
                            "max_allocation_percent": 25,
                            "max_strategies": 5
                        },
                        {
                            "name": "Phase 3 - Expanded Deployment",
                            "duration_days": 30,
                            "max_allocation_percent": 50,
                            "max_strategies": 8
                        },
                        {
                            "name": "Phase 4 - Full Deployment",
                            "duration_days": 60,
                            "max_allocation_percent": 80,
                            "max_strategies": 12
                        }
                    ],
                    "strategy_weights": {},  # Will be populated with strategy names and weights
                    "symbol_weights": {},  # Will be populated with symbol names and weights
                    "rebalance_threshold": 0.1,  # 10% deviation triggers rebalance
                    "emergency_reduction": 0.5  # Reduce allocation by 50% during emergencies
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
                "allocation_interval": 86400,
                "initial_allocation": 0.05,
                "max_allocation": 0.8,
                "allocation_increment": 0.05,
                "performance_thresholds": {
                    "min_win_rate": 0.55,
                    "min_profit_factor": 1.5,
                    "max_drawdown": 0.15,
                    "min_sharpe_ratio": 1.0,
                    "min_trades": 20
                }
            }
    
    def initialize_components(self) -> bool:
        """Initialize all components
        
        Returns:
            bool: True if all components initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing components...")
            
            # Initialize components
            self.components["live_trading"] = LiveTrading()
            self.components["risk_controller"] = RiskController()
            self.components["strategy_manager"] = StrategyManager()
            self.components["emergency_protocol"] = EmergencyProtocol()
            self.components["memory_engine"] = MemoryEngine()
            self.components["backtest_engine"] = BacktestEngine()
            
            logger.info("All components initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            return False
    
    def start_allocator(self):
        """Start the capital allocator thread"""
        if self.running:
            logger.warning("Capital allocator already running")
            return
        
        if not ALL_IMPORTS_SUCCESSFUL:
            logger.error("Cannot start capital allocator due to import errors")
            return
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components")
            return
        
        # Connect to broker
        live_trading = self.components["live_trading"]
        if not live_trading.connect():
            logger.error("Failed to connect to broker")
            return
        
        # Load allocation history
        self._load_allocation_history()
        
        # Update strategy performance
        self._update_strategy_performance()
        
        self.running = True
        self.allocator_thread = threading.Thread(target=self._allocator_loop)
        self.allocator_thread.daemon = True
        self.allocator_thread.start()
        
        logger.info("Capital allocator started")
    
    def stop_allocator(self):
        """Stop the capital allocator thread"""
        if not self.running:
            logger.warning("Capital allocator not running")
            return
        
        self.running = False
        
        if self.allocator_thread and self.allocator_thread.is_alive():
            self.allocator_thread.join(timeout=5)
        
        # Disconnect from broker
        try:
            live_trading = self.components["live_trading"]
            live_trading.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from broker: {e}")
        
        logger.info("Capital allocator stopped")
    
    def _allocator_loop(self):
        """Main allocator loop"""
        while self.running:
            try:
                # Check if it's time to update allocations
                current_time = datetime.now()
                allocation_interval = self.config.get("allocation_interval", 86400)  # Default: 1 day
                
                if (current_time - self.last_allocation_time).total_seconds() >= allocation_interval:
                    # Update strategy performance
                    self._update_strategy_performance()
                    
                    # Update capital allocations
                    self._update_capital_allocations()
                    
                    # Save allocation history
                    self._save_allocation_history()
                    
                    # Update last allocation time
                    self.last_allocation_time = current_time
                
                # Sleep for a while
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in allocator loop: {e}")
                time.sleep(60)  # Sleep for a minute before retrying
    
    def _load_allocation_history(self):
        """Load allocation history from file"""
        try:
            file_path = os.path.join("data", "capital_allocator", "allocation_history.json")
            
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    self.allocation_history = json.load(f)
                
                logger.info(f"Loaded {len(self.allocation_history)} allocation records from history")
        except Exception as e:
            logger.error(f"Error loading allocation history: {e}")
    
    def _save_allocation_history(self):
        """Save allocation history to file"""
        try:
            file_path = os.path.join("data", "capital_allocator", "allocation_history.json")
            
            with open(file_path, "w") as f:
                json.dump(self.allocation_history, f, indent=4)
            
            logger.info(f"Saved {len(self.allocation_history)} allocation records to history")
        except Exception as e:
            logger.error(f"Error saving allocation history: {e}")
    
    def _update_strategy_performance(self):
        """Update strategy performance metrics"""
        try:
            # Get strategy manager
            strategy_manager = self.components["strategy_manager"]
            
            # Get all strategies
            strategies = strategy_manager.get_all_strategies()
            
            # Get live trading component
            live_trading = self.components["live_trading"]
            
            # Update performance for each strategy
            for strategy_name in strategies:
                # Get strategy performance from live trading
                performance = live_trading.get_trading_stats(strategy=strategy_name)
                
                # Store performance metrics
                self.strategy_performance[strategy_name] = {
                    "win_rate": performance.get("win_rate", 0),
                    "profit_factor": performance.get("profit_factor", 0),
                    "total_trades": performance.get("total_trades", 0),
                    "total_profit": performance.get("total_profit", 0),
                    "max_drawdown": performance.get("max_drawdown", 0),
                    "sharpe_ratio": performance.get("sharpe_ratio", 0),
                    "last_updated": datetime.now().isoformat()
                }
            
            logger.info(f"Updated performance metrics for {len(strategies)} strategies")
        except Exception as e:
            logger.error(f"Error updating strategy performance: {e}")
    
    def _get_current_phase(self) -> Dict:
        """Get the current allocation phase based on system age
        
        Returns:
            Dict: Current phase configuration
        """
        try:
            # Get allocation phases from config
            phases = self.config.get("allocation_phases", [])
            
            if not phases:
                # Return default phase if none defined
                return {
                    "name": "Default Phase",
                    "max_allocation_percent": 10,
                    "max_strategies": 3
                }
            
            # Get system start date (first allocation record or current date)
            if self.allocation_history:
                start_date = datetime.fromisoformat(self.allocation_history[0]["timestamp"])
            else:
                start_date = datetime.now()
            
            # Calculate system age in days
            system_age_days = (datetime.now() - start_date).days
            
            # Find current phase
            current_phase = phases[0]
            cumulative_days = 0
            
            for phase in phases:
                cumulative_days += phase.get("duration_days", 0)
                
                if system_age_days <= cumulative_days:
                    current_phase = phase
                    break
                
                # If we've gone through all phases, use the last one
                current_phase = phase
            
            logger.info(f"Current allocation phase: {current_phase['name']} (system age: {system_age_days} days)")
            return current_phase
        except Exception as e:
            logger.error(f"Error determining current phase: {e}")
            # Return default phase
            return {
                "name": "Default Phase",
                "max_allocation_percent": 10,
                "max_strategies": 3
            }
    
    def _update_capital_allocations(self):
        """Update capital allocations for all strategies"""
        try:
            # Get live trading component
            live_trading = self.components["live_trading"]
            
            # Get account info
            account_info = live_trading.get_account_info()
            total_capital = account_info.get("balance", 0)
            
            if total_capital <= 0:
                logger.error("Invalid account balance, cannot update allocations")
                return
            
            # Get current phase
            current_phase = self._get_current_phase()
            max_allocation_percent = current_phase.get("max_allocation_percent", 10)
            max_strategies = current_phase.get("max_strategies", 3)
            
            # Calculate maximum allocatable capital
            max_allocatable_capital = total_capital * (max_allocation_percent / 100)
            
            # Check if emergency protocol is active
            emergency_protocol = self.components["emergency_protocol"]
            is_emergency = emergency_protocol.is_emergency_active()
            
            if is_emergency:
                # Reduce allocation during emergencies
                emergency_reduction = self.config.get("emergency_reduction", 0.5)
                max_allocatable_capital *= (1 - emergency_reduction)
                logger.warning(f"Emergency protocol active, reducing allocation by {emergency_reduction * 100}%")
            
            # Get performance thresholds
            thresholds = self.config.get("performance_thresholds", {})
            
            # Filter strategies that meet performance criteria
            qualified_strategies = {}
            
            for strategy_name, performance in self.strategy_performance.items():
                # Check if strategy meets minimum performance criteria
                if (
                    performance.get("win_rate", 0) >= thresholds.get("min_win_rate", 0.55) and
                    performance.get("profit_factor", 0) >= thresholds.get("min_profit_factor", 1.5) and
                    performance.get("max_drawdown", 1.0) <= thresholds.get("max_drawdown", 0.15) and
                    performance.get("sharpe_ratio", 0) >= thresholds.get("min_sharpe_ratio", 1.0) and
                    performance.get("total_trades", 0) >= thresholds.get("min_trades", 20)
                ):
                    # Calculate performance score
                    score = (
                        performance.get("win_rate", 0) * 0.3 +
                        min(performance.get("profit_factor", 0), 3.0) / 3.0 * 0.3 +
                        (1.0 - performance.get("max_drawdown", 0) / thresholds.get("max_drawdown", 0.15)) * 0.2 +
                        min(performance.get("sharpe_ratio", 0), 3.0) / 3.0 * 0.2
                    )
                    
                    qualified_strategies[strategy_name] = score
            
            # Sort strategies by performance score
            sorted_strategies = sorted(
                qualified_strategies.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Limit to maximum number of strategies for current phase
            top_strategies = sorted_strategies[:max_strategies]
            
            if not top_strategies:
                logger.warning("No strategies meet performance criteria, skipping allocation update")
                return
            
            # Calculate allocation weights based on performance scores
            total_score = sum(score for _, score in top_strategies)
            strategy_weights = {}
            
            for strategy_name, score in top_strategies:
                strategy_weights[strategy_name] = score / total_score if total_score > 0 else 1.0 / len(top_strategies)
            
            # Calculate capital allocation for each strategy
            allocations = {}
            
            for strategy_name, weight in strategy_weights.items():
                allocations[strategy_name] = max_allocatable_capital * weight
            
            # Update risk controller with new allocations
            risk_controller = self.components["risk_controller"]
            
            for strategy_name, allocation in allocations.items():
                risk_controller.set_strategy_capital(strategy_name, allocation)
            
            # Record allocation update
            allocation_record = {
                "timestamp": datetime.now().isoformat(),
                "total_capital": total_capital,
                "allocated_capital": sum(allocations.values()),
                "allocation_percent": (sum(allocations.values()) / total_capital) * 100 if total_capital > 0 else 0,
                "phase": current_phase["name"],
                "is_emergency": is_emergency,
                "allocations": allocations,
                "strategy_weights": strategy_weights
            }
            
            # Add to history
            self.allocation_history.append(allocation_record)
            
            # Update config with latest strategy weights
            self.config["strategy_weights"] = strategy_weights
            
            logger.info(f"Updated capital allocations for {len(allocations)} strategies, total allocated: {sum(allocations.values()):.2f}")
        except Exception as e:
            logger.error(f"Error updating capital allocations: {e}")
    
    def get_strategy_allocation(self, strategy_name: str) -> float:
        """Get current allocation for a strategy
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            float: Current allocation amount
        """
        try:
            # Get risk controller
            risk_controller = self.components["risk_controller"]
            
            # Get strategy capital
            return risk_controller.get_strategy_capital(strategy_name)
        except Exception as e:
            logger.error(f"Error getting strategy allocation: {e}")
            return 0.0
    
    def get_allocation_history(self, days: int = 30) -> List[Dict]:
        """Get allocation history
        
        Args:
            days: Number of days of history to return
            
        Returns:
            List[Dict]: Allocation history
        """
        try:
            # Calculate start date
            start_date = datetime.now() - timedelta(days=days)
            
            # Filter history by date
            filtered_history = [
                record for record in self.allocation_history
                if datetime.fromisoformat(record["timestamp"]) >= start_date
            ]
            
            return filtered_history
        except Exception as e:
            logger.error(f"Error getting allocation history: {e}")
            return []
    
    def get_current_allocations(self) -> Dict:
        """Get current allocations for all strategies
        
        Returns:
            Dict: Current allocations
        """
        try:
            # Get risk controller
            risk_controller = self.components["risk_controller"]
            
            # Get strategy manager
            strategy_manager = self.components["strategy_manager"]
            
            # Get all strategies
            strategies = strategy_manager.get_all_strategies()
            
            # Get allocations for each strategy
            allocations = {}
            
            for strategy_name in strategies:
                allocations[strategy_name] = risk_controller.get_strategy_capital(strategy_name)
            
            return allocations
        except Exception as e:
            logger.error(f"Error getting current allocations: {e}")
            return {}
    
    def get_allocation_summary(self) -> Dict:
        """Get allocation summary
        
        Returns:
            Dict: Allocation summary
        """
        try:
            # Get live trading component
            live_trading = self.components["live_trading"]
            
            # Get account info
            account_info = live_trading.get_account_info()
            total_capital = account_info.get("balance", 0)
            
            # Get current allocations
            allocations = self.get_current_allocations()
            total_allocated = sum(allocations.values())
            
            # Get current phase
            current_phase = self._get_current_phase()
            
            # Calculate allocation percentage
            allocation_percent = (total_allocated / total_capital) * 100 if total_capital > 0 else 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_capital": total_capital,
                "allocated_capital": total_allocated,
                "allocation_percent": allocation_percent,
                "current_phase": current_phase["name"],
                "max_allocation_percent": current_phase.get("max_allocation_percent", 10),
                "strategy_count": len(allocations),
                "max_strategies": current_phase.get("max_strategies", 3)
            }
        except Exception as e:
            logger.error(f"Error getting allocation summary: {e}")
            return {}
    
    def generate_allocation_charts(self):
        """Generate allocation charts"""
        try:
            # Create charts directory
            charts_dir = os.path.join("data", "capital_allocator", "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Get allocation history
            history = self.get_allocation_history(days=90)
            
            if not history:
                logger.warning("No allocation history available for charts")
                return
            
            # Convert to DataFrame
            df_history = pd.DataFrame([
                {
                    "timestamp": datetime.fromisoformat(record["timestamp"]),
                    "total_capital": record["total_capital"],
                    "allocated_capital": record["allocated_capital"],
                    "allocation_percent": record["allocation_percent"],
                    "phase": record["phase"],
                    "is_emergency": record["is_emergency"]
                }
                for record in history
            ])
            
            # Generate allocation percentage chart
            plt.figure(figsize=(12, 6))
            plt.plot(df_history["timestamp"], df_history["allocation_percent"])
            plt.title("Capital Allocation Percentage Over Time")
            plt.xlabel("Date")
            plt.ylabel("Allocation (%)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "allocation_percentage.png"))
            plt.close()
            
            # Generate allocated vs total capital chart
            plt.figure(figsize=(12, 6))
            plt.plot(df_history["timestamp"], df_history["total_capital"], label="Total Capital")
            plt.plot(df_history["timestamp"], df_history["allocated_capital"], label="Allocated Capital")
            plt.title("Total vs Allocated Capital Over Time")
            plt.xlabel("Date")
            plt.ylabel("Capital")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "capital_allocation.png"))
            plt.close()
            
            # Generate strategy allocation chart (most recent allocation)
            if history and "allocations" in history[-1]:
                latest_allocations = history[-1]["allocations"]
                
                # Sort strategies by allocation amount
                sorted_allocations = sorted(
                    latest_allocations.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                strategies = [s[0] for s in sorted_allocations]
                amounts = [s[1] for s in sorted_allocations]
                
                plt.figure(figsize=(12, 6))
                plt.bar(strategies, amounts)
                plt.title("Current Strategy Allocations")
                plt.xlabel("Strategy")
                plt.ylabel("Allocated Capital")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                plt.savefig(os.path.join(charts_dir, "strategy_allocations.png"))
                plt.close()
            
            logger.info(f"Generated allocation charts in {charts_dir}")
        except Exception as e:
            logger.error(f"Error generating allocation charts: {e}")

# Main function to run the capital allocator
def main():
    """Main function to run the capital allocator"""
    logger.info("Starting capital allocator")
    
    # Create capital allocator instance
    capital_allocator = CapitalAllocator()
    
    # Start allocator
    capital_allocator.start_allocator()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping capital allocator")
        capital_allocator.stop_allocator()

# Run the capital allocator if this script is executed directly
if __name__ == "__main__":
    main()