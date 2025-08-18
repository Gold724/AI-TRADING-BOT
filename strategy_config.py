# Bulenox Gold Scalping Strategy Configuration
# Tesla 3-6-9 Rhythm + Fibonacci Growth Model

class StrategyConfig:
    """
    Configuration class for Bulenox Gold Scalping Strategy
    Allows easy parameter tuning without modifying main algorithm
    """
    
    # === PROFIT TARGETS ===
    CAMPAIGN_TARGET = 15000.0          # Total campaign target ($15,000 in 28 days)
    CAMPAIGN_DAYS = 28                 # Campaign duration
    DAILY_PROFIT_TARGET = 535.71       # Daily profit target (CAMPAIGN_TARGET / CAMPAIGN_DAYS)
    DAILY_MAX_DRAWDOWN = 267.0         # Daily max loss (50% of daily target)
    
    # === TRADING RHYTHM (Tesla 3-6-9) ===
    TRADES_PER_SESSION = 3             # Trades per session
    SESSIONS_PER_DAY = 3               # Number of trading sessions
    MAX_TRADES_PER_DAY = 9             # Total daily trades (3×3)
    
    # === POSITION SIZING ===
    DEFAULT_CONTRACTS = 1              # Default contract size
    MAX_CONTRACTS = 3                  # Maximum contracts per trade
    
    # === FIBONACCI SEQUENCE ===
    # Profit targets in USD for each trade in sequence
    FIB_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]
    
    # Alternative Fibonacci sequences for different risk profiles
    FIB_CONSERVATIVE = [5, 5, 10, 15, 25, 40, 65]
    FIB_AGGRESSIVE = [15, 15, 30, 45, 75, 120, 195]
    
    # === TRADING SESSIONS (NY TIME) ===
    TRADING_SESSIONS = {
        'morning': {
            'start_hour': 3,
            'start_minute': 0,
            'end_hour': 6,
            'end_minute': 0,
            'name': 'Asian Close / London Open'
        },
        'midday': {
            'start_hour': 8,
            'start_minute': 20,
            'end_hour': 11,
            'end_minute': 30,
            'name': 'London / NY Overlap'
        },
        'afternoon': {
            'start_hour': 13,
            'start_minute': 0,
            'end_hour': 15,
            'end_minute': 30,
            'name': 'NY Afternoon'
        }
    }
    
    # === RISK MANAGEMENT ===
    RISK_REWARD_RATIO = 2.5            # Target risk:reward ratio
    STOP_LOSS_MULTIPLIER = 0.4         # Stop loss as % of profit target
    MAX_DAILY_TRADES = 9               # Hard limit on daily trades
    POSITION_TIMEOUT_MINUTES = 30      # Max time to hold position
    
    # === TECHNICAL INDICATORS ===
    VWAP_PERIOD = 20                   # VWAP calculation period
    VOLUME_SMA_PERIOD = 20             # Volume SMA period
    VOLUME_SPIKE_MULTIPLIER = 2.0      # Volume spike threshold (2x average)
    VWAP_TOLERANCE = 0.001             # VWAP confluence tolerance (0.1%)
    
    # === ENTRY SIGNALS ===
    REQUIRE_VOLUME_SPIKE = True        # Require volume spike for entry
    REQUIRE_VWAP_CONFLUENCE = True     # Require price near VWAP
    REQUIRE_SESSION_SWEEP = True       # Require session high/low sweep
    
    # === MARKET DATA ===
    SYMBOL = 'GC'                      # Gold Futures symbol
    RESOLUTION = 'Minute'              # Data resolution
    POINTS_PER_DOLLAR = 0.1           # Approximate points per dollar for GC
    
    # === LOGGING ===
    LOG_LEVEL = 'INFO'                 # Logging level
    LOG_TRADES = True                  # Log individual trades
    LOG_SIGNALS = True                 # Log entry signals
    LOG_DAILY_SUMMARY = True           # Log daily summaries
    LOG_FIBONACCI_PROGRESS = True      # Log Fibonacci sequence progress
    
    # === BACKTESTING ===
    START_DATE = (2024, 1, 1)         # Backtest start date
    END_DATE = (2024, 12, 31)         # Backtest end date
    INITIAL_CAPITAL = 100000           # Starting capital
    
    # === LIVE TRADING ===
    PAPER_TRADING = True               # Use paper trading for testing
    LIVE_TRADING_START_TIME = (9, 0)  # Live trading start time
    LIVE_TRADING_END_TIME = (16, 0)   # Live trading end time
    
    @classmethod
    def get_session_config(cls, session_name):
        """Get configuration for specific trading session"""
        return cls.TRADING_SESSIONS.get(session_name, {})
    
    @classmethod
    def get_fibonacci_target(cls, index, sequence_type='default'):
        """Get Fibonacci profit target for given index"""
        sequences = {
            'default': cls.FIB_SEQUENCE,
            'conservative': cls.FIB_CONSERVATIVE,
            'aggressive': cls.FIB_AGGRESSIVE
        }
        
        sequence = sequences.get(sequence_type, cls.FIB_SEQUENCE)
        return sequence[min(index, len(sequence) - 1)]
    
    @classmethod
    def validate_config(cls):
        """Validate configuration parameters"""
        errors = []
        
        # Validate profit targets
        if cls.DAILY_PROFIT_TARGET <= 0:
            errors.append("Daily profit target must be positive")
        
        if cls.DAILY_MAX_DRAWDOWN <= 0:
            errors.append("Daily max drawdown must be positive")
        
        # Validate trading parameters
        if cls.MAX_CONTRACTS < cls.DEFAULT_CONTRACTS:
            errors.append("Max contracts must be >= default contracts")
        
        if cls.TRADES_PER_SESSION <= 0 or cls.SESSIONS_PER_DAY <= 0:
            errors.append("Trades per session and sessions per day must be positive")
        
        # Validate Fibonacci sequence
        if not cls.FIB_SEQUENCE or len(cls.FIB_SEQUENCE) == 0:
            errors.append("Fibonacci sequence cannot be empty")
        
        # Validate trading sessions
        for session_name, config in cls.TRADING_SESSIONS.items():
            if config['start_hour'] >= config['end_hour']:
                errors.append(f"Invalid time range for {session_name} session")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("=== BULENOX GOLD SCALPING STRATEGY CONFIG ===")
        print(f"Campaign Target: ${cls.CAMPAIGN_TARGET:,.2f} in {cls.CAMPAIGN_DAYS} days")
        print(f"Daily Target: ${cls.DAILY_PROFIT_TARGET:.2f}")
        print(f"Daily Max Loss: ${cls.DAILY_MAX_DRAWDOWN:.2f}")
        print(f"Trading Rhythm: {cls.TRADES_PER_SESSION} trades × {cls.SESSIONS_PER_DAY} sessions = {cls.MAX_TRADES_PER_DAY} max trades/day")
        print(f"Position Sizing: {cls.DEFAULT_CONTRACTS}-{cls.MAX_CONTRACTS} contracts")
        print(f"Fibonacci Sequence: {cls.FIB_SEQUENCE}")
        print("\nTrading Sessions:")
        for name, config in cls.TRADING_SESSIONS.items():
            print(f"  {name.title()}: {config['start_hour']:02d}:{config['start_minute']:02d} - {config['end_hour']:02d}:{config['end_minute']:02d} ({config['name']})")
        print("="*50)


