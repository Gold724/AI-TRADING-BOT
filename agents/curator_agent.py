# agents/curator_agent.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import os
import json
import numpy as np

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('curator_agent')

class CuratorAgent(BaseAgent):
    """Maintains library of strategy variants and archives underperformers"""
    
    def __init__(self, agent_id: str = "curator", config: Dict[str, Any] = None):
        """Initialize the Curator agent
        
        Args:
            agent_id (str, optional): Unique identifier for this agent. Defaults to "curator".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id=agent_id, role="manager", config=config)
        
        # Initialize with default config if none provided
        if config is None:
            config = {}
        
        # Configuration parameters
        self.min_trades_for_evaluation = config.get("min_trades_for_evaluation", 20)
        self.archive_threshold = config.get("archive_threshold", 0.4)  # Performance below this gets archived
        self.promotion_threshold = config.get("promotion_threshold", 0.7)  # Performance above this gets promoted
        self.strategy_library_path = config.get("strategy_library_path", "data/strategy_library")
        self.archive_path = config.get("archive_path", "data/strategy_archive")
        
        # Ensure directories exist
        os.makedirs(self.strategy_library_path, exist_ok=True)
        os.makedirs(self.archive_path, exist_ok=True)
        
        # Internal state
        self.strategy_registry: Dict[str, Dict[str, Any]] = {}
        self.load_strategy_registry()
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a trade action based on the provided context
        
        Args:
            context (Dict[str, Any]): Trading context including market data, signals, etc.
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Extract relevant data from context
        strategy = context.get("strategy", "unknown")
        strategy_performance = context.get("strategy_performance", {})
        strategy_variants = context.get("strategy_variants", [])
        
        # Update strategy registry with new information
        if strategy and strategy_performance:
            self.update_strategy_registry(strategy, strategy_performance)
        
        # Default proposal
        proposal = {
            "action": "continue",
            "confidence": 50,
            "reason": "Insufficient data for strategy evaluation",
            "timestamp": datetime.now().isoformat(),
            "strategy_recommendation": None
        }
        
        # Check if we have enough data for this strategy
        if strategy in self.strategy_registry:
            strategy_data = self.strategy_registry[strategy]
            trades_count = strategy_data.get("trades_count", 0)
            
            if trades_count >= self.min_trades_for_evaluation:
                # Evaluate strategy performance
                performance_score = self.calculate_performance_score(strategy_data)
                
                # Make recommendation based on performance
                if performance_score < self.archive_threshold:
                    proposal["action"] = "archive"
                    proposal["confidence"] = 75
                    proposal["reason"] = f"Strategy '{strategy}' is underperforming with score {performance_score:.2f}"
                    proposal["strategy_recommendation"] = {
                        "action": "archive",
                        "strategy": strategy,
                        "performance_score": performance_score
                    }
                    
                    # Archive the strategy
                    self.archive_strategy(strategy)
                    
                elif performance_score > self.promotion_threshold:
                    proposal["action"] = "promote"
                    proposal["confidence"] = 80
                    proposal["reason"] = f"Strategy '{strategy}' is performing well with score {performance_score:.2f}"
                    proposal["strategy_recommendation"] = {
                        "action": "promote",
                        "strategy": strategy,
                        "performance_score": performance_score
                    }
                    
                    # Promote the strategy
                    self.promote_strategy(strategy)
                    
                else:
                    proposal["action"] = "continue"
                    proposal["confidence"] = 60
                    proposal["reason"] = f"Strategy '{strategy}' has acceptable performance with score {performance_score:.2f}"
                    proposal["strategy_recommendation"] = {
                        "action": "continue",
                        "strategy": strategy,
                        "performance_score": performance_score
                    }
        
        # Check if we should recommend a variant
        if strategy_variants and proposal["action"] == "archive":
            # Find the best performing variant
            best_variant = self.find_best_variant(strategy_variants)
            if best_variant:
                proposal["strategy_recommendation"]["replacement"] = best_variant
                proposal["reason"] += f". Recommend replacing with variant '{best_variant['name']}'"
        
        return proposal
    
    def load_strategy_registry(self) -> None:
        """Load strategy registry from disk"""
        try:
            registry_path = os.path.join(self.strategy_library_path, "registry.json")
            if os.path.exists(registry_path):
                with open(registry_path, "r") as f:
                    self.strategy_registry = json.load(f)
                logger.info(f"Loaded strategy registry with {len(self.strategy_registry)} strategies")
        except Exception as e:
            logger.error(f"Error loading strategy registry: {e}")
    
    def save_strategy_registry(self) -> None:
        """Save strategy registry to disk"""
        try:
            registry_path = os.path.join(self.strategy_library_path, "registry.json")
            with open(registry_path, "w") as f:
                json.dump(self.strategy_registry, f, indent=2)
            logger.info(f"Saved strategy registry with {len(self.strategy_registry)} strategies")
        except Exception as e:
            logger.error(f"Error saving strategy registry: {e}")
    
    def update_strategy_registry(self, strategy: str, performance: Dict[str, Any]) -> None:
        """Update strategy registry with new performance data
        
        Args:
            strategy (str): Strategy name
            performance (Dict[str, Any]): Performance metrics
        """
        if strategy not in self.strategy_registry:
            # Initialize new strategy entry
            self.strategy_registry[strategy] = {
                "name": strategy,
                "created_at": datetime.now().isoformat(),
                "trades_count": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_profit": 0.0,
                "max_drawdown": 0.0,
                "status": "active",
                "variants": []
            }
        
        # Update with new performance data
        strategy_data = self.strategy_registry[strategy]
        strategy_data["trades_count"] = performance.get("trades_count", strategy_data["trades_count"])
        strategy_data["win_rate"] = performance.get("win_rate", strategy_data["win_rate"])
        strategy_data["profit_factor"] = performance.get("profit_factor", strategy_data["profit_factor"])
        strategy_data["total_profit"] = performance.get("total_profit", strategy_data["total_profit"])
        strategy_data["max_drawdown"] = performance.get("max_drawdown", strategy_data["max_drawdown"])
        strategy_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated registry
        self.save_strategy_registry()
    
    def calculate_performance_score(self, strategy_data: Dict[str, Any]) -> float:
        """Calculate overall performance score for a strategy
        
        Args:
            strategy_data (Dict[str, Any]): Strategy performance data
            
        Returns:
            float: Performance score between 0.0 and 1.0
        """
        # Extract metrics
        win_rate = strategy_data.get("win_rate", 0.0)
        profit_factor = strategy_data.get("profit_factor", 0.0)
        max_drawdown = strategy_data.get("max_drawdown", 0.0)
        
        # Normalize profit factor (cap at 3.0 for scoring)
        norm_profit_factor = min(profit_factor, 3.0) / 3.0
        
        # Normalize drawdown (0% is best, 20%+ is worst)
        norm_drawdown = max(0.0, 1.0 - (max_drawdown / 20.0))
        
        # Calculate weighted score
        # 40% win rate, 40% profit factor, 20% drawdown resilience
        score = (0.4 * win_rate) + (0.4 * norm_profit_factor) + (0.2 * norm_drawdown)
        
        return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
    
    def archive_strategy(self, strategy: str) -> None:
        """Archive an underperforming strategy
        
        Args:
            strategy (str): Strategy name to archive
        """
        if strategy in self.strategy_registry:
            # Mark as archived in registry
            self.strategy_registry[strategy]["status"] = "archived"
            self.strategy_registry[strategy]["archived_at"] = datetime.now().isoformat()
            
            # Save strategy data to archive
            archive_file = os.path.join(self.archive_path, f"{strategy}.json")
            with open(archive_file, "w") as f:
                json.dump(self.strategy_registry[strategy], f, indent=2)
            
            logger.info(f"Archived strategy '{strategy}' due to poor performance")
            
            # Log the archiving event
            self.log_strategy_event(strategy, "archive")
    
    def promote_strategy(self, strategy: str) -> None:
        """Promote a well-performing strategy
        
        Args:
            strategy (str): Strategy name to promote
        """
        if strategy in self.strategy_registry:
            # Mark as promoted in registry
            self.strategy_registry[strategy]["status"] = "promoted"
            self.strategy_registry[strategy]["promoted_at"] = datetime.now().isoformat()
            
            logger.info(f"Promoted strategy '{strategy}' due to good performance")
            
            # Log the promotion event
            self.log_strategy_event(strategy, "promote")
    
    def find_best_variant(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the best performing strategy variant
        
        Args:
            variants (List[Dict[str, Any]]): List of strategy variants with performance data
            
        Returns:
            Dict[str, Any]: Best performing variant or None if no good variants
        """
        if not variants:
            return None
        
        # Calculate performance score for each variant
        scored_variants = []
        for variant in variants:
            if variant.get("trades_count", 0) >= self.min_trades_for_evaluation:
                score = self.calculate_performance_score(variant)
                scored_variants.append((score, variant))
        
        # Sort by score (descending)
        scored_variants.sort(reverse=True, key=lambda x: x[0])
        
        # Return the best variant if it meets promotion threshold
        if scored_variants and scored_variants[0][0] >= self.promotion_threshold:
            return scored_variants[0][1]
        
        return None
    
    def log_strategy_event(self, strategy: str, event_type: str) -> None:
        """Log strategy event to file
        
        Args:
            strategy (str): Strategy name
            event_type (str): Event type (archive, promote, etc.)
        """
        try:
            import os
            import json
            from datetime import datetime
            
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy,
                "event": event_type,
                "agent_id": self.agent_id,
                "performance": self.strategy_registry.get(strategy, {})
            }
            
            # Append to log file
            with open("logs/strategy_events.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging strategy event: {e}")
    
    def is_specialized_for(self, context: Dict[str, Any]) -> bool:
        """Check if this agent is specialized for the given context
        
        Args:
            context (Dict[str, Any]): Trading context
            
        Returns:
            bool: True if agent is specialized for this context, False otherwise
        """
        # Curator specializes in strategy management and evaluation
        return "strategy" in context or "strategy_performance" in context or "strategy_variants" in context