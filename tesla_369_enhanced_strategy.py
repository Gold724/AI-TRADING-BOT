#!/usr/bin/env python3
"""
Enhanced Tesla 369 Gold Scalping Strategy
=========================================

Enhanced version of the original Tesla 3-6-9 Fibonacci strategy that integrates
with the new comprehensive trade plan system while maintaining full backward compatibility.

Key Enhancements:
- Advanced liquidity detection and fair value gap analysis
- Multi-timeframe trend confirmation
- Session-based validation with news guard
- Optional lunar timing optimization
- Enhanced risk management with circuit breakers
- Real-time trade plan generation and execution
- Comprehensive logging and telemetry

Maintains Original Features:
- Tesla 3-6-9 trading rhythm (3 trades per session, 3 sessions per day)
- Fibonacci profit targets [10, 10, 20, 30, 50, 80, 130]
- Daily profit target: $535.71
- Daily max drawdown: $267.00
- Gold futures (GC) contract sizing

Author: TRAE-SentinelOps
Version: 3.0.0
"""

import os
import sys
import json
import logging
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import existing strategy for inheritance
from bulenox_gold_scalping_strategy import BulenoxGoldScalpingStrategy

# Import new trade plan system
from tesla_369_integration import Tesla369StrategyIntegrator, Tesla369IntegrationConfig
from trade_plan_generator import TradePlanGenerator
from liquidity_detector import LiquidityDetector
from session_manager import SessionManager
from news_guard import NewsGuard
from lunar_calendar import LunarCalendar

# Import configuration
from bulenox_strategy_config import BulenoxStrategyConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_tesla_369.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedTradeMetrics:
    """Enhanced trade metrics with new system integration"""
    trade_id: str
    session: str
    fibonacci_target: float
    liquidity_score: float
    trend_strength: float
    news_impact: str
    lunar_factor: float
    execution_time: float
    slippage: float
    fill_quality: float