# === PRESET CONFIGURATIONS ===

class ConservativeConfig(StrategyConfig):
    """Conservative risk profile"""
    DAILY_PROFIT_TARGET = 400.0
    DAILY_MAX_DRAWDOWN = 200.0
    FIB_SEQUENCE = [5, 5, 10, 15, 25, 40, 65]
    MAX_CONTRACTS = 2
    VOLUME_SPIKE_MULTIPLIER = 2.5

class AggressiveConfig(StrategyConfig):
    """Aggressive risk profile"""
    DAILY_PROFIT_TARGET = 700.0
    DAILY_MAX_DRAWDOWN = 350.0
    FIB_SEQUENCE = [15, 15, 30, 45, 75, 120, 195]
    MAX_CONTRACTS = 5
    VOLUME_SPIKE_MULTIPLIER = 1.5

class ScalpingConfig(StrategyConfig):
    """High-frequency scalping profile"""
    TRADES_PER_SESSION = 5
    MAX_TRADES_PER_DAY = 15
    FIB_SEQUENCE = [5, 5, 8, 13, 21, 34, 55]
    VWAP_TOLERANCE = 0.0005
    POSITION_TIMEOUT_MINUTES = 15


# === USAGE EXAMPLE ===
if __name__ == "__main__":
    # Validate and print default configuration
    errors = StrategyConfig.validate_config()
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    StrategyConfig.print_config()
    
    # Example of using different risk profiles
    print("\n=== ALTERNATIVE CONFIGURATIONS ===")
    print("Conservative:", ConservativeConfig.FIB_SEQUENCE)
    print("Aggressive:", AggressiveConfig.FIB_SEQUENCE)
    print("Scalping:", ScalpingConfig.FIB_SEQUENCE)