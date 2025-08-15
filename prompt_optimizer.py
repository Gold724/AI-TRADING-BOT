# prompt_optimizer.py

import os
import json
import random
import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prompt_optimizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PromptOptimizer")

# Try to import from other modules
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    logger.warning("Could not import TradePerformanceEvaluator, using minimal version")
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_strategy_performance(self, strategy_name):
            return {}
        def get_recent_trades(self, limit=10):
            return []

try:
    from memory_engine import MemoryEngine
except ImportError:
    logger.warning("Could not import MemoryEngine, using minimal version")
    # Define a minimal version if the import fails
    class MemoryEngine:
        def get_best_strategy_for_condition(self, market_condition):
            return None, 0
        def get_best_symbol_for_strategy(self, strategy_name):
            return None, 0

class PromptOptimizer:
    """A class to optimize LLM prompts for trading decisions
    
    This class is responsible for generating, testing, and optimizing prompts
    for the sentinel_decider.py module. It uses historical performance data,
    market conditions, and psychological state to create more effective prompts.
    """
    
    def __init__(self, config_path: str = "config/prompt_optimizer_config.json"):
        """Initialize the PromptOptimizer
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.prompt_templates = self.config.get("prompt_templates", {})
        self.prompt_components = self.config.get("prompt_components", {})
        self.performance_metrics = self.config.get("performance_metrics", {})
        self.prompt_history = self.config.get("prompt_history", [])
        
        # Initialize components
        self.data_dir = os.path.join("data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.evaluator = TradePerformanceEvaluator()
        self.memory_engine = MemoryEngine()
        
        # Load prompt performance data
        self.prompt_performance_path = os.path.join(self.data_dir, "prompt_performance.json")
        self.prompt_performance = self._load_prompt_performance()
    
    def _load_config(self) -> Dict:
        """Load configuration from file
        
        Returns:
            Dict: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    return json.load(f)
            else:
                # Create default config
                default_config = self._create_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration
        
        Returns:
            Dict: Default configuration dictionary
        """
        return {
            "prompt_templates": {
                "standard": (
                    "You are an expert trading advisor with deep knowledge of forex and financial markets. "
                    "Analyze the following trade opportunity and provide a confidence score (0-100) "
                    "and a recommendation (Take Trade, Reduce Size, Skip Trade).\n\n"
                    "{strategy_context}\n\n"
                    "{market_context}\n\n"
                    "{trade_context}\n\n"
                    "{psychological_context}\n\n"
                    "Based on this information, provide:\n"
                    "1. A confidence score from 0-100\n"
                    "2. A recommendation: Take Trade, Reduce Size, or Skip Trade\n"
                    "3. A brief explanation of your reasoning"
                ),
                "concise": (
                    "As a trading advisor, evaluate this trade:\n\n"
                    "{strategy_context}\n"
                    "{market_context}\n"
                    "{trade_context}\n"
                    "Provide: confidence score (0-100), recommendation (Take/Reduce/Skip), brief reason."
                ),
                "detailed": (
                    "You are an expert trading advisor specializing in forex markets and algorithmic trading strategies. "
                    "Your task is to analyze the following trade opportunity in detail, considering all provided factors, "
                    "and provide a comprehensive assessment.\n\n"
                    "## Strategy Information\n{strategy_context}\n\n"
                    "## Market Conditions\n{market_context}\n\n"
                    "## Trade Details\n{trade_context}\n\n"
                    "## Psychological Factors\n{psychological_context}\n\n"
                    "## Historical Performance\n{historical_context}\n\n"
                    "Based on your analysis, please provide:\n"
                    "1. A confidence score from 0-100, where 0 is no confidence and 100 is absolute confidence\n"
                    "2. A clear recommendation: Take Trade, Reduce Size, or Skip Trade\n"
                    "3. A detailed explanation of your reasoning, including key factors that influenced your decision\n"
                    "4. Any specific risk factors or considerations that should be monitored during this trade"
                )
            },
            "prompt_components": {
                "strategy_context": [
                    "Strategy: {strategy_name}\nWin Rate: {win_rate}%\nProfit Factor: {profit_factor}\nAverage Win: {avg_win}\nAverage Loss: {avg_loss}",
                    "Trading Strategy: {strategy_name}\nHistorical Performance: Win Rate {win_rate}%, Profit Factor {profit_factor}\nTypical Results: Average Win {avg_win}, Average Loss {avg_loss}",
                    "Strategy '{strategy_name}' has a {win_rate}% win rate with a profit factor of {profit_factor}. Average winning trade is {avg_win} and average losing trade is {avg_loss}."
                ],
                "market_context": [
                    "Market Condition: {market_condition}\nVolatility: {volatility}\nTrend Strength: {trend_strength}\nRecent News Impact: {news_impact}",
                    "Current Market: {market_condition} conditions with {volatility} volatility\nTrend: {trend_strength} strength\nNews: {news_impact} impact from recent events",
                    "The market is currently showing {market_condition} conditions. Volatility is {volatility}, trend strength is {trend_strength}, and recent news has had {news_impact} impact."
                ],
                "trade_context": [
                    "Symbol: {symbol}\nDirection: {direction}\nEntry Price: {entry_price}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}\nRisk-Reward Ratio: {risk_reward}",
                    "Trade Details: {direction} {symbol} at {entry_price}\nRisk Management: Stop Loss at {stop_loss}, Take Profit at {take_profit}\nR:R Ratio: {risk_reward}",
                    "Considering a {direction} trade on {symbol} at {entry_price}. Stop loss is set at {stop_loss} and take profit at {take_profit}, giving a risk-reward ratio of {risk_reward}."
                ],
                "psychological_context": [
                    "Recent Performance: {recent_performance}\nConsecutive Wins/Losses: {consecutive_trades}\nPsychological State: {psychological_state}",
                    "Trading Psychology: Currently in a {psychological_state} state\nRecent Results: {recent_performance}\nStreak: {consecutive_trades}",
                    "Your recent performance has been {recent_performance}. You've had {consecutive_trades}. Your current psychological state appears to be {psychological_state}."
                ],
                "historical_context": [
                    "Similar Past Trades: {similar_trades_count} identified\nSuccess Rate: {similar_trades_win_rate}%\nBest Time Performance: {best_time_performance}",
                    "Historical Analysis: Found {similar_trades_count} similar past trades with {similar_trades_win_rate}% success rate\nOptimal Timing: {best_time_performance}",
                    "Looking at historical data, we found {similar_trades_count} similar trades with a {similar_trades_win_rate}% success rate. The best performance for this type of trade typically occurs {best_time_performance}."
                ]
            },
            "performance_metrics": {
                "prompt_evaluation_window": 50,  # Number of trades to evaluate prompt performance
                "confidence_score_weight": 0.7,  # Weight for confidence score accuracy
                "recommendation_weight": 0.3,    # Weight for recommendation accuracy
                "optimization_frequency": 100    # Number of trades before optimizing prompts
            },
            "prompt_history": []
        }
    
    def _load_prompt_performance(self) -> Dict:
        """Load prompt performance data from file
        
        Returns:
            Dict: Prompt performance data
        """
        try:
            if os.path.exists(self.prompt_performance_path):
                with open(self.prompt_performance_path, "r") as f:
                    return json.load(f)
            else:
                return {"templates": {}, "components": {}}
        except Exception as e:
            logger.error(f"Error loading prompt performance data: {e}")
            return {"templates": {}, "components": {}}
    
    def _save_prompt_performance(self):
        """Save prompt performance data to file"""
        try:
            with open(self.prompt_performance_path, "w") as f:
                json.dump(self.prompt_performance, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving prompt performance data: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def generate_prompt(self, 
                        strategy_name: str, 
                        symbol: str, 
                        direction: str, 
                        entry_price: float, 
                        stop_loss: float, 
                        take_profit: float,
                        market_condition: str = "normal",
                        volatility: str = "medium",
                        trend_strength: str = "medium",
                        news_impact: str = "low",
                        template_name: str = "standard") -> str:
        """Generate a prompt for the given trade parameters
        
        Args:
            strategy_name: Name of the strategy
            symbol: Trading symbol
            direction: Trade direction (buy/sell)
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            market_condition: Current market condition
            volatility: Current market volatility
            trend_strength: Current trend strength
            news_impact: Impact of recent news
            template_name: Name of the prompt template to use
            
        Returns:
            str: Generated prompt
        """
        # Get strategy performance
        strategy_perf = self.evaluator.get_strategy_performance(strategy_name)
        win_rate = strategy_perf.get("win_rate", 50)
        profit_factor = strategy_perf.get("profit_factor", 1.0)
        avg_win = strategy_perf.get("avg_win", 0)
        avg_loss = strategy_perf.get("avg_loss", 0)
        
        # Calculate risk-reward ratio
        if direction.lower() == "buy":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:  # sell
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
            
        risk_reward = round(reward / risk, 2) if risk > 0 else 0
        
        # Get recent performance
        recent_trades = self.evaluator.get_recent_trades(limit=10)
        wins = sum(1 for trade in recent_trades if trade.get("profit_loss", 0) > 0)
        losses = len(recent_trades) - wins
        
        if wins > losses:
            recent_performance = "positive"
        elif losses > wins:
            recent_performance = "negative"
        else:
            recent_performance = "neutral"
            
        # Determine consecutive trades
        consecutive_wins = 0
        consecutive_losses = 0
        
        for trade in recent_trades:
            if trade.get("profit_loss", 0) > 0:
                consecutive_wins += 1
                consecutive_losses = 0
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                
        if consecutive_wins > 2:
            consecutive_trades = f"{consecutive_wins} consecutive wins"
        elif consecutive_losses > 2:
            consecutive_trades = f"{consecutive_losses} consecutive losses"
        else:
            consecutive_trades = "no significant streak"
            
        # Determine psychological state
        if consecutive_losses > 3:
            psychological_state = "potentially stressed"
        elif consecutive_wins > 3:
            psychological_state = "confident"
        elif recent_performance == "negative":
            psychological_state = "cautious"
        elif recent_performance == "positive":
            psychological_state = "positive"
        else:
            psychological_state = "neutral"
            
        # Get similar trades data from memory engine
        best_strategy, strategy_confidence = self.memory_engine.get_best_strategy_for_condition(market_condition)
        best_symbol, symbol_confidence = self.memory_engine.get_best_symbol_for_strategy(strategy_name)
        
        similar_trades_count = random.randint(5, 20)  # Placeholder
        similar_trades_win_rate = random.randint(40, 80)  # Placeholder
        
        # Determine best time performance (placeholder)
        times = ["during London session", "during New York session", "during Asian session", 
                "during market overlaps", "during low volatility periods", "during high volatility periods"]
        best_time_performance = random.choice(times)
        
        # Select component templates
        strategy_context_template = random.choice(self.prompt_components["strategy_context"])
        market_context_template = random.choice(self.prompt_components["market_context"])
        trade_context_template = random.choice(self.prompt_components["trade_context"])
        psychological_context_template = random.choice(self.prompt_components["psychological_context"])
        historical_context_template = random.choice(self.prompt_components["historical_context"])
        
        # Format component templates
        strategy_context = strategy_context_template.format(
            strategy_name=strategy_name,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss
        )
        
        market_context = market_context_template.format(
            market_condition=market_condition,
            volatility=volatility,
            trend_strength=trend_strength,
            news_impact=news_impact
        )
        
        trade_context = trade_context_template.format(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=risk_reward
        )
        
        psychological_context = psychological_context_template.format(
            recent_performance=recent_performance,
            consecutive_trades=consecutive_trades,
            psychological_state=psychological_state
        )
        
        historical_context = historical_context_template.format(
            similar_trades_count=similar_trades_count,
            similar_trades_win_rate=similar_trades_win_rate,
            best_time_performance=best_time_performance
        )
        
        # Get prompt template
        prompt_template = self.prompt_templates.get(template_name, self.prompt_templates["standard"])
        
        # Format prompt template
        prompt = prompt_template.format(
            strategy_context=strategy_context,
            market_context=market_context,
            trade_context=trade_context,
            psychological_context=psychological_context,
            historical_context=historical_context
        )
        
        # Record prompt in history
        self._record_prompt(prompt, template_name, strategy_name, symbol, direction)
        
        return prompt
    
    def _record_prompt(self, prompt: str, template_name: str, strategy_name: str, symbol: str, direction: str):
        """Record a prompt in the history
        
        Args:
            prompt: The generated prompt
            template_name: Name of the prompt template used
            strategy_name: Name of the strategy
            symbol: Trading symbol
            direction: Trade direction
        """
        prompt_record = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "template_name": template_name,
            "strategy_name": strategy_name,
            "symbol": symbol,
            "direction": direction,
            "result": None  # To be updated later
        }
        
        self.prompt_history.append(prompt_record)
        self.config["prompt_history"] = self.prompt_history[-100:]  # Keep only the last 100 prompts
        self._save_config()
    
    def record_prompt_result(self, prompt_index: int, confidence_score: int, recommendation: str, trade_result: Dict):
        """Record the result of a prompt
        
        Args:
            prompt_index: Index of the prompt in the history
            confidence_score: Confidence score provided by the LLM
            recommendation: Recommendation provided by the LLM
            trade_result: Result of the trade
        """
        if prompt_index < 0 or prompt_index >= len(self.prompt_history):
            logger.error(f"Invalid prompt index: {prompt_index}")
            return
            
        prompt_record = self.prompt_history[prompt_index]
        prompt_record["result"] = {
            "confidence_score": confidence_score,
            "recommendation": recommendation,
            "trade_result": trade_result,
            "timestamp": datetime.now().isoformat()
        }
        
        self._save_config()
        self._update_prompt_performance(prompt_record)
    
    def _update_prompt_performance(self, prompt_record: Dict):
        """Update prompt performance metrics
        
        Args:
            prompt_record: Record of the prompt and its result
        """
        template_name = prompt_record["template_name"]
        result = prompt_record["result"]
        
        if not result:
            return
            
        # Initialize template performance if not exists
        if template_name not in self.prompt_performance["templates"]:
            self.prompt_performance["templates"][template_name] = {
                "count": 0,
                "correct_confidence": 0,
                "correct_recommendation": 0,
                "avg_confidence_error": 0,
                "trades": []
            }
            
        template_perf = self.prompt_performance["templates"][template_name]
        template_perf["count"] += 1
        
        # Calculate confidence score accuracy
        confidence_score = result["confidence_score"]
        trade_result = result["trade_result"]
        profit_loss = trade_result.get("profit_loss", 0)
        
        # Normalize profit/loss to a 0-100 scale for comparison with confidence
        # This is a simplified approach and should be refined based on actual data
        expected_confidence = 50  # Default neutral
        if profit_loss > 0:
            # Winning trade, expected confidence should be high
            expected_confidence = min(50 + (profit_loss / 10) * 50, 100)
        elif profit_loss < 0:
            # Losing trade, expected confidence should be low
            expected_confidence = max(50 - (abs(profit_loss) / 10) * 50, 0)
            
        confidence_error = abs(confidence_score - expected_confidence)
        template_perf["avg_confidence_error"] = (
            (template_perf["avg_confidence_error"] * (template_perf["count"] - 1) + confidence_error) / 
            template_perf["count"]
        )
        
        # Consider confidence correct if error is less than 20
        if confidence_error < 20:
            template_perf["correct_confidence"] += 1
            
        # Calculate recommendation accuracy
        recommendation = result["recommendation"]
        correct_recommendation = False
        
        if profit_loss > 0 and recommendation == "Take Trade":
            correct_recommendation = True
        elif profit_loss < 0 and recommendation == "Skip Trade":
            correct_recommendation = True
        elif abs(profit_loss) < 2 and recommendation == "Reduce Size":
            correct_recommendation = True
            
        if correct_recommendation:
            template_perf["correct_recommendation"] += 1
            
        # Add trade to template performance history
        template_perf["trades"].append({
            "timestamp": result["timestamp"],
            "confidence_score": confidence_score,
            "recommendation": recommendation,
            "profit_loss": profit_loss,
            "confidence_error": confidence_error,
            "correct_recommendation": correct_recommendation
        })
        
        # Keep only the last 100 trades
        template_perf["trades"] = template_perf["trades"][-100:]
        
        # Save prompt performance
        self._save_prompt_performance()
        
        # Check if optimization is needed
        if template_perf["count"] % self.performance_metrics["optimization_frequency"] == 0:
            self.optimize_prompts()
    
    def get_best_template(self) -> str:
        """Get the best performing prompt template
        
        Returns:
            str: Name of the best performing template
        """
        best_template = "standard"  # Default
        best_score = 0
        
        for template_name, perf in self.prompt_performance["templates"].items():
            if perf["count"] < 10:  # Require at least 10 trades for evaluation
                continue
                
            confidence_accuracy = perf["correct_confidence"] / perf["count"]
            recommendation_accuracy = perf["correct_recommendation"] / perf["count"]
            
            # Calculate weighted score
            score = (
                confidence_accuracy * self.performance_metrics["confidence_score_weight"] +
                recommendation_accuracy * self.performance_metrics["recommendation_weight"]
            )
            
            if score > best_score:
                best_score = score
                best_template = template_name
                
        return best_template
    
    def optimize_prompts(self):
        """Optimize prompt templates and components based on performance"""
        logger.info("Optimizing prompts based on performance data")
        
        # Analyze template performance
        template_performance = {}
        for template_name, perf in self.prompt_performance["templates"].items():
            if perf["count"] < 10:  # Require at least 10 trades for evaluation
                continue
                
            confidence_accuracy = perf["correct_confidence"] / perf["count"]
            recommendation_accuracy = perf["correct_recommendation"] / perf["count"]
            
            # Calculate weighted score
            score = (
                confidence_accuracy * self.performance_metrics["confidence_score_weight"] +
                recommendation_accuracy * self.performance_metrics["recommendation_weight"]
            )
            
            template_performance[template_name] = {
                "score": score,
                "confidence_accuracy": confidence_accuracy,
                "recommendation_accuracy": recommendation_accuracy,
                "avg_confidence_error": perf["avg_confidence_error"]
            }
            
        # Log template performance
        logger.info(f"Template performance: {template_performance}")
        
        # Identify best and worst templates
        if not template_performance:
            logger.info("Not enough data to optimize prompts")
            return
            
        best_template = max(template_performance.items(), key=lambda x: x[1]["score"])[0]
        worst_template = min(template_performance.items(), key=lambda x: x[1]["score"])[0]
        
        logger.info(f"Best template: {best_template}, Worst template: {worst_template}")
        
        # Analyze what makes the best template effective
        best_template_text = self.prompt_templates[best_template]
        worst_template_text = self.prompt_templates[worst_template]
        
        # Simple analysis of template characteristics
        best_length = len(best_template_text)
        worst_length = len(worst_template_text)
        
        best_questions = len(re.findall(r'\?', best_template_text))
        worst_questions = len(re.findall(r'\?', worst_template_text))
        
        best_specificity = len(re.findall(r'specific|detail|precise', best_template_text.lower()))
        worst_specificity = len(re.findall(r'specific|detail|precise', worst_template_text.lower()))
        
        logger.info(f"Best template length: {best_length}, questions: {best_questions}, specificity: {best_specificity}")
        logger.info(f"Worst template length: {worst_length}, questions: {worst_questions}, specificity: {worst_specificity}")
        
        # Create a new template based on the best one with some variations
        if "optimized" not in self.prompt_templates or random.random() < 0.3:  # 30% chance to create new template
            new_template = best_template_text
            
            # Add more specificity if that seems to help
            if best_specificity > worst_specificity:
                specificity_phrases = [
                    "Please be very specific in your analysis.",
                    "Provide detailed reasoning for your confidence score.",
                    "Consider all factors in detail before making your recommendation."
                ]
                new_template += "\n\n" + random.choice(specificity_phrases)
                
            # Add more questions if that seems to help
            if best_questions > worst_questions:
                question_phrases = [
                    "What specific market conditions support this trade? What contradicts it?",
                    "How does this trade align with the strategy's historical performance?",
                    "What is the most significant risk factor for this trade?"
                ]
                new_template += "\n\n" + random.choice(question_phrases)
                
            # Adjust length if that seems to help
            if best_length < worst_length and len(new_template) > best_length * 1.2:
                # Simplify if shorter is better
                new_template = new_template.replace("\n\n", "\n").replace("  ", " ")
                
            # Save the new optimized template
            self.prompt_templates["optimized"] = new_template
            self.config["prompt_templates"] = self.prompt_templates
            self._save_config()
            
            logger.info(f"Created new optimized template: {new_template[:100]}...")
    
    def analyze_prompt_performance(self) -> Dict:
        """Analyze the performance of different prompt templates and components
        
        Returns:
            Dict: Performance analysis results
        """
        results = {
            "template_performance": {},
            "best_template": self.get_best_template(),
            "component_performance": {},
            "recommendations": []
        }
        
        # Analyze template performance
        for template_name, perf in self.prompt_performance["templates"].items():
            if perf["count"] < 5:  # Require at least 5 trades for basic analysis
                continue
                
            confidence_accuracy = perf["correct_confidence"] / perf["count"]
            recommendation_accuracy = perf["correct_recommendation"] / perf["count"]
            
            # Calculate weighted score
            score = (
                confidence_accuracy * self.performance_metrics["confidence_score_weight"] +
                recommendation_accuracy * self.performance_metrics["recommendation_weight"]
            )
            
            results["template_performance"][template_name] = {
                "score": score,
                "confidence_accuracy": confidence_accuracy,
                "recommendation_accuracy": recommendation_accuracy,
                "avg_confidence_error": perf["avg_confidence_error"],
                "count": perf["count"]
            }
            
        # Generate recommendations
        if results["template_performance"]:
            best_template = max(results["template_performance"].items(), key=lambda x: x[1]["score"])[0]
            results["recommendations"].append(f"Use the '{best_template}' template for best results")
            
            # Analyze confidence score accuracy
            avg_errors = [perf["avg_confidence_error"] for perf in results["template_performance"].values()]
            avg_error = sum(avg_errors) / len(avg_errors)
            
            if avg_error > 30:
                results["recommendations"].append("Confidence scores have high error rates. Consider recalibrating the confidence scale.")
            
            # Analyze recommendation accuracy
            avg_rec_accuracy = sum(perf["recommendation_accuracy"] for perf in results["template_performance"].values()) / len(results["template_performance"])
            
            if avg_rec_accuracy < 0.6:
                results["recommendations"].append("Recommendation accuracy is low. Consider simplifying the recommendation options or providing more context.")
        else:
            results["recommendations"].append("Not enough data to analyze prompt performance")
            
        return results

    def get_prompt_stats(self) -> Dict:
        """Get statistics about prompt usage and performance
        
        Returns:
            Dict: Prompt statistics
        """
        stats = {
            "total_prompts": len(self.prompt_history),
            "templates": {},
            "strategies": {},
            "symbols": {},
            "directions": {},
            "performance": {}
        }
        
        # Count template usage
        for prompt in self.prompt_history:
            template = prompt["template_name"]
            strategy = prompt["strategy_name"]
            symbol = prompt["symbol"]
            direction = prompt["direction"]
            
            # Count templates
            if template not in stats["templates"]:
                stats["templates"][template] = 0
            stats["templates"][template] += 1
            
            # Count strategies
            if strategy not in stats["strategies"]:
                stats["strategies"][strategy] = 0
            stats["strategies"][strategy] += 1
            
            # Count symbols
            if symbol not in stats["symbols"]:
                stats["symbols"][symbol] = 0
            stats["symbols"][symbol] += 1
            
            # Count directions
            if direction not in stats["directions"]:
                stats["directions"][direction] = 0
            stats["directions"][direction] += 1
            
        # Calculate performance metrics
        completed_prompts = [p for p in self.prompt_history if p.get("result")]
        
        if completed_prompts:
            correct_confidence = sum(1 for p in completed_prompts 
                                   if p.get("result") and 
                                   abs(p["result"]["confidence_score"] - 50) < 20)
            
            correct_recommendation = sum(1 for p in completed_prompts 
                                       if p.get("result") and 
                                       ((p["result"]["recommendation"] == "Take Trade" and p["result"]["trade_result"].get("profit_loss", 0) > 0) or
                                        (p["result"]["recommendation"] == "Skip Trade" and p["result"]["trade_result"].get("profit_loss", 0) < 0) or
                                        (p["result"]["recommendation"] == "Reduce Size" and abs(p["result"]["trade_result"].get("profit_loss", 0)) < 2)))
            
            stats["performance"] = {
                "completed_prompts": len(completed_prompts),
                "confidence_accuracy": correct_confidence / len(completed_prompts) if completed_prompts else 0,
                "recommendation_accuracy": correct_recommendation / len(completed_prompts) if completed_prompts else 0
            }
            
        return stats

# Example usage
if __name__ == "__main__":
    optimizer = PromptOptimizer()
    
    # Generate a prompt
    prompt = optimizer.generate_prompt(
        strategy_name="Fibonacci Retracement",
        symbol="EURUSD",
        direction="buy",
        entry_price=1.1050,
        stop_loss=1.1000,
        take_profit=1.1150,
        market_condition="trending",
        volatility="medium",
        trend_strength="strong",
        news_impact="low",
        template_name="standard"
    )
    
    print("Generated prompt:")
    print(prompt)
    
    # Simulate recording a result
    optimizer.record_prompt_result(
        prompt_index=0,
        confidence_score=75,
        recommendation="Take Trade",
        trade_result={"profit_loss": 5.0, "win": True}
    )
    
    # Analyze performance
    performance = optimizer.analyze_prompt_performance()
    print("\nPerformance analysis:")
    print(json.dumps(performance, indent=2))
    
    # Get stats
    stats = optimizer.get_prompt_stats()
    print("\nPrompt statistics:")
    print(json.dumps(stats, indent=2))