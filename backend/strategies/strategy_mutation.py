import json
import os
import time
import logging
from datetime import datetime
import importlib.util
import sys

logger = logging.getLogger(__name__)

class StrategyMutator:
    """Handles the mutation of trading strategies and version control."""
    
    def __init__(self, strategy_dir="strategies", 
                 strategy_file="strategy.json", 
                 history_file="strategy_history.json"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.strategy_dir = os.path.join(self.base_dir, strategy_dir)
        self.strategy_file = os.path.join(self.base_dir, strategy_file)
        self.history_file = os.path.join(self.base_dir, history_file)
        
        # Ensure strategy directory exists
        os.makedirs(self.strategy_dir, exist_ok=True)
        
        # Initialize history if it doesn't exist
        if not os.path.exists(self.history_file):
            self._initialize_history()
    
    def _initialize_history(self):
        """Initialize the strategy history file if it doesn't exist."""
        try:
            # If strategy file exists, use it as the first entry
            if os.path.exists(self.strategy_file):
                with open(self.strategy_file, 'r') as f:
                    current_strategy = json.load(f)
                
                history = [{
                    "strategy": current_strategy.get("strategy", "default"),
                    "parameters": current_strategy.get("parameters", {}),
                    "updated_at": datetime.now().isoformat(),
                    "version": 1,
                    "description": "Initial strategy from existing configuration"
                }]
            else:
                # Create default history
                history = [{
                    "strategy": "default",
                    "parameters": {
                        "stop_loss": 0.5,
                        "take_profit": 1.5,
                        "max_trades": 3,
                        "risk_percentage": 2
                    },
                    "updated_at": datetime.now().isoformat(),
                    "version": 1,
                    "description": "Initial default strategy"
                }]
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"Initialized strategy history at {self.history_file}")
        except Exception as e:
            logger.error(f"Failed to initialize strategy history: {str(e)}")
            raise
    
    def get_current_strategy(self):
        """Get the current active strategy configuration."""
        try:
            if os.path.exists(self.strategy_file):
                with open(self.strategy_file, 'r') as f:
                    return json.load(f)
            else:
                # If no strategy file exists, get the latest from history
                history = self.get_strategy_history()
                if history:
                    latest = history[0]  # Assuming history is sorted by version desc
                    strategy_data = {
                        "strategy": latest["strategy"],
                        "parameters": latest["parameters"]
                    }
                    # Save this to the strategy file
                    with open(self.strategy_file, 'w') as f:
                        json.dump(strategy_data, f, indent=2)
                    return strategy_data
                else:
                    # Fallback to default
                    return {
                        "strategy": "default",
                        "parameters": {
                            "stop_loss": 0.5,
                            "take_profit": 1.5,
                            "max_trades": 3,
                            "risk_percentage": 2
                        }
                    }
        except Exception as e:
            logger.error(f"Error getting current strategy: {str(e)}")
            # Return default on error
            return {
                "strategy": "default",
                "parameters": {
                    "stop_loss": 0.5,
                    "take_profit": 1.5,
                    "max_trades": 3,
                    "risk_percentage": 2
                }
            }
    
    def get_strategy_history(self, limit=10):
        """Get the strategy mutation history."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                # Return most recent entries first, limited by limit
                return sorted(history, key=lambda x: x.get('version', 0), reverse=True)[:limit]
            else:
                self._initialize_history()
                return self.get_strategy_history(limit)
        except Exception as e:
            logger.error(f"Error getting strategy history: {str(e)}")
            return []
    
    def update_strategy(self, strategy_data, description="Strategy updated"):
        """Update the current strategy and record in history."""
        try:
            # Validate strategy data
            if not isinstance(strategy_data, dict):
                raise ValueError("Strategy data must be a dictionary")
            
            if "strategy" not in strategy_data:
                raise ValueError("Strategy data must contain 'strategy' field")
            
            # Get current history to determine next version
            history = self.get_strategy_history()
            next_version = 1
            if history:
                next_version = history[0].get('version', 0) + 1
            
            # Create history entry
            timestamp = datetime.now().isoformat()
            history_entry = {
                "strategy": strategy_data["strategy"],
                "parameters": strategy_data.get("parameters", {}),
                "updated_at": timestamp,
                "version": next_version,
                "description": description
            }
            
            # Update history file
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.insert(0, history_entry)  # Add to beginning (newest first)
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            # Update current strategy file
            with open(self.strategy_file, 'w') as f:
                json.dump(strategy_data, f, indent=2)
            
            logger.info(f"Strategy updated to version {next_version}: {strategy_data['strategy']}")
            return history_entry
        except Exception as e:
            logger.error(f"Error updating strategy: {str(e)}")
            raise
    
    def mutate_strategy_from_prompt(self, prompt, current_strategy=None):
        """Placeholder for AI-based strategy mutation from natural language.
        This would integrate with an AI service like OpenAI to generate strategy changes.
        """
        # This is a placeholder - in a real implementation, this would call an AI service
        logger.info(f"Strategy mutation requested via prompt: {prompt[:50]}...")
        
        if current_strategy is None:
            current_strategy = self.get_current_strategy()
        
        # For now, just log the request and return the current strategy unchanged
        # In a real implementation, this would send the prompt to an AI service
        # and process the response to update the strategy
        
        return current_strategy
    
    def get_available_strategies(self):
        """Get list of available strategy modules in the strategies directory."""
        strategies = []
        
        # Look for Python files in the strategy directory
        for file in os.listdir(self.strategy_dir):
            if file.endswith(".py") and not file.startswith("__") and file != "strategy_mutation.py":
                strategy_name = file[:-3]  # Remove .py extension
                strategies.append(strategy_name)
        
        return strategies
    
    def load_strategy_module(self, strategy_name):
        """Dynamically load a strategy module by name."""
        try:
            strategy_path = os.path.join(self.strategy_dir, f"{strategy_name}.py")
            
            if not os.path.exists(strategy_path):
                logger.error(f"Strategy module not found: {strategy_path}")
                return None
            
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(strategy_name, strategy_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[strategy_name] = module
            spec.loader.exec_module(module)
            
            logger.info(f"Successfully loaded strategy module: {strategy_name}")
            return module
        except Exception as e:
            logger.error(f"Error loading strategy module {strategy_name}: {str(e)}")
            return None