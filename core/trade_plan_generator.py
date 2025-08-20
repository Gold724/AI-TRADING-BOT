#!/usr/bin/env python3
"""
AI Trading Sentinel - Advanced Trade Plan Generator
TRAE-SentinelOps: High-quality, risk-controlled trade plans with multi-timeframe analysis

Integrates:
1. Trend-first bias (H1/H4)
2. Bollinger logic aligned with trend
3. Liquidity detection on higher timeframes
4. Optional lunar timing as volatility modulator
5. Existing strategies (safe/moderate/recovery_scalp)
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd

# Import existing modules
try:
    from core.indicators import BollingerBands, EMA, ATR
    from core.liquidity_detector import LiquidityDetector
    from core.lunar_calendar import LunarCalendar
    from core.risk_manager import RiskManager
    from core.session_manager import SessionManager
    from core.news_guard import NewsGuard
except ImportError:
    logging.warning("Some core modules not found, using mock implementations")

class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    MIXED = "mixed"

class VolatilityState(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class LunarPhase(Enum):
    NONE = "none"
    NEW = "new"
    FULL = "full"

class TradingMode(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    RECOVERY_SCALP = "recovery_scalp"

@dataclass
class MarketRegime:
    trend: TrendDirection
    atr_state: VolatilityState
    h4_bias: TrendDirection
    h1_bias: TrendDirection

@dataclass
class LiquidityLevel:
    type: str  # eq_highs, eq_lows, sweep, fvg
    timeframe: str
    price: float
    note: str

@dataclass
class LunarContext:
    phase: LunarPhase
    window: str  # pre, post, none
    adjustment: str  # -15%..+15%

@dataclass
class TradeEntry:
    symbol: str
    direction: str  # long, short
    setup: str
    timeframe: str
    entry_type: str  # limit, market, stop
    entry_price: Optional[float]
    sl_price: float
    tp_price: float
    sizing: Dict[str, Any]
    guards: Dict[str, Any]
    valid_for_minutes: int
    notes: str

@dataclass
class TradePlan:
    plan_id: str
    timestamp_utc: str
    market_regime: Dict[str, str]
    context: Dict[str, Any]
    entries: List[Dict[str, Any]]
    mode: str
    risk: Dict[str, Any]
    ops: Dict[str, Any]
    telemetry: Dict[str, Any]

class TradePlanGenerator:
    """
    Advanced trade plan generator with multi-timeframe analysis,
    liquidity detection, and risk-controlled execution.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.RISK_PER_TRADE = config.get('risk_per_trade', 0.02)  # 2%
        self.MAX_DD_INTRADAY = config.get('max_dd_intraday', 0.05)  # 5%
        self.SPREAD_MAX = config.get('spread_max', 3.0)  # pips
        self.VOL_ATR_MIN = config.get('vol_atr_min', 10.0)  # pips
        self.SCALP_MAX_LAYERS = config.get('scalp_max_layers', 3)
        self.SCALP_MULTIPLIER = config.get('scalp_multiplier', 1.2)
        
        # Initialize components
        self.liquidity_detector = LiquidityDetector()
        self.lunar_calendar = LunarCalendar() if config.get('lunar_enabled') else None
        self.risk_manager = RiskManager(config)
        self.session_manager = SessionManager()
        self.news_guard = NewsGuard() if config.get('news_guard_enabled') else None
        
    def generate_trade_plan(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive trade plan based on market analysis.
        
        Args:
            market_data: Dictionary containing OHLC data, indicators, and broker state
            
        Returns:
            JSON-formatted trade plan
        """
        try:
            # 1. Analyze market regime
            regime = self._analyze_market_regime(market_data)
            
            # 2. Check session and conditions
            if not self._validate_trading_conditions(market_data):
                return self._generate_empty_plan("Trading conditions not met")
            
            # 3. Detect liquidity levels
            liquidity_levels = self._detect_liquidity_levels(market_data)
            
            # 4. Get lunar context (if enabled)
            lunar_context = self._get_lunar_context() if self.lunar_calendar else None
            
            # 5. Generate trade entries
            entries = self._generate_entries(market_data, regime, liquidity_levels, lunar_context)
            
            # 6. Determine trading mode
            mode = self._determine_trading_mode(market_data)
            
            # 7. Build complete trade plan
            plan = self._build_trade_plan(regime, liquidity_levels, lunar_context, entries, mode)
            
            self.logger.info(f"Generated trade plan with {len(entries)} entries")
            return asdict(plan)
            
        except Exception as e:
            self.logger.error(f"Error generating trade plan: {e}")
            return self._generate_empty_plan(f"Error: {str(e)}")
    
    def _analyze_market_regime(self, data: Dict[str, Any]) -> MarketRegime:
        """
        Analyze market regime using H4/H1 timeframes.
        """
        h4_data = data.get('H4', {})
        h1_data = data.get('H1', {})
        
        # Trend analysis using EMA crossover and market structure
        h4_bias = self._get_trend_bias(h4_data)
        h1_bias = self._get_trend_bias(h1_data)
        
        # Overall trend (hierarchical)
        if h4_bias == h1_bias:
            trend = h4_bias
        else:
            trend = TrendDirection.MIXED
        
        # Volatility state using ATR percentile
        atr_state = self._get_volatility_state(data)
        
        return MarketRegime(
            trend=trend,
            atr_state=atr_state,
            h4_bias=h4_bias,
            h1_bias=h1_bias
        )
    
    def _get_trend_bias(self, tf_data: Dict[str, Any]) -> TrendDirection:
        """
        Determine trend bias for a specific timeframe.
        """
        if not tf_data:
            return TrendDirection.MIXED
            
        ema50 = tf_data.get('ema50', [])
        ema200 = tf_data.get('ema200', [])
        highs = tf_data.get('high', [])
        lows = tf_data.get('low', [])
        
        if len(ema50) < 2 or len(ema200) < 2:
            return TrendDirection.MIXED
        
        # EMA crossover
        ema_bullish = ema50[-1] > ema200[-1] and ema50[-2] <= ema200[-2]
        ema_bearish = ema50[-1] < ema200[-1] and ema50[-2] >= ema200[-2]
        ema_up = ema50[-1] > ema200[-1]
        
        # Market structure (simplified)
        if len(highs) >= 3 and len(lows) >= 3:
            higher_highs = highs[-1] > highs[-2] > highs[-3]
            higher_lows = lows[-1] > lows[-2] > lows[-3]
            lower_highs = highs[-1] < highs[-2] < highs[-3]
            lower_lows = lows[-1] < lows[-2] < lows[-3]
            
            structure_up = higher_highs and higher_lows
            structure_down = lower_highs and lower_lows
        else:
            structure_up = structure_down = False
        
        # Combine signals
        if (ema_up and structure_up) or ema_bullish:
            return TrendDirection.UP
        elif (not ema_up and structure_down) or ema_bearish:
            return TrendDirection.DOWN
        else:
            return TrendDirection.MIXED
    
    def _get_volatility_state(self, data: Dict[str, Any]) -> VolatilityState:
        """
        Determine volatility state using ATR percentile.
        """
        m15_data = data.get('M15', {})
        atr_values = m15_data.get('atr14', [])
        
        if len(atr_values) < 20:
            return VolatilityState.NORMAL
        
        current_atr = atr_values[-1]
        atr_percentile = np.percentile(atr_values[-100:], 50) if len(atr_values) >= 100 else np.mean(atr_values)
        
        if current_atr < atr_percentile * 0.7:
            return VolatilityState.LOW
        elif current_atr > atr_percentile * 1.3:
            return VolatilityState.HIGH
        else:
            return VolatilityState.NORMAL
    
    def _validate_trading_conditions(self, data: Dict[str, Any]) -> bool:
        """
        Validate trading conditions (session, spread, volatility, news).
        """
        broker_state = data.get('broker', {})
        
        # Check spread
        spread = broker_state.get('spread', 0)
        if spread > self.SPREAD_MAX:
            self.logger.info(f"Spread too wide: {spread} > {self.SPREAD_MAX}")
            return False
        
        # Check ATR minimum
        m15_data = data.get('M15', {})
        atr_values = m15_data.get('atr14', [])
        if atr_values and atr_values[-1] < self.VOL_ATR_MIN:
            self.logger.info(f"ATR too low: {atr_values[-1]} < {self.VOL_ATR_MIN}")
            return False
        
        # Check session
        if not self.session_manager.is_trading_session():
            self.logger.info("Outside trading session")
            return False
        
        # Check news guard
        if self.news_guard and self.news_guard.is_news_blackout():
            self.logger.info("News blackout active")
            return False
        
        # Check drawdown
        if self.risk_manager.get_current_drawdown() >= self.MAX_DD_INTRADAY:
            self.logger.info("Maximum intraday drawdown reached")
            return False
        
        return True
    
    def _detect_liquidity_levels(self, data: Dict[str, Any]) -> List[LiquidityLevel]:
        """
        Detect liquidity levels on higher timeframes.
        """
        levels = []
        
        for tf in ['H4', 'H1']:
            tf_data = data.get(tf, {})
            if not tf_data:
                continue
                
            # Detect equal highs/lows
            eq_levels = self.liquidity_detector.find_equal_levels(tf_data)
            for level in eq_levels:
                levels.append(LiquidityLevel(
                    type=level['type'],
                    timeframe=tf,
                    price=level['price'],
                    note=f"Equal {level['type']} at {level['price']}"
                ))
            
            # Detect FVGs/imbalances
            fvgs = self.liquidity_detector.find_fair_value_gaps(tf_data)
            for fvg in fvgs:
                levels.append(LiquidityLevel(
                    type="fvg",
                    timeframe=tf,
                    price=fvg['price'],
                    note=f"FVG {fvg['direction']} at {fvg['price']}"
                ))
        
        return levels
    
    def _get_lunar_context(self) -> Optional[LunarContext]:
        """
        Get lunar phase context for volatility modulation.
        """
        if not self.lunar_calendar:
            return None
            
        phase_info = self.lunar_calendar.get_current_phase()
        
        if phase_info['phase'] in ['new', 'full']:
            # Calculate adjustment based on phase
            if phase_info['phase'] == 'new':
                adjustment = "+10%"  # Expansion bias
            else:
                adjustment = "-10%"  # Mean reversion bias
                
            return LunarContext(
                phase=LunarPhase(phase_info['phase']),
                window=phase_info.get('window', 'none'),
                adjustment=adjustment
            )
        
        return LunarContext(
            phase=LunarPhase.NONE,
            window="none",
            adjustment="0%"
        )
    
    def _generate_entries(self, data: Dict[str, Any], regime: MarketRegime, 
                         liquidity_levels: List[LiquidityLevel], 
                         lunar_context: Optional[LunarContext]) -> List[TradeEntry]:
        """
        Generate trade entries based on analysis.
        """
        entries = []
        
        # Only trade with trend or post-liquidity-sweep continuations
        if regime.trend == TrendDirection.MIXED:
            # Look for liquidity sweep setups only
            sweep_entries = self._generate_sweep_entries(data, liquidity_levels)
            entries.extend(sweep_entries)
        else:
            # Generate trend-aligned entries
            bb_entries = self._generate_bollinger_entries(data, regime, lunar_context)
            entries.extend(bb_entries)
            
            # Add liquidity-based entries if they align with trend
            liquidity_entries = self._generate_liquidity_entries(data, regime, liquidity_levels)
            entries.extend(liquidity_entries)
        
        # Apply lunar adjustments if available
        if lunar_context and lunar_context.phase != LunarPhase.NONE:
            entries = self._apply_lunar_adjustments(entries, lunar_context)
        
        return entries[:3]  # Limit to 3 entries max
    
    def _generate_bollinger_entries(self, data: Dict[str, Any], regime: MarketRegime, 
                                   lunar_context: Optional[LunarContext]) -> List[TradeEntry]:
        """
        Generate Bollinger Band entries aligned with trend.
        """
        entries = []
        m15_data = data.get('M15', {})
        
        if not m15_data:
            return entries
        
        bb_data = m15_data.get('bollinger', {})
        if not bb_data:
            return entries
        
        current_price = m15_data.get('close', [])[-1] if m15_data.get('close') else None
        if not current_price:
            return entries
        
        upper_band = bb_data.get('upper', [])[-1] if bb_data.get('upper') else None
        lower_band = bb_data.get('lower', [])[-1] if bb_data.get('lower') else None
        middle_band = bb_data.get('middle', [])[-1] if bb_data.get('middle') else None
        
        if not all([upper_band, lower_band, middle_band]):
            return entries
        
        # Bollinger pullback entries (with trend)
        if regime.trend == TrendDirection.UP:
            # Long on pullback to lower band or middle in uptrend
            if current_price <= middle_band * 1.001:  # Near middle band
                entry = self._create_bollinger_entry(
                    direction="long",
                    setup="bb_pullback",
                    entry_price=current_price,
                    sl_price=lower_band * 0.999,
                    tp_price=upper_band * 0.999,
                    data=data
                )
                if entry:
                    entries.append(entry)
        
        elif regime.trend == TrendDirection.DOWN:
            # Short on pullback to upper band or middle in downtrend
            if current_price >= middle_band * 0.999:  # Near middle band
                entry = self._create_bollinger_entry(
                    direction="short",
                    setup="bb_pullback",
                    entry_price=current_price,
                    sl_price=upper_band * 1.001,
                    tp_price=lower_band * 1.001,
                    data=data
                )
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _create_bollinger_entry(self, direction: str, setup: str, entry_price: float,
                               sl_price: float, tp_price: float, data: Dict[str, Any]) -> Optional[TradeEntry]:
        """
        Create a Bollinger Band trade entry.
        """
        # Calculate position sizing
        sl_distance = abs(entry_price - sl_price)
        risk_amount = self.risk_manager.get_account_balance() * self.RISK_PER_TRADE
        lot_size = self.risk_manager.calculate_lot_size(risk_amount, sl_distance)
        
        if lot_size <= 0:
            return None
        
        return TradeEntry(
            symbol="XAUUSD",
            direction=direction,
            setup=setup,
            timeframe="M15",
            entry_type="limit",
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            sizing={
                "risk_pct": self.RISK_PER_TRADE,
                "lots": lot_size
            },
            guards={
                "spread_max": self.SPREAD_MAX,
                "atr_min": self.VOL_ATR_MIN,
                "cooldown_s": 300
            },
            valid_for_minutes=60,
            notes=f"BB {setup} {direction} with trend alignment"
        )
    
    def _generate_sweep_entries(self, data: Dict[str, Any], 
                               liquidity_levels: List[LiquidityLevel]) -> List[TradeEntry]:
        """
        Generate entries based on liquidity sweeps.
        """
        entries = []
        # Implementation for sweep-based entries
        # This would analyze recent price action for liquidity sweeps
        # and generate continuation entries
        return entries
    
    def _generate_liquidity_entries(self, data: Dict[str, Any], regime: MarketRegime,
                                   liquidity_levels: List[LiquidityLevel]) -> List[TradeEntry]:
        """
        Generate entries based on liquidity levels aligned with trend.
        """
        entries = []
        # Implementation for liquidity-based entries
        # This would look for entries near liquidity levels that align with trend
        return entries
    
    def _apply_lunar_adjustments(self, entries: List[TradeEntry], 
                                lunar_context: LunarContext) -> List[TradeEntry]:
        """
        Apply lunar phase adjustments to entries.
        """
        if lunar_context.phase == LunarPhase.NONE:
            return entries
        
        adjustment_pct = float(lunar_context.adjustment.rstrip('%')) / 100
        
        for entry in entries:
            if lunar_context.phase == LunarPhase.NEW:
                # Expansion bias - wider TP
                tp_distance = abs(entry.tp_price - entry.entry_price)
                entry.tp_price = entry.entry_price + (tp_distance * (1 + adjustment_pct) * 
                                                     (1 if entry.direction == "long" else -1))
            elif lunar_context.phase == LunarPhase.FULL:
                # Mean reversion bias - tighter SL/TP
                sl_distance = abs(entry.sl_price - entry.entry_price)
                tp_distance = abs(entry.tp_price - entry.entry_price)
                
                entry.sl_price = entry.entry_price + (sl_distance * (1 + adjustment_pct) * 
                                                      (-1 if entry.direction == "long" else 1))
                entry.tp_price = entry.entry_price + (tp_distance * (1 + adjustment_pct) * 
                                                     (1 if entry.direction == "long" else -1))
        
        return entries
    
    def _determine_trading_mode(self, data: Dict[str, Any]) -> TradingMode:
        """
        Determine appropriate trading mode based on current conditions.
        """
        current_dd = self.risk_manager.get_current_drawdown()
        
        if current_dd >= self.MAX_DD_INTRADAY * 0.8:  # 80% of max DD
            return TradingMode.RECOVERY_SCALP
        elif current_dd >= self.MAX_DD_INTRADAY * 0.5:  # 50% of max DD
            return TradingMode.SAFE
        else:
            return TradingMode.MODERATE
    
    def _build_trade_plan(self, regime: MarketRegime, liquidity_levels: List[LiquidityLevel],
                         lunar_context: Optional[LunarContext], entries: List[TradeEntry],
                         mode: TradingMode) -> TradePlan:
        """
        Build complete trade plan structure.
        """
        plan_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Convert entries to dict format
        entry_dicts = [asdict(entry) for entry in entries]
        
        # Build context
        context = {
            "htf_bias": {
                "H4": regime.h4_bias.value,
                "H1": regime.h1_bias.value
            },
            "liquidity": [asdict(level) for level in liquidity_levels],
            "lunar": asdict(lunar_context) if lunar_context else {
                "phase": "none",
                "window": "none",
                "adjustment": "0%"
            }
        }
        
        return TradePlan(
            plan_id=plan_id,
            timestamp_utc=timestamp,
            market_regime={
                "trend": regime.trend.value,
                "atr_state": regime.atr_state.value
            },
            context=context,
            entries=entry_dicts,
            mode=mode.value,
            risk={
                "max_positions": 3,
                "max_intraday_dd_pct": self.MAX_DD_INTRADAY,
                "scalp": {
                    "enabled": mode == TradingMode.RECOVERY_SCALP,
                    "max_layers": self.SCALP_MAX_LAYERS,
                    "mult": self.SCALP_MULTIPLIER,
                    "tp_pips": 10,
                    "sl_pips": 5
                }
            },
            ops={
                "news_guard": self.news_guard is not None,
                "session_whitelist": "FX",
                "rollover_block": True
            },
            telemetry={
                "log_level": "INFO",
                "emit_events": [
                    "plan_generated",
                    "order_submitted",
                    "order_filled",
                    "order_canceled",
                    "risk_tripped"
                ]
            }
        )
    
    def _generate_empty_plan(self, reason: str) -> Dict[str, Any]:
        """
        Generate empty trade plan with reason.
        """
        plan_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return {
            "plan_id": plan_id,
            "timestamp_utc": timestamp,
            "market_regime": {"trend": "mixed", "atr_state": "normal"},
            "context": {
                "htf_bias": {"H4": "mixed", "H1": "mixed"},
                "liquidity": [],
                "lunar": {"phase": "none", "window": "none", "adjustment": "0%"}
            },
            "entries": [],
            "mode": "safe",
            "risk": {
                "max_positions": 0,
                "max_intraday_dd_pct": self.MAX_DD_INTRADAY,
                "scalp": {"enabled": False, "max_layers": 0, "mult": 1.0, "tp_pips": 0, "sl_pips": 0}
            },
            "ops": {
                "news_guard": True,
                "session_whitelist": "NONE",
                "rollover_block": True
            },
            "telemetry": {
                "log_level": "INFO",
                "emit_events": ["plan_generated"],
                "reason": reason
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Configuration
    config = {
        'risk_per_trade': 0.02,
        'max_dd_intraday': 0.05,
        'spread_max': 3.0,
        'vol_atr_min': 10.0,
        'scalp_max_layers': 3,
        'scalp_multiplier': 1.2,
        'lunar_enabled': True,
        'news_guard_enabled': True
    }
    
    # Mock market data
    market_data = {
        'H4': {
            'ema50': [2000, 2010, 2020],
            'ema200': [1990, 1995, 2000],
            'high': [2025, 2030, 2035],
            'low': [1995, 2000, 2005],
            'close': [2020, 2025, 2030]
        },
        'H1': {
            'ema50': [2015, 2020, 2025],
            'ema200': [2000, 2005, 2010],
            'high': [2030, 2032, 2035],
            'low': [2010, 2015, 2020],
            'close': [2025, 2028, 2030]
        },
        'M15': {
            'atr14': [15, 16, 17, 18, 20],
            'close': [2030],
            'bollinger': {
                'upper': [2040],
                'middle': [2025],
                'lower': [2010]
            }
        },
        'broker': {
            'spread': 2.5,
            'margin_free': 10000,
            'balance': 10000
        }
    }
    
    # Generate trade plan
    generator = TradePlanGenerator(config)
    plan = generator.generate_trade_plan(market_data)
    
    # Output JSON
    print(json.dumps(plan, indent=2))