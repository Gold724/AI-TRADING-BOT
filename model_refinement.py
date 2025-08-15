# model_refinement.py

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Try to import components
try:
    from prompt_optimizer import PromptOptimizer
    from memory_engine import MemoryEngine
    from strategy_manager import StrategyManager
    from live_trading import LiveTrading
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
        logging.FileHandler("model_refinement.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("model_refinement")

class ModelRefinement:
    """Model refinement system for continuously improving AI models and prompts
    
    This class manages the continuous refinement of AI models and prompt optimization
    based on real-world performance data. It analyzes trading results, identifies
    patterns in successful and unsuccessful trades, and refines the models and prompts
    to improve future performance.
    """
    
    def __init__(self, config_path: str = "config/model_refinement_config.json"):
        """Initialize the model refinement system
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.components = {}
        self.refinement_history = []
        self.model_performance = {}
        self.running = False
        self.refinement_thread = None
        self.last_refinement_time = datetime.now()
        
        # Create data directory
        os.makedirs("data/model_refinement", exist_ok=True)
        
        logger.info("Model refinement system initialized")
    
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
                    "refinement_interval": 86400,  # seconds (1 day)
                    "min_trades_for_analysis": 50,
                    "performance_window_days": 30,
                    "backtest_iterations": 10,
                    "prompt_optimization": {
                        "enabled": True,
                        "max_variants": 5,
                        "test_trades": 20,
                        "optimization_frequency_days": 7
                    },
                    "model_evaluation": {
                        "metrics": [
                            "win_rate",
                            "profit_factor",
                            "average_win_loss_ratio",
                            "max_drawdown",
                            "sharpe_ratio"
                        ],
                        "weights": {
                            "win_rate": 0.3,
                            "profit_factor": 0.3,
                            "average_win_loss_ratio": 0.15,
                            "max_drawdown": 0.15,
                            "sharpe_ratio": 0.1
                        }
                    },
                    "market_conditions": [
                        "trending_bullish",
                        "trending_bearish",
                        "ranging_low_volatility",
                        "ranging_high_volatility",
                        "breakout",
                        "reversal"
                    ],
                    "learning_rate": 0.1,  # How quickly to adapt to new data
                    "auto_deploy": False  # Whether to automatically deploy refined models
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
                "refinement_interval": 86400,
                "min_trades_for_analysis": 50,
                "performance_window_days": 30,
                "prompt_optimization": {
                    "enabled": True,
                    "max_variants": 5,
                    "test_trades": 20
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
            self.components["prompt_optimizer"] = PromptOptimizer()
            self.components["memory_engine"] = MemoryEngine()
            self.components["strategy_manager"] = StrategyManager()
            self.components["live_trading"] = LiveTrading()
            self.components["backtest_engine"] = BacktestEngine()
            
            logger.info("All components initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            return False
    
    def start_refinement(self):
        """Start the model refinement thread"""
        if self.running:
            logger.warning("Model refinement already running")
            return
        
        if not ALL_IMPORTS_SUCCESSFUL:
            logger.error("Cannot start model refinement due to import errors")
            return
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components")
            return
        
        # Load refinement history
        self._load_refinement_history()
        
        self.running = True
        self.refinement_thread = threading.Thread(target=self._refinement_loop)
        self.refinement_thread.daemon = True
        self.refinement_thread.start()
        
        logger.info("Model refinement started")
    
    def stop_refinement(self):
        """Stop the model refinement thread"""
        if not self.running:
            logger.warning("Model refinement not running")
            return
        
        self.running = False
        
        if self.refinement_thread and self.refinement_thread.is_alive():
            self.refinement_thread.join(timeout=5)
        
        logger.info("Model refinement stopped")
    
    def _refinement_loop(self):
        """Main refinement loop"""
        while self.running:
            try:
                # Check if it's time to refine models
                current_time = datetime.now()
                refinement_interval = self.config.get("refinement_interval", 86400)  # Default: 1 day
                
                if (current_time - self.last_refinement_time).total_seconds() >= refinement_interval:
                    # Analyze trading performance
                    self._analyze_trading_performance()
                    
                    # Optimize prompts if enabled
                    if self.config.get("prompt_optimization", {}).get("enabled", True):
                        self._optimize_prompts()
                    
                    # Refine models based on performance
                    self._refine_models()
                    
                    # Save refinement history
                    self._save_refinement_history()
                    
                    # Update last refinement time
                    self.last_refinement_time = current_time
                
                # Sleep for a while
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in refinement loop: {e}")
                time.sleep(300)  # Sleep for 5 minutes before retrying
    
    def _load_refinement_history(self):
        """Load refinement history from file"""
        try:
            file_path = os.path.join("data", "model_refinement", "refinement_history.json")
            
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    self.refinement_history = json.load(f)
                
                logger.info(f"Loaded {len(self.refinement_history)} refinement records from history")
        except Exception as e:
            logger.error(f"Error loading refinement history: {e}")
    
    def _save_refinement_history(self):
        """Save refinement history to file"""
        try:
            file_path = os.path.join("data", "model_refinement", "refinement_history.json")
            
            with open(file_path, "w") as f:
                json.dump(self.refinement_history, f, indent=4)
            
            logger.info(f"Saved {len(self.refinement_history)} refinement records to history")
        except Exception as e:
            logger.error(f"Error saving refinement history: {e}")
    
    def _analyze_trading_performance(self):
        """Analyze trading performance to identify patterns"""
        try:
            # Get live trading component
            live_trading = self.components["live_trading"]
            
            # Get memory engine
            memory_engine = self.components["memory_engine"]
            
            # Get strategy manager
            strategy_manager = self.components["strategy_manager"]
            
            # Get all strategies
            strategies = strategy_manager.get_all_strategies()
            
            # Get performance window
            performance_window_days = self.config.get("performance_window_days", 30)
            start_date = datetime.now() - timedelta(days=performance_window_days)
            
            # Analyze each strategy
            for strategy_name in strategies:
                # Get order history for the strategy
                order_history = live_trading.get_order_history(
                    strategy=strategy_name,
                    start_date=start_date
                )
                
                # Skip if not enough trades
                min_trades = self.config.get("min_trades_for_analysis", 50)
                if len(order_history) < min_trades:
                    logger.info(f"Strategy {strategy_name} has insufficient trades for analysis ({len(order_history)} < {min_trades})")
                    continue
                
                # Analyze trades by market condition
                market_conditions = self.config.get("market_conditions", [])
                condition_performance = {condition: {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0.0,
                    "win_rate": 0.0,
                    "avg_profit": 0.0
                } for condition in market_conditions}
                
                # Process each trade
                for order in order_history:
                    # Get market condition for this trade
                    trade_time = datetime.fromisoformat(order.get("close_time", order.get("open_time", "")))
                    symbol = order.get("symbol", "")
                    
                    # Get market condition from memory engine
                    condition = memory_engine.get_market_condition(symbol, trade_time)
                    
                    if condition in condition_performance:
                        # Update condition performance
                        condition_performance[condition]["trades"] += 1
                        
                        profit = order.get("profit", 0)
                        if profit > 0:
                            condition_performance[condition]["wins"] += 1
                        else:
                            condition_performance[condition]["losses"] += 1
                        
                        condition_performance[condition]["profit"] += profit
                
                # Calculate performance metrics for each condition
                for condition, perf in condition_performance.items():
                    if perf["trades"] > 0:
                        perf["win_rate"] = perf["wins"] / perf["trades"] * 100
                        perf["avg_profit"] = perf["profit"] / perf["trades"]
                
                # Store strategy performance by market condition
                self.model_performance[strategy_name] = {
                    "timestamp": datetime.now().isoformat(),
                    "total_trades": len(order_history),
                    "condition_performance": condition_performance
                }
                
                logger.info(f"Analyzed performance for strategy {strategy_name} across {len(market_conditions)} market conditions")
            
            # Save model performance to file
            self._save_model_performance()
        except Exception as e:
            logger.error(f"Error analyzing trading performance: {e}")
    
    def _save_model_performance(self):
        """Save model performance to file"""
        try:
            file_path = os.path.join("data", "model_refinement", "model_performance.json")
            
            with open(file_path, "w") as f:
                json.dump(self.model_performance, f, indent=4)
            
            logger.info(f"Saved performance data for {len(self.model_performance)} models")
        except Exception as e:
            logger.error(f"Error saving model performance: {e}")
    
    def _optimize_prompts(self):
        """Optimize prompts based on performance analysis"""
        try:
            # Get prompt optimizer
            prompt_optimizer = self.components["prompt_optimizer"]
            
            # Get memory engine
            memory_engine = self.components["memory_engine"]
            
            # Check if it's time to optimize prompts
            last_optimization = None
            for record in reversed(self.refinement_history):
                if record.get("type") == "prompt_optimization":
                    last_optimization = datetime.fromisoformat(record.get("timestamp", ""))
                    break
            
            optimization_frequency_days = self.config.get("prompt_optimization", {}).get("optimization_frequency_days", 7)
            
            if last_optimization and (datetime.now() - last_optimization).days < optimization_frequency_days:
                logger.info(f"Skipping prompt optimization, last optimization was {(datetime.now() - last_optimization).days} days ago")
                return
            
            # Get strategies with sufficient performance data
            strategies_to_optimize = []
            for strategy_name, performance in self.model_performance.items():
                if performance.get("total_trades", 0) >= self.config.get("min_trades_for_analysis", 50):
                    strategies_to_optimize.append(strategy_name)
            
            if not strategies_to_optimize:
                logger.info("No strategies have sufficient data for prompt optimization")
                return
            
            # Optimize prompts for each strategy
            optimization_results = {}
            
            for strategy_name in strategies_to_optimize:
                # Get current performance by market condition
                condition_performance = self.model_performance[strategy_name].get("condition_performance", {})
                
                # Identify conditions that need improvement
                conditions_to_improve = []
                for condition, perf in condition_performance.items():
                    # Only consider conditions with sufficient trades
                    if perf["trades"] >= 10 and perf["win_rate"] < 50:
                        conditions_to_improve.append(condition)
                
                if not conditions_to_improve:
                    logger.info(f"No market conditions need improvement for strategy {strategy_name}")
                    continue
                
                # Generate optimized prompts for each condition
                strategy_results = {}
                
                for condition in conditions_to_improve:
                    # Get current prompt for this condition
                    current_prompt = prompt_optimizer.get_prompt(
                        strategy=strategy_name,
                        market_condition=condition
                    )
                    
                    # Generate variants
                    max_variants = self.config.get("prompt_optimization", {}).get("max_variants", 5)
                    variants = prompt_optimizer.generate_prompt_variants(
                        strategy=strategy_name,
                        market_condition=condition,
                        base_prompt=current_prompt,
                        num_variants=max_variants
                    )
                    
                    # Test variants with backtest engine
                    backtest_engine = self.components["backtest_engine"]
                    variant_results = {}
                    
                    for i, variant in enumerate(variants):
                        # Create test configuration
                        test_config = {
                            "strategy": strategy_name,
                            "market_condition": condition,
                            "prompt": variant,
                            "num_trades": self.config.get("prompt_optimization", {}).get("test_trades", 20)
                        }
                        
                        # Run backtest with this prompt variant
                        result = backtest_engine.run_prompt_backtest(test_config)
                        
                        # Store results
                        variant_results[f"variant_{i+1}"] = {
                            "prompt": variant,
                            "win_rate": result.get("win_rate", 0),
                            "profit_factor": result.get("profit_factor", 0),
                            "total_profit": result.get("total_profit", 0),
                            "trades": result.get("total_trades", 0)
                        }
                    
                    # Find best variant
                    best_variant = None
                    best_score = 0
                    
                    for variant_id, result in variant_results.items():
                        # Calculate score based on win rate and profit factor
                        score = result["win_rate"] * 0.6 + min(result["profit_factor"], 3.0) / 3.0 * 0.4
                        
                        if score > best_score:
                            best_score = score
                            best_variant = variant_id
                    
                    # Store results for this condition
                    strategy_results[condition] = {
                        "current_performance": condition_performance[condition],
                        "variant_results": variant_results,
                        "best_variant": best_variant,
                        "best_score": best_score
                    }
                    
                    # Update prompt if best variant is better than current
                    if best_variant and best_score > 0.6:  # Threshold for improvement
                        best_prompt = variant_results[best_variant]["prompt"]
                        prompt_optimizer.update_prompt(
                            strategy=strategy_name,
                            market_condition=condition,
                            prompt=best_prompt
                        )
                        
                        logger.info(f"Updated prompt for strategy {strategy_name}, condition {condition} with {best_variant}")
                
                # Store results for this strategy
                optimization_results[strategy_name] = strategy_results
            
            # Record optimization in history
            if optimization_results:
                refinement_record = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "prompt_optimization",
                    "strategies_optimized": list(optimization_results.keys()),
                    "results": optimization_results
                }
                
                self.refinement_history.append(refinement_record)
                
                logger.info(f"Completed prompt optimization for {len(optimization_results)} strategies")
        except Exception as e:
            logger.error(f"Error optimizing prompts: {e}")
    
    def _refine_models(self):
        """Refine models based on performance analysis"""
        try:
            # Get memory engine
            memory_engine = self.components["memory_engine"]
            
            # Get strategy manager
            strategy_manager = self.components["strategy_manager"]
            
            # Update memory engine with latest performance data
            for strategy_name, performance in self.model_performance.items():
                condition_performance = performance.get("condition_performance", {})
                
                for condition, perf in condition_performance.items():
                    if perf["trades"] > 0:
                        # Update memory with this performance data
                        memory_engine.update_strategy_memory(
                            strategy=strategy_name,
                            market_condition=condition,
                            win_rate=perf["win_rate"] / 100,  # Convert to decimal
                            profit_factor=perf["profit"] / abs(perf["losses"]) if perf["losses"] != 0 else 1.0,
                            trade_count=perf["trades"]
                        )
            
            # Get evaluation metrics and weights
            metrics = self.config.get("model_evaluation", {}).get("metrics", [])
            weights = self.config.get("model_evaluation", {}).get("weights", {})
            
            # Calculate overall performance score for each strategy
            strategy_scores = {}
            
            for strategy_name in self.model_performance:
                # Get trading stats
                live_trading = self.components["live_trading"]
                stats = live_trading.get_trading_stats(strategy=strategy_name)
                
                # Calculate weighted score
                score = 0.0
                for metric in metrics:
                    if metric in stats and metric in weights:
                        # Normalize metric value
                        if metric == "win_rate":
                            value = stats[metric] / 100  # Convert to decimal
                        elif metric == "profit_factor":
                            value = min(stats[metric], 3.0) / 3.0  # Cap at 3.0
                        elif metric == "average_win_loss_ratio":
                            value = min(stats[metric], 3.0) / 3.0  # Cap at 3.0
                        elif metric == "max_drawdown":
                            value = 1.0 - stats[metric]  # Invert so lower is better
                        elif metric == "sharpe_ratio":
                            value = min(stats[metric], 3.0) / 3.0  # Cap at 3.0
                        else:
                            value = stats.get(metric, 0)
                        
                        # Add weighted value to score
                        score += value * weights.get(metric, 0)
                
                strategy_scores[strategy_name] = score
            
            # Record model refinement in history
            refinement_record = {
                "timestamp": datetime.now().isoformat(),
                "type": "model_refinement",
                "strategy_scores": strategy_scores,
                "memory_updates": len(self.model_performance)
            }
            
            self.refinement_history.append(refinement_record)
            
            logger.info(f"Completed model refinement for {len(strategy_scores)} strategies")
            
            # Generate performance charts
            self._generate_performance_charts()
        except Exception as e:
            logger.error(f"Error refining models: {e}")
    
    def _generate_performance_charts(self):
        """Generate performance charts"""
        try:
            # Create charts directory
            charts_dir = os.path.join("data", "model_refinement", "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Generate strategy performance by market condition chart
            for strategy_name, performance in self.model_performance.items():
                condition_performance = performance.get("condition_performance", {})
                
                if not condition_performance:
                    continue
                
                # Extract data for chart
                conditions = []
                win_rates = []
                trade_counts = []
                
                for condition, perf in condition_performance.items():
                    if perf["trades"] > 0:
                        conditions.append(condition)
                        win_rates.append(perf["win_rate"])
                        trade_counts.append(perf["trades"])
                
                if not conditions:
                    continue
                
                # Create win rate by condition chart
                plt.figure(figsize=(12, 6))
                bars = plt.bar(conditions, win_rates)
                
                # Add trade count labels
                for i, bar in enumerate(bars):
                    plt.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 1,
                        f"{trade_counts[i]} trades",
                        ha="center",
                        va="bottom",
                        rotation=0
                    )
                
                plt.title(f"Win Rate by Market Condition - {strategy_name}")
                plt.xlabel("Market Condition")
                plt.ylabel("Win Rate (%)")
                plt.axhline(y=50, color="r", linestyle="--")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                plt.savefig(os.path.join(charts_dir, f"{strategy_name}_win_rate_by_condition.png"))
                plt.close()
            
            # Generate refinement history chart
            if len(self.refinement_history) > 1:
                # Extract data for chart
                timestamps = []
                prompt_optimizations = []
                model_refinements = []
                
                for record in self.refinement_history:
                    timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                    timestamps.append(timestamp)
                    
                    if record.get("type") == "prompt_optimization":
                        prompt_optimizations.append(len(record.get("strategies_optimized", [])))
                        model_refinements.append(0)
                    elif record.get("type") == "model_refinement":
                        prompt_optimizations.append(0)
                        model_refinements.append(record.get("memory_updates", 0))
                
                # Create refinement history chart
                plt.figure(figsize=(12, 6))
                plt.plot(timestamps, prompt_optimizations, label="Prompt Optimizations")
                plt.plot(timestamps, model_refinements, label="Model Refinements")
                plt.title("Refinement History")
                plt.xlabel("Date")
                plt.ylabel("Count")
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(os.path.join(charts_dir, "refinement_history.png"))
                plt.close()
            
            logger.info(f"Generated performance charts in {charts_dir}")
        except Exception as e:
            logger.error(f"Error generating performance charts: {e}")
    
    def get_refinement_history(self, days: int = 30) -> List[Dict]:
        """Get refinement history
        
        Args:
            days: Number of days of history to return
            
        Returns:
            List[Dict]: Refinement history
        """
        try:
            # Calculate start date
            start_date = datetime.now() - timedelta(days=days)
            
            # Filter history by date
            filtered_history = [
                record for record in self.refinement_history
                if datetime.fromisoformat(record["timestamp"]) >= start_date
            ]
            
            return filtered_history
        except Exception as e:
            logger.error(f"Error getting refinement history: {e}")
            return []
    
    def get_model_performance(self, strategy_name: Optional[str] = None) -> Dict:
        """Get model performance
        
        Args:
            strategy_name: Strategy name (optional)
            
        Returns:
            Dict: Model performance
        """
        try:
            if strategy_name:
                return self.model_performance.get(strategy_name, {})
            else:
                return self.model_performance
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {}
    
    def get_refinement_summary(self) -> Dict:
        """Get refinement summary
        
        Returns:
            Dict: Refinement summary
        """
        try:
            # Count refinements by type
            prompt_optimizations = 0
            model_refinements = 0
            
            for record in self.refinement_history:
                if record.get("type") == "prompt_optimization":
                    prompt_optimizations += 1
                elif record.get("type") == "model_refinement":
                    model_refinements += 1
            
            # Get last refinement time
            last_refinement = self.refinement_history[-1]["timestamp"] if self.refinement_history else None
            
            # Get strategies with performance data
            strategies_with_data = list(self.model_performance.keys())
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_refinements": len(self.refinement_history),
                "prompt_optimizations": prompt_optimizations,
                "model_refinements": model_refinements,
                "last_refinement": last_refinement,
                "strategies_with_data": strategies_with_data,
                "next_refinement": self.last_refinement_time + timedelta(seconds=self.config.get("refinement_interval", 86400))
            }
        except Exception as e:
            logger.error(f"Error getting refinement summary: {e}")
            return {}

# Main function to run the model refinement system
def main():
    """Main function to run the model refinement system"""
    logger.info("Starting model refinement system")
    
    # Create model refinement instance
    model_refinement = ModelRefinement()
    
    # Start refinement
    model_refinement.start_refinement()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping model refinement system")
        model_refinement.stop_refinement()

# Run the model refinement system if this script is executed directly
if __name__ == "__main__":
    main()