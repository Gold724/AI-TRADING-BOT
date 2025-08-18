# Tesla 3-6-9 Trading Strategy - Backend Mode Configuration
# Dynamic mode switching between Safe and Fast trading modes

from datetime import datetime
from typing import Dict, Any, Optional
import json
import os

class TradingModeConfig:
    """Configuration manager for Tesla 3-6-9 trading strategy modes"""
    
    def __init__(self, config_file: str = "trading_mode.json"):
        self.config_file = config_file
        self.current_mode = "safe"  # Default to safe mode
        self.mode_configs = self._initialize_mode_configs()
        self.load_current_mode()
    
    def _initialize_mode_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the configuration for both trading modes"""
        return {
            "safe": {
                "name": "Safe Mode",
                "emoji": "🛡",
                "max_contracts": 1,
                "default_contracts": 1,
                "daily_profit_target": 535.71,
                "daily_max_drawdown": 267.00,
                "tesla_rhythm": "3-6-9 trades/day",
                "risk_level": "minimal",
                "description": "Conservative trading with minimal risk",
                "high_conf_contracts": None  # No high confidence boost in safe mode
            },
            "fast": {
                "name": "Fast Mode",
                "emoji": "⚡",
                "max_contracts": 2,
                "default_contracts": 1,
                "high_conf_contracts": 2,  # Only for high-confidence setups
                "daily_profit_target": 1500.00,
                "daily_max_drawdown": 750.00,  # Proportional to profit target
                "tesla_rhythm": "3-6-9 trades/day",
                "risk_level": "higher",
                "description": "Aggressive trading on high-confidence setups",
                "high_confidence_required": True
            }
        }
    
    def get_current_mode(self) -> str:
        """Get the current trading mode"""
        return self.current_mode
    
    def get_mode_config(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for specified mode or current mode"""
        target_mode = mode or self.current_mode
        return self.mode_configs.get(target_mode, self.mode_configs["safe"])
    
    def set_mode(self, mode: str) -> bool:
        """Set the current trading mode"""
        if mode.lower() in self.mode_configs:
            self.current_mode = mode.lower()
            self.save_current_mode()
            return True
        return False
    
    def get_contracts_for_setup(self, is_high_confidence: bool = False) -> int:
        """Determine number of contracts based on setup confidence and mode"""
        config = self.get_mode_config()
        
        # In fast mode with high confidence setup, use high_conf_contracts
        if (self.current_mode == "fast" and 
            is_high_confidence and 
            config.get("high_conf_contracts")):
            return config["high_conf_contracts"]
        
        # Otherwise use default contracts
        return config["default_contracts"]
    
    def get_daily_profit_target(self) -> float:
        """Get daily profit target for current mode"""
        return self.get_mode_config()["daily_profit_target"]
    
    def get_daily_max_drawdown(self) -> float:
        """Get daily max drawdown for current mode"""
        return self.get_mode_config()["daily_max_drawdown"]
    
    def is_high_confidence_required(self) -> bool:
        """Check if current mode requires high confidence for increased contracts"""
        return self.get_mode_config().get("high_confidence_required", False)
    
    def get_mode_display_name(self) -> str:
        """Get formatted display name for current mode"""
        config = self.get_mode_config()
        return f"{config['emoji']} {config['name']}"
    
    def load_current_mode(self):
        """Load current mode from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.current_mode = data.get('current_mode', 'safe')
        except Exception as e:
            print(f"Warning: Could not load mode config: {e}. Using default safe mode.")
            self.current_mode = 'safe'
    
    def save_current_mode(self):
        """Save current mode to config file"""
        try:
            config_data = {
                'current_mode': self.current_mode,
                'last_updated': datetime.now().isoformat(),
                'available_modes': list(self.mode_configs.keys())
            }
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save mode config: {e}")
    
    def get_mode_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of current mode"""
        config = self.get_mode_config()
        return {
            'mode': self.current_mode,
            'display_name': self.get_mode_display_name(),
            'contracts': {
                'default': config['default_contracts'],
                'max': config['max_contracts'],
                'high_confidence': config.get('high_conf_contracts')
            },
            'targets': {
                'daily_profit': config['daily_profit_target'],
                'daily_drawdown': config['daily_max_drawdown']
            },
            'risk_level': config['risk_level'],
            'tesla_rhythm': config['tesla_rhythm']
        }

# Global instance for easy access
TRADING_MODE = TradingModeConfig()

# Convenience functions for strategy integration
def get_current_mode() -> str:
    """Get the current trading mode"""
    global TRADING_MODE
    return TRADING_MODE.get_current_mode()

def set_trading_mode(mode: str) -> bool:
    """Set the trading mode"""
    global TRADING_MODE
    return TRADING_MODE.set_mode(mode)

def get_contracts_for_setup(is_high_confidence: bool = False) -> int:
    """Get contract size based on current mode and setup confidence"""
    global TRADING_MODE
    return TRADING_MODE.get_contracts_for_setup(is_high_confidence)

def get_daily_targets() -> Dict[str, float]:
    """Get daily profit target and max drawdown for current mode"""
    global TRADING_MODE
    return {
        'profit_target': TRADING_MODE.get_daily_profit_target(),
        'max_drawdown': TRADING_MODE.get_daily_max_drawdown()
    }

def get_mode_info() -> Dict[str, Any]:
    """Get current mode information"""
    global TRADING_MODE
    return {
        'mode': TRADING_MODE.get_current_mode(),
        'display_name': TRADING_MODE.get_mode_display_name(),
        'summary': TRADING_MODE.get_mode_summary()
    }

def set_global_mode(mode: str) -> Dict[str, Any]:
    """Set the global trading mode and return summary"""
    global TRADING_MODE
    TRADING_MODE.set_mode(mode)
    return TRADING_MODE.get_mode_summary()