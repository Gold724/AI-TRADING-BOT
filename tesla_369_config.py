#!/usr/bin/env python3
"""
Tesla 369 Enhanced Strategy Configuration
=======================================

Comprehensive configuration for the enhanced Tesla 369 strategy integration.
This file provides easy-to-tune parameters for all enhanced features.

Author: TRAE-SentinelOps
Version: 3.0.0
"""

from datetime import time
from typing import Dict, List, Tuple
import json

class Tesla369EnhancedConfig:
    """
    Configuration class for enhanced Tesla 369 strategy.
    
    This class provides centralized configuration for:
    - Tesla 3-6-9 core parameters
    - Enhanced feature toggles
    - Risk management settings
    - Integration parameters
    - Performance tuning options
    """
    
    # ========================================
    # TESLA 3-6-9 CORE PARAMETERS
    # ========================================
    
    # Tesla Rhythm Configuration
    TRADES_PER_SESSION = 3
    SESSIONS_PER_DAY = 3
    MAX_TRADES_PER_DAY = TRADES_PER_SESSION * SESSIONS_PER_DAY  # 9 trades max
    
    # Fibonacci Profit Sequence (USD)
    FIBONACCI_SEQUENCE = [10.0, 10.0, 20.0, 30.0, 50.0, 80.0, 130.0]
    
    # Daily Targets (Doubled for enhanced performance)
    DAILY_PROFIT_TARGET = 1071.42  # $30,000 in 28 days (doubled from $15,000)
    DAILY_MAX_DRAWDOWN = 535.71   # 50% of daily profit target
    
    # Position Sizing
    DEFAULT_CONTRACTS = 1
    MAX_CONTRACTS = 3
    MIN_CONTRACTS = 1
    
    # ========================================
    # ENHANCED FEATURE TOGGLES
    # ========================================
    
    # Feature Enable/Disable Flags
    ENABLE_LIQUIDITY_DETECTION = True
    ENABLE_TREND_ANALYSIS = True
    ENABLE_NEWS_GUARD = True
    ENABLE_LUNAR_TIMING = True
    ENABLE_SESSION_VALIDATION = True
    ENABLE_ADVANCED_RISK = True
    
    # ========================================
    # LIQUIDITY DETECTION CONFIG
    # ========================================
    
    # Liquidity Analysis Parameters
    LIQUIDITY_LOOKBACK_BARS = 50
    LIQUIDITY_THRESHOLD = 0.7
    MIN_LIQUIDITY_SCORE = 0.5
    
    # Fair Value Gap Parameters
    FVG_MIN_SIZE = 0.001  # Minimum 0.1% price gap
    FVG_MAX_AGE = 30      # Maximum 30 minutes old
    
    # Order Block Parameters
    OB_MIN_STRENGTH = 0.6
    OB_LOOKBACK = 20
    
    # ========================================
    # TREND ANALYSIS CONFIG
    # ========================================
    
    # Timeframe Configuration
    H4_LOOKBACK = 200
    H1_LOOKBACK = 100
    M15_LOOKBACK = 50
    M5_LOOKBACK = 20
    
    # Trend Strength Thresholds
    STRONG_TREND_THRESHOLD = 0.7
    MODERATE_TREND_THRESHOLD = 0.4
    WEAK_TREND_THRESHOLD = 0.2
    
    # Volatility Thresholds
    HIGH_VOLATILITY_MULTIPLIER = 1.5
    LOW_VOLATILITY_MULTIPLIER = 0.7
    
    # ========================================
    # NEWS GUARD CONFIG
    # ========================================
    
    # News Impact Thresholds
    HIGH_IMPACT_PAUSE_MINUTES = 15
    MEDIUM_IMPACT_PAUSE_MINUTES = 10
    LOW_IMPACT_PAUSE_MINUTES = 5
    
    # Pre/Post Event Restrictions
    PRE_EVENT_RESTRICTION_MINUTES = 5
    POST_EVENT_RESTRICTION_MINUTES = 5
    
    # ========================================
    # LUNAR TIMING CONFIG
    # ========================================
    
    # Lunar Phase Impact
    NEW_MOON_VOLATILITY_BOOST = 1.2
    FULL_MOON_VOLATILITY_BOOST = 1.3
    QUARTER_MOON_NEUTRAL = 1.0
    
    # Risk Adjustment Factors
    LUNAR_RISK_INCREASE = 0.1  # 10% risk increase during high volatility
    LUNAR_RISK_DECREASE = -0.05  # 5% risk decrease during favorable phases
    
    # ========================================
    # TRADING SESSIONS (NY TIME)
    # ========================================
    
    TRADING_SESSIONS = {
        'morning': {
            'start': time(3, 0),
            'end': time(6, 0),
            'name': 'Asian Close / London Open',
            'description': 'High liquidity, moderate volatility',
            'preferred_contracts': 1,
            'max_trades': 3
        },
        'midday': {
            'start': time(8, 20),
            'end': time(11, 30),
            'name': 'US Pre-Market / London Close',
            'description': 'High volatility, good liquidity',
            'preferred_contracts': 2,
            'max_trades': 3
        },
        'afternoon': {
            'start': time(13, 0),
            'end': time(15, 30),
            'name': 'US Session',
            'description': 'Peak volatility and volume',
            'preferred_contracts': 3,
            'max_trades': 3
        }
    }
    
    # ========================================
    # RISK MANAGEMENT CONFIG
    # ========================================
    
    # Circuit Breaker Parameters
    CIRCUIT_BREAKER_ENABLED = True
    MAX_CONSECUTIVE_LOSSES = 3
    MAX_DAILY_LOSSES = 5
    
    # Position Sizing Rules
    HIGH_CONFIDENCE_MULTIPLIER = 1.5
    LOW_CONFIDENCE_MULTIPLIER = 0.5
    
    # Stop Loss Parameters
    BASE_STOP_LOSS_PERCENT = 0.02  # 2%
    DYNAMIC_STOP_ENABLED = True
    TRAILING_STOP_ENABLED = True
    TRAILING_STOP_ACTIVATION = 0.5  # Activate at 50% profit
    TRAILING_STOP_DISTANCE = 0.01  # 1% trailing distance
    TRAILING_STOP_INCREMENT = 0.005  # 0.5% increment steps
    TAKE_PROFIT_LOCK_IN = 0.3  # Lock in 30% of profit when trailing starts
    
    # ========================================
    # INTEGRATION CONFIG
    # ========================================
    
    # Integration Parameters
    BACKWARD_COMPATIBILITY = True
    ENHANCED_LOGGING = True
    REAL_TIME_MONITORING = True
    STATE_PERSISTENCE = True
    
    # Performance Tuning
    LOG_LEVEL = "INFO"
    METRICS_RETENTION_DAYS = 30
    MAX_LOG_FILE_SIZE_MB = 100
    
    # ========================================
    # SYMBOL CONFIGURATION
    # ========================================
    
    # Gold Futures Configuration
    SYMBOL = "GC"
    FULL_SYMBOL = "F.US.GCE"
    CONTRACT_SIZE = 100  # $100 per point
    MIN_TICK_SIZE = 0.1  # $10 per tick
    
    # ========================================
    # PERFORMANCE MONITORING
    # ========================================
    
    # Performance Thresholds
    MAX_EXECUTION_TIME_SECONDS = 2.0
    MAX_SLIPPAGE_POINTS = 0.5
    MIN_FILL_QUALITY = 0.8
    
    # Alert Thresholds
    HIGH_LATENCY_ALERT = 1.0
    HIGH_SLIPPAGE_ALERT = 1.0
    LOW_LIQUIDITY_ALERT = 0.3
    
    # ========================================
    # METHODS
    # ========================================
    
    @classmethod
    def get_session_config(cls, session_name: str) -> Dict:
        """Get configuration for specific trading session"""
        return cls.TRADING_SESSIONS.get(session_name, {})
    
    @classmethod
    def get_fibonacci_target(cls, index: int) -> float:
        """Get Fibonacci target for given index"""
        if index < 0 or index >= len(cls.FIBONACCI_SEQUENCE):
            return cls.FIBONACCI_SEQUENCE[-1]
        return cls.FIBONACCI_SEQUENCE[index]
    
    @classmethod
    def get_risk_adjusted_contracts(cls, base_contracts: int, confidence: float, 
                                  lunar_factor: float = 1.0) -> int:
        """Calculate risk-adjusted contract size"""
        
        # Apply confidence adjustment
        if confidence >= 0.8:
            adjusted = base_contracts * cls.HIGH_CONFIDENCE_MULTIPLIER
        elif confidence <= 0.3:
            adjusted = base_contracts * cls.LOW_CONFIDENCE_MULTIPLIER
        else:
            adjusted = base_contracts
        
        # Apply lunar adjustment
        adjusted *= lunar_factor
        
        # Ensure within limits
        return max(cls.MIN_CONTRACTS, min(int(adjusted), cls.MAX_CONTRACTS))
    
    @classmethod
    def validate_configuration(cls) -> Dict[str, bool]:
        """Validate configuration parameters"""
        
        validation = {
            'fibonacci_sequence_valid': len(cls.FIBONACCI_SEQUENCE) > 0,
            'daily_targets_valid': cls.DAILY_PROFIT_TARGET > 0 and cls.DAILY_MAX_DRAWDOWN > 0,
            'position_limits_valid': cls.MIN_CONTRACTS <= cls.DEFAULT_CONTRACTS <= cls.MAX_CONTRACTS,
            'session_times_valid': all(
                session['start'] < session['end'] 
                for session in cls.TRADING_SESSIONS.values()
            ),
            'risk_parameters_valid': cls.BASE_STOP_LOSS_PERCENT > 0,
            'feature_flags_valid': True  # All boolean flags are valid
        }
        
        return validation
    
    @classmethod
    def export_configuration(cls, filepath: str = None) -> str:
        """Export configuration to JSON file"""
        
        if filepath is None:
            filepath = "tesla_369_config.json"
        
        config_dict = {
            'tesla_369_core': {
                'trades_per_session': cls.TRADES_PER_SESSION,
                'sessions_per_day': cls.SESSIONS_PER_DAY,
                'max_trades_per_day': cls.MAX_TRADES_PER_DAY,
                'fibonacci_sequence': cls.FIBONACCI_SEQUENCE,
                'daily_profit_target': cls.DAILY_PROFIT_TARGET,
                'daily_max_drawdown': cls.DAILY_MAX_DRAWDOWN
            },
            'enhanced_features': {
                'liquidity_detection': cls.ENABLE_LIQUIDITY_DETECTION,
                'trend_analysis': cls.ENABLE_TREND_ANALYSIS,
                'news_guard': cls.ENABLE_NEWS_GUARD,
                'lunar_timing': cls.ENABLE_LUNAR_TIMING,
                'session_validation': cls.ENABLE_SESSION_VALIDATION,
                'advanced_risk': cls.ENABLE_ADVANCED_RISK
            },
            'risk_management': {
                'max_consecutive_losses': cls.MAX_CONSECUTIVE_LOSSES,
                'max_daily_losses': cls.MAX_DAILY_LOSSES,
                'base_stop_loss_percent': cls.BASE_STOP_LOSS_PERCENT,
                'trailing_stop_enabled': cls.TRAILING_STOP_ENABLED
            },
            'trading_sessions': cls.TRADING_SESSIONS,
            'symbol_config': {
                'symbol': cls.SYMBOL,
                'full_symbol': cls.FULL_SYMBOL,
                'contract_size': cls.CONTRACT_SIZE,
                'min_tick_size': cls.MIN_TICK_SIZE
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        return filepath
    
    @classmethod
    def load_configuration(cls, filepath: str) -> Dict:
        """Load configuration from JSON file"""
        
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            return config
            
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {str(e)}")
    
    @classmethod
    def print_configuration_summary(cls):
        """Print configuration summary"""
        
        print("=== Tesla 369 Enhanced Configuration ===")
        print(f"Tesla Rhythm: {cls.TRADES_PER_SESSION} trades × {cls.SESSIONS_PER_DAY} sessions = {cls.MAX_TRADES_PER_DAY} max trades/day")
        print(f"Fibonacci Sequence: {cls.FIBONACCI_SEQUENCE}")
        print(f"Daily Targets: ${cls.DAILY_PROFIT_TARGET} profit, ${cls.DAILY_MAX_DRAWDOWN} max loss")
        print(f"Position Sizing: {cls.MIN_CONTRACTS}-{cls.MAX_CONTRACTS} contracts")
        print(f"Symbol: {cls.SYMBOL} ({cls.FULL_SYMBOL})")
        print()
        
        print("Enhanced Features:")
        print(f"  Liquidity Detection: {cls.ENABLE_LIQUIDITY_DETECTION}")
        print(f"  Trend Analysis: {cls.ENABLE_TREND_ANALYSIS}")
        print(f"  News Guard: {cls.ENABLE_NEWS_GUARD}")
        print(f"  Lunar Timing: {cls.ENABLE_LUNAR_TIMING}")
        print(f"  Session Validation: {cls.ENABLE_SESSION_VALIDATION}")
        print()
        
        print("Trading Sessions:")
        for name, session in cls.TRADING_SESSIONS.items():
            print(f"  {name.title()}: {session['start'].strftime('%H:%M')}-{session['end'].strftime('%H:%M')} - {session['description']}")

# Configuration presets for different risk profiles
class Tesla369Presets:
    """Configuration presets for different risk profiles"""
    
    @classmethod
    def conservative(cls) -> Tesla369EnhancedConfig:
        """Conservative risk profile preset"""
        
        config = Tesla369EnhancedConfig()
        config.FIBONACCI_SEQUENCE = [5, 5, 10, 15, 25, 40, 65]
        config.DAILY_PROFIT_TARGET = 267.86  # Half of aggressive
        config.DAILY_MAX_DRAWDOWN = 133.93  # Half of aggressive
        config.MAX_CONTRACTS = 2
        config.HIGH_CONFIDENCE_MULTIPLIER = 1.2
        config.LOW_CONFIDENCE_MULTIPLIER = 0.7
        
        return config
    
    @classmethod
    def aggressive(cls) -> Tesla369EnhancedConfig:
        """Aggressive risk profile preset"""
        
        config = Tesla369EnhancedConfig()
        config.FIBONACCI_SEQUENCE = [15, 15, 30, 45, 75, 120, 195]
        config.DAILY_PROFIT_TARGET = 1071.43  # Double of conservative
        config.DAILY_MAX_DRAWDOWN = 535.71  # Double of conservative
        config.MAX_CONTRACTS = 5
        config.HIGH_CONFIDENCE_MULTIPLIER = 2.0
        config.LOW_CONFIDENCE_MULTIPLIER = 0.8
        
        return config
    
    @classmethod
    def paper_trading(cls) -> Tesla369EnhancedConfig:
        """Paper trading preset (safe for testing)"""
        
        config = Tesla369EnhancedConfig()
        config.FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13]
        config.DAILY_PROFIT_TARGET = 100.0
        config.DAILY_MAX_DRAWDOWN = 50.0
        config.MAX_CONTRACTS = 1
        config.DEFAULT_CONTRACTS = 1
        
        return config

if __name__ == "__main__":
    # Test configuration
    config = Tesla369EnhancedConfig()
    config.print_configuration_summary()
    
    # Export configuration
    config_file = config.export_configuration()
    print(f"\nConfiguration exported to: {config_file}")
    
    # Test presets
    print("\n=== Configuration Presets ===")
    
    conservative = Tesla369Presets.conservative()
    print(f"\nConservative Preset:")
    print(f"  Daily Target: ${conservative.DAILY_PROFIT_TARGET}")
    print(f"  Fibonacci Sequence: {conservative.FIBONACCI_SEQUENCE}")
    
    aggressive = Tesla369Presets.aggressive()
    print(f"\nAggressive Preset:")
    print(f"  Daily Target: ${aggressive.DAILY_PROFIT_TARGET}")
    print(f"  Fibonacci Sequence: {aggressive.FIBONACCI_SEQUENCE}")
    
    paper = Tesla369Presets.paper_trading()
    print(f"\nPaper Trading Preset:")
    print(f"  Daily Target: ${paper.DAILY_PROFIT_TARGET}")
    print(f"  Fibonacci Sequence: {paper.FIBONACCI_SEQUENCE}")
    
    # Validate configuration
    validation = config.validate_configuration()
    print(f"\nConfiguration Validation: {validation}")