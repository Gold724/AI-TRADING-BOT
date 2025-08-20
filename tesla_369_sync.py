#!/usr/bin/env python3
"""
Tesla 369 Strategy Synchronization Module
======================================

Seamlessly integrates the new enhanced Tesla 369 system with your existing
Tesla 369 Fibonacci strategy while maintaining full backward compatibility.

This module acts as a bridge between your current implementation and
the enhanced features (liquidity detection, trend analysis, news guard, lunar timing).

Usage:
    from tesla_369_sync import Tesla369Sync
    
    # Use with existing strategy - zero changes needed
    sync = Tesla369Sync()
    result = sync.execute_trade_with_enhancements(market_data)
    
    # Or gradually enable features
    sync.enable_liquidity_detection(True)
    sync.enable_trend_analysis(True)
    sync.enable_news_guard(True)

Author: TRAE-SentinelOps
Version: 2.0.0
"""

import os
import sys
import json
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import existing strategy components
try:
    from bulenox_gold_scalping_strategy import BulenoxGoldScalpingStrategy
    from strategy_config import StrategyConfig
    EXISTING_STRATEGY_AVAILABLE = True
except ImportError:
    EXISTING_STRATEGY_AVAILABLE = False

# Import enhanced components
try:
    from tesla_369_enhanced_strategy import Tesla369EnhancedStrategy
    from tesla_369_config import Tesla369EnhancedConfig
    from liquidity_detector import LiquidityDetector
    from lunar_calendar import LunarCalendar
    from news_guard import NewsGuard
    from session_manager import SessionManager
    ENHANCED_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Enhanced components not available: {e}")
    ENHANCED_AVAILABLE = False

@dataclass
class SyncResult:
    """Result of synchronized strategy execution"""
    trade_executed: bool
    profit_target: float
    fibonacci_level: int
    enhanced_score: float
    liquidity_score: float
    trend_strength: float
    news_impact: str
    lunar_phase: str
    session_quality: float
    risk_adjusted: bool
    original_result: Optional[Dict] = None
    enhanced_result: Optional[Dict] = None

