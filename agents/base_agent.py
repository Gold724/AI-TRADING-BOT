# base_agent.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('base_agent')

class BaseAgent(ABC):
    """Base class for all trading agents in the multi-agent system"""
    
    def __init__(self, agent_id: str, role: str, config: Dict[str, Any] = None):
        """Initialize the base agent
        
        Args:
            agent_id (str): Unique identifier for this agent
            role (str): Role of the agent (strategy, guard, context)
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        self.agent_id = agent_id
        self.role = role
        self.config = config or {}
        self.weight = self.config.get('weight', 1.0)
        self.veto_rights = self.config.get('veto_rights', False)
        self.active = self.config.get('active', True)
        self.specialization = self.config.get('specialization', [])
        
        # Performance tracking
        self.performance = {
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'trades_count': 0,
            'wins': 0,
            'losses': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'last_updated': datetime.now().isoformat()
        }
        
        # Load existing performance if available
        self.load_performance()
        
        logger.info(f"Agent {agent_id} ({role}) initialized")
    
    @abstractmethod
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a trade action based on the provided context
        
        Args:
            context (Dict[str, Any]): Trading context including market data, signals, etc.
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        pass
    
    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """Update agent performance metrics based on trade result
        
        Args:
            trade_result (Dict[str, Any]): Result of a trade including profit/loss
        """
        # Extract trade data
        profit = trade_result.get('profit', 0.0)
        win = profit > 0
        
        # Update performance metrics
        self.performance['trades_count'] += 1
        
        if win:
            self.performance['wins'] += 1
            self.performance['total_profit'] += profit
        else:
            self.performance['losses'] += 1
            self.performance['total_loss'] += abs(profit)
        
        # Recalculate win rate
        if self.performance['trades_count'] > 0:
            self.performance['win_rate'] = self.performance['wins'] / self.performance['trades_count']
        
        # Recalculate profit factor
        if self.performance['total_loss'] > 0:
            self.performance['profit_factor'] = self.performance['total_profit'] / self.performance['total_loss']
        
        # Update timestamp
        self.performance['last_updated'] = datetime.now().isoformat()
        
        # Save updated performance
        self.save_performance()
        
        logger.info(f"Updated performance for agent {self.agent_id}: win_rate={self.performance['win_rate']:.2f}, profit_factor={self.performance['profit_factor']:.2f}")
    
    def save_performance(self) -> None:
        """Save agent performance metrics to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs('data/agent_performance', exist_ok=True)
            
            # Save performance to file
            import json
            with open(f'data/agent_performance/{self.agent_id}.json', 'w') as f:
                json.dump(self.performance, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving performance for agent {self.agent_id}: {e}")
    
    def load_performance(self) -> None:
        """Load agent performance metrics from disk"""
        try:
            import json
            file_path = f'data/agent_performance/{self.agent_id}.json'
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    saved_performance = json.load(f)
                    self.performance.update(saved_performance)
                    logger.info(f"Loaded performance for agent {self.agent_id}: win_rate={self.performance['win_rate']:.2f}, profit_factor={self.performance['profit_factor']:.2f}")
        except Exception as e:
            logger.error(f"Error loading performance for agent {self.agent_id}: {e}")
    
    def get_effective_weight(self) -> float:
        """Get the effective weight of this agent based on performance
        
        Returns:
            float: Effective weight for voting
        """
        base_weight = self.weight
        
        # Apply performance-based adjustments if agent has enough trades
        if self.performance['trades_count'] >= 20:
            # Boost weight for agents with good win rate and profit factor
            if self.performance['win_rate'] > 0.6 and self.performance['profit_factor'] > 1.5:
                return base_weight * 1.5
            # Reduce weight for underperforming agents
            elif self.performance['win_rate'] < 0.4 or self.performance['profit_factor'] < 0.8:
                return base_weight * 0.5
        
        return base_weight
    
    def is_specialized_for(self, strategy_type: str) -> bool:
        """Check if this agent is specialized for a given strategy type
        
        Args:
            strategy_type (str): Strategy type to check
            
        Returns:
            bool: True if agent is specialized for this strategy, False otherwise
        """
        return strategy_type in self.specialization