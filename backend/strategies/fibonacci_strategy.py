import logging
import math

logger = logging.getLogger(__name__)

class FibonacciStrategy:
    """A trading strategy based on Fibonacci retracement levels."""
    
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.name = "fibonacci"
        
        # Set default parameters if not provided
        if "fib_levels" not in self.parameters:
            self.parameters["fib_levels"] = [0.236, 0.382, 0.5, 0.618, 0.786]
        
        if "stop_loss" not in self.parameters:
            self.parameters["stop_loss"] = 0.5
        
        if "take_profit" not in self.parameters:
            self.parameters["take_profit"] = 1.5
        
        if "risk_percentage" not in self.parameters:
            self.parameters["risk_percentage"] = 2.0
        
        logger.info(f"Fibonacci strategy initialized with parameters: {self.parameters}")
    
    def calculate_entry_points(self, high_price, low_price):
        """Calculate Fibonacci retracement levels for entry points."""
        price_range = high_price - low_price
        entry_points = {}
        
        for level in self.parameters["fib_levels"]:
            retracement = high_price - (price_range * level)
            entry_points[f"fib_{level}"] = round(retracement, 5)
        
        return entry_points
    
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
    
    def generate_signal(self, market_data, account_balance=10000):
        """Generate a trading signal based on market data."""
        try:
            # Extract market data
            high_price = market_data.get("high", 0)
            low_price = market_data.get("low", 0)
            current_price = market_data.get("current", 0)
            symbol = market_data.get("symbol", "EURUSD")
            
            if high_price <= 0 or low_price <= 0 or current_price <= 0:
                logger.error("Invalid market data: prices must be positive")
                return None
            
            # Calculate Fibonacci levels
            entry_points = self.calculate_entry_points(high_price, low_price)
            
            # Determine if price is near a Fibonacci level
            closest_level = None
            min_distance = float('inf')
            
            for level_name, level_price in entry_points.items():
                distance = abs(current_price - level_price)
                if distance < min_distance:
                    min_distance = distance
                    closest_level = (level_name, level_price)
            
            # If price is within 0.1% of a Fibonacci level, generate a signal
            price_threshold = current_price * 0.001  # 0.1% threshold
            
            if min_distance <= price_threshold and closest_level:
                level_name, level_price = closest_level
                
                # Determine trade direction based on price movement
                if current_price > level_price:
                    side = "buy"
                else:
                    side = "sell"
                
                # Calculate stop loss and take profit
                stop_loss_price = self.calculate_stop_loss(current_price, side)
                take_profit_price = self.calculate_take_profit(current_price, side)
                
                # Calculate position size
                quantity = self.calculate_position_size(account_balance, current_price, stop_loss_price)
                
                # Generate signal
                signal = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": current_price,
                    "stop_loss": stop_loss_price,
                    "take_profit": take_profit_price,
                    "fibonacci_level": level_name,
                    "reasoning": f"Price is near {level_name} Fibonacci level at {level_price}"
                }
                
                logger.info(f"Generated signal: {signal}")
                return signal
            
            logger.info(f"No signal generated: price not near any Fibonacci level")
            return None
            
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return None

# Function to create a strategy instance
def create_strategy(parameters=None):
    return FibonacciStrategy(parameters)