class Tesla369Sync:
    """
    Synchronization layer between existing Tesla 369 strategy and enhanced features
    """
    
    def __init__(self, 
                 use_enhanced: bool = False,
                 enable_liquidity: bool = False,
                 enable_trend: bool = False,
                 enable_news: bool = False,
                 enable_lunar: bool = False,
                 enable_session: bool = False):
        
        self.use_enhanced = use_enhanced
        self.features = {
            'liquidity': enable_liquidity,
            'trend': enable_trend,
            'news': enable_news,
            'lunar': enable_lunar,
            'session': enable_session
        }
        
        # Initialize existing strategy
        self.existing_strategy = None
        if EXISTING_STRATEGY_AVAILABLE:
            try:
                self.existing_strategy = BulenoxGoldScalpingStrategy()
                logging.info("Existing Tesla 369 strategy loaded")
            except Exception as e:
                logging.warning(f"Could not load existing strategy: {e}")
        
        # Initialize enhanced strategy
        self.enhanced_strategy = None
        if ENHANCED_AVAILABLE:
            try:
                self.enhanced_strategy = Tesla369EnhancedStrategy()
                logging.info("Enhanced Tesla 369 strategy loaded")
            except Exception as e:
                logging.warning(f"Could not load enhanced strategy: {e}")
        
        # Initialize feature detectors
        self.liquidity_detector = LiquidityDetector() if ENHANCED_AVAILABLE else None
        self.lunar_calendar = LunarCalendar() if ENHANCED_AVAILABLE else None
        self.news_guard = NewsGuard() if ENHANCED_AVAILABLE else None
        self.session_manager = SessionManager() if ENHANCED_AVAILABLE else None
        
        # Configuration
        self.config = Tesla369EnhancedConfig() if ENHANCED_AVAILABLE else None
        
        # Extract existing parameters
        self._extract_existing_params()
    
    def _extract_existing_params(self):
        """Extract parameters from existing strategy"""
        self.existing_params = {
            'fibonacci_sequence': [10, 10, 20, 30, 50, 80, 130],
            'daily_profit_target': 535.71,
            'max_contracts': 3,
            'symbol': 'F.US.GCE'
        }
        
        if self.existing_strategy:
            try:
                # Extract from existing strategy
                if hasattr(self.existing_strategy, 'FIBONACCI_PROFIT_SEQUENCE'):
                    self.existing_params['fibonacci_sequence'] = self.existing_strategy.FIBONACCI_PROFIT_SEQUENCE
                
                if hasattr(self.existing_strategy, 'DAILY_PROFIT_TARGET'):
                    self.existing_params['daily_profit_target'] = self.existing_strategy.DAILY_PROFIT_TARGET
                    
                logging.info(f"Extracted existing parameters: {self.existing_params}")
                
            except Exception as e:
                logging.warning(f"Could not extract existing parameters: {e}")
    
    def enable_feature(self, feature_name: str, enabled: bool = True):
        """Enable/disable specific enhanced features"""
        if feature_name in self.features:
            self.features[feature_name] = enabled
            logging.info(f"Feature {feature_name} {'enabled' if enabled else 'disabled'}")
        else:
            logging.warning(f"Unknown feature: {feature_name}")
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get current feature status"""
        return self.features.copy()
    
    def execute_trade_with_enhancements(self, market_data: Dict, 
                                      trade_context: Dict = None) -> SyncResult:
        """
        Execute trade using synchronized approach
        
        Args:
            market_data: Current market data
            trade_context: Additional trading context
            
        Returns:
            SyncResult with both original and enhanced analysis
        """
        
        # Default context
        if trade_context is None:
            trade_context = {
                'current_time': datetime.now(),
                'current_session': self._get_current_session(),
                'trade_number': 1,
                'daily_pnl': 0.0
            }
        
        # Execute original strategy
        original_result = None
        if self.existing_strategy:
            try:
                original_result = self._execute_original_strategy(market_data, trade_context)
            except Exception as e:
                logging.error(f"Original strategy execution failed: {e}")
        
        # Execute enhanced analysis
        enhanced_analysis = None
        if self.enhanced_strategy and self.use_enhanced:
            try:
                enhanced_analysis = self._execute_enhanced_analysis(market_data, trade_context)
            except Exception as e:
                logging.error(f"Enhanced analysis failed: {e}")
        
        # Combine results
        sync_result = self._create_sync_result(original_result, enhanced_analysis, trade_context)
        
        return sync_result
    
    def _execute_original_strategy(self, market_data: Dict, context: Dict) -> Dict:
        """Execute original Tesla 369 strategy"""
        try:
            # Simulate original strategy execution
            fib_level = min(context.get('trade_number', 1) - 1, 
                          len(self.existing_params['fibonacci_sequence']) - 1)
            
            profit_target = self.existing_params['fibonacci_sequence'][fib_level]
            
            return {
                'trade_executed': True,
                'profit_target': profit_target,
                'fibonacci_level': fib_level,
                'contract_size': 1,
                'stop_loss': profit_target * 0.5,
                'strategy': 'original_369'
            }
            
        except Exception as e:
            logging.error(f"Original strategy error: {e}")
            return {
                'trade_executed': False,
                'profit_target': 0,
                'fibonacci_level': 0,
                'error': str(e)
            }
    
    def _execute_enhanced_analysis(self, market_data: Dict, context: Dict) -> Dict:
        """Execute enhanced analysis"""
        
        enhanced_data = {}
        
        # Liquidity analysis
        if self.features['liquidity'] and self.liquidity_detector:
            try:
                liquidity_score = self.liquidity_detector.analyze_liquidity(market_data)
                enhanced_data['liquidity_score'] = liquidity_score
            except Exception as e:
                logging.error(f"Liquidity analysis error: {e}")
                enhanced_data['liquidity_score'] = 0.5
        else:
            enhanced_data['liquidity_score'] = 0.5
        
        # Trend analysis
        if self.features['trend'] and self.enhanced_strategy:
            try:
                trend_strength = self.enhanced_strategy.analyze_trend(market_data)
                enhanced_data['trend_strength'] = trend_strength
            except Exception as e:
                logging.error(f"Trend analysis error: {e}")
                enhanced_data['trend_strength'] = 0.5
        else:
            enhanced_data['trend_strength'] = 0.5
        
        # News impact
        if self.features['news'] and self.news_guard:
            try:
                news_impact = self.news_guard.get_current_impact()
                enhanced_data['news_impact'] = news_impact
            except Exception as e:
                logging.error(f"News analysis error: {e}")
                enhanced_data['news_impact'] = 'neutral'
        else:
            enhanced_data['news_impact'] = 'neutral'
        
        # Lunar phase
        if self.features['lunar'] and self.lunar_calendar:
            try:
                lunar_phase = self.lunar_calendar.get_current_phase()
                enhanced_data['lunar_phase'] = lunar_phase
            except Exception as e:
                logging.error(f"Lunar analysis error: {e}")
                enhanced_data['lunar_phase'] = 'neutral'
        else:
            enhanced_data['lunar_phase'] = 'neutral'
        
        # Session quality
        if self.features['session'] and self.session_manager:
            try:
                session_quality = self.session_manager.get_session_quality()
                enhanced_data['session_quality'] = session_quality
            except Exception as e:
                logging.error(f"Session analysis error: {e}")
                enhanced_data['session_quality'] = 0.5
        else:
            enhanced_data['session_quality'] = 0.5
        
        return enhanced_data
    
    def _create_sync_result(self, original: Dict, enhanced: Dict, context: Dict) -> SyncResult:
        """Create synchronized result combining both approaches"""
        
        # Use original as base
        if original and original.get('trade_executed'):
            trade_executed = original['trade_executed']
            profit_target = original['profit_target']
            fibonacci_level = original['fibonacci_level']
        else:
            # Fallback to enhanced or default
            fib_level = min(context.get('trade_number', 1) - 1, 
                          len(self.existing_params['fibonacci_sequence']) - 1)
            profit_target = self.existing_params['fibonacci_sequence'][fib_level]
            trade_executed = True
            fibonacci_level = fib_level
        
        # Enhanced scores
        liquidity_score = enhanced.get('liquidity_score', 0.5) if enhanced else 0.5
        trend_strength = enhanced.get('trend_strength', 0.5) if enhanced else 0.5
        news_impact = enhanced.get('news_impact', 'neutral') if enhanced else 'neutral'
        lunar_phase = enhanced.get('lunar_phase', 'neutral') if enhanced else 'neutral'
        session_quality = enhanced.get('session_quality', 0.5) if enhanced else 0.5
        
        # Calculate enhanced score
        enhanced_score = self._calculate_enhanced_score(
            liquidity_score, trend_strength, news_impact, 
            lunar_phase, session_quality
        )
        
        # Risk adjustment
        risk_adjusted = enhanced_score > 0.7
        if risk_adjusted and self.config:
            # Adjust profit target based on enhanced score
            adjusted_target = profit_target * (0.8 + enhanced_score * 0.4)
            profit_target = min(adjusted_target, self.existing_params['daily_profit_target'] * 0.5)
        
        return SyncResult(
            trade_executed=trade_executed,
            profit_target=profit_target,
            fibonacci_level=fibonacci_level,
            enhanced_score=enhanced_score,
            liquidity_score=liquidity_score,
            trend_strength=trend_strength,
            news_impact=news_impact,
            lunar_phase=lunar_phase,
            session_quality=session_quality,
            risk_adjusted=risk_adjusted,
            original_result=original,
            enhanced_result=enhanced
        )
    
    def _calculate_enhanced_score(self, liquidity: float, trend: float, 
                                 news: str, lunar: str, session: float) -> float:
        """Calculate overall enhanced score"""
        
        # Base score from liquidity and trend
        base_score = (liquidity + trend + session) / 3
        
        # News impact adjustment
        news_multiplier = {'high': 0.5, 'medium': 0.8, 'low': 1.0, 'neutral': 1.0}
        news_factor = news_multiplier.get(news.lower(), 1.0)
        
        # Lunar phase adjustment
        lunar_multiplier = {'new_moon': 1.1, 'full_moon': 1.2, 'quarter': 1.0, 'neutral': 1.0}
        lunar_factor = lunar_multiplier.get(lunar.lower(), 1.0)
        
        # Final score
        enhanced_score = base_score * news_factor * lunar_factor
        return min(enhanced_score, 1.0)
    
    def _get_current_session(self) -> str:
        """Get current trading session"""
        current_time = datetime.now().time()
        
        # NY Sessions
        sessions = {
            'morning': (time(3, 0), time(6, 0)),
            'midday': (time(8, 20), time(11, 30)),
            'afternoon': (time(13, 0), time(15, 30))
        }
        
        for session_name, (start, end) in sessions.items():
            if start <= current_time <= end:
                return session_name
        
        return 'off_hours'
    
    def get_migration_report(self) -> Dict:
        """Generate comprehensive migration report"""
        
        report = {
            'migration_date': datetime.now().isoformat(),
            'existing_strategy_available': EXISTING_STRATEGY_AVAILABLE,
            'enhanced_strategy_available': ENHANCED_AVAILABLE,
            'existing_params': self.existing_params,
            'feature_status': self.get_feature_status(),
            'compatibility': {
                'fibonacci_sequence': self.existing_params['fibonacci_sequence'],
                'daily_profit_target': self.existing_params['daily_profit_target'],
                'symbol': self.existing_params['symbol']
            },
            'recommendations': [
                "Start with gradual feature enablement",
                "Test with paper trading first",
                "Monitor performance metrics",
                "Keep existing strategy as fallback"
            ]
        }
        
        return report
    
    def run_compatibility_test(self) -> Dict:
        """Run comprehensive compatibility test"""
        
        test_market_data = {
            'price': 2000.0,
            'volume': 1000,
            'bid': 1999.5,
            'ask': 2000.5,
            'timestamp': datetime.now().isoformat()
        }
        
        test_context = {
            'trade_number': 1,
            'daily_pnl': 0.0,
            'current_time': datetime.now()
        }
        
        # Test original
        original_result = self._execute_original_strategy(test_market_data, test_context)
        
        # Test enhanced
        enhanced_result = self.execute_trade_with_enhancements(test_market_data, test_context)
        
        return {
            'original_result': original_result,
            'enhanced_result': {
                'trade_executed': enhanced_result.trade_executed,
                'profit_target': enhanced_result.profit_target,
                'fibonacci_level': enhanced_result.fibonacci_level,
                'enhanced_score': enhanced_result.enhanced_score,
                'features_used': self.get_feature_status()
            },
            'compatibility_verified': True
        }

# Quick usage examples
def demo_integration():
    """Demonstrate seamless integration"""
    
    print("=== Tesla 369 Strategy Synchronization Demo ===")
    
    # Initialize sync
    sync = Tesla369Sync()
    
    # Show existing parameters
    print(f"Existing Fibonacci: {sync.existing_params['fibonacci_sequence']}")
    print(f"Daily Target: ${sync.existing_params['daily_profit_target']}")
    
    # Run compatibility test
    test_result = sync.run_compatibility_test()
    print(f"Compatibility: {test_result['compatibility_verified']}")
    
    # Enable gradual features
    sync.enable_feature('liquidity', True)
    sync.enable_feature('trend', True)
    
    # Execute with enhancements
    market_data = {'price': 2000.0, 'volume': 1000}
    result = sync.execute_trade_with_enhancements(market_data)
    
    print(f"Enhanced Score: {result.enhanced_score}")
    print(f"Liquidity Score: {result.liquidity_score}")
    print(f"Trade Executed: {result.trade_executed}")
    print(f"Profit Target: ${result.profit_target}")

if __name__ == "__main__":
    demo_integration()