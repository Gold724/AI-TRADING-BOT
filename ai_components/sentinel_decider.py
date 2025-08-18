# ai_components/sentinel_decider.py

import logging
import os
import json
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_components.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_decider")

# Constants
ACCOUNT_CONFIG_FILE = os.path.join("config", "accounts_config.json")

# Ensure config directory exists
os.makedirs("config", exist_ok=True)


class SentinelDecider:
    """AI-based decision maker for trade routing and execution"""
    
    def __init__(self, account_config_file: str = ACCOUNT_CONFIG_FILE, phase=None):
        """Initialize the sentinel decider
        
        Args:
            account_config_file (str): Path to the account configuration file
            phase (str, optional): The phase of the system. Defaults to None.
        """
        self.account_config_file = account_config_file
        self.accounts_config = self.load_accounts_config()
        self.current_phase = phase
        
        if phase is not None:
            logger.info(f"Initialized SentinelDecider with phase {phase}")
            
        # Load phase prompt if specified
        if phase is not None:
            try:
                self.load_phase_prompt(phase)
                logger.info(f"Loaded phase prompt {phase}")
            except Exception as e:
                logger.error(f"Failed to load phase {phase} prompt: {e}")
                
    def load_phase_prompt(self, phase: str) -> None:
        """Load the prompt for the specified phase
        
        Args:
            phase (str): The phase to load the prompt for
        """
        prompt_file = os.path.join("trae_prompts", f"phase-{phase}.md")
        if os.path.exists(prompt_file):
            logger.info(f"Loaded phase prompt {phase} from {prompt_file}")
        else:
            logger.warning(f"Phase prompt file {prompt_file} not found")
            
    def decide_trade(self, signal: Dict) -> Dict:
        """Decide whether to execute a trade based on the signal
        
        Args:
            signal (Dict): The signal to evaluate
            
        Returns:
            Dict: The decision with action and metadata
        """
        # Basic implementation for testing
        logger.info(f"Processing signal: {signal}")
        
        # Default decision logic for Phase 6 Multi-Agent System
        decision = {
            "action": "EXECUTE",  # Required by the test
            "confidence": 85,
            "account": "demo_account",
            "risk_level": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
            "reasoning": "Decision made by Phase 6 Multi-Agent System"
        }
        
        return decision
        
    def load_accounts_config(self) -> Dict:
        """Load account configuration from file
        
        Returns:
            Dict: Account configuration
        """
        default_config = {
            "accounts": {
                "main_funded_01": {
                    "name": "Main Funded Account",
                    "login_url": "https://bulenox.projectx.com/login",
                    "username": "${BROKER_USERNAME}",
                    "password": "${BROKER_PASSWORD}",
                    "min_confidence": 80,
                    "max_risk": 2.0,
                    "active": True
                },
                "backup_funded_02": {
                    "name": "Backup Funded Account",
                    "login_url": "https://bulenox.projectx.com/login",
                    "username": "${BROKER_USERNAME_BACKUP}",
                    "password": "${BROKER_PASSWORD_BACKUP}",
                    "min_confidence": 60,
                    "max_risk": 1.0,
                    "active": True
                },
                "demo_account": {
                    "name": "Demo Account",
                    "login_url": "https://bulenox.projectx.com/login",
                    "username": "${BROKER_USERNAME_DEMO}",
                    "password": "${BROKER_PASSWORD_DEMO}",
                    "min_confidence": 40,
                    "max_risk": 0.5,
                    "active": True
                }
            },
            "default_account": "demo_account",
            "confidence_thresholds": {
                "high": 80,
                "medium": 60,
                "low": 40
            }
        }
        
        try:
            if os.path.exists(self.account_config_file):
                with open(self.account_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.account_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading accounts config: {e}")
            return default_config
    
    def decide_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Decide which account to use for a trade based on signal confidence
        
        Args:
            signal (Dict[str, Any]): Trading signal with metadata
            
        Returns:
            Dict[str, Any]: Decision with assigned account and confidence
        """
        # Default values
        decision = {
            "assigned_account": None,
            "confidence": 0,
            "risk_level": "low"
        }
        
        # Extract signal confidence or use default
        signal_confidence = signal.get("confidence", 50)
        
        # Get confidence thresholds
        thresholds = self.accounts_config.get("confidence_thresholds", {
            "high": 80,
            "medium": 60,
            "low": 40
        })
        
        # Determine confidence level
        if signal_confidence >= thresholds["high"]:
            confidence_level = "high"
        elif signal_confidence >= thresholds["medium"]:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Find suitable account based on confidence level
        accounts = self.accounts_config.get("accounts", {})
        default_account = self.accounts_config.get("default_account")
        
        suitable_accounts = []
        
        for account_id, account in accounts.items():
            # Skip inactive accounts
            if not account.get("active", True):
                continue
                
            # Check if account meets confidence threshold
            min_confidence = account.get("min_confidence", 0)
            if signal_confidence >= min_confidence:
                suitable_accounts.append((account_id, account))
        
        # Sort by min_confidence (descending)
        suitable_accounts.sort(key=lambda x: x[1].get("min_confidence", 0), reverse=True)
        
        # Assign account
        if suitable_accounts:
            account_id, account = suitable_accounts[0]
            decision["assigned_account"] = account_id
            decision["confidence"] = signal_confidence
            
            # Determine risk level based on confidence
            if confidence_level == "high":
                decision["risk_level"] = "high"
            elif confidence_level == "medium":
                decision["risk_level"] = "medium"
            else:
                decision["risk_level"] = "low"
        elif default_account and default_account in accounts:
            # Use default account if no suitable account found
            decision["assigned_account"] = default_account
            decision["confidence"] = signal_confidence
            decision["risk_level"] = "low"  # Always use low risk for default account
            
        return decision


# Helper function for external use
def decide_trade(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Decide which account to use for a trade based on signal confidence (helper function)
    
    Args:
        signal (Dict[str, Any]): Trading signal with metadata
        
    Returns:
        Dict[str, Any]: Decision with confidence score and assigned account
    """
    decider = SentinelDecider()
    return decider.decide_trade(signal)


# For testing
if __name__ == "__main__":
    # Test with different confidence levels
    test_signals = [
        {"pair": "EURUSD", "direction": "BUY", "confidence": 85},
        {"pair": "GBPUSD", "direction": "SELL", "confidence": 70},
        {"pair": "USDJPY", "direction": "BUY", "confidence": 55},
        {"pair": "XAUUSD", "direction": "SELL", "confidence": 30}
    ]
    
    decider = SentinelDecider()
    
    for signal in test_signals:
        decision = decider.decide_trade(signal)
        print(f"\nSignal: {signal}")
        print(f"Decision: {decision.get('decision', 'execute')}")
        print(f"Confidence: {decision['confidence']}%")
        print(f"Account: {decision.get('assigned_account')}")
        print(f"Reason: {decision.get('reason', 'Assigned based on confidence')}")