class EnhancedTesla369Strategy(BulenoxGoldScalpingStrategy):
    """
    Enhanced Tesla 369 Strategy with new trade plan system integration
    
    This class extends the original BulenoxGoldScalpingStrategy to add
    advanced features while maintaining backward compatibility.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize enhanced components
        self.integration_config = Tesla369IntegrationConfig(
            enable_tesla_rhythm=True,
            enable_liquidity_detection=True,
            enable_trend_analysis=True,
            enable_news_guard=True,
            enable_lunar_timing=True,
            enable_session_validation=True,
            fibonacci_sequence=BulenoxStrategyConfig.FIBONACCI_PROFIT_SEQUENCE,
            daily_profit_target=BulenoxStrategyConfig.DAILY_PROFIT_TARGET,
            daily_max_drawdown=BulenoxStrategyConfig.DAILY_MAX_DRAWDOWN,
            max_contracts=BulenoxStrategyConfig.MAX_CONTRACTS
        )
        
        # Initialize integration system
        self.integrator = Tesla369StrategyIntegrator(self.integration_config)
        
        # Enhanced metrics tracking
        self.enhanced_metrics = []
        self.liquidity_detector = LiquidityDetector()
        self.session_manager = SessionManager()
        self.news_guard = NewsGuard()
        self.lunar_calendar = LunarCalendar()
        
        # Enhanced state tracking
        self.current_liquidity_score = 0.0
        self.current_trend_strength = 0.0
        self.current_news_impact = "neutral"
        self.current_lunar_factor = 1.0
        
        logger.info("Enhanced Tesla 369 Strategy initialized")
        logger.info("Enhanced features: liquidity detection, trend analysis, news guard, lunar timing")
    
    def get_enhanced_market_data(self) -> Dict:
        """Collect enhanced market data for trade plan generation"""
        
        # Get basic market data from parent
        basic_data = self.get_market_snapshot()
        
        # Add enhanced data
        enhanced_data = {
            **basic_data,
            'liquidity_analysis': self.analyze_liquidity(),
            'trend_analysis': self.analyze_trend_strength(),
            'news_status': self.get_news_status(),
            'lunar_timing': self.get_lunar_recommendation(),
            'session_validation': self.validate_session_conditions(),
            'timestamp': datetime.now().isoformat()
        }
        
        return enhanced_data
    
    def analyze_liquidity(self) -> Dict:
        """Analyze liquidity conditions using new system"""
        try:
            # Get current price data
            recent_bars = self.get_recent_bars(50)
            if not recent_bars:
                return {'score': 0.5, 'fair_value_gaps': [], 'liquidity_levels': []}
            
            # Analyze liquidity
            liquidity_analysis = self.liquidity_detector.analyze_liquidity(recent_bars)
            
            return {
                'score': liquidity_analysis.liquidity_score,
                'fair_value_gaps': [
                    {'start': gap.start_price, 'end': gap.end_price, 'type': gap.gap_type}
                    for gap in liquidity_analysis.fair_value_gaps
                ],
                'liquidity_levels': [
                    {'price': level.price, 'type': level.level_type, 'strength': level.strength}
                    for level in liquidity_analysis.liquidity_levels
                ]
            }
            
        except Exception as e:
            logger.warning(f"Liquidity analysis failed: {str(e)}")
            return {'score': 0.5, 'fair_value_gaps': [], 'liquidity_levels': []}
    
    def analyze_trend_strength(self) -> Dict:
        """Analyze multi-timeframe trend strength"""
        try:
            # Get trend analysis from trade plan generator
            trend_data = self.get_trend_data()
            
            return {
                'h4_trend': trend_data.get('h4_bias', 'neutral'),
                'h1_trend': trend_data.get('h1_bias', 'neutral'),
                'm15_trend': trend_data.get('m15_bias', 'neutral'),
                'strength_score': trend_data.get('trend_strength', 0.5),
                'volatility_level': trend_data.get('volatility_level', 'normal')
            }
            
        except Exception as e:
            logger.warning(f"Trend analysis failed: {str(e)}")
            return {'h4_trend': 'neutral', 'h1_trend': 'neutral', 'm15_trend': 'neutral', 
                   'strength_score': 0.5, 'volatility_level': 'normal'}
    
    def get_news_status(self) -> Dict:
        """Get current news guard status"""
        try:
            news_status = self.news_guard.get_trading_status()
            
            return {
                'can_trade': news_status.can_trade,
                'next_event_minutes': news_status.next_event_minutes,
                'impact_level': news_status.impact_level,
                'event_description': news_status.event_description
            }
            
        except Exception as e:
            logger.warning(f"News status check failed: {str(e)}")
            return {'can_trade': True, 'next_event_minutes': 999, 'impact_level': 'low', 'event_description': 'No events'}
    
    def get_lunar_recommendation(self) -> Dict:
        """Get lunar timing recommendation"""
        try:
            if not self.integration_config.enable_lunar_timing:
                return {'enabled': False, 'factor': 1.0, 'recommendation': 'neutral'}
            
            lunar_rec = self.lunar_calendar.get_recommendation()
            
            return {
                'enabled': True,
                'factor': lunar_rec.risk_adjustment,
                'recommendation': lunar_rec.trading_recommendation,
                'phase': lunar_rec.moon_phase,
                'volatility_expectation': lunar_rec.volatility_expectation
            }
            
        except Exception as e:
            logger.warning(f"Lunar recommendation failed: {str(e)}")
            return {'enabled': False, 'factor': 1.0, 'recommendation': 'neutral'}
    
    def validate_session_conditions(self) -> Dict:
        """Validate all session-based trading conditions"""
        try:
            validation = self.integrator.validate_session_rules()
            
            return {
                'session_valid': validation['within_session'],
                'session_limit_ok': validation['session_limit_ok'],
                'daily_limit_ok': validation['daily_limit_ok'],
                'news_clear': validation['news_clear'],
                'lunar_favorable': validation['lunar_favorable'],
                'overall_valid': all(validation.values())
            }
            
        except Exception as e:
            logger.warning(f"Session validation failed: {str(e)}")
            return {'session_valid': True, 'session_limit_ok': True, 'daily_limit_ok': True,
                   'news_clear': True, 'lunar_favorable': True, 'overall_valid': True}
    
    def generate_enhanced_trade_signal(self) -> Optional[Dict]:
        """Generate enhanced trade signal using new system"""
        
        # Get enhanced market data
        market_data = self.get_enhanced_market_data()
        
        # Check if all conditions are met
        if not market_data['session_validation']['overall_valid']:
            return None
        
        # Generate trade plan
        trade_plan = self.integrator.generate_enhanced_trade_plan(market_data)
        
        if not trade_plan:
            return None
        
        # Create enhanced signal
        signal = {
            'action': trade_plan['context']['bias'],
            'entry_price': trade_plan['entries'][0]['price'],
            'take_profit': trade_plan['entries'][0]['take_profit'],
            'stop_loss': trade_plan['entries'][0]['stop_loss'],
            'contracts': min(trade_plan['risk']['max_contracts'], self.config.max_contracts),
            'confidence': self.calculate_confidence_score(market_data),
            'enhanced_data': market_data,
            'trade_plan': trade_plan
        }
        
        return signal
    
    def calculate_confidence_score(self, market_data: Dict) -> float:
        """Calculate trade confidence score based on enhanced analysis"""
        
        weights = {
            'liquidity': 0.25,
            'trend': 0.25,
            'news': 0.20,
            'lunar': 0.15,
            'session': 0.15
        }
        
        # Liquidity score (0-1)
        liquidity_score = market_data['liquidity_analysis']['score']
        
        # Trend score (0-1)
        trend_score = market_data['trend_analysis']['strength_score']
        
        # News score (0-1)
        news_score = 1.0 if market_data['news_status']['can_trade'] else 0.0
        
        # Lunar score (0-1)
        lunar_factor = market_data['lunar_timing']['factor'] if market_data['lunar_timing']['enabled'] else 1.0
        lunar_score = (lunar_factor - 0.5) * 2  # Normalize to 0-1
        
        # Session score (0-1)
        session_score = 1.0 if market_data['session_validation']['overall_valid'] else 0.0
        
        # Calculate weighted confidence
        confidence = (
            liquidity_score * weights['liquidity'] +
            trend_score * weights['trend'] +
            news_score * weights['news'] +
            lunar_score * weights['lunar'] +
            session_score * weights['session']
        )
        
        return min(max(confidence, 0.0), 1.0)
    
    def execute_enhanced_trade(self, signal: Dict) -> Dict:
        """Execute trade with enhanced monitoring"""
        
        start_time = datetime.now()
        
        try:
            # Execute through parent strategy (maintains proven execution)
            parent_result = super().ExecuteTrade(
                is_long=signal['action'] == 'long',
                entry_price=signal['entry_price'],
                is_high_confidence=signal['confidence'] > 0.8
            )
            
            # Execute through integration system
            integration_result = self.integrator.execute_integrated_trade(signal['trade_plan'])
            
            # Calculate execution metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create enhanced metrics
            metrics = EnhancedTradeMetrics(
                trade_id=integration_result.get('trade_id', 'unknown'),
                session=self.get_current_session(),
                fibonacci_target=signal['trade_plan']['tesla_metadata']['fibonacci_target'],
                liquidity_score=signal['enhanced_data']['liquidity_analysis']['score'],
                trend_strength=signal['enhanced_data']['trend_analysis']['strength_score'],
                news_impact=signal['enhanced_data']['news_status']['impact_level'],
                lunar_factor=signal['enhanced_data']['lunar_timing']['factor'],
                execution_time=execution_time,
                slippage=abs(parent_result.get('fill_price', signal['entry_price']) - signal['entry_price']),
                fill_quality=parent_result.get('fill_quality', 0.5)
            )
            
            self.enhanced_metrics.append(asdict(metrics))
            
            return {
                'parent_result': parent_result,
                'integration_result': integration_result,
                'enhanced_metrics': asdict(metrics),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Enhanced trade execution failed: {str(e)}")
            return {'error': str(e), 'success': False, 'timestamp': datetime.now().isoformat()}
    
    def get_market_snapshot(self) -> Dict:
        """Get basic market snapshot (placeholder - implement based on your data source)"""
        return {
            'symbol': 'GC',
            'current_price': 2400.0,
            'volume': 1000,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_trend_data(self) -> Dict:
        """Get trend data (placeholder - implement based on your data source)"""
        return {
            'h4_bias': 'bullish',
            'h1_bias': 'bullish',
            'm15_bias': 'bullish',
            'trend_strength': 0.8,
            'volatility_level': 'normal'
    }
    
    def get_recent_bars(self, count: int) -> List[Dict]:
        """Get recent price bars (placeholder - implement based on your data source)"""
        return []
    
    def get_enhanced_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        
        # Get parent strategy summary
        parent_summary = self.get_performance_summary()
        
        # Add enhanced metrics
        enhanced_summary = {
            **parent_summary,
            'enhanced_features': {
                'liquidity_detection_enabled': self.integration_config.enable_liquidity_detection,
                'trend_analysis_enabled': self.integration_config.enable_trend_analysis,
                'news_guard_enabled': self.integration_config.enable_news_guard,
                'lunar_timing_enabled': self.integration_config.enable_lunar_timing,
                'session_validation_enabled': self.integration_config.enable_session_validation
            },
            'enhanced_metrics': {
                'total_enhanced_trades': len(self.enhanced_metrics),
                'average_confidence_score': sum(m['confidence'] for m in self.enhanced_metrics) / len(self.enhanced_metrics) if self.enhanced_metrics else 0,
                'average_liquidity_score': sum(m['liquidity_score'] for m in self.enhanced_metrics) / len(self.enhanced_metrics) if self.enhanced_metrics else 0,
                'average_trend_strength': sum(m['trend_strength'] for m in self.enhanced_metrics) / len(self.enhanced_metrics) if self.enhanced_metrics else 0,
                'average_execution_time': sum(m['execution_time'] for m in self.enhanced_metrics) / len(self.enhanced_metrics) if self.enhanced_metrics else 0,
                'average_slippage': sum(m['slippage'] for m in self.enhanced_metrics) / len(self.enhanced_metrics) if self.enhanced_metrics else 0
            },
            'integration_status': self.integrator.get_integration_summary()
        }
        
        return enhanced_summary
    
    def save_enhanced_state(self, filepath: str = None):
        """Save enhanced strategy state"""
        if filepath is None:
            filepath = Path(__file__).parent / "enhanced_tesla_369_state.json"
        
        state = {
            'performance_summary': self.get_enhanced_performance_summary(),
            'enhanced_metrics': self.enhanced_metrics,
            'integration_config': asdict(self.integration_config),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Enhanced strategy state saved to {filepath}")

# Usage example and testing
if __name__ == "__main__":
    # Test enhanced strategy
    strategy = EnhancedTesla369Strategy()
    
    # Generate enhanced trade signal
    signal = strategy.generate_enhanced_trade_signal()
    
    if signal:
        print("=== Enhanced Trade Signal ===")
        print(json.dumps(signal, indent=2))
        
        # Execute enhanced trade
        result = strategy.execute_enhanced_trade(signal)
        print("\n=== Trade Execution Result ===")
        print(json.dumps(result, indent=2))
    else:
        print("No trade signal generated - conditions not met")
    
    # Get performance summary
    summary = strategy.get_enhanced_performance_summary()
    print("\n=== Enhanced Performance Summary ===")
    print(json.dumps(summary, indent=2))
    
    # Save state
    strategy.save_enhanced_state()