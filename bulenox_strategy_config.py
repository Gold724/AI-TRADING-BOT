#!/usr/bin/env python3
"""
Bulenox Gold Scalping Strategy Configuration
==========================================

Comprehensive configuration file for the Tesla 3-6-9 trade rhythm combined with
intra-session Fibonacci growth model for position sizing on Gold Futures (GC).

This configuration allows easy tuning of all strategy parameters without
modifying the core algorithm code.

Author: TradeBot Sentinel AI
Version: 1.0.0
Target: $15,000 profit in 28 days
"""

from datetime import time
from typing import Dict, List, Tuple

class BulenoxStrategyConfig:
    """
    Configuration class for Bulenox Gold Scalping Strategy.
    All parameters are easily adjustable for different risk profiles and market conditions.
    """
    
    # ========================================
    # CORE STRATEGY PARAMETERS
    # ========================================
    
    # Tesla 3-6-9 Trade Rhythm Configuration
    TRADES_PER_SESSION = 3  # Number of trades per session (3, 6, or 9 for different intensities)
    SESSIONS_PER_DAY = 3    # Fixed: morning, midday, afternoon
    MAX_TRADES_PER_DAY = TRADES_PER_SESSION * SESSIONS_PER_DAY  # 9 trades max
    
    # Daily Profit and Risk Targets
    DAILY_PROFIT_TARGET = 535.71    # $535.71 daily target for $15k in 28 days
    DAILY_MAX_DRAWDOWN = 267.00     # Maximum daily loss limit (50% of profit target)
    MONTHLY_PROFIT_TARGET = 15000   # $15,000 in 28 days
    CAMPAIGN_DAYS = 28              # Trading campaign duration
    
    # Position Sizing Limits
    DEFAULT_CONTRACTS = 1           # Default position size
    MAX_CONTRACTS = 3               # Maximum contracts per trade
    MIN_CONTRACTS = 1               # Minimum contracts per trade
    
    # ========================================
    # FIBONACCI SEQUENCE CONFIGURATION
    # ========================================
    
    # Fibonacci Profit Targets (per trade in USD)
    FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]  # Fibonacci-based profit targets
    
    # Alternative: Fibonacci Contract Sizing (if using contract-based progression)
    FIBONACCI_CONTRACT_SEQUENCE = [1, 1, 1, 2, 2, 3, 3]  # Contract sizes following Fibonacci logic
    
    # Fibonacci Reset Conditions
    RESET_FIBONACCI_ON_LOSS = True          # Reset sequence after any losing trade
    RESET_FIBONACCI_PER_SESSION = True      # Reset sequence at start of each session
    FIBONACCI_MAX_LEVEL = len(FIBONACCI_PROFIT_SEQUENCE) - 1  # Maximum Fibonacci level
    
    # ========================================
    # TRADING SESSIONS CONFIGURATION
    # ========================================
    
    # Trading Session Windows (NY Time)
    TRADING_SESSIONS = {
        'morning': {
            'start': time(3, 0),    # 03:00 NY
            'end': time(6, 0),      # 06:00 NY
            'name': 'Morning Session',
            'volatility_factor': 1.2  # Higher volatility expected
        },
        'midday': {
            'start': time(8, 20),   # 08:20 NY
            'end': time(11, 30),    # 11:30 NY
            'name': 'Midday Session',
            'volatility_factor': 1.0  # Normal volatility
        },
        'afternoon': {
            'start': time(13, 0),   # 13:00 NY
            'end': time(15, 30),    # 15:30 NY
            'name': 'Afternoon Session',
            'volatility_factor': 0.8  # Lower volatility expected
        }
    }
    
    # Session Break Buffers (minutes before/after session)
    SESSION_START_BUFFER = 5    # Wait 5 minutes after session start
    SESSION_END_BUFFER = 10     # Stop trading 10 minutes before session end
    
    # ========================================
    # INSTRUMENT CONFIGURATION
    # ========================================
    
    # Primary Trading Instrument
    SYMBOL = "GC"               # Gold Futures base symbol
    CONTRACT_MONTH = "Z25"      # December 2025 contract
    FULL_SYMBOL = "GCZ25"       # Complete symbol
    
    # Contract Specifications
    CONTRACT_SIZE = 100         # 100 troy ounces per contract
    TICK_SIZE = 0.10           # $0.10 per tick
    TICK_VALUE = 10.0          # $10 per tick (100 oz * $0.10)
    MARGIN_REQUIREMENT = 8000   # Approximate margin per contract
    
    # ========================================
    # TECHNICAL INDICATORS CONFIGURATION
    # ========================================
    
    # VWAP Configuration
    VWAP_PERIOD = 20           # VWAP calculation period
    VWAP_DEVIATION_THRESHOLD = 0.02  # 2% deviation from VWAP for signals
    
    # Volume Analysis
    VOLUME_SMA_PERIOD = 20     # Volume moving average period
    VOLUME_SPIKE_MULTIPLIER = 1.5  # Volume must be 1.5x average for spike
    MIN_VOLUME_THRESHOLD = 1000     # Minimum volume for valid signals
    
    # Session High/Low Analysis
    SESSION_RANGE_LOOKBACK = 5      # Days to look back for session ranges
    SWEEP_REJECTION_THRESHOLD = 0.5  # Minimum rejection distance in ticks
    
    # ========================================
    # ENTRY SIGNAL CONFIGURATION
    # ========================================
    
    # Signal Confluence Requirements
    REQUIRE_VWAP_CONFLUENCE = True      # Must have VWAP signal
    REQUIRE_VOLUME_SPIKE = True         # Must have volume confirmation
    REQUIRE_SESSION_SWEEP = True        # Must have session high/low sweep
    
    # Signal Timing
    MIN_TIME_BETWEEN_SIGNALS = 300      # 5 minutes between signals (seconds)
    SIGNAL_EXPIRY_TIME = 60            # Signal expires after 60 seconds
    
    # Entry Execution
    USE_MARKET_ORDERS = True           # Use market orders for entries
    MAX_SLIPPAGE_TICKS = 2            # Maximum acceptable slippage
    
    # ========================================
    # EXIT LOGIC CONFIGURATION
    # ========================================
    
    # Take Profit Settings
    BASE_TAKE_PROFIT_PERCENT = 0.15    # 0.15% base take profit
    TAKE_PROFIT_TICKS = 15             # Alternative: fixed ticks
    USE_DYNAMIC_TP = True              # Adjust TP based on volatility
    
    # Stop Loss Settings
    BASE_STOP_LOSS_PERCENT = 0.02      # 0.02% base stop loss
    STOP_LOSS_TICKS = 5                # Alternative: fixed ticks
    USE_DYNAMIC_SL = True              # Adjust SL based on volatility
    
    # Risk/Reward Ratios
    MIN_RISK_REWARD_RATIO = 2.5        # Minimum 2.5:1 R:R ratio
    TARGET_RISK_REWARD_RATIO = 7.5     # Target 7.5:1 R:R ratio (0.15% / 0.02%)
    
    # Trailing Stop Configuration
    ENABLE_TRAILING_STOP = True        # Enable trailing stop functionality
    TRAILING_STOP_ACTIVATION = 0.5     # Activate when 50% of target reached
    TRAILING_STOP_DISTANCE = 3         # Trail by 3 ticks
    
    # Order Management
    USE_BRACKET_ORDERS = True          # Use bracket orders (TP + SL)
    CANCEL_OPPOSITE_ON_FILL = True     # Cancel remaining orders on fill
    ORDER_TIMEOUT_SECONDS = 300        # Cancel unfilled orders after 5 minutes
    
    # ========================================
    # RISK MANAGEMENT CONFIGURATION
    # ========================================
    
    # Daily Risk Limits
    MAX_DAILY_LOSS = DAILY_MAX_DRAWDOWN    # Maximum daily loss
    MAX_DAILY_TRADES = MAX_TRADES_PER_DAY  # Maximum trades per day
    
    # Consecutive Loss Protection
    MAX_CONSECUTIVE_LOSSES = 3         # Stop after 3 consecutive losses
    CONSECUTIVE_LOSS_COOLDOWN = 1800   # 30-minute cooldown after max losses
    
    # Portfolio Heat Management
    MAX_PORTFOLIO_HEAT = 0.02          # Maximum 2% account risk per trade
    MAX_TOTAL_EXPOSURE = 0.10          # Maximum 10% total account exposure
    
    # Drawdown Protection
    MAX_ACCOUNT_DRAWDOWN = 0.05        # Stop trading at 5% account drawdown
    DAILY_LOSS_RESET_TIME = time(17, 0) # Reset daily counters at 5 PM NY
    
    # ========================================
    # VOLATILITY ADJUSTMENT CONFIGURATION
    # ========================================
    
    # Volatility Measurement
    VOLATILITY_LOOKBACK_DAYS = 5       # Days to calculate volatility
    VOLATILITY_PERCENTILE_HIGH = 80    # High volatility threshold (percentile)
    VOLATILITY_PERCENTILE_LOW = 20     # Low volatility threshold (percentile)
    
    # Volatility-Based Adjustments
    HIGH_VOLATILITY_TP_MULTIPLIER = 1.5    # Increase TP in high volatility
    HIGH_VOLATILITY_SL_MULTIPLIER = 1.3    # Increase SL in high volatility
    LOW_VOLATILITY_TP_MULTIPLIER = 0.8     # Decrease TP in low volatility
    LOW_VOLATILITY_SL_MULTIPLIER = 0.9     # Decrease SL in low volatility
    
    # ========================================
    # LOGGING AND MONITORING CONFIGURATION
    # ========================================
    
    # Logging Levels
    ENABLE_DETAILED_LOGGING = True     # Enable comprehensive logging
    LOG_TRADE_ENTRIES = True           # Log all trade entries
    LOG_TRADE_EXITS = True             # Log all trade exits
    LOG_SIGNAL_ANALYSIS = True         # Log signal analysis details
    LOG_RISK_CHECKS = True             # Log risk management decisions
    LOG_FIBONACCI_PROGRESSION = True   # Log Fibonacci sequence progression
    
    # Performance Tracking
    TRACK_SESSION_PERFORMANCE = True   # Track per-session statistics
    TRACK_FIBONACCI_PERFORMANCE = True # Track Fibonacci level performance
    CALCULATE_SHARPE_RATIO = True      # Calculate and log Sharpe ratio
    CALCULATE_MAX_DRAWDOWN = True      # Track maximum drawdown
    
    # Alert Thresholds
    PROFIT_TARGET_ALERT_THRESHOLD = 0.8    # Alert at 80% of daily target
    LOSS_LIMIT_ALERT_THRESHOLD = 0.8       # Alert at 80% of daily loss limit
    
    # ========================================
    # BACKTESTING CONFIGURATION
    # ========================================
    
    # Backtesting Period
    BACKTEST_START_DATE = "2024-01-01"     # Start date for backtesting
    BACKTEST_END_DATE = "2024-12-31"       # End date for backtesting
    BACKTEST_INITIAL_CAPITAL = 100000      # Starting capital for backtesting
    
    # Slippage and Fees
    ESTIMATED_SLIPPAGE_TICKS = 1           # Expected slippage per trade
    COMMISSION_PER_CONTRACT = 4.50         # Commission per contract (round trip)
    
    # ========================================
    # LIVE TRADING CONFIGURATION
    # ========================================
    
    # Broker Settings
    BROKER_NAME = "Bulenox"                # Broker name
    ACCOUNT_TYPE = "Live"                  # Account type (Live/Paper)
    
    # Connection Settings
    MAX_CONNECTION_RETRIES = 3             # Maximum connection retry attempts
    CONNECTION_TIMEOUT_SECONDS = 30        # Connection timeout
    HEARTBEAT_INTERVAL_SECONDS = 60        # Heartbeat interval
    
    # Safety Settings
    ENABLE_KILL_SWITCH = True              # Enable emergency kill switch
    MAX_DAILY_VOLUME = 50                  # Maximum contracts traded per day
    REQUIRE_MANUAL_APPROVAL = False        # Require manual approval for trades
    
    # ========================================
    # ALTERNATIVE CONFIGURATION PROFILES
    # ========================================
    
    @classmethod
    def get_conservative_config(cls):
        """
        Get conservative configuration for lower risk tolerance.
        """
        config = cls()
        config.TRADES_PER_SESSION = 2          # Fewer trades
        config.MAX_CONTRACTS = 2               # Lower position sizes
        config.DAILY_PROFIT_TARGET = 400       # Lower daily target
        config.DAILY_MAX_DRAWDOWN = 200        # Lower loss limit
        config.MIN_RISK_REWARD_RATIO = 3.0     # Higher R:R requirement
        config.MAX_CONSECUTIVE_LOSSES = 2      # Stop sooner on losses
        return config
    
    @classmethod
    def get_aggressive_config(cls):
        """
        Get aggressive configuration for higher risk tolerance.
        """
        config = cls()
        config.TRADES_PER_SESSION = 4          # More trades
        config.MAX_CONTRACTS = 5               # Higher position sizes
        config.DAILY_PROFIT_TARGET = 700       # Higher daily target
        config.DAILY_MAX_DRAWDOWN = 350        # Higher loss limit
        config.MIN_RISK_REWARD_RATIO = 2.0     # Lower R:R requirement
        config.MAX_CONSECUTIVE_LOSSES = 4      # Allow more losses
        return config
    
    @classmethod
    def get_scalping_config(cls):
        """
        Get high-frequency scalping configuration.
        """
        config = cls()
        config.TRADES_PER_SESSION = 6          # More frequent trades
        config.BASE_TAKE_PROFIT_PERCENT = 0.08 # Smaller profit targets
        config.BASE_STOP_LOSS_PERCENT = 0.04   # Tighter stops
        config.MIN_TIME_BETWEEN_SIGNALS = 120  # Shorter signal intervals
        config.FIBONACCI_PROFIT_SEQUENCE = [5, 5, 10, 15, 25, 40, 65]  # Smaller targets
        return config
    
    # ========================================
    # VALIDATION METHODS
    # ========================================
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration parameters and return list of warnings/errors.
        """
        warnings = []
        
        # Validate daily targets
        if self.DAILY_PROFIT_TARGET <= 0:
            warnings.append("Daily profit target must be positive")
        
        if self.DAILY_MAX_DRAWDOWN <= 0:
            warnings.append("Daily max drawdown must be positive")
        
        if self.DAILY_MAX_DRAWDOWN >= self.DAILY_PROFIT_TARGET:
            warnings.append("Daily max drawdown should be less than profit target")
        
        # Validate position sizing
        if self.MAX_CONTRACTS < self.MIN_CONTRACTS:
            warnings.append("Max contracts must be >= min contracts")
        
        if self.DEFAULT_CONTRACTS > self.MAX_CONTRACTS:
            warnings.append("Default contracts must be <= max contracts")
        
        # Validate Fibonacci sequence
        if len(self.FIBONACCI_PROFIT_SEQUENCE) == 0:
            warnings.append("Fibonacci profit sequence cannot be empty")
        
        if any(x <= 0 for x in self.FIBONACCI_PROFIT_SEQUENCE):
            warnings.append("All Fibonacci profit targets must be positive")
        
        # Validate risk/reward ratios
        if self.MIN_RISK_REWARD_RATIO <= 1.0:
            warnings.append("Minimum risk/reward ratio should be > 1.0")
        
        # Validate session times
        for session_name, session_config in self.TRADING_SESSIONS.items():
            if session_config['start'] >= session_config['end']:
                warnings.append(f"Session {session_name}: start time must be before end time")
        
        return warnings
    
    def get_config_summary(self) -> Dict:
        """
        Get a summary of key configuration parameters.
        """
        return {
            'strategy_name': 'Bulenox Gold Scalping - Tesla 3-6-9 + Fibonacci',
            'daily_target': f"${self.DAILY_PROFIT_TARGET:.2f}",
            'daily_max_loss': f"${self.DAILY_MAX_DRAWDOWN:.2f}",
            'max_trades_per_day': self.MAX_TRADES_PER_DAY,
            'max_contracts': self.MAX_CONTRACTS,
            'fibonacci_sequence': self.FIBONACCI_PROFIT_SEQUENCE,
            'trading_sessions': len(self.TRADING_SESSIONS),
            'risk_reward_ratio': f"{self.MIN_RISK_REWARD_RATIO}:1",
            'symbol': self.FULL_SYMBOL,
            'campaign_duration': f"{self.CAMPAIGN_DAYS} days",
            'monthly_target': f"${self.MONTHLY_PROFIT_TARGET:,}"
        }

# ========================================
# CONFIGURATION INSTANCE
# ========================================

# Default configuration instance
CONFIG = BulenoxStrategyConfig()

# Validate configuration on import
config_warnings = CONFIG.validate_config()
if config_warnings:
    print("Configuration Warnings:")
    for warning in config_warnings:
        print(f"  - {warning}")

# Print configuration summary
if __name__ == "__main__":
    print("\n" + "="*60)
    print("BULENOX GOLD SCALPING STRATEGY CONFIGURATION")
    print("="*60)
    
    summary = CONFIG.get_config_summary()
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\nTrading Sessions:")
    for session_name, session_config in CONFIG.TRADING_SESSIONS.items():
        print(f"  {session_config['name']}: {session_config['start']} - {session_config['end']}")
    
    print(f"\nFibonacci Profit Sequence: {CONFIG.FIBONACCI_PROFIT_SEQUENCE}")
    print(f"Risk Management: Max {CONFIG.MAX_CONSECUTIVE_LOSSES} consecutive losses")
    print(f"Volatility Adjustment: Enabled with {CONFIG.VOLATILITY_LOOKBACK_DAYS}-day lookback")
    
    print("\n✅ Configuration loaded successfully!")
    print("="*60)