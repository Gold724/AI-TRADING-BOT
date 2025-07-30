# O.R.I.G.I.N. Cloud Prime - Strategy Mutation Module
# Enables dynamic strategy evolution and version control

import os
import json
import time
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/strategy_mutation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("strategy_mutator")

class StrategyMutator:
    """Manages strategy mutations and version control"""
    
    def __init__(self, 
                 strategy_file: str = "strategy.json",
                 history_file: str = "strategy_history.json",
                 strategies_dir: str = "strategies"):
        """Initialize the strategy mutator
        
        Args:
            strategy_file: Path to the current strategy file
            history_file: Path to the strategy history file
            strategies_dir: Directory to store strategy versions
        """
        self.strategy_file = strategy_file
        self.history_file = history_file
        self.strategies_dir = strategies_dir
        
        # Create directories if they don't exist
        os.makedirs(self.strategies_dir, exist_ok=True)
        
        # Load current strategy and history
        self.current_strategy = self._load_current_strategy()
        self.strategy_history = self._load_strategy_history()
        
        logger.info(f"Strategy Mutator initialized with {len(self.strategy_history)} historical versions")
    
    def _load_current_strategy(self) -> Dict[str, Any]:
        """Load the current strategy from file"""
        try:
            if os.path.exists(self.strategy_file):
                with open(self.strategy_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default strategy if none exists
                default_strategy = {
                    "strategy": "default",
                    "version": "0.1.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "parameters": {
                        "risk_level": "medium",
                        "max_trades": 5,
                        "stop_loss_pct": 2.0,
                        "take_profit_pct": 5.0
                    },
                    "logic": {
                        "entry_conditions": ["price_above_ma_200", "rsi_below_30"],
                        "exit_conditions": ["price_below_ma_50", "rsi_above_70"]
                    }
                }
                self._save_current_strategy(default_strategy)
                return default_strategy
        except Exception as e:
            logger.error(f"Error loading current strategy: {str(e)}")
            return {}
    
    def _save_current_strategy(self, strategy: Dict[str, Any]) -> bool:
        """Save the current strategy to file"""
        try:
            with open(self.strategy_file, 'w') as f:
                json.dump(strategy, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving current strategy: {str(e)}")
            return False
    
    def _load_strategy_history(self) -> List[Dict[str, Any]]:
        """Load the strategy history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading strategy history: {str(e)}")
            return []
    
    def _save_strategy_history(self) -> bool:
        """Save the strategy history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.strategy_history, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy history: {str(e)}")
            return False
    
    def _archive_strategy_version(self, strategy: Dict[str, Any]) -> str:
        """Archive a strategy version to the strategies directory"""
        try:
            version = strategy.get("version", "unknown")
            timestamp = int(time.time())
            filename = f"{version}_{timestamp}.json"
            filepath = os.path.join(self.strategies_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(strategy, f, indent=2)
            
            return filepath
        except Exception as e:
            logger.error(f"Error archiving strategy version: {str(e)}")
            return ""
    
    def get_current_strategy(self) -> Dict[str, Any]:
        """Get the current active strategy"""
        return self.current_strategy
    
    def get_strategy_history(self) -> List[Dict[str, Any]]:
        """Get the strategy mutation history"""
        return self.strategy_history
    
    def update_strategy(self, updates: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """Update the current strategy with new parameters or logic
        
        Args:
            updates: Dictionary of updates to apply to the strategy
            description: Description of the mutation
            
        Returns:
            Updated strategy dictionary
        """
        try:
            # Make a copy of the current strategy
            old_strategy = self.current_strategy.copy()
            
            # Create a new version number
            current_version = old_strategy.get("version", "0.1.0")
            major, minor, patch = map(int, current_version.split("."))
            new_version = f"{major}.{minor}.{patch + 1}"
            
            # Archive the old version
            archive_path = self._archive_strategy_version(old_strategy)
            
            # Update the strategy
            new_strategy = old_strategy.copy()
            
            # Update top-level fields
            for key, value in updates.items():
                if key != "parameters" and key != "logic":
                    new_strategy[key] = value
            
            # Update parameters if provided
            if "parameters" in updates:
                if "parameters" not in new_strategy:
                    new_strategy["parameters"] = {}
                for param_key, param_value in updates["parameters"].items():
                    new_strategy["parameters"][param_key] = param_value
            
            # Update logic if provided
            if "logic" in updates:
                if "logic" not in new_strategy:
                    new_strategy["logic"] = {}
                for logic_key, logic_value in updates["logic"].items():
                    new_strategy["logic"][logic_key] = logic_value
            
            # Update metadata
            new_strategy["version"] = new_version
            new_strategy["updated_at"] = datetime.now().isoformat()
            
            # Save the updated strategy
            self._save_current_strategy(new_strategy)
            
            # Add to history
            history_entry = {
                "version": new_version,
                "previous_version": current_version,
                "updated_at": new_strategy["updated_at"],
                "description": description,
                "changes": updates,
                "archive_path": archive_path
            }
            
            self.strategy_history.append(history_entry)
            self._save_strategy_history()
            
            # Update the current strategy reference
            self.current_strategy = new_strategy
            
            logger.info(f"Strategy updated to version {new_version}: {description}")
            return new_strategy
            
        except Exception as e:
            logger.error(f"Error updating strategy: {str(e)}")
            return self.current_strategy
    
    def mutate_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Mutate the strategy based on a natural language prompt
        
        This is a placeholder for future AI integration. In a real implementation,
        this would call an AI service to interpret the prompt and generate strategy changes.
        
        Args:
            prompt: Natural language description of desired changes
            
        Returns:
            Updated strategy dictionary
        """
        try:
            # This is where you would integrate with an AI service
            # For now, we'll just log the prompt and make a simple change
            
            logger.info(f"Received mutation prompt: {prompt}")
            
            # Example simple mutation based on keywords in the prompt
            updates = {}
            
            if "aggressive" in prompt.lower():
                updates["parameters"] = {
                    "risk_level": "high",
                    "max_trades": 10,
                    "stop_loss_pct": 1.5,
                    "take_profit_pct": 7.0
                }
            elif "conservative" in prompt.lower():
                updates["parameters"] = {
                    "risk_level": "low",
                    "max_trades": 3,
                    "stop_loss_pct": 3.0,
                    "take_profit_pct": 4.0
                }
            
            if updates:
                return self.update_strategy(updates, f"Mutation from prompt: {prompt}")
            else:
                logger.warning(f"Could not determine mutation from prompt: {prompt}")
                return self.current_strategy
                
        except Exception as e:
            logger.error(f"Error mutating strategy from prompt: {str(e)}")
            return self.current_strategy
    
    def list_available_strategies(self) -> List[Dict[str, Any]]:
        """List all available strategy versions"""
        strategies = []
        
        # Add current strategy
        current = self.current_strategy.copy()
        current["is_current"] = True
        strategies.append(current)
        
        # Add historical versions from the history
        for entry in self.strategy_history:
            version = entry.get("version")
            archive_path = entry.get("archive_path")
            
            if archive_path and os.path.exists(archive_path):
                try:
                    with open(archive_path, 'r') as f:
                        strategy = json.load(f)
                        strategy["is_current"] = False
                        strategies.append(strategy)
                except Exception as e:
                    logger.error(f"Error loading archived strategy {version}: {str(e)}")
        
        return strategies

# Create a global instance
strategy_mutator = StrategyMutator()