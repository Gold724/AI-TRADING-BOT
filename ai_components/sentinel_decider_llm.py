#!/usr/bin/env python
# Sentinel Decider - LLM-powered strategy validation component

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sentinel_decider_llm")

# Constants
STRATEGY_HISTORY_FILE = os.path.join("data", "strategy_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")
DECIDER_CONFIG_FILE = os.path.join("config", "sentinel_decider_config.json")

class SentinelDeciderLLM:
    """LLM-powered decision maker for trade validation and strategy optimization"""
    
    def __init__(self, 
                 strategy_history_file: str = STRATEGY_HISTORY_FILE,
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 decider_config_file: str = DECIDER_CONFIG_FILE):
        """Initialize the LLM-powered sentinel decider
        
        Args:
            strategy_history_file (str): Path to the strategy history file
            strategy_stats_file (str): Path to the strategy statistics file
            decider_config_file (str): Path to the decider configuration file
        """
        self.strategy_history_file = strategy_history_file
        self.strategy_stats_file = strategy_stats_file
        self.decider_config_file = decider_config_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(strategy_history_file), exist_ok=True)
        os.makedirs(os.path.dirname(strategy_stats_file), exist_ok=True)
        os.makedirs(os.path.dirname(decider_config_file), exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize strategy stats if file doesn't exist
        if not os.path.exists(strategy_stats_file):
            self.initialize_strategy_stats()
        
        logger.info("LLM-powered Sentinel Decider initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load the decider configuration
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            if os.path.exists(self.decider_config_file):
                with open(self.decider_config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "llm_provider": "openai",
                    "model": "gpt-4",
                    "confidence_threshold": 70,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "strategy_validation": {
                        "enabled": True,
                        "min_trades": 10,
                        "win_rate_threshold": 55
                    },
                    "continuous_learning": {
                        "enabled": True,
                        "learning_rate": 0.1,
                        "update_frequency": "daily"
                    }
                }
                
                # Save default configuration
                with open(self.decider_config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def initialize_strategy_stats(self) -> None:
        """Initialize strategy statistics"""
        try:
            default_stats = {
                "strategies": {},
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.strategy_stats_file, 'w') as f:
                json.dump(default_stats, f, indent=4)
            
            logger.info("Initialized strategy statistics")
        except Exception as e:
            logger.error(f"Error initializing strategy statistics: {e}")
    
    def validate_strategy(self, strategy_name: str, market_condition: str, 
                         symbol: str, direction: str) -> Dict[str, Any]:
        """Validate a trading strategy using LLM
        
        Args:
            strategy_name (str): Name of the strategy
            market_condition (str): Current market condition
            symbol (str): Trading symbol
            direction (str): Trade direction (buy/sell)
            
        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            # Load strategy history and stats
            strategy_history = self.load_strategy_history()
            strategy_stats = self.load_strategy_stats()
            
            # Get strategy performance
            strategy_performance = self.get_strategy_performance(strategy_name, symbol)
            
            # Prepare prompt for LLM
            prompt = self.prepare_validation_prompt(
                strategy_name=strategy_name,
                market_condition=market_condition,
                symbol=symbol,
                direction=direction,
                strategy_performance=strategy_performance
            )
            
            # Get LLM response
            llm_response = self.query_llm(prompt)
            
            # Parse LLM response
            validation_result = self.parse_llm_response(llm_response)
            
            # Update strategy stats with this validation
            self.update_strategy_stats(strategy_name, symbol, validation_result)
            
            return validation_result
        except Exception as e:
            logger.error(f"Error validating strategy: {e}")
            return {
                "valid": False,
                "confidence": 0,
                "explanation": f"Error: {str(e)}",
                "recommendations": []
            }
    
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
    
    def load_strategy_stats(self) -> Dict[str, Any]:
        """Load strategy statistics
        
        Returns:
            Dict[str, Any]: Strategy statistics
        """
        try:
            if os.path.exists(self.strategy_stats_file):
                with open(self.strategy_stats_file, 'r') as f:
                    return json.load(f)
            return {"strategies": {}, "last_updated": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error loading strategy statistics: {e}")
            return {"strategies": {}, "last_updated": datetime.now().isoformat()}
    
    def get_strategy_performance(self, strategy_name: str, symbol: str) -> Dict[str, Any]:
        """Get performance metrics for a strategy
        
        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        try:
            # Load strategy history
            strategy_history = self.load_strategy_history()
            
            # Filter trades for this strategy and symbol
            strategy_trades = [trade for trade in strategy_history 
                              if trade.get("strategy") == strategy_name 
                              and trade.get("symbol") == symbol]
            
            # Calculate performance metrics
            total_trades = len(strategy_trades)
            winning_trades = sum(1 for trade in strategy_trades if trade.get("win", False))
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate average profit
            total_profit = sum(trade.get("profit", 0) for trade in strategy_trades)
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            
            # Calculate recent performance (last 10 trades)
            recent_trades = strategy_trades[-10:] if len(strategy_trades) >= 10 else strategy_trades
            recent_winning_trades = sum(1 for trade in recent_trades if trade.get("win", False))
            recent_win_rate = (recent_winning_trades / len(recent_trades) * 100) if recent_trades else 0
            
            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": win_rate,
                "avg_profit": avg_profit,
                "recent_win_rate": recent_win_rate,
                "consecutive_wins": self.get_consecutive_count(strategy_trades, True),
                "consecutive_losses": self.get_consecutive_count(strategy_trades, False)
            }
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "recent_win_rate": 0,
                "consecutive_wins": 0,
                "consecutive_losses": 0
            }
    
    def get_consecutive_count(self, trades: List[Dict[str, Any]], win: bool) -> int:
        """Get the count of consecutive wins or losses
        
        Args:
            trades (List[Dict[str, Any]]): List of trades
            win (bool): True for wins, False for losses
            
        Returns:
            int: Count of consecutive wins or losses
        """
        if not trades:
            return 0
        
        count = 0
        for trade in reversed(trades):
            if trade.get("win", False) == win:
                count += 1
            else:
                break
        
        return count
    
    def prepare_validation_prompt(self, strategy_name: str, market_condition: str,
                                 symbol: str, direction: str, 
                                 strategy_performance: Dict[str, Any]) -> str:
        """Prepare a prompt for LLM validation
        
        Args:
            strategy_name (str): Name of the strategy
            market_condition (str): Current market condition
            symbol (str): Trading symbol
            direction (str): Trade direction
            strategy_performance (Dict[str, Any]): Strategy performance metrics
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""
        You are an expert trading strategy validator for the TRAE AI Trading System.
        
        STRATEGY INFORMATION:
        - Strategy: {strategy_name}
        - Symbol: {symbol}
        - Direction: {direction}
        - Market Condition: {market_condition}
        
        HISTORICAL PERFORMANCE:
        - Total Trades: {strategy_performance['total_trades']}
        - Win Rate: {strategy_performance['win_rate']:.2f}%
        - Recent Win Rate (last 10): {strategy_performance['recent_win_rate']:.2f}%
        - Average Profit: {strategy_performance['avg_profit']:.2f}
        - Consecutive Wins: {strategy_performance['consecutive_wins']}
        - Consecutive Losses: {strategy_performance['consecutive_losses']}
        
        TASK:
        Evaluate whether this strategy should be executed in the current market conditions.
        Consider historical performance, current market conditions, and risk factors.
        
        RESPONSE FORMAT:
        Provide a JSON response with the following fields:
        - valid: boolean (true if the strategy should be executed, false otherwise)
        - confidence: number (0-100, your confidence in this decision)
        - explanation: string (detailed explanation of your decision)
        - recommendations: array of strings (suggestions for improving the strategy)
        """
        
        return prompt
    
    def query_llm(self, prompt: str) -> str:
        """Query the LLM with a prompt
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: LLM response
        """
        try:
            # This is a placeholder for actual LLM integration
            # In a real implementation, this would call an LLM API
            
            # Simulate LLM response for now
            time.sleep(0.5)  # Simulate API call latency
            
            # Mock response based on prompt content
            if "win_rate" in prompt and "50" in prompt:
                return json.dumps({
                    "valid": True,
                    "confidence": 75,
                    "explanation": "The strategy has shown consistent performance with a reasonable win rate. Market conditions are favorable for this approach.",
                    "recommendations": [
                        "Consider tightening stop loss to improve risk-reward ratio",
                        "Monitor for increased volatility which may affect performance"
                    ]
                })
            else:
                return json.dumps({
                    "valid": True,
                    "confidence": 65,
                    "explanation": "The strategy appears viable but has limited historical data. Proceed with caution.",
                    "recommendations": [
                        "Gather more data on this strategy-symbol combination",
                        "Consider reducing position size until more data is available"
                    ]
                })
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return json.dumps({
                "valid": False,
                "confidence": 0,
                "explanation": f"Error querying LLM: {str(e)}",
                "recommendations": ["Check LLM service connectivity"]
            })
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response
        
        Args:
            response (str): LLM response string
            
        Returns:
            Dict[str, Any]: Parsed response
        """
        try:
            # Parse JSON response
            parsed = json.loads(response)
            
            # Validate required fields
            required_fields = ["valid", "confidence", "explanation", "recommendations"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            return parsed
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "valid": False,
                "confidence": 0,
                "explanation": f"Error parsing LLM response: {str(e)}",
                "recommendations": []
            }
    
    def update_strategy_stats(self, strategy_name: str, symbol: str, 
                             validation_result: Dict[str, Any]) -> None:
        """Update strategy statistics with validation result
        
        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            validation_result (Dict[str, Any]): Validation result from LLM
        """
        try:
            # Load current stats
            stats = self.load_strategy_stats()
            
            # Initialize strategy if not exists
            if strategy_name not in stats["strategies"]:
                stats["strategies"][strategy_name] = {}
            
            # Initialize symbol if not exists
            if symbol not in stats["strategies"][strategy_name]:
                stats["strategies"][strategy_name][symbol] = {
                    "validations": [],
                    "confidence_trend": [],
                    "recommendations": []
                }
            
            # Add validation result
            stats["strategies"][strategy_name][symbol]["validations"].append({
                "timestamp": datetime.now().isoformat(),
                "valid": validation_result["valid"],
                "confidence": validation_result["confidence"],
                "explanation": validation_result["explanation"]
            })
            
            # Update confidence trend
            stats["strategies"][strategy_name][symbol]["confidence_trend"].append({
                "timestamp": datetime.now().isoformat(),
                "confidence": validation_result["confidence"]
            })
            
            # Keep only the last 100 confidence points
            if len(stats["strategies"][strategy_name][symbol]["confidence_trend"]) > 100:
                stats["strategies"][strategy_name][symbol]["confidence_trend"] = \
                    stats["strategies"][strategy_name][symbol]["confidence_trend"][-100:]
            
            # Add new recommendations
            for recommendation in validation_result["recommendations"]:
                if recommendation not in stats["strategies"][strategy_name][symbol]["recommendations"]:
                    stats["strategies"][strategy_name][symbol]["recommendations"].append(recommendation)
            
            # Keep only the last 10 recommendations
            stats["strategies"][strategy_name][symbol]["recommendations"] = \
                stats["strategies"][strategy_name][symbol]["recommendations"][-10:]
            
            # Update last updated timestamp
            stats["last_updated"] = datetime.now().isoformat()
            
            # Save updated stats
            with open(self.strategy_stats_file, 'w') as f:
                json.dump(stats, f, indent=4)
            
            logger.info(f"Updated strategy stats for {strategy_name} on {symbol}")
        except Exception as e:
            logger.error(f"Error updating strategy stats: {e}")
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate a weekly performance report
        
        Returns:
            Dict[str, Any]: Weekly report data
        """
        try:
            # Load strategy history and stats
            strategy_history = self.load_strategy_history()
            strategy_stats = self.load_strategy_stats()
            
            # Calculate overall performance
            total_trades = len(strategy_history)
            winning_trades = sum(1 for trade in strategy_history if trade.get("win", False))
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate performance by strategy
            strategy_performance = {}
            for strategy_name, strategy_data in strategy_stats["strategies"].items():
                strategy_trades = [trade for trade in strategy_history 
                                  if trade.get("strategy") == strategy_name]
                
                strategy_total = len(strategy_trades)
                strategy_wins = sum(1 for trade in strategy_trades if trade.get("win", False))
                strategy_win_rate = (strategy_wins / strategy_total * 100) if strategy_total > 0 else 0
                
                strategy_performance[strategy_name] = {
                    "total_trades": strategy_total,
                    "winning_trades": strategy_wins,
                    "win_rate": strategy_win_rate,
                    "symbols": {}
                }
                
                # Calculate performance by symbol
                for symbol, symbol_data in strategy_data.items():
                    symbol_trades = [trade for trade in strategy_trades 
                                   if trade.get("symbol") == symbol]
                    
                    symbol_total = len(symbol_trades)
                    symbol_wins = sum(1 for trade in symbol_trades if trade.get("win", False))
                    symbol_win_rate = (symbol_wins / symbol_total * 100) if symbol_total > 0 else 0
                    
                    # Get recent confidence trend
                    confidence_trend = symbol_data.get("confidence_trend", [])
                    recent_confidence = confidence_trend[-1]["confidence"] if confidence_trend else 0
                    
                    strategy_performance[strategy_name]["symbols"][symbol] = {
                        "total_trades": symbol_total,
                        "winning_trades": symbol_wins,
                        "win_rate": symbol_win_rate,
                        "recent_confidence": recent_confidence,
                        "recommendations": symbol_data.get("recommendations", [])
                    }
            
            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "period": "weekly",
                "overall": {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "win_rate": win_rate
                },
                "strategies": strategy_performance,
                "recommendations": self.generate_system_recommendations(strategy_stats)
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "period": "weekly",
                "error": str(e)
            }
    
    def generate_system_recommendations(self, strategy_stats: Dict[str, Any]) -> List[str]:
        """Generate system-wide recommendations based on strategy stats
        
        Args:
            strategy_stats (Dict[str, Any]): Strategy statistics
            
        Returns:
            List[str]: System recommendations
        """
        recommendations = []
        
        try:
            # Identify underperforming strategies
            underperforming = []
            for strategy_name, strategy_data in strategy_stats["strategies"].items():
                for symbol, symbol_data in strategy_data.items():
                    validations = symbol_data.get("validations", [])
                    if validations:
                        recent_validations = validations[-5:] if len(validations) >= 5 else validations
                        valid_count = sum(1 for v in recent_validations if v.get("valid", False))
                        valid_rate = valid_count / len(recent_validations) * 100
                        
                        if valid_rate < 40:
                            underperforming.append((strategy_name, symbol, valid_rate))
            
            # Add recommendations for underperforming strategies
            if underperforming:
                for strategy_name, symbol, valid_rate in underperforming:
                    recommendations.append(
                        f"Consider retiring or modifying {strategy_name} for {symbol} (valid rate: {valid_rate:.1f}%)"
                    )
            
            # Add general recommendations
            recommendations.append("Regularly review and update strategy parameters based on market conditions")
            recommendations.append("Consider A/B testing variations of successful strategies")
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating system recommendations: {e}")
            return ["Error generating recommendations: " + str(e)]


# For testing
if __name__ == "__main__":
    # Create sentinel decider
    decider = SentinelDeciderLLM()
    
    # Test strategy validation
    validation = decider.validate_strategy(
        strategy_name="fibonacci_retracement",
        market_condition="trending",
        symbol="EURUSD",
        direction="buy"
    )
    
    print("\nStrategy Validation Result:")
    print(f"Valid: {validation['valid']}")
    print(f"Confidence: {validation['confidence']}%")
    print(f"Explanation: {validation['explanation']}")
    print("Recommendations:")
    for rec in validation['recommendations']:
        print(f"- {rec}")
    
    # Generate weekly report
    report = decider.generate_weekly_report()
    
    print("\nWeekly Report:")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Overall Win Rate: {report['overall']['win_rate']:.2f}%")
    print("Strategies:")
    for strategy_name, strategy_data in report['strategies'].items():
        print(f"- {strategy_name}: {strategy_data['win_rate']:.2f}% win rate")
    
    print("System Recommendations:")
    for rec in report['recommendations']:
        print(f"- {rec}")