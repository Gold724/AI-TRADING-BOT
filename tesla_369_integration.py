#!/usr/bin/env python3
"""
Tesla 369 + Fibonacci Strategy Integration
=========================================

Complete integration bridge between:
1. Existing Tesla 3-6-9 Fibonacci strategy (bulenox_gold_scalping_strategy.py)
2. New comprehensive trade plan system (trade_plan_executor.py)

This integration maintains the proven Tesla 3-6-9 rhythm while incorporating:
- Advanced liquidity detection
- Multi-timeframe trend analysis
- Session-based validation
- News guard protection
- Lunar timing optimization
- Enhanced risk management

Author: TRAE-SentinelOps
Version: 3.0.0
"""

import json
import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Import existing strategy components
from bulenox_gold_scalping_strategy import BulenoxGoldScalpingStrategy
from bulenox_strategy_config import BulenoxStrategyConfig

# Import new trade plan system
from trade_plan_executor import TradePlanExecutor
from trade_plan_generator import TradePlanGenerator
from liquidity_detector import LiquidityDetector
from session_manager import SessionManager
from news_guard import NewsGuard
from lunar_calendar import LunarCalendar

@dataclass
class Tesla369IntegrationConfig:
    """Configuration for Tesla 369 integration"""
    
    # Tesla 3-6-9 core parameters
    enable_tesla_rhythm: bool = True
    trades_per_session: int = 3
    sessions_per_day: int = 3
    max_trades_per_day: int = 9
    
    # Fibonacci profit targets
    fibonacci_sequence: List[float] = None
    
    # Integration switches
    enable_liquidity_detection: bool = True
    enable_trend_analysis: bool = True
    enable_news_guard: bool = True
    enable_lunar_timing: bool = True
    enable_session_validation: bool = True
    
    # Risk parameters
    daily_profit_target: float = 535.71
    daily_max_drawdown: float = 267.0
    max_contracts: int = 3
    
    def __post_init__(self):
        if self.fibonacci_sequence is None:
            self.fibonacci_sequence = [10.0, 10.0, 20.0, 30.0, 50.0, 80.0, 130.0]

