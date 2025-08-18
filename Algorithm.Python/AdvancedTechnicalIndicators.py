from AlgorithmImports import *
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import math

@dataclass
class RSIDivergence:
    """Container for RSI divergence analysis"""
    type: str  # 'bullish', 'bearish', 'hidden_bullish', 'hidden_bearish', 'none'
    strength: float  # 0-1, strength of divergence
    lookback_bars: int  # Number of bars in divergence pattern
    price_swing_high: float
    price_swing_low: float
    rsi_swing_high: float
    rsi_swing_low: float
    confidence: float  # 0-1, confidence in divergence signal

@dataclass
class MACDAnalysis:
    """Container for comprehensive MACD analysis"""
    macd_line: float
    signal_line: float
    histogram: float
    histogram_trend: str  # 'increasing', 'decreasing', 'neutral'
    zero_line_cross: str  # 'bullish', 'bearish', 'none'
    signal_cross: str  # 'bullish', 'bearish', 'none'
    momentum_strength: float  # 0-1
    divergence_signal: str  # 'bullish', 'bearish', 'none'

@dataclass
class ATRVolatilityFilter:
    """Container for ATR-based volatility filtering"""
    current_atr: float
    atr_percentile: float  # Current ATR vs historical percentiles
    volatility_regime: str  # 'low', 'normal', 'high', 'extreme'
    trend_strength: float  # 0-1, based on ATR and price movement
    breakout_threshold: float  # Price move needed for valid breakout
    noise_level: float  # Expected random price movement
    trade_size_multiplier: float  # Suggested position size adjustment

@dataclass
class IchimokuAnalysis:
    """Container for Ichimoku cloud analysis"""
    tenkan_sen: float  # Conversion line
    kijun_sen: float  # Base line
    senkou_span_a: float  # Leading span A
    senkou_span_b: float  # Leading span B
    chikou_span: float  # Lagging span
    cloud_color: str  # 'bullish' (green), 'bearish' (red)
    price_vs_cloud: str  # 'above', 'below', 'inside'
    tk_cross: str  # 'bullish', 'bearish', 'none'
    price_vs_kijun: str  # 'above', 'below'
    chikou_clear: bool  # Is chikou span clear of price action
    overall_bias: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-1, overall signal strength

@dataclass
class TechnicalSignalSummary:
    """Container for combined technical analysis"""
    rsi_divergence: RSIDivergence
    macd_analysis: MACDAnalysis
    atr_filter: ATRVolatilityFilter
    ichimoku_analysis: IchimokuAnalysis
    combined_signal: str  # 'strong_bullish', 'bullish', 'neutral', 'bearish', 'strong_bearish'
    signal_strength: float  # 0-1
    confidence: float  # 0-1
    recommended_action: str  # 'buy', 'sell', 'hold', 'reduce'

