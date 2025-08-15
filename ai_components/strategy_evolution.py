#!/usr/bin/env python
# Strategy Evolution - A/B testing and strategy optimization

import json
import logging
import os
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("strategy_evolution")

# Constants
STRATEGY_HISTORY_FILE = os.path.join("data", "strategy_history.json")
STRATEGY_CONFIG_FILE = os.path.join("config", "strategy_config.json")
STRATEGY_VARIANTS_FILE = os.path.join("data", "strategy_variants.json")

class StrategyEvolution:
    """System for evolving trading strategies through A/B testing and optimization"""
    
    def __init__(self, 
                 strategy_history_file: str = STRATEGY_HISTORY_FILE,
                 strategy_config_file: str = STRATEGY_CONFIG_FILE,
                 strategy_variants_file: str = STRATEGY_VARIANTS_FILE):
        """Initialize the strategy evolution system
        
        Args:
            strategy_history_file (str): Path to the strategy history file
            strategy_config_file (str): Path to the strategy configuration file
            strategy_variants_file (str): Path to the strategy variants file
        """
        self.strategy_history_file = strategy_history_file
        self.strategy_config_file = strategy_config_file
        self.strategy_variants_file = strategy_variants_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(strategy_history_file), exist_ok=True)
        os.makedirs(os.path.dirname(strategy_config_file), exist_ok=True)
        os.makedirs(os.path.dirname(strategy_variants_file), exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize strategy variants if file doesn't exist
        if not os.path.exists(strategy_variants_file):
            self.initialize_strategy_variants()
        
        logger.info("Strategy Evolution system initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load the strategy evolution configuration
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            if os.path.exists(self.strategy_config_file):
                with open(self.strategy_config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "evolution": {
                        "enabled": True,
                        "min_trades_for_evaluation": 20,  # Minimum trades before evaluating a strategy
                        "evaluation_period_days": 30,    # Days to evaluate before making decisions
                        "retirement_threshold": 40,      # Win rate below this threshold may trigger retirement
                        "mutation_rate": 0.1,           # Rate of parameter mutation
                        "crossover_rate": 0.3,          # Rate of parameter crossover between strategies
                        "population_size": 5,           # Number of variants to maintain per strategy
                        "tournament_size": 3            # Number of variants to compare in tournament selection
                    },
                    "ab_testing": {
                        "enabled": True,
                        "test_allocation": 0.2,         # Percentage of trades to allocate to test variants
                        "min_confidence": 60,           # Minimum confidence to deploy a variant
                        "max_active_tests": 3           # Maximum number of active A/B tests
                    },
                    "optimization": {
                        "enabled": True,
                        "optimization_interval_days": 7, # Days between optimization runs
                        "parameter_bounds": {            # Default parameter bounds for optimization
                            "fast_period": [5, 20],
                            "slow_period": [20, 50],
                            "signal_period": [5, 15],
                            "rsi_period": [7, 21],
                            "rsi_overbought": [70, 80],
                            "rsi_oversold": [20, 30],
                            "atr_period": [7, 21],
                            "atr_multiplier": [1.5, 3.5],
                            "profit_target": [1.0, 3.0],
                            "stop_loss": [0.5, 2.0]
                        }
                    },
                    "triggers": {
                        "time_based": {
                            "enabled": True,
                            "daily_evaluation": False,
                            "weekly_evaluation": True,
                            "monthly_optimization": True
                        },
                        "signal_based": {
                            "enabled": True,
                            "trades_threshold": 50,      # Evaluate after this many trades
                            "consecutive_losses": 5,     # Evaluate after this many consecutive losses
                            "drawdown_threshold": 10     # Evaluate after this percentage drawdown
                        },
                        "manual": {
                            "enabled": True
                        }
                    }
                }
                
                # Save default configuration
                with open(self.strategy_config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def initialize_strategy_variants(self) -> None:
        """Initialize strategy variants"""
        try:
            default_variants = {
                "strategies": {},
                "active_tests": [],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.strategy_variants_file, 'w') as f:
                json.dump(default_variants, f, indent=4)
            
            logger.info("Initialized strategy variants")
        except Exception as e:
            logger.error(f"Error initializing strategy variants: {e}")
    
    def load_strategy_history(self) -> List[Dict[str, Any]]:
        """Load strategy history
        
        Returns:
            List[Dict[str, Any]]: List of historical trades
        """
        try:
            if os.path.exists(self.strategy_history_file):
                with open(self.strategy_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading strategy history: {e}")
            return []
    
    def load_strategy_variants(self) -> Dict[str, Any]:
        """Load strategy variants
        
        Returns:
            Dict[str, Any]: Strategy variants
        """
        try:
            if os.path.exists(self.strategy_variants_file):
                with open(self.strategy_variants_file, 'w') as f:
                    return json.load(f)
            return {"strategies": {}, "active_tests": [], "last_updated": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error loading strategy variants: {e}")
            return {"strategies": {}, "active_tests": [], "last_updated": datetime.now().isoformat()}
    
    def evaluate_strategies(self) -> Dict[str, Any]:
        """Evaluate all strategies and make evolution decisions
        
        Returns:
            Dict[str, Any]: Evaluation results
        """
        try:
            # Load strategy history
            strategy_history = self.load_strategy_history()
            
            # Group trades by strategy
            strategy_trades = {}
            for trade in strategy_history:
                strategy = trade.get("strategy")
                if strategy:
                    if strategy not in strategy_trades:
                        strategy_trades[strategy] = []
                    strategy_trades[strategy].append(trade)
            
            # Evaluate each strategy
            evaluation_results = {}
            for strategy, trades in strategy_trades.items():
                # Skip strategies with insufficient trades
                if len(trades) < self.config["evolution"]["min_trades_for_evaluation"]:
                    continue
                
                # Calculate performance metrics
                metrics = self.calculate_performance_metrics(trades)
                
                # Make evolution decision
                decision = self.make_evolution_decision(strategy, metrics)
                
                evaluation_results[strategy] = {
                    "metrics": metrics,
                    "decision": decision
                }
                
                # Execute decision if not just monitoring
                if decision["action"] != "monitor":
                    self.execute_evolution_decision(strategy, decision, metrics)
            
            return evaluation_results
        except Exception as e:
            logger.error(f"Error evaluating strategies: {e}")
            return {}
    
    def calculate_performance_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics for a set of trades
        
        Args:
            trades (List[Dict[str, Any]]): List of trades
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        # Filter recent trades based on evaluation period
        cutoff_date = datetime.now() - timedelta(days=self.config["evolution"]["evaluation_period_days"])
        recent_trades = []
        
        for trade in trades:
            if "timestamp" in trade:
                try:
                    trade_date = datetime.fromisoformat(trade["timestamp"])
                    if trade_date >= cutoff_date:
                        recent_trades.append(trade)
                except (ValueError, TypeError):
                    pass
        
        # Use recent trades if available, otherwise use all trades
        evaluation_trades = recent_trades if recent_trades else trades
        
        # Calculate metrics
        total_trades = len(evaluation_trades)
        winning_trades = sum(1 for trade in evaluation_trades if trade.get("win", False))
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate profit metrics
        total_profit = sum(trade.get("profit", 0) for trade in evaluation_trades)
        total_loss = sum(abs(trade.get("profit", 0)) for trade in evaluation_trades if trade.get("profit", 0) < 0)
        
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
        
        # Calculate drawdown
        balance_curve = []
        running_balance = 0
        for trade in evaluation_trades:
            running_balance += trade.get("profit", 0)
            balance_curve.append(running_balance)
        
        max_drawdown = 0
        peak = 0
        
        for balance in balance_curve:
            if balance > peak:
                peak = balance
            else:
                drawdown = (peak - balance) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0
        
        for trade in evaluation_trades:
            if trade.get("win", False):
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            else:
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        # Calculate average profit per trade
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "avg_profit": avg_profit,
            "total_profit": total_profit
        }
    
    def make_evolution_decision(self, strategy: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision about strategy evolution
        
        Args:
            strategy (str): Strategy name
            metrics (Dict[str, Any]): Performance metrics
            
        Returns:
            Dict[str, Any]: Evolution decision
        """
        decision = {
            "action": "monitor",  # Default action
            "reason": "Strategy is performing adequately",
            "confidence": 0
        }
        
        # Check for retirement
        if metrics["win_rate"] < self.config["evolution"]["retirement_threshold"] and metrics["profit_factor"] < 1.0:
            decision["action"] = "retire"
            decision["reason"] = f"Poor performance: Win rate {metrics['win_rate']:.2f}% below threshold, negative profit factor"
            decision["confidence"] = 80
            return decision
        
        # Check for optimization
        if metrics["win_rate"] < 50 or metrics["profit_factor"] < 1.2:
            decision["action"] = "optimize"
            decision["reason"] = f"Suboptimal performance: Win rate {metrics['win_rate']:.2f}%, profit factor {metrics['profit_factor']:.2f}"
            decision["confidence"] = 70
            return decision
        
        # Check for A/B testing
        if metrics["win_rate"] >= 50 and metrics["profit_factor"] >= 1.2:
            # Strategy is performing well, consider creating variants for A/B testing
            variants = self.get_strategy_variants(strategy)
            
            if len(variants) < self.config["evolution"]["population_size"]:
                decision["action"] = "create_variant"
                decision["reason"] = f"Strategy performing well, creating variant for potential improvement"
                decision["confidence"] = 60
                return decision
        
        return decision
    
    def execute_evolution_decision(self, strategy: str, decision: Dict[str, Any], 
                                  metrics: Dict[str, Any]) -> None:
        """Execute a strategy evolution decision
        
        Args:
            strategy (str): Strategy name
            decision (Dict[str, Any]): Evolution decision
            metrics (Dict[str, Any]): Performance metrics
        """
        try:
            action = decision["action"]
            
            if action == "retire":
                self.retire_strategy(strategy)
                logger.info(f"Retired strategy '{strategy}' due to poor performance")
            
            elif action == "optimize":
                optimized_params = self.optimize_strategy(strategy)
                logger.info(f"Optimized strategy '{strategy}' with new parameters: {optimized_params}")
            
            elif action == "create_variant":
                variant = self.create_strategy_variant(strategy)
                logger.info(f"Created variant of strategy '{strategy}': {variant['name']}")
            
            # Record the decision
            self.record_evolution_decision(strategy, decision, metrics)
        except Exception as e:
            logger.error(f"Error executing evolution decision: {e}")
    
    def retire_strategy(self, strategy: str) -> None:
        """Retire a poorly performing strategy
        
        Args:
            strategy (str): Strategy name
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Mark strategy as retired
            if strategy in variants["strategies"]:
                variants["strategies"][strategy]["status"] = "retired"
                variants["strategies"][strategy]["retired_date"] = datetime.now().isoformat()
                
                # Remove from active tests
                variants["active_tests"] = [test for test in variants["active_tests"] 
                                         if test.get("strategy") != strategy]
                
                # Save updated variants
                with open(self.strategy_variants_file, 'w') as f:
                    json.dump(variants, f, indent=4)
                
                logger.info(f"Strategy '{strategy}' has been retired")
        except Exception as e:
            logger.error(f"Error retiring strategy: {e}")
    
    def optimize_strategy(self, strategy: str) -> Dict[str, Any]:
        """Optimize a strategy's parameters
        
        Args:
            strategy (str): Strategy name
            
        Returns:
            Dict[str, Any]: Optimized parameters
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Get current parameters or create default
            if strategy in variants["strategies"]:
                current_params = variants["strategies"][strategy].get("parameters", {})
            else:
                current_params = {}
                variants["strategies"][strategy] = {
                    "status": "active",
                    "created_date": datetime.now().isoformat(),
                    "parameters": current_params,
                    "variants": []
                }
            
            # Perform optimization (placeholder for actual optimization algorithm)
            # In a real implementation, this would use historical data to find optimal parameters
            optimized_params = self.perform_parameter_optimization(strategy, current_params)
            
            # Update strategy parameters
            variants["strategies"][strategy]["parameters"] = optimized_params
            variants["strategies"][strategy]["last_optimized"] = datetime.now().isoformat()
            
            # Save updated variants
            with open(self.strategy_variants_file, 'w') as f:
                json.dump(variants, f, indent=4)
            
            logger.info(f"Optimized parameters for strategy '{strategy}'")
            return optimized_params
        except Exception as e:
            logger.error(f"Error optimizing strategy: {e}")
            return {}
    
    def perform_parameter_optimization(self, strategy: str, 
                                     current_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform parameter optimization for a strategy
        
        Args:
            strategy (str): Strategy name
            current_params (Dict[str, Any]): Current parameters
            
        Returns:
            Dict[str, Any]: Optimized parameters
        """
        # This is a placeholder for actual optimization algorithm
        # In a real implementation, this would use historical data and optimization techniques
        # such as grid search, genetic algorithms, or Bayesian optimization
        
        # For now, we'll just make small random adjustments to current parameters
        optimized_params = current_params.copy()
        
        # Get parameter bounds from config
        param_bounds = self.config["optimization"]["parameter_bounds"]
        
        # Adjust each parameter within bounds
        for param, value in current_params.items():
            if param in param_bounds:
                bounds = param_bounds[param]
                # Random adjustment within bounds
                adjustment = random.uniform(-0.1, 0.1)  # Adjust by up to ±10%
                new_value = value * (1 + adjustment)
                # Ensure within bounds
                optimized_params[param] = max(bounds[0], min(bounds[1], new_value))
        
        return optimized_params
    
    def create_strategy_variant(self, strategy: str) -> Dict[str, Any]:
        """Create a variant of an existing strategy
        
        Args:
            strategy (str): Strategy name
            
        Returns:
            Dict[str, Any]: New variant
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Get current parameters or create default
            if strategy in variants["strategies"]:
                current_params = variants["strategies"][strategy].get("parameters", {})
            else:
                current_params = {}
                variants["strategies"][strategy] = {
                    "status": "active",
                    "created_date": datetime.now().isoformat(),
                    "parameters": current_params,
                    "variants": []
                }
            
            # Create variant name
            variant_count = len(variants["strategies"][strategy]["variants"]) + 1
            variant_name = f"{strategy}_v{variant_count}"
            
            # Create variant parameters (mutate current parameters)
            variant_params = self.mutate_parameters(current_params)
            
            # Create variant
            variant = {
                "name": variant_name,
                "parent": strategy,
                "created_date": datetime.now().isoformat(),
                "status": "testing",
                "parameters": variant_params,
                "trades": [],
                "metrics": {}
            }
            
            # Add variant to strategy
            variants["strategies"][strategy]["variants"].append(variant)
            
            # Create A/B test if enabled
            if self.config["ab_testing"]["enabled"] and len(variants["active_tests"]) < self.config["ab_testing"]["max_active_tests"]:
                test = {
                    "id": f"test_{strategy}_{variant_name}_{datetime.now().strftime('%Y%m%d')}",
                    "strategy": strategy,
                    "variant": variant_name,
                    "start_date": datetime.now().isoformat(),
                    "allocation": self.config["ab_testing"]["test_allocation"],
                    "status": "active"
                }
                variants["active_tests"].append(test)
            
            # Save updated variants
            with open(self.strategy_variants_file, 'w') as f:
                json.dump(variants, f, indent=4)
            
            logger.info(f"Created variant '{variant_name}' of strategy '{strategy}'")
            return variant
        except Exception as e:
            logger.error(f"Error creating strategy variant: {e}")
            return {}
    
    def mutate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate strategy parameters to create a variant
        
        Args:
            parameters (Dict[str, Any]): Original parameters
            
        Returns:
            Dict[str, Any]: Mutated parameters
        """
        mutated_params = parameters.copy()
        
        # Get parameter bounds from config
        param_bounds = self.config["optimization"]["parameter_bounds"]
        
        # Mutate each parameter with probability based on mutation rate
        for param, value in parameters.items():
            if param in param_bounds and random.random() < self.config["evolution"]["mutation_rate"]:
                bounds = param_bounds[param]
                # Random mutation within bounds
                mutation = random.uniform(-0.2, 0.2)  # Mutate by up to ±20%
                new_value = value * (1 + mutation)
                # Ensure within bounds
                mutated_params[param] = max(bounds[0], min(bounds[1], new_value))
        
        return mutated_params
    
    def get_strategy_variants(self, strategy: str) -> List[Dict[str, Any]]:
        """Get variants of a strategy
        
        Args:
            strategy (str): Strategy name
            
        Returns:
            List[Dict[str, Any]]: List of variants
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Get variants for this strategy
            if strategy in variants["strategies"]:
                return variants["strategies"][strategy].get("variants", [])
            
            return []
        except Exception as e:
            logger.error(f"Error getting strategy variants: {e}")
            return []
    
    def record_evolution_decision(self, strategy: str, decision: Dict[str, Any], 
                                metrics: Dict[str, Any]) -> None:
        """Record a strategy evolution decision
        
        Args:
            strategy (str): Strategy name
            decision (Dict[str, Any]): Evolution decision
            metrics (Dict[str, Any]): Performance metrics
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Ensure strategy exists
            if strategy not in variants["strategies"]:
                variants["strategies"][strategy] = {
                    "status": "active",
                    "created_date": datetime.now().isoformat(),
                    "parameters": {},
                    "variants": [],
                    "decisions": []
                }
            
            # Add decision record
            if "decisions" not in variants["strategies"][strategy]:
                variants["strategies"][strategy]["decisions"] = []
            
            variants["strategies"][strategy]["decisions"].append({
                "timestamp": datetime.now().isoformat(),
                "action": decision["action"],
                "reason": decision["reason"],
                "confidence": decision["confidence"],
                "metrics": metrics
            })
            
            # Keep only the last 20 decisions
            if len(variants["strategies"][strategy]["decisions"]) > 20:
                variants["strategies"][strategy]["decisions"] = variants["strategies"][strategy]["decisions"][-20:]
            
            # Save updated variants
            with open(self.strategy_variants_file, 'w') as f:
                json.dump(variants, f, indent=4)
            
            logger.info(f"Recorded evolution decision for strategy '{strategy}'")
        except Exception as e:
            logger.error(f"Error recording evolution decision: {e}")
    
    def evaluate_ab_tests(self) -> Dict[str, Any]:
        """Evaluate active A/B tests and make decisions
        
        Returns:
            Dict[str, Any]: Test evaluation results
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Get active tests
            active_tests = variants["active_tests"]
            
            # Evaluate each test
            test_results = {}
            for test in active_tests:
                strategy = test.get("strategy")
                variant_name = test.get("variant")
                
                if not strategy or not variant_name:
                    continue
                
                # Find variant
                variant = None
                if strategy in variants["strategies"]:
                    for v in variants["strategies"][strategy]["variants"]:
                        if v["name"] == variant_name:
                            variant = v
                            break
                
                if not variant:
                    continue
                
                # Calculate performance metrics for original strategy and variant
                strategy_metrics = self.calculate_strategy_metrics(strategy)
                variant_metrics = self.calculate_variant_metrics(variant)
                
                # Compare metrics
                comparison = self.compare_metrics(strategy_metrics, variant_metrics)
                
                # Make decision
                decision = self.make_ab_test_decision(test, comparison)
                
                # Record results
                test_results[test["id"]] = {
                    "strategy": strategy,
                    "variant": variant_name,
                    "comparison": comparison,
                    "decision": decision
                }
                
                # Execute decision
                self.execute_ab_test_decision(test, decision, variants)
            
            # Save updated variants
            with open(self.strategy_variants_file, 'w') as f:
                json.dump(variants, f, indent=4)
            
            return test_results
        except Exception as e:
            logger.error(f"Error evaluating A/B tests: {e}")
            return {}
    
    def calculate_strategy_metrics(self, strategy: str) -> Dict[str, Any]:
        """Calculate performance metrics for a strategy
        
        Args:
            strategy (str): Strategy name
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        # Load trade history
        trade_history = self.load_strategy_history()
        
        # Filter trades for this strategy (excluding variants)
        strategy_trades = [trade for trade in trade_history 
                          if trade.get("strategy") == strategy 
                          and not trade.get("variant")]
        
        # Calculate metrics
        return self.calculate_performance_metrics(strategy_trades)
    
    def calculate_variant_metrics(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for a strategy variant
        
        Args:
            variant (Dict[str, Any]): Variant data
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        # Get trades from variant
        variant_trades = variant.get("trades", [])
        
        # Calculate metrics
        return self.calculate_performance_metrics(variant_trades)
    
    def compare_metrics(self, strategy_metrics: Dict[str, Any], 
                       variant_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance metrics between strategy and variant
        
        Args:
            strategy_metrics (Dict[str, Any]): Strategy metrics
            variant_metrics (Dict[str, Any]): Variant metrics
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        # Skip comparison if not enough trades
        if variant_metrics["total_trades"] < 10:
            return {
                "winner": "inconclusive",
                "reason": "Insufficient trades for variant",
                "confidence": 0
            }
        
        # Compare win rates
        win_rate_diff = variant_metrics["win_rate"] - strategy_metrics["win_rate"]
        
        # Compare profit factors
        profit_factor_diff = variant_metrics["profit_factor"] - strategy_metrics["profit_factor"]
        
        # Compare average profit
        avg_profit_diff = variant_metrics["avg_profit"] - strategy_metrics["avg_profit"]
        
        # Calculate overall score (weighted sum of differences)
        score = (0.4 * win_rate_diff) + (0.4 * profit_factor_diff * 10) + (0.2 * avg_profit_diff * 100)
        
        # Determine winner
        if score > 5:
            winner = "variant"
            reason = f"Variant outperforms original: Win rate +{win_rate_diff:.2f}%, Profit factor +{profit_factor_diff:.2f}"
            confidence = min(90, 50 + abs(score))
        elif score < -5:
            winner = "original"
            reason = f"Original outperforms variant: Win rate +{-win_rate_diff:.2f}%, Profit factor +{-profit_factor_diff:.2f}"
            confidence = min(90, 50 + abs(score))
        else:
            winner = "inconclusive"
            reason = "Performance difference is not significant"
            confidence = 50
        
        return {
            "winner": winner,
            "reason": reason,
            "confidence": confidence,
            "score": score,
            "win_rate_diff": win_rate_diff,
            "profit_factor_diff": profit_factor_diff,
            "avg_profit_diff": avg_profit_diff
        }
    
    def make_ab_test_decision(self, test: Dict[str, Any], 
                            comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision about an A/B test
        
        Args:
            test (Dict[str, Any]): Test data
            comparison (Dict[str, Any]): Comparison results
            
        Returns:
            Dict[str, Any]: Test decision
        """
        # Check if test has been running long enough
        start_date = datetime.fromisoformat(test["start_date"])
        test_duration = (datetime.now() - start_date).days
        
        # Minimum test duration (14 days)
        if test_duration < 14 and comparison["winner"] == "inconclusive":
            return {
                "action": "continue",
                "reason": f"Test running for {test_duration} days, continuing to collect data",
                "confidence": 0
            }
        
        # Make decision based on comparison
        if comparison["winner"] == "variant" and comparison["confidence"] >= self.config["ab_testing"]["min_confidence"]:
            return {
                "action": "promote",
                "reason": comparison["reason"],
                "confidence": comparison["confidence"]
            }
        elif comparison["winner"] == "original" and comparison["confidence"] >= self.config["ab_testing"]["min_confidence"]:
            return {
                "action": "discard",
                "reason": comparison["reason"],
                "confidence": comparison["confidence"]
            }
        elif test_duration >= 30:  # Maximum test duration (30 days)
            if comparison["winner"] == "variant":
                return {
                    "action": "promote",
                    "reason": f"Test completed after {test_duration} days. {comparison['reason']}",
                    "confidence": comparison["confidence"]
                }
            else:
                return {
                    "action": "discard",
                    "reason": f"Test completed after {test_duration} days. {comparison['reason']}",
                    "confidence": comparison["confidence"]
                }
        else:
            return {
                "action": "continue",
                "reason": f"Test inconclusive after {test_duration} days, continuing",
                "confidence": 0
            }
    
    def execute_ab_test_decision(self, test: Dict[str, Any], decision: Dict[str, Any],
                               variants: Dict[str, Any]) -> None:
        """Execute a decision for an A/B test
        
        Args:
            test (Dict[str, Any]): Test data
            decision (Dict[str, Any]): Test decision
            variants (Dict[str, Any]): Strategy variants data
        """
        action = decision["action"]
        strategy = test["strategy"]
        variant_name = test["variant"]
        
        if action == "continue":
            # Continue test
            test["status"] = "active"
            logger.info(f"Continuing A/B test for {variant_name}")
        
        elif action == "promote":
            # Promote variant to replace original strategy
            if strategy in variants["strategies"]:
                # Find variant
                variant = None
                for v in variants["strategies"][strategy]["variants"]:
                    if v["name"] == variant_name:
                        variant = v
                        break
                
                if variant:
                    # Update original strategy parameters with variant parameters
                    variants["strategies"][strategy]["parameters"] = variant["parameters"]
                    variants["strategies"][strategy]["last_updated"] = datetime.now().isoformat()
                    
                    # Mark variant as promoted
                    variant["status"] = "promoted"
                    variant["promotion_date"] = datetime.now().isoformat()
                    
                    # Mark test as completed
                    test["status"] = "completed"
                    test["end_date"] = datetime.now().isoformat()
                    test["result"] = "promoted"
                    
                    logger.info(f"Promoted variant {variant_name} to replace {strategy}")
        
        elif action == "discard":
            # Discard variant
            if strategy in variants["strategies"]:
                # Find variant
                for v in variants["strategies"][strategy]["variants"]:
                    if v["name"] == variant_name:
                        # Mark variant as discarded
                        v["status"] = "discarded"
                        v["discard_date"] = datetime.now().isoformat()
                        break
                
                # Mark test as completed
                test["status"] = "completed"
                test["end_date"] = datetime.now().isoformat()
                test["result"] = "discarded"
                
                logger.info(f"Discarded variant {variant_name}")
    
    def generate_evolution_report(self) -> Dict[str, Any]:
        """Generate a report on strategy evolution
        
        Returns:
            Dict[str, Any]: Evolution report
        """
        try:
            # Load strategy variants
            variants = self.load_strategy_variants()
            
            # Collect strategy statistics
            strategy_stats = {}
            for strategy, data in variants["strategies"].items():
                if data["status"] == "retired":
                    continue
                
                # Calculate metrics for original strategy
                metrics = self.calculate_strategy_metrics(strategy)
                
                # Collect variant information
                variant_info = []
                for variant in data.get("variants", []):
                    if variant["status"] not in ["discarded", "retired"]:
                        variant_metrics = self.calculate_variant_metrics(variant)
                        variant_info.append({
                            "name": variant["name"],
                            "status": variant["status"],
                            "metrics": variant_metrics
                        })
                
                # Get recent decisions
                recent_decisions = data.get("decisions", [])[-5:] if "decisions" in data else []
                
                strategy_stats[strategy] = {
                    "metrics": metrics,
                    "variants": variant_info,
                    "recent_decisions": recent_decisions
                }
            
            # Collect active test information
            active_tests = []
            for test in variants["active_tests"]:
                if test["status"] == "active":
                    active_tests.append({
                        "id": test["id"],
                        "strategy": test["strategy"],
                        "variant": test["variant"],
                        "start_date": test["start_date"],
                        "duration_days": (datetime.now() - datetime.fromisoformat(test["start_date"])).days
                    })
            
            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "strategies": strategy_stats,
                "active_tests": active_tests,
                "recent_promotions": self.get_recent_promotions(variants),
                "recent_retirements": self.get_recent_retirements(variants),
                "recommendations": self.generate_evolution_recommendations(strategy_stats)
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating evolution report: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_recent_promotions(self, variants: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recent variant promotions
        
        Args:
            variants (Dict[str, Any]): Strategy variants data
            
        Returns:
            List[Dict[str, Any]]: Recent promotions
        """
        promotions = []
        
        # Look for recently promoted variants
        for strategy, data in variants["strategies"].items():
            for variant in data.get("variants", []):
                if variant["status"] == "promoted" and "promotion_date" in variant:
                    promotion_date = datetime.fromisoformat(variant["promotion_date"])
                    # Include promotions from the last 30 days
                    if (datetime.now() - promotion_date).days <= 30:
                        promotions.append({
                            "strategy": strategy,
                            "variant": variant["name"],
                            "date": variant["promotion_date"]
                        })
        
        # Sort by date (most recent first)
        promotions.sort(key=lambda x: x["date"], reverse=True)
        
        return promotions
    
    def get_recent_retirements(self, variants: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recent strategy retirements
        
        Args:
            variants (Dict[str, Any]): Strategy variants data
            
        Returns:
            List[Dict[str, Any]]: Recent retirements
        """
        retirements = []
        
        # Look for recently retired strategies
        for strategy, data in variants["strategies"].items():
            if data["status"] == "retired" and "retired_date" in data:
                retirement_date = datetime.fromisoformat(data["retired_date"])
                # Include retirements from the last 30 days
                if (datetime.now() - retirement_date).days <= 30:
                    retirements.append({
                        "strategy": strategy,
                        "date": data["retired_date"]
                    })
        
        # Sort by date (most recent first)
        retirements.sort(key=lambda x: x["date"], reverse=True)
        
        return retirements
    
    def generate_evolution_recommendations(self, 
                                         strategy_stats: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations for strategy evolution
        
        Args:
            strategy_stats (Dict[str, Dict[str, Any]]): Strategy statistics
            
        Returns:
            List[str]: Evolution recommendations
        """
        recommendations = []
        
        # Identify strategies with no variants
        for strategy, stats in strategy_stats.items():
            if not stats["variants"]:
                recommendations.append(f"Create variants for strategy '{strategy}' to explore potential improvements")
        
        # Identify strategies with poor performance
        for strategy, stats in strategy_stats.items():
            metrics = stats["metrics"]
            if metrics["win_rate"] < 45 and metrics["profit_factor"] < 1.0:
                recommendations.append(f"Consider retiring or significantly optimizing strategy '{strategy}' due to poor performance")
        
        # Identify strategies with good performance but no recent optimization
        for strategy, stats in strategy_stats.items():
            metrics = stats["metrics"]
            recent_decisions = stats["recent_decisions"]
            
            if metrics["win_rate"] > 55 and metrics["profit_factor"] > 1.5:
                # Check if there's been a recent optimization or variant creation
                has_recent_evolution = False
                for decision in recent_decisions:
                    if decision["action"] in ["optimize", "create_variant"]:
                        decision_date = datetime.fromisoformat(decision["timestamp"])
                        if (datetime.now() - decision_date).days <= 14:
                            has_recent_evolution = True
                            break
                
                if not has_recent_evolution:
                    recommendations.append(f"Strategy '{strategy}' is performing well. Consider creating new variants to potentially improve further")
        
        # Add general recommendations
        recommendations.append("Regularly review A/B test results and adjust allocation based on performance")
        recommendations.append("Consider creating specialized variants for different market conditions")
        
        return recommendations


# For testing
if __name__ == "__main__":
    # Create strategy evolution system
    evolution = StrategyEvolution()
    
    # Evaluate strategies
    evaluation = evolution.evaluate_strategies()
    
    print("\nStrategy Evaluation:")
    for strategy, result in evaluation.items():
        print(f"Strategy: {strategy}")
        print(f"Win Rate: {result['metrics']['win_rate']:.2f}%")
        print(f"Profit Factor: {result['metrics']['profit_factor']:.2f}")
        print(f"Decision: {result['decision']['action']} ({result['decision']['reason']})")
        print()
    
    # Generate evolution report
    report = evolution.generate_evolution_report()
    
    print("\nEvolution Report:")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Active Tests: {len(report['active_tests'])}")
    print(f"Recent Promotions: {len(report['recent_promotions'])}")
    print(f"Recent Retirements: {len(report['recent_retirements'])}")
    
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"- {rec}")