class Tesla369StrategyIntegrator:
    """
    Main integration class that synchronizes Tesla 3-6-9 strategy with new trade plan system
    """
    
    def __init__(self, config: Tesla369IntegrationConfig = None):
        self.config = config or Tesla369IntegrationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize existing strategy
        self.existing_strategy = BulenoxGoldScalpingStrategy()
        self.strategy_config = BulenoxStrategyConfig()
        
        # Initialize new components
        self.trade_executor = TradePlanExecutor()
        self.plan_generator = TradePlanGenerator()
        self.liquidity_detector = LiquidityDetector()
        self.session_manager = SessionManager()
        self.news_guard = NewsGuard()
        self.lunar_calendar = LunarCalendar()
        
        # Integration state
        self.current_session = None
        self.session_trade_count = 0
        self.daily_trade_count = 0
        self.fibonacci_index = 0
        self.integration_log = []
        
        self.logger.info("Tesla 369 Strategy Integrator initialized")
    
    def get_current_session(self) -> str:
        """Get current trading session based on time"""
        now = datetime.now().time()
        
        sessions = {
            'morning': (dt_time(3, 0), dt_time(6, 0)),
            'midday': (dt_time(8, 20), dt_time(11, 30)),
            'afternoon': (dt_time(13, 0), dt_time(15, 30))
        }
        
        for session_name, (start, end) in sessions.items():
            if start <= now <= end:
                return session_name
        
        return 'outside_session'
    
    def validate_session_rules(self) -> Dict[str, bool]:
        """Validate all session-based rules"""
        validation = {
            'within_session': False,
            'session_limit_ok': False,
            'daily_limit_ok': False,
            'news_clear': False,
            'lunar_favorable': True  # Default to True if disabled
        }
        
        # Check current session
        current_session = self.get_current_session()
        validation['within_session'] = current_session != 'outside_session'
        
        # Check session trade limits
        validation['session_limit_ok'] = self.session_trade_count < self.config.trades_per_session
        
        # Check daily trade limits
        validation['daily_limit_ok'] = self.daily_trade_count < self.config.max_trades_per_day
        
        # Check news guard
        if self.config.enable_news_guard:
            news_status = self.news_guard.get_trading_status()
            validation['news_clear'] = news_status.can_trade
        
        # Check lunar timing
        if self.config.enable_lunar_timing:
            lunar_recommendation = self.lunar_calendar.get_recommendation()
            validation['lunar_favorable'] = lunar_recommendation.risk_adjustment >= 0.9
        
        return validation
    
    def generate_enhanced_trade_plan(self, market_data: Dict) -> Dict:
        """Generate trade plan using new system with Tesla 369 constraints"""
        
        # Validate session rules
        validation = self.validate_session_rules()
        if not all(validation.values()):
            self.logger.warning(f"Trade validation failed: {validation}")
            return None
        
        # Generate comprehensive trade plan
        trade_plan = self.plan_generator.generate_trade_plan(market_data)
        
        if not trade_plan:
            return None
        
        # Apply Tesla 369 constraints
        enhanced_plan = self.apply_tesla_constraints(trade_plan)
        
        return enhanced_plan
    
    def apply_tesla_constraints(self, trade_plan: Dict) -> Dict:
        """Apply Tesla 3-6-9 constraints to trade plan"""
        
        # Get current Fibonacci target
        fib_target = self.config.fibonacci_sequence[
            min(self.fibonacci_index, len(self.config.fibonacci_sequence) - 1)
        ]
        
        # Override risk parameters with Tesla constraints
        trade_plan['risk'] = {
            'daily_profit_target': self.config.daily_profit_target,
            'daily_max_drawdown': self.config.daily_max_drawdown,
            'per_trade_risk': fib_target,
            'max_contracts': self.config.max_contracts,
            'circuit_breaker_enabled': True
        }
        
        # Override entries with Tesla-specific logic
        for entry in trade_plan.get('entries', []):
            entry['target_profit'] = fib_target
            entry['max_contracts'] = self.config.max_contracts
            entry['session_constraint'] = 'tesla_369'
        
        # Add Tesla metadata
        trade_plan['tesla_metadata'] = {
            'session': self.get_current_session(),
            'session_trade': self.session_trade_count + 1,
            'daily_trade': self.daily_trade_count + 1,
            'fibonacci_target': fib_target,
            'fibonacci_index': self.fibonacci_index
        }
        
        return trade_plan
    
    def execute_integrated_trade(self, trade_plan: Dict) -> Dict:
        """Execute trade using both existing and new systems"""
        
        try:
            # Log integration details
            self.logger.info(f"Executing Tesla 369 trade - Session: {trade_plan['tesla_metadata']['session']}")
            self.logger.info(f"Fibonacci target: ${trade_plan['tesla_metadata']['fibonacci_target']}")
            
            # Execute through existing strategy (maintains proven execution)
            execution_result = self.existing_strategy.execute_trade(trade_plan)
            
            # Execute through new system (adds enhanced monitoring)
            new_system_result = self.trade_executor.execute_trade_plan(trade_plan)
            
            # Update counters
            self.session_trade_count += 1
            self.daily_trade_count += 1
            self.fibonacci_index += 1
            
            # Log results
            result = {
                'timestamp': datetime.now().isoformat(),
                'trade_plan': trade_plan,
                'execution_result': execution_result,
                'new_system_result': new_system_result,
                'session_trade_count': self.session_trade_count,
                'daily_trade_count': self.daily_trade_count,
                'fibonacci_index': self.fibonacci_index
            }
            
            self.integration_log.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Trade execution failed: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def reset_session_counters(self):
        """Reset session-specific counters"""
        self.session_trade_count = 0
        self.current_session = self.get_current_session()
        self.logger.info(f"Session reset - New session: {self.current_session}")
    
    def reset_daily_counters(self):
        """Reset daily counters"""
        self.daily_trade_count = 0
        self.fibonacci_index = 0
        self.session_trade_count = 0
        self.integration_log.clear()
        self.logger.info("Daily counters reset")
    
    def get_integration_summary(self) -> Dict:
        """Get summary of integration performance"""
        return {
            'current_session': self.get_current_session(),
            'session_trades': self.session_trade_count,
            'daily_trades': self.daily_trade_count,
            'current_fibonacci_target': self.config.fibonacci_sequence[
                min(self.fibonacci_index, len(self.config.fibonacci_sequence) - 1)
            ],
            'fibonacci_progress': f"{self.fibonacci_index}/{len(self.config.fibonacci_sequence)}",
            'total_trades_today': len(self.integration_log),
            'integration_enabled': {
                'tesla_rhythm': self.config.enable_tesla_rhythm,
                'liquidity_detection': self.config.enable_liquidity_detection,
                'trend_analysis': self.config.enable_trend_analysis,
                'news_guard': self.config.enable_news_guard,
                'lunar_timing': self.config.enable_lunar_timing,
                'session_validation': self.config.enable_session_validation
            }
        }
    
    def save_integration_state(self, filepath: str = None):
        """Save current integration state to file"""
        if filepath is None:
            filepath = Path(__file__).parent / "tesla_369_integration_state.json"
        
        state = {
            'config': asdict(self.config),
            'summary': self.get_integration_summary(),
            'integration_log': self.integration_log,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"Integration state saved to {filepath}")
    
    def load_integration_state(self, filepath: str = None):
        """Load integration state from file"""
        if filepath is None:
            filepath = Path(__file__).parent / "tesla_369_integration_state.json"
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Restore counters
            self.daily_trade_count = state['summary']['daily_trades']
            self.session_trade_count = state['summary']['session_trades']
            self.fibonacci_index = int(state['summary']['fibonacci_progress'].split('/')[0])
            
            self.logger.info(f"Integration state loaded from {filepath}")
            
        except Exception as e:
            self.logger.warning(f"Could not load integration state: {str(e)}")