class AdvancedTechnicalIndicators:
    """Advanced technical analysis with divergence detection and multi-indicator confluence"""
    
    def __init__(self, algorithm, symbol: Symbol):
        self.algorithm = algorithm
        self.symbol = symbol
        
        # Initialize indicators
        self.rsi = RelativeStrengthIndex(14)
        self.macd = MovingAverageConvergenceDivergence(12, 26, 9)
        self.atr = AverageTrueRange(14)
        
        # Ichimoku components
        self.tenkan_sen = Maximum(9) - Minimum(9)  # Will be divided by 2
        self.kijun_sen = Maximum(26) - Minimum(26)  # Will be divided by 2
        self.senkou_span_a_high = Maximum(52)
        self.senkou_span_a_low = Minimum(52)
        self.senkou_span_b_high = Maximum(52)
        self.senkou_span_b_low = Minimum(52)
        
        # Historical data storage
        self.price_history = deque(maxlen=200)
        self.rsi_history = deque(maxlen=200)
        self.macd_history = deque(maxlen=200)
        self.atr_history = deque(maxlen=200)
        self.volume_history = deque(maxlen=200)
        
        # Ichimoku historical data
        self.tenkan_history = deque(maxlen=200)
        self.kijun_history = deque(maxlen=200)
        self.senkou_a_history = deque(maxlen=200)
        self.senkou_b_history = deque(maxlen=200)
        
        # Analysis parameters
        self.divergence_lookback = 20
        self.min_swing_bars = 5
        self.atr_lookback = 50
        self.volatility_percentiles = [10, 25, 75, 90]  # For regime classification
        
        # Register indicators with algorithm
        algorithm.RegisterIndicator(symbol, self.rsi, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.macd, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.atr, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.tenkan_sen, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.kijun_sen, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.senkou_span_a_high, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.senkou_span_a_low, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.senkou_span_b_high, Resolution.Minute)
        algorithm.RegisterIndicator(symbol, self.senkou_span_b_low, Resolution.Minute)
        
        self.algorithm.Debug(f"📊 Advanced Technical Indicators initialized for {symbol}")
    
    def update(self, bar: TradeBar):
        """Update all indicators and historical data"""
        try:
            # Store current bar data
            self.price_history.append({
                'time': bar.Time,
                'open': bar.Open,
                'high': bar.High,
                'low': bar.Low,
                'close': bar.Close,
                'volume': bar.Volume
            })
            
            # Update indicator histories if ready
            if self.rsi.IsReady:
                self.rsi_history.append({
                    'time': bar.Time,
                    'value': self.rsi.Current.Value
                })
            
            if self.macd.IsReady:
                self.macd_history.append({
                    'time': bar.Time,
                    'macd': self.macd.Current.Value,
                    'signal': self.macd.Signal.Current.Value,
                    'histogram': self.macd.Histogram.Current.Value
                })
            
            if self.atr.IsReady:
                self.atr_history.append({
                    'time': bar.Time,
                    'value': self.atr.Current.Value
                })
            
            # Update Ichimoku components
            if self.tenkan_sen.IsReady and self.kijun_sen.IsReady:
                tenkan_value = (self.tenkan_sen.Current.Value) / 2
                kijun_value = (self.kijun_sen.Current.Value) / 2
                
                self.tenkan_history.append({
                    'time': bar.Time,
                    'value': tenkan_value
                })
                
                self.kijun_history.append({
                    'time': bar.Time,
                    'value': kijun_value
                })
                
                # Calculate Senkou spans
                if len(self.tenkan_history) >= 26 and len(self.kijun_history) >= 26:
                    senkou_a = (tenkan_value + kijun_value) / 2
                    
                    if self.senkou_span_b_high.IsReady and self.senkou_span_b_low.IsReady:
                        senkou_b = (self.senkou_span_b_high.Current.Value + self.senkou_span_b_low.Current.Value) / 2
                        
                        self.senkou_a_history.append({
                            'time': bar.Time,
                            'value': senkou_a
                        })
                        
                        self.senkou_b_history.append({
                            'time': bar.Time,
                            'value': senkou_b
                        })
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Error updating technical indicators: {e}")
    
    def analyze_rsi_divergence(self) -> RSIDivergence:
        """Detect RSI divergence patterns"""
        try:
            if len(self.price_history) < self.divergence_lookback or len(self.rsi_history) < self.divergence_lookback:
                return RSIDivergence('none', 0, 0, 0, 0, 0, 0, 0)
            
            # Get recent price and RSI data
            recent_prices = list(self.price_history)[-self.divergence_lookback:]
            recent_rsi = list(self.rsi_history)[-self.divergence_lookback:]
            
            if len(recent_prices) != len(recent_rsi):
                return RSIDivergence('none', 0, 0, 0, 0, 0, 0, 0)
            
            # Find swing highs and lows
            price_highs = self.find_swing_highs([p['high'] for p in recent_prices])
            price_lows = self.find_swing_lows([p['low'] for p in recent_prices])
            rsi_highs = self.find_swing_highs([r['value'] for r in recent_rsi])
            rsi_lows = self.find_swing_lows([r['value'] for r in recent_rsi])
            
            # Check for bearish divergence (price higher highs, RSI lower highs)
            bearish_div = self.check_bearish_divergence(price_highs, rsi_highs, recent_prices, recent_rsi)
            if bearish_div['detected']:
                return RSIDivergence(
                    'bearish',
                    bearish_div['strength'],
                    bearish_div['lookback_bars'],
                    bearish_div['price_high'],
                    0,
                    bearish_div['rsi_high'],
                    0,
                    bearish_div['confidence']
                )
            
            # Check for bullish divergence (price lower lows, RSI higher lows)
            bullish_div = self.check_bullish_divergence(price_lows, rsi_lows, recent_prices, recent_rsi)
            if bullish_div['detected']:
                return RSIDivergence(
                    'bullish',
                    bullish_div['strength'],
                    bullish_div['lookback_bars'],
                    0,
                    bullish_div['price_low'],
                    0,
                    bullish_div['rsi_low'],
                    bullish_div['confidence']
                )
            
            return RSIDivergence('none', 0, 0, 0, 0, 0, 0, 0)
            
        except Exception as e:
            self.algorithm.Debug(f"❌ RSI divergence analysis failed: {e}")
            return RSIDivergence('none', 0, 0, 0, 0, 0, 0, 0)
    
    def find_swing_highs(self, data: List[float], min_bars: int = 3) -> List[Tuple[int, float]]:
        """Find swing high points in data"""
        highs = []
        for i in range(min_bars, len(data) - min_bars):
            is_high = True
            for j in range(i - min_bars, i + min_bars + 1):
                if j != i and data[j] >= data[i]:
                    is_high = False
                    break
            if is_high:
                highs.append((i, data[i]))
        return highs
    
    def find_swing_lows(self, data: List[float], min_bars: int = 3) -> List[Tuple[int, float]]:
        """Find swing low points in data"""
        lows = []
        for i in range(min_bars, len(data) - min_bars):
            is_low = True
            for j in range(i - min_bars, i + min_bars + 1):
                if j != i and data[j] <= data[i]:
                    is_low = False
                    break
            if is_low:
                lows.append((i, data[i]))
        return lows
    
    def check_bearish_divergence(self, price_highs: List[Tuple[int, float]], 
                               rsi_highs: List[Tuple[int, float]], 
                               price_data: List[Dict], rsi_data: List[Dict]) -> Dict:
        """Check for bearish divergence pattern"""
        if len(price_highs) < 2 or len(rsi_highs) < 2:
            return {'detected': False}
        
        # Get the two most recent highs
        recent_price_high = price_highs[-1]
        prev_price_high = price_highs[-2]
        
        # Find corresponding RSI highs (within reasonable time window)
        recent_rsi_high = None
        prev_rsi_high = None
        
        for rsi_high in rsi_highs:
            if abs(rsi_high[0] - recent_price_high[0]) <= 3:  # Within 3 bars
                recent_rsi_high = rsi_high
            if abs(rsi_high[0] - prev_price_high[0]) <= 3:
                prev_rsi_high = rsi_high
        
        if not recent_rsi_high or not prev_rsi_high:
            return {'detected': False}
        
        # Check divergence conditions
        price_higher = recent_price_high[1] > prev_price_high[1]
        rsi_lower = recent_rsi_high[1] < prev_rsi_high[1]
        
        if price_higher and rsi_lower:
            # Calculate strength and confidence
            price_diff = (recent_price_high[1] - prev_price_high[1]) / prev_price_high[1]
            rsi_diff = abs(recent_rsi_high[1] - prev_rsi_high[1]) / 100
            
            strength = min(1.0, (price_diff + rsi_diff) * 2)
            confidence = min(1.0, strength * 0.8 + 0.2)  # Base confidence of 20%
            
            return {
                'detected': True,
                'strength': strength,
                'confidence': confidence,
                'lookback_bars': recent_price_high[0] - prev_price_high[0],
                'price_high': recent_price_high[1],
                'rsi_high': recent_rsi_high[1]
            }
        
        return {'detected': False}
    
    def check_bullish_divergence(self, price_lows: List[Tuple[int, float]], 
                               rsi_lows: List[Tuple[int, float]], 
                               price_data: List[Dict], rsi_data: List[Dict]) -> Dict:
        """Check for bullish divergence pattern"""
        if len(price_lows) < 2 or len(rsi_lows) < 2:
            return {'detected': False}
        
        # Get the two most recent lows
        recent_price_low = price_lows[-1]
        prev_price_low = price_lows[-2]
        
        # Find corresponding RSI lows
        recent_rsi_low = None
        prev_rsi_low = None
        
        for rsi_low in rsi_lows:
            if abs(rsi_low[0] - recent_price_low[0]) <= 3:
                recent_rsi_low = rsi_low
            if abs(rsi_low[0] - prev_price_low[0]) <= 3:
                prev_rsi_low = rsi_low
        
        if not recent_rsi_low or not prev_rsi_low:
            return {'detected': False}
        
        # Check divergence conditions
        price_lower = recent_price_low[1] < prev_price_low[1]
        rsi_higher = recent_rsi_low[1] > prev_rsi_low[1]
        
        if price_lower and rsi_higher:
            # Calculate strength and confidence
            price_diff = abs(recent_price_low[1] - prev_price_low[1]) / prev_price_low[1]
            rsi_diff = abs(recent_rsi_low[1] - prev_rsi_low[1]) / 100
            
            strength = min(1.0, (price_diff + rsi_diff) * 2)
            confidence = min(1.0, strength * 0.8 + 0.2)
            
            return {
                'detected': True,
                'strength': strength,
                'confidence': confidence,
                'lookback_bars': recent_price_low[0] - prev_price_low[0],
                'price_low': recent_price_low[1],
                'rsi_low': recent_rsi_low[1]
            }
        
        return {'detected': False}
    
    def analyze_macd(self) -> MACDAnalysis:
        """Comprehensive MACD analysis including histogram trends"""
        try:
            if not self.macd.IsReady or len(self.macd_history) < 10:
                return MACDAnalysis(0, 0, 0, 'neutral', 'none', 'none', 0, 'none')
            
            current_macd = self.macd.Current.Value
            current_signal = self.macd.Signal.Current.Value
            current_histogram = self.macd.Histogram.Current.Value
            
            # Analyze histogram trend
            recent_histograms = [h['histogram'] for h in list(self.macd_history)[-5:]]
            if len(recent_histograms) >= 3:
                if recent_histograms[-1] > recent_histograms[-2] > recent_histograms[-3]:
                    histogram_trend = 'increasing'
                elif recent_histograms[-1] < recent_histograms[-2] < recent_histograms[-3]:
                    histogram_trend = 'decreasing'
                else:
                    histogram_trend = 'neutral'
            else:
                histogram_trend = 'neutral'
            
            # Check for zero line crosses
            zero_line_cross = 'none'
            if len(self.macd_history) >= 2:
                prev_macd = self.macd_history[-2]['macd']
                if prev_macd <= 0 and current_macd > 0:
                    zero_line_cross = 'bullish'
                elif prev_macd >= 0 and current_macd < 0:
                    zero_line_cross = 'bearish'
            
            # Check for signal line crosses
            signal_cross = 'none'
            if len(self.macd_history) >= 2:
                prev_macd = self.macd_history[-2]['macd']
                prev_signal = self.macd_history[-2]['signal']
                
                if prev_macd <= prev_signal and current_macd > current_signal:
                    signal_cross = 'bullish'
                elif prev_macd >= prev_signal and current_macd < current_signal:
                    signal_cross = 'bearish'
            
            # Calculate momentum strength
            momentum_strength = min(1.0, abs(current_histogram) / 0.5)  # Normalize to 0-1
            
            # Check for MACD divergence (simplified)
            divergence_signal = 'none'
            if len(self.macd_history) >= 10 and len(self.price_history) >= 10:
                # This is a simplified divergence check
                recent_price_trend = self.price_history[-1]['close'] - self.price_history[-10]['close']
                recent_macd_trend = current_macd - self.macd_history[-10]['macd']
                
                if recent_price_trend > 0 and recent_macd_trend < 0:
                    divergence_signal = 'bearish'
                elif recent_price_trend < 0 and recent_macd_trend > 0:
                    divergence_signal = 'bullish'
            
            return MACDAnalysis(
                macd_line=current_macd,
                signal_line=current_signal,
                histogram=current_histogram,
                histogram_trend=histogram_trend,
                zero_line_cross=zero_line_cross,
                signal_cross=signal_cross,
                momentum_strength=momentum_strength,
                divergence_signal=divergence_signal
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ MACD analysis failed: {e}")
            return MACDAnalysis(0, 0, 0, 'neutral', 'none', 'none', 0, 'none')
    
    def analyze_atr_volatility(self) -> ATRVolatilityFilter:
        """ATR-based volatility regime analysis"""
        try:
            if not self.atr.IsReady or len(self.atr_history) < self.atr_lookback:
                return ATRVolatilityFilter(0, 50, 'normal', 0.5, 0, 0, 1.0)
            
            current_atr = self.atr.Current.Value
            
            # Calculate ATR percentile
            historical_atr = [a['value'] for a in list(self.atr_history)[-self.atr_lookback:]]
            atr_percentile = (sum(1 for atr in historical_atr if atr <= current_atr) / len(historical_atr)) * 100
            
            # Determine volatility regime
            if atr_percentile <= self.volatility_percentiles[0]:  # Bottom 10%
                volatility_regime = 'low'
                trade_size_multiplier = 1.3  # Increase size in low vol
            elif atr_percentile <= self.volatility_percentiles[1]:  # Bottom 25%
                volatility_regime = 'normal'
                trade_size_multiplier = 1.1
            elif atr_percentile >= self.volatility_percentiles[3]:  # Top 10%
                volatility_regime = 'extreme'
                trade_size_multiplier = 0.5  # Reduce size in extreme vol
            elif atr_percentile >= self.volatility_percentiles[2]:  # Top 25%
                volatility_regime = 'high'
                trade_size_multiplier = 0.7
            else:
                volatility_regime = 'normal'
                trade_size_multiplier = 1.0
            
            # Calculate trend strength using ATR and price movement
            if len(self.price_history) >= 10:
                price_range = self.price_history[-1]['close'] - self.price_history[-10]['close']
                expected_range = current_atr * 10  # Expected range over 10 bars
                trend_strength = min(1.0, abs(price_range) / max(0.01, expected_range))
            else:
                trend_strength = 0.5
            
            # Calculate breakout threshold (2x ATR is common)
            breakout_threshold = current_atr * 2.0
            
            # Estimate noise level (0.5x ATR)
            noise_level = current_atr * 0.5
            
            return ATRVolatilityFilter(
                current_atr=current_atr,
                atr_percentile=atr_percentile,
                volatility_regime=volatility_regime,
                trend_strength=trend_strength,
                breakout_threshold=breakout_threshold,
                noise_level=noise_level,
                trade_size_multiplier=trade_size_multiplier
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ ATR volatility analysis failed: {e}")
            return ATRVolatilityFilter(0, 50, 'normal', 0.5, 0, 0, 1.0)
    
    def analyze_ichimoku(self) -> IchimokuAnalysis:
        """Comprehensive Ichimoku cloud analysis"""
        try:
            if (len(self.tenkan_history) < 26 or len(self.kijun_history) < 26 or 
                len(self.senkou_a_history) < 26 or len(self.senkou_b_history) < 26):
                return IchimokuAnalysis(0, 0, 0, 0, 0, 'neutral', 'neutral', 'none', 'neutral', False, 'neutral', 0)
            
            # Get current values
            current_price = self.price_history[-1]['close']
            tenkan_sen = self.tenkan_history[-1]['value']
            kijun_sen = self.kijun_history[-1]['value']
            
            # Get cloud values (26 periods ahead)
            if len(self.senkou_a_history) >= 26 and len(self.senkou_b_history) >= 26:
                senkou_span_a = self.senkou_a_history[-26]['value']  # 26 periods ago for current cloud
                senkou_span_b = self.senkou_b_history[-26]['value']
            else:
                senkou_span_a = self.senkou_a_history[-1]['value']
                senkou_span_b = self.senkou_b_history[-1]['value']
            
            # Chikou span (current price 26 periods ago)
            if len(self.price_history) >= 26:
                chikou_span = self.price_history[-26]['close']
            else:
                chikou_span = current_price
            
            # Determine cloud color
            cloud_color = 'bullish' if senkou_span_a > senkou_span_b else 'bearish'
            
            # Price vs cloud position
            cloud_top = max(senkou_span_a, senkou_span_b)
            cloud_bottom = min(senkou_span_a, senkou_span_b)
            
            if current_price > cloud_top:
                price_vs_cloud = 'above'
            elif current_price < cloud_bottom:
                price_vs_cloud = 'below'
            else:
                price_vs_cloud = 'inside'
            
            # Tenkan-Kijun cross
            tk_cross = 'none'
            if len(self.tenkan_history) >= 2 and len(self.kijun_history) >= 2:
                prev_tenkan = self.tenkan_history[-2]['value']
                prev_kijun = self.kijun_history[-2]['value']
                
                if prev_tenkan <= prev_kijun and tenkan_sen > kijun_sen:
                    tk_cross = 'bullish'
                elif prev_tenkan >= prev_kijun and tenkan_sen < kijun_sen:
                    tk_cross = 'bearish'
            
            # Price vs Kijun
            price_vs_kijun = 'above' if current_price > kijun_sen else 'below'
            
            # Chikou span clear of price action (simplified check)
            chikou_clear = True  # Simplified - would need more complex logic
            
            # Overall bias calculation
            bullish_signals = 0
            bearish_signals = 0
            
            if price_vs_cloud == 'above':
                bullish_signals += 1
            elif price_vs_cloud == 'below':
                bearish_signals += 1
            
            if cloud_color == 'bullish':
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            if tk_cross == 'bullish':
                bullish_signals += 2
            elif tk_cross == 'bearish':
                bearish_signals += 2
            
            if price_vs_kijun == 'above':
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # Determine overall bias
            if bullish_signals > bearish_signals + 1:
                overall_bias = 'bullish'
                strength = min(1.0, (bullish_signals - bearish_signals) / 5)
            elif bearish_signals > bullish_signals + 1:
                overall_bias = 'bearish'
                strength = min(1.0, (bearish_signals - bullish_signals) / 5)
            else:
                overall_bias = 'neutral'
                strength = 0.5
            
            return IchimokuAnalysis(
                tenkan_sen=tenkan_sen,
                kijun_sen=kijun_sen,
                senkou_span_a=senkou_span_a,
                senkou_span_b=senkou_span_b,
                chikou_span=chikou_span,
                cloud_color=cloud_color,
                price_vs_cloud=price_vs_cloud,
                tk_cross=tk_cross,
                price_vs_kijun=price_vs_kijun,
                chikou_clear=chikou_clear,
                overall_bias=overall_bias,
                strength=strength
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Ichimoku analysis failed: {e}")
            return IchimokuAnalysis(0, 0, 0, 0, 0, 'neutral', 'neutral', 'none', 'neutral', False, 'neutral', 0)
    
    def get_comprehensive_analysis(self) -> TechnicalSignalSummary:
        """Get comprehensive technical analysis combining all indicators"""
        try:
            # Get individual analyses
            rsi_div = self.analyze_rsi_divergence()
            macd_analysis = self.analyze_macd()
            atr_filter = self.analyze_atr_volatility()
            ichimoku_analysis = self.analyze_ichimoku()
            
            # Calculate combined signal
            bullish_score = 0
            bearish_score = 0
            total_weight = 0
            
            # RSI Divergence (weight: 3)
            if rsi_div.type == 'bullish':
                bullish_score += 3 * rsi_div.strength
            elif rsi_div.type == 'bearish':
                bearish_score += 3 * rsi_div.strength
            total_weight += 3
            
            # MACD Analysis (weight: 2.5)
            macd_score = 0
            if macd_analysis.zero_line_cross == 'bullish':
                macd_score += 1
            elif macd_analysis.zero_line_cross == 'bearish':
                macd_score -= 1
            
            if macd_analysis.signal_cross == 'bullish':
                macd_score += 0.8
            elif macd_analysis.signal_cross == 'bearish':
                macd_score -= 0.8
            
            if macd_analysis.histogram_trend == 'increasing':
                macd_score += 0.5
            elif macd_analysis.histogram_trend == 'decreasing':
                macd_score -= 0.5
            
            if macd_score > 0:
                bullish_score += 2.5 * min(1.0, macd_score / 2.3)
            else:
                bearish_score += 2.5 * min(1.0, abs(macd_score) / 2.3)
            total_weight += 2.5
            
            # Ichimoku Analysis (weight: 2)
            if ichimoku_analysis.overall_bias == 'bullish':
                bullish_score += 2 * ichimoku_analysis.strength
            elif ichimoku_analysis.overall_bias == 'bearish':
                bearish_score += 2 * ichimoku_analysis.strength
            total_weight += 2
            
            # ATR Volatility Filter (weight: 1.5) - affects confidence more than direction
            volatility_confidence_multiplier = 1.0
            if atr_filter.volatility_regime == 'extreme':
                volatility_confidence_multiplier = 0.5
            elif atr_filter.volatility_regime == 'high':
                volatility_confidence_multiplier = 0.7
            elif atr_filter.volatility_regime == 'low':
                volatility_confidence_multiplier = 1.2
            
            # Calculate final scores
            if total_weight > 0:
                bullish_normalized = bullish_score / total_weight
                bearish_normalized = bearish_score / total_weight
            else:
                bullish_normalized = bearish_normalized = 0
            
            # Determine combined signal
            signal_strength = abs(bullish_normalized - bearish_normalized)
            
            if bullish_normalized > bearish_normalized + 0.3:
                if signal_strength > 0.7:
                    combined_signal = 'strong_bullish'
                else:
                    combined_signal = 'bullish'
                recommended_action = 'buy'
            elif bearish_normalized > bullish_normalized + 0.3:
                if signal_strength > 0.7:
                    combined_signal = 'strong_bearish'
                else:
                    combined_signal = 'bearish'
                recommended_action = 'sell'
            else:
                combined_signal = 'neutral'
                recommended_action = 'hold'
            
            # Calculate confidence
            base_confidence = signal_strength
            
            # Boost confidence for confluence
            confluence_count = 0
            if rsi_div.type != 'none':
                confluence_count += 1
            if macd_analysis.signal_cross != 'none' or macd_analysis.zero_line_cross != 'none':
                confluence_count += 1
            if ichimoku_analysis.overall_bias != 'neutral':
                confluence_count += 1
            
            confluence_boost = min(0.3, confluence_count * 0.1)
            final_confidence = min(1.0, (base_confidence + confluence_boost) * volatility_confidence_multiplier)
            
            return TechnicalSignalSummary(
                rsi_divergence=rsi_div,
                macd_analysis=macd_analysis,
                atr_filter=atr_filter,
                ichimoku_analysis=ichimoku_analysis,
                combined_signal=combined_signal,
                signal_strength=signal_strength,
                confidence=final_confidence,
                recommended_action=recommended_action
            )
            
        except Exception as e:
            self.algorithm.Debug(f"❌ Comprehensive technical analysis failed: {e}")
            return TechnicalSignalSummary(
                RSIDivergence('none', 0, 0, 0, 0, 0, 0, 0),
                MACDAnalysis(0, 0, 0, 'neutral', 'none', 'none', 0, 'none'),
                ATRVolatilityFilter(0, 50, 'normal', 0.5, 0, 0, 1.0),
                IchimokuAnalysis(0, 0, 0, 0, 0, 'neutral', 'neutral', 'none', 'neutral', False, 'neutral', 0),
                'neutral', 0, 0, 'hold'
            )
    
    def is_ready(self) -> bool:
        """Check if all indicators are ready for analysis"""
        return (self.rsi.IsReady and self.macd.IsReady and self.atr.IsReady and 
                len(self.price_history) >= 50 and len(self.rsi_history) >= 20)