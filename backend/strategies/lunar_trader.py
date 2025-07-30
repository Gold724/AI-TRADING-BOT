import logging
import datetime
import math
import random
import json
import os
from utils.lunar_phase import get_lunar_phase

logger = logging.getLogger(__name__)

class LunarTraderStrategy:
    """A trading strategy that aligns with the 8-phase lunar cycle."""
    
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.name = "lunar_trader"
        
        # Set default parameters if not provided
        if "phase_weights" not in self.parameters:
            # Default weights for each lunar phase
            self.parameters["phase_weights"] = {
                "New Moon 🌑": {"buy": 0.2, "sell": 0.8},  # Bearish bias
                "Waxing Crescent 🌒": {"buy": 0.4, "sell": 0.6},  # Slightly bearish
                "First Quarter 🌓": {"buy": 0.6, "sell": 0.4},  # Slightly bullish
                "Waxing Gibbous 🌔": {"buy": 0.8, "sell": 0.2},  # Bullish bias
                "Full Moon 🌕": {"buy": 0.7, "sell": 0.3},  # Bullish but volatile
                "Waning Gibbous 🌖": {"buy": 0.5, "sell": 0.5},  # Neutral
                "Last Quarter 🌗": {"buy": 0.3, "sell": 0.7},  # Slightly bearish
                "Waning Crescent 🌘": {"buy": 0.1, "sell": 0.9}   # Strongly bearish
            }
        
        if "risk_percentage" not in self.parameters:
            self.parameters["risk_percentage"] = 2.0
        
        if "stop_loss" not in self.parameters:
            self.parameters["stop_loss"] = 0.5
        
        if "take_profit" not in self.parameters:
            self.parameters["take_profit"] = 1.5
            
        # Symbolic layer tracking
        self.synchronicity_log_file = os.path.join("logs", "synchronicities.json")
        self.dream_log_file = os.path.join("logs", "dream_logs.json")
        
        # Ensure log directories exist
        os.makedirs("logs", exist_ok=True)
        
        # Initialize log files if they don't exist
        for log_file in [self.synchronicity_log_file, self.dream_log_file]:
            if not os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    json.dump([], f)
        
        logger.info(f"Lunar Trader strategy initialized with parameters: {self.parameters}")
    
    def get_current_lunar_phase(self):
        """Get the current lunar phase."""
        return get_lunar_phase()
    
    def calculate_phase_bias(self, lunar_phase):
        """Calculate trading bias based on lunar phase."""
        phase_weights = self.parameters["phase_weights"]
        
        if lunar_phase in phase_weights:
            return phase_weights[lunar_phase]
        else:
            # Default to neutral if phase not found
            logger.warning(f"Unknown lunar phase: {lunar_phase}, defaulting to neutral bias")
            return {"buy": 0.5, "sell": 0.5}
    
    def calculate_stop_loss(self, entry_price, side="buy"):
        """Calculate stop loss price based on entry price and side."""
        stop_percentage = self.parameters["stop_loss"] / 100
        
        if side.lower() == "buy":
            return round(entry_price * (1 - stop_percentage), 5)
        else:  # sell
            return round(entry_price * (1 + stop_percentage), 5)
    
    def calculate_take_profit(self, entry_price, side="buy"):
        """Calculate take profit price based on entry price and side."""
        profit_percentage = self.parameters["take_profit"] / 100
        
        if side.lower() == "buy":
            return round(entry_price * (1 + profit_percentage), 5)
        else:  # sell
            return round(entry_price * (1 - profit_percentage), 5)
    
    def calculate_position_size(self, account_balance, entry_price, stop_loss_price):
        """Calculate position size based on risk percentage."""
        risk_amount = account_balance * (self.parameters["risk_percentage"] / 100)
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            logger.warning("Price difference is zero, cannot calculate position size")
            return 0
        
        position_size = risk_amount / price_difference
        return round(position_size, 2)
    
    def check_symbolic_layer(self, lunar_phase):
        """Check for synchronicities or dream logs that match lunar reversal points."""
        try:
            # Load synchronicity logs
            with open(self.synchronicity_log_file, 'r') as f:
                synchronicities = json.load(f)
            
            # Load dream logs
            with open(self.dream_log_file, 'r') as f:
                dream_logs = json.load(f)
            
            # Check for recent entries (last 24 hours)
            current_time = datetime.datetime.now()
            cutoff_time = current_time - datetime.timedelta(hours=24)
            
            # Filter recent logs
            recent_synchronicities = [s for s in synchronicities if datetime.datetime.fromisoformat(s.get("timestamp", "")).replace(tzinfo=None) > cutoff_time]
            recent_dreams = [d for d in dream_logs if datetime.datetime.fromisoformat(d.get("timestamp", "")).replace(tzinfo=None) > cutoff_time]
            
            # Check if we're at a reversal point (New Moon or Full Moon)
            is_reversal = lunar_phase in ["New Moon 🌑", "Full Moon 🌕"]
            
            # If we have recent synchronicities/dreams and we're at a reversal point
            if is_reversal and (recent_synchronicities or recent_dreams):
                logger.info(f"Symbolic layer activated: {len(recent_synchronicities)} synchronicities and {len(recent_dreams)} dreams at {lunar_phase}")
                return True, recent_synchronicities, recent_dreams
            
            return False, [], []
            
        except Exception as e:
            logger.error(f"Error checking symbolic layer: {str(e)}")
            return False, [], []
    
    def generate_signal(self, market_data, account_balance=10000):
        """Generate a trading signal based on market data and lunar phase."""
        try:
            # Extract market data
            current_price = market_data.get("current", 0)
            symbol = market_data.get("symbol", "EURUSD")
            session = market_data.get("session", "NY")
            
            if current_price <= 0:
                logger.error("Invalid market data: price must be positive")
                return None
            
            # Get current lunar phase
            lunar_phase = self.get_current_lunar_phase()
            
            # Calculate bias based on lunar phase
            phase_bias = self.calculate_phase_bias(lunar_phase)
            
            # Check symbolic layer
            symbolic_active, synchronicities, dreams = self.check_symbolic_layer(lunar_phase)
            
            # Determine trade direction based on lunar phase bias
            # Use random number weighted by the phase bias
            random_value = random.random()
            
            # Adjust bias if symbolic layer is active
            if symbolic_active:
                # Strengthen the bias in either direction
                if phase_bias["buy"] > phase_bias["sell"]:
                    phase_bias["buy"] += 0.2
                    phase_bias["sell"] -= 0.2
                else:
                    phase_bias["buy"] -= 0.2
                    phase_bias["sell"] += 0.2
                
                # Normalize to ensure they sum to 1
                total = phase_bias["buy"] + phase_bias["sell"]
                phase_bias["buy"] /= total
                phase_bias["sell"] /= total
            
            # Determine side based on weighted random choice
            if random_value < phase_bias["buy"]:
                side = "buy"
            else:
                side = "sell"
            
            # Calculate stop loss and take profit
            stop_loss_price = self.calculate_stop_loss(current_price, side)
            take_profit_price = self.calculate_take_profit(current_price, side)
            
            # Calculate position size
            quantity = self.calculate_position_size(account_balance, current_price, stop_loss_price)
            
            # Calculate confidence based on phase bias and symbolic layer
            if side == "buy":
                confidence = phase_bias["buy"]
            else:
                confidence = phase_bias["sell"]
            
            # Boost confidence if symbolic layer is active
            if symbolic_active:
                confidence = min(0.99, confidence + 0.1)
            
            # Generate signal
            signal = {
                "symbol": symbol,
                "entry_type": f"{side.upper()}_LIMIT",
                "entry_price": current_price,
                "stop_loss": stop_loss_price,
                "take_profit": take_profit_price,
                "confidence": round(confidence, 2),
                "session": session,
                "strategy": f"Lunar Phase: {lunar_phase}",
                "quantity": quantity,
                "side": side,
                "lunar_phase": lunar_phase
            }
            
            logger.info(f"Generated lunar signal: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Error generating lunar signal: {str(e)}")
            return None

# Function to create a strategy instance
def create_strategy(parameters=None):
    return LunarTraderStrategy(parameters)