# Integration bridge for existing strategy
class Tesla369Bridge:
    """
    Bridge class to integrate Tesla 369 strategy with new trade plan system
    without modifying existing strategy files
    """
    
    def __init__(self, integrator: Tesla369StrategyIntegrator):
        self.integrator = integrator
        self.logger = logging.getLogger(__name__)
    
    def wrap_existing_strategy(self, market_data: Dict) -> Dict:
        """Wrap existing strategy execution with new system enhancements"""
        
        # Generate enhanced trade plan
        trade_plan = self.integrator.generate_enhanced_trade_plan(market_data)
        
        if trade_plan:
            # Execute integrated trade
            result = self.integrator.execute_integrated_trade(trade_plan)
            return result
        
        return {'status': 'no_trade', 'reason': 'validation_failed'}
    
    def get_real_time_status(self) -> Dict:
        """Get real-time integration status"""
        return {
            'integration': self.integrator.get_integration_summary(),
            'market_conditions': {
                'current_session': self.integrator.get_current_session(),
                'session_validation': self.integrator.validate_session_rules(),
                'news_status': self.integrator.news_guard.get_trading_status() if self.integrator.config.enable_news_guard else None,
                'lunar_recommendation': self.integrator.lunar_calendar.get_recommendation() if self.integrator.config.enable_lunar_timing else None
            }
        }

# Usage example and initialization
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create integration config
    config = Tesla369IntegrationConfig(
        enable_tesla_rhythm=True,
        enable_liquidity_detection=True,
        enable_trend_analysis=True,
        enable_news_guard=True,
        enable_lunar_timing=True,
        enable_session_validation=True
    )
    
    # Initialize integrator
    integrator = Tesla369StrategyIntegrator(config)
    bridge = Tesla369Bridge(integrator)
    
    # Example market data
    market_data = {
        'symbol': 'GC',
        'current_price': 2400.0,
        'volume': 1000,
        'session': 'morning',
        'timestamp': datetime.now().isoformat()
    }
    
    # Test integration
    print("=== Tesla 369 Integration Test ===")
    status = bridge.get_real_time_status()
    print(json.dumps(status, indent=2))
    
    # Save state
    integrator.save_integration_state()