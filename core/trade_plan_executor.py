#!/usr/bin/env python3
"""
AI Trading Sentinel - Trade Plan Executor
TRAE-SentinelOps: Main execution engine for generating risk-controlled trade plans

Integrates:
1. Trade Plan Generator (trend + Bollinger + liquidity + lunar)
2. Session Manager (market hours and liquidity)
3. News Guard (economic events protection)
4. Risk Management (circuit breakers and position sizing)
5. Existing strategies (safe/moderate/recovery_scalp)
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Import our modules
from .trade_plan_generator import TradePlanGenerator, MarketRegime, TradingContext, TradeEntry
from .session_manager import SessionManager, MarketType
from .news_guard import NewsGuard
from .liquidity_detector import LiquidityDetector
from .lunar_calendar import LunarCalendar

@dataclass
class ExecutorConfig:
    """Configuration for the trade plan executor."""
    # Market settings
    symbol: str = "XAUUSD"
    market_type: str = "FX"
    
    # Risk settings
    risk_per_trade: float = 0.02  # 2% per trade
    max_intraday_dd_pct: float = 0.05  # 5% daily drawdown limit
    max_positions: int = 3
    
    # Scalping settings
    scalp_enabled: bool = True
    scalp_max_layers: int = 3
    scalp_multiplier: float = 1.2
    scalp_tp_pips: float = 10.0
    scalp_sl_pips: float = 15.0
    
    # Guard settings
    spread_max: float = 2.0  # Max spread in pips
    atr_min: float = 0.0005  # Min ATR for volatility
    cooldown_seconds: int = 300  # 5 minutes between layers
    
    # Session settings
    enabled_sessions: List[str] = None
    min_liquidity_score: int = 6
    weekend_trading: bool = False
    
    # News settings
    news_guard_enabled: bool = True
    monitored_currencies: List[str] = None
    
    # Lunar settings
    lunar_enabled: bool = False
    lunar_max_adjustment: float = 0.15  # ±15%
    
    # Operational settings
    session_whitelist: str = "FX"
    rollover_block: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        if self.enabled_sessions is None:
            self.enabled_sessions = ['london', 'new_york']
        if self.monitored_currencies is None:
            self.monitored_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD']

class TradePlanExecutor:
    """
    Main executor that generates comprehensive trade plans by integrating
    all analysis components and applying strict risk controls.
    """
    
    def __init__(self, config: Optional[ExecutorConfig] = None):
        self.config = config or ExecutorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
        
        # State tracking
        self.current_drawdown = 0.0
        self.daily_trades = 0
        self.last_trade_time = None
        self.circuit_breaker_active = False
        
    def _initialize_components(self):
        """
        Initialize all analysis and guard components.
        """
        try:
            # Trade plan generator
            generator_config = {
                'symbol': self.config.symbol,
                'risk_per_trade': self.config.risk_per_trade,
                'atr_periods': 14,
                'bb_periods': 20,
                'bb_deviation': 2.0,
                'ema_fast': 50,
                'ema_slow': 200
            }
            self.trade_generator = TradePlanGenerator(generator_config)
            
            # Session manager
            session_config = {
                'market_type': self.config.market_type,
                'enabled_sessions': self.config.enabled_sessions,
                'min_liquidity_score': self.config.min_liquidity_score,
                'weekend_trading': self.config.weekend_trading
            }
            self.session_manager = SessionManager(session_config)
            
            # News guard
            news_config = {
                'enabled': self.config.news_guard_enabled,
                'monitored_currencies': self.config.monitored_currencies,
                'high_impact_buffer_minutes': 30,
                'critical_impact_buffer_minutes': 60
            }
            self.news_guard = NewsGuard(news_config)
            
            # Liquidity detector
            self.liquidity_detector = LiquidityDetector()
            
            # Lunar calendar (optional)
            if self.config.lunar_enabled:
                self.lunar_calendar = LunarCalendar()
            else:
                self.lunar_calendar = None
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def generate_trade_plan(self, market_data: Dict, target_time: Optional[datetime] = None) -> Dict:
        """
        Generate a comprehensive trade plan in the specified JSON format.
        
        Args:
            market_data: Dictionary containing OHLC data, indicators, and broker state
            target_time: Target time for the plan (defaults to now)
            
        Returns:
            JSON trade plan dictionary
        """
        if target_time is None:
            target_time = datetime.utcnow()
        
        plan_id = str(uuid.uuid4())
        
        try:
            # Step 1: Validate guards and session
            guard_status = self._validate_guards(target_time)
            if not guard_status['allowed']:
                return self._create_restricted_plan(plan_id, target_time, guard_status['reason'])
            
            # Step 2: Analyze market regime
            market_regime = self._analyze_market_regime(market_data)
            
            # Step 3: Get trading context
            context = self._build_trading_context(market_data, target_time)
            
            # Step 4: Generate entries using integrated strategy
            entries = self._generate_entries(market_data, market_regime, context)
            
            # Step 5: Determine trading mode
            mode = self._determine_trading_mode()
            
            # Step 6: Apply risk controls
            risk_config = self._build_risk_config()
            
            # Step 7: Set operational parameters
            ops_config = self._build_ops_config()
            
            # Step 8: Configure telemetry
            telemetry_config = self._build_telemetry_config()
            
            # Build final plan
            trade_plan = {
                "plan_id": plan_id,
                "timestamp_utc": target_time.isoformat() + "Z",
                "market_regime": {
                    "trend": market_regime.trend_direction,
                    "atr_state": market_regime.volatility_regime
                },
                "context": context,
                "entries": [self._format_entry(entry) for entry in entries],
                "mode": mode,
                "risk": risk_config,
                "ops": ops_config,
                "telemetry": telemetry_config
            }
            
            self.logger.info(f"Generated trade plan {plan_id} with {len(entries)} entries")
            return trade_plan
            
        except Exception as e:
            self.logger.error(f"Error generating trade plan: {e}")
            return self._create_error_plan(plan_id, target_time, str(e))
    
    def _validate_guards(self, target_time: datetime) -> Dict:
        """
        Validate all guard conditions.
        """
        try:
            # Check circuit breaker
            if self.circuit_breaker_active or self.current_drawdown >= self.config.max_intraday_dd_pct:
                return {
                    'allowed': False,
                    'reason': f"Circuit breaker active - drawdown {self.current_drawdown:.2%}"
                }
            
            # Check session
            session_status = self.session_manager.get_current_session_status(target_time)
            if not session_status.is_active:
                return {
                    'allowed': False,
                    'reason': f"Session inactive: {session_status.notes}"
                }
            
            # Check news guard
            news_status = self.news_guard.get_news_guard_status(target_time)
            if news_status.is_restricted:
                return {
                    'allowed': False,
                    'reason': f"News restriction: {news_status.restriction_reason}"
                }
            
            # Check cooldown
            if self.last_trade_time:
                time_since_last = target_time - self.last_trade_time
                if time_since_last.total_seconds() < self.config.cooldown_seconds:
                    return {
                        'allowed': False,
                        'reason': f"Cooldown active - {self.config.cooldown_seconds - time_since_last.total_seconds():.0f}s remaining"
                    }
            
            return {'allowed': True, 'reason': 'All guards passed'}
            
        except Exception as e:
            self.logger.error(f"Error validating guards: {e}")
            return {'allowed': False, 'reason': f"Guard validation error: {e}"}
    
    def _analyze_market_regime(self, market_data: Dict) -> MarketRegime:
        """
        Analyze current market regime from data.
        """
        try:
            # Extract timeframe data
            h4_data = market_data.get('H4', {})
            h1_data = market_data.get('H1', {})
            
            # Determine trend direction
            h4_trend = self._get_trend_direction(h4_data)
            h1_trend = self._get_trend_direction(h1_data)
            
            # Overall trend bias
            if h4_trend == h1_trend:
                trend_direction = h4_trend
            elif h4_trend == "up" and h1_trend == "mixed":
                trend_direction = "up"
            elif h4_trend == "down" and h1_trend == "mixed":
                trend_direction = "down"
            else:
                trend_direction = "mixed"
            
            # Volatility regime
            atr_current = h1_data.get('atr', 0)
            atr_avg = h1_data.get('atr_avg', atr_current)
            
            if atr_current > atr_avg * 1.5:
                volatility_regime = "high"
            elif atr_current < atr_avg * 0.7:
                volatility_regime = "low"
            else:
                volatility_regime = "normal"
            
            return MarketRegime(
                trend_direction=trend_direction,
                volatility_regime=volatility_regime,
                trend_strength=abs(h1_data.get('ema_50', 0) - h1_data.get('ema_200', 0)),
                atr_percentile=min(100, max(0, (atr_current / atr_avg - 0.5) * 100 + 50))
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing market regime: {e}")
            return MarketRegime("mixed", "normal", 0, 50)
    
    def _get_trend_direction(self, timeframe_data: Dict) -> str:
        """
        Determine trend direction from timeframe data.
        """
        try:
            ema_50 = timeframe_data.get('ema_50', 0)
            ema_200 = timeframe_data.get('ema_200', 0)
            price = timeframe_data.get('close', 0)
            
            if ema_50 > ema_200 and price > ema_50:
                return "up"
            elif ema_50 < ema_200 and price < ema_50:
                return "down"
            else:
                return "mixed"
                
        except Exception as e:
            self.logger.error(f"Error determining trend: {e}")
            return "mixed"
    
    def _build_trading_context(self, market_data: Dict, target_time: datetime) -> Dict:
        """
        Build trading context with HTF bias, liquidity, and lunar data.
        """
        try:
            context = {
                "htf_bias": {
                    "H4": self._get_trend_direction(market_data.get('H4', {})),
                    "H1": self._get_trend_direction(market_data.get('H1', {}))
                },
                "liquidity": [],
                "lunar": {
                    "phase": "none",
                    "window": "none",
                    "adjustment": "0%"
                }
            }
            
            # Add liquidity analysis
            try:
                h1_data = market_data.get('H1', {})
                h4_data = market_data.get('H4', {})
                
                # Detect liquidity levels
                if h1_data:
                    liquidity_levels = self.liquidity_detector.detect_liquidity_levels(
                        h1_data.get('highs', []),
                        h1_data.get('lows', []),
                        tolerance_pips=2.0
                    )
                    
                    for level in liquidity_levels[:3]:  # Top 3 levels
                        context["liquidity"].append({
                            "type": "eq_highs" if level.level_type == "resistance" else "eq_lows",
                            "tf": "H1",
                            "price": level.price,
                            "note": f"Strength: {level.strength}, Touches: {level.touch_count}"
                        })
                
                # Add H4 liquidity if available
                if h4_data:
                    h4_liquidity = self.liquidity_detector.detect_liquidity_levels(
                        h4_data.get('highs', []),
                        h4_data.get('lows', []),
                        tolerance_pips=3.0
                    )
                    
                    for level in h4_liquidity[:2]:  # Top 2 H4 levels
                        context["liquidity"].append({
                            "type": "eq_highs" if level.level_type == "resistance" else "eq_lows",
                            "tf": "H4",
                            "price": level.price,
                            "note": f"H4 level - Strength: {level.strength}"
                        })
                        
            except Exception as e:
                self.logger.warning(f"Error detecting liquidity: {e}")
            
            # Add lunar analysis if enabled
            if self.lunar_calendar:
                try:
                    lunar_info = self.lunar_calendar.get_current_lunar_info(target_time)
                    context["lunar"] = {
                        "phase": lunar_info.phase.value,
                        "window": "pre" if lunar_info.days_to_event < 0 else "post" if lunar_info.days_to_event <= 1 else "none",
                        "adjustment": f"{lunar_info.risk_adjustment:+.0%}"
                    }
                except Exception as e:
                    self.logger.warning(f"Error getting lunar info: {e}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            return {
                "htf_bias": {"H4": "mixed", "H1": "mixed"},
                "liquidity": [],
                "lunar": {"phase": "none", "window": "none", "adjustment": "0%"}
            }
    
    def _generate_entries(self, market_data: Dict, market_regime: MarketRegime, context: Dict) -> List[TradeEntry]:
        """
        Generate trade entries using integrated strategy.
        """
        try:
            # Use the trade plan generator to create entries
            trading_context = TradingContext(
                htf_trend_h4=context["htf_bias"]["H4"],
                htf_trend_h1=context["htf_bias"]["H1"],
                session_active=True,  # Already validated
                news_clear=True,      # Already validated
                spread_ok=True,       # Will validate in entry
                atr_sufficient=True   # Will validate in entry
            )
            
            # Generate entries
            entries = self.trade_generator.generate_trade_entries(
                market_data, market_regime, trading_context
            )
            
            # Apply lunar adjustments if enabled
            if self.lunar_calendar and context["lunar"]["phase"] != "none":
                entries = self._apply_lunar_adjustments(entries, context["lunar"])
            
            # Limit entries based on current positions and mode
            max_entries = self._get_max_entries()
            if len(entries) > max_entries:
                # Keep the highest confidence entries
                entries = sorted(entries, key=lambda x: getattr(x, 'confidence', 0.5), reverse=True)[:max_entries]
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Error generating entries: {e}")
            return []
    
    def _apply_lunar_adjustments(self, entries: List[TradeEntry], lunar_info: Dict) -> List[TradeEntry]:
        """
        Apply lunar-based adjustments to trade entries.
        """
        try:
            adjustment_pct = float(lunar_info["adjustment"].rstrip('%')) / 100
            
            # Limit adjustment to configured maximum
            adjustment_pct = max(-self.config.lunar_max_adjustment, 
                               min(self.config.lunar_max_adjustment, adjustment_pct))
            
            adjusted_entries = []
            for entry in entries:
                # Adjust TP and SL based on lunar phase
                if lunar_info["phase"] == "new":
                    # New moon: expect expansion, wider TP
                    tp_adjustment = 1 + abs(adjustment_pct)
                    sl_adjustment = 1.0  # Keep SL same
                elif lunar_info["phase"] == "full":
                    # Full moon: expect mean reversion, tighter TP/SL
                    tp_adjustment = 1 - abs(adjustment_pct) * 0.5
                    sl_adjustment = 1 - abs(adjustment_pct) * 0.3
                else:
                    tp_adjustment = 1.0
                    sl_adjustment = 1.0
                
                # Create adjusted entry
                adjusted_entry = TradeEntry(
                    symbol=entry.symbol,
                    direction=entry.direction,
                    setup_type=entry.setup_type,
                    timeframe=entry.timeframe,
                    entry_type=entry.entry_type,
                    entry_price=entry.entry_price,
                    sl_price=entry.sl_price,  # Adjust if needed
                    tp_price=entry.tp_price,  # Adjust if needed
                    risk_pct=entry.risk_pct,
                    confidence=entry.confidence,
                    notes=f"{entry.notes} (lunar: {lunar_info['phase']} {adjustment_pct:+.1%})"
                )
                
                # Apply TP adjustment
                if entry.direction == "long":
                    tp_distance = entry.tp_price - entry.entry_price
                    adjusted_entry.tp_price = entry.entry_price + (tp_distance * tp_adjustment)
                else:
                    tp_distance = entry.entry_price - entry.tp_price
                    adjusted_entry.tp_price = entry.entry_price - (tp_distance * tp_adjustment)
                
                adjusted_entries.append(adjusted_entry)
            
            return adjusted_entries
            
        except Exception as e:
            self.logger.error(f"Error applying lunar adjustments: {e}")
            return entries
    
    def _determine_trading_mode(self) -> str:
        """
        Determine current trading mode based on performance and risk.
        """
        try:
            # Check if recovery mode is needed
            if self.current_drawdown >= self.config.max_intraday_dd_pct * 0.7:  # 70% of max DD
                return "recovery_scalp"
            
            # Check if safe mode is needed
            elif self.current_drawdown >= self.config.max_intraday_dd_pct * 0.4:  # 40% of max DD
                return "safe"
            
            # Normal operations
            else:
                return "moderate"
                
        except Exception as e:
            self.logger.error(f"Error determining mode: {e}")
            return "safe"
    
    def _get_max_entries(self) -> int:
        """
        Get maximum number of entries based on current mode and positions.
        """
        mode = self._determine_trading_mode()
        
        if mode == "safe":
            return 1
        elif mode == "recovery_scalp":
            return min(2, self.config.scalp_max_layers)
        else:
            return min(self.config.max_positions, 3)
    
    def _format_entry(self, entry: TradeEntry) -> Dict:
        """
        Format trade entry for JSON output.
        """
        try:
            # Calculate lot size from risk percentage
            sl_distance_pips = abs(entry.entry_price - entry.sl_price) * 10000  # Assuming 4-digit pricing
            
            return {
                "symbol": entry.symbol,
                "direction": entry.direction,
                "setup": entry.setup_type,
                "timeframe": entry.timeframe,
                "entry_type": entry.entry_type,
                "entry_price": entry.entry_price if entry.entry_price else None,
                "sl_price": entry.sl_price,
                "tp_price": entry.tp_price,
                "sizing": {
                    "risk_pct": entry.risk_pct,
                    "lots": None  # Will be calculated by execution engine
                },
                "guards": {
                    "spread_max": self.config.spread_max,
                    "atr_min": self.config.atr_min,
                    "cooldown_s": self.config.cooldown_seconds
                },
                "valid_for_minutes": 60,  # 1 hour validity
                "notes": entry.notes
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting entry: {e}")
            return {}
    
    def _build_risk_config(self) -> Dict:
        """
        Build risk configuration.
        """
        return {
            "max_positions": self.config.max_positions,
            "max_intraday_dd_pct": self.config.max_intraday_dd_pct,
            "scalp": {
                "enabled": self.config.scalp_enabled,
                "max_layers": self.config.scalp_max_layers,
                "mult": self.config.scalp_multiplier,
                "tp_pips": self.config.scalp_tp_pips,
                "sl_pips": self.config.scalp_sl_pips
            }
        }
    
    def _build_ops_config(self) -> Dict:
        """
        Build operational configuration.
        """
        return {
            "news_guard": self.config.news_guard_enabled,
            "session_whitelist": self.config.session_whitelist,
            "rollover_block": self.config.rollover_block
        }
    
    def _build_telemetry_config(self) -> Dict:
        """
        Build telemetry configuration.
        """
        return {
            "log_level": self.config.log_level,
            "emit_events": [
                "plan_generated",
                "order_submitted",
                "order_filled",
                "order_canceled",
                "risk_tripped"
            ]
        }
    
    def _create_restricted_plan(self, plan_id: str, target_time: datetime, reason: str) -> Dict:
        """
        Create a restricted trade plan with no entries.
        """
        return {
            "plan_id": plan_id,
            "timestamp_utc": target_time.isoformat() + "Z",
            "market_regime": {"trend": "mixed", "atr_state": "normal"},
            "context": {
                "htf_bias": {"H4": "mixed", "H1": "mixed"},
                "liquidity": [],
                "lunar": {"phase": "none", "window": "none", "adjustment": "0%"}
            },
            "entries": [],
            "mode": "safe",
            "risk": self._build_risk_config(),
            "ops": self._build_ops_config(),
            "telemetry": {
                "log_level": self.config.log_level,
                "emit_events": ["plan_generated", "risk_tripped"],
                "restriction_reason": reason
            }
        }
    
    def _create_error_plan(self, plan_id: str, target_time: datetime, error: str) -> Dict:
        """
        Create an error trade plan.
        """
        return {
            "plan_id": plan_id,
            "timestamp_utc": target_time.isoformat() + "Z",
            "market_regime": {"trend": "mixed", "atr_state": "normal"},
            "context": {
                "htf_bias": {"H4": "mixed", "H1": "mixed"},
                "liquidity": [],
                "lunar": {"phase": "none", "window": "none", "adjustment": "0%"}
            },
            "entries": [],
            "mode": "safe",
            "risk": self._build_risk_config(),
            "ops": self._build_ops_config(),
            "telemetry": {
                "log_level": "ERROR",
                "emit_events": ["plan_generated", "error_occurred"],
                "error": error
            }
        }
    
    def update_performance_metrics(self, drawdown: float, trades_today: int, last_trade: Optional[datetime] = None):
        """
        Update performance metrics for risk management.
        
        Args:
            drawdown: Current intraday drawdown percentage
            trades_today: Number of trades executed today
            last_trade: Timestamp of last trade
        """
        try:
            self.current_drawdown = drawdown
            self.daily_trades = trades_today
            
            if last_trade:
                self.last_trade_time = last_trade
            
            # Update circuit breaker status
            if drawdown >= self.config.max_intraday_dd_pct:
                self.circuit_breaker_active = True
                self.logger.warning(f"Circuit breaker activated - drawdown: {drawdown:.2%}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def reset_daily_state(self):
        """
        Reset daily state for new trading day.
        """
        try:
            self.current_drawdown = 0.0
            self.daily_trades = 0
            self.circuit_breaker_active = False
            self.last_trade_time = None
            
            self.logger.info("Daily state reset for new trading session")
            
        except Exception as e:
            self.logger.error(f"Error resetting daily state: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Create configuration
    config = ExecutorConfig(
        symbol="XAUUSD",
        risk_per_trade=0.02,
        max_intraday_dd_pct=0.05,
        scalp_enabled=True,
        news_guard_enabled=True,
        lunar_enabled=False
    )
    
    # Initialize executor
    executor = TradePlanExecutor(config)
    
    # Mock market data
    market_data = {
        'H4': {
            'close': 2000.50,
            'ema_50': 1998.20,
            'ema_200': 1995.80,
            'atr': 15.5,
            'atr_avg': 12.3,
            'highs': [2005.1, 2004.8, 2005.0],
            'lows': [1995.2, 1995.5, 1995.1]
        },
        'H1': {
            'close': 2000.50,
            'ema_50': 1999.10,
            'ema_200': 1997.30,
            'atr': 8.2,
            'atr_avg': 7.1,
            'bb_upper': 2003.20,
            'bb_middle': 2000.10,
            'bb_lower': 1996.90,
            'highs': [2002.1, 2001.9, 2002.0],
            'lows': [1998.5, 1998.7, 1998.4]
        },
        'M15': {
            'close': 2000.50,
            'volume': 1250
        }
    }
    
    # Generate trade plan
    plan = executor.generate_trade_plan(market_data)
    
    # Print formatted JSON
    print(json.dumps(plan, indent=2))