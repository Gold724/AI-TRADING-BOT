#!/usr/bin/env python3
"""
AI Trading Sentinel - Liquidity Detection Engine
TRAE-SentinelOps: Smart money liquidity level detection for higher timeframe analysis

Detects:
1. Equal highs and lows (liquidity pools)
2. Wick sweeps and liquidity grabs
3. Fair Value Gaps (FVGs) and imbalances
4. Order block formations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class LiquidityLevel:
    price: float
    type: str  # 'eq_highs', 'eq_lows', 'sweep', 'fvg', 'order_block'
    strength: int  # 1-5 rating
    timeframe: str
    timestamp: str
    volume: Optional[float] = None
    touches: int = 0
    swept: bool = False

@dataclass
class FairValueGap:
    top: float
    bottom: float
    direction: str  # 'bullish', 'bearish'
    timeframe: str
    timestamp: str
    filled_percentage: float = 0.0
    strength: int = 1

class LiquidityDetector:
    """
    Advanced liquidity detection for smart money analysis.
    Identifies key levels where institutional orders likely reside.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Detection parameters
        self.EQUAL_LEVEL_TOLERANCE = self.config.get('equal_level_tolerance', 0.0005)  # 0.05%
        self.MIN_TOUCHES = self.config.get('min_touches', 2)
        self.MAX_LOOKBACK = self.config.get('max_lookback', 100)
        self.FVG_MIN_SIZE = self.config.get('fvg_min_size', 10)  # pips
        self.SWEEP_TOLERANCE = self.config.get('sweep_tolerance', 5)  # pips
        
    def find_equal_levels(self, ohlc_data: Dict[str, List[float]], 
                         timeframe: str = "H1") -> List[Dict]:
        """
        Find equal highs and lows that represent liquidity pools.
        
        Args:
            ohlc_data: Dictionary with 'high', 'low', 'close', 'open' lists
            timeframe: Timeframe identifier
            
        Returns:
            List of equal level dictionaries
        """
        levels = []
        
        try:
            highs = ohlc_data.get('high', [])
            lows = ohlc_data.get('low', [])
            
            if len(highs) < self.MIN_TOUCHES or len(lows) < self.MIN_TOUCHES:
                return levels
            
            # Find equal highs
            eq_highs = self._find_equal_points(highs, 'high', timeframe)
            levels.extend(eq_highs)
            
            # Find equal lows
            eq_lows = self._find_equal_points(lows, 'low', timeframe)
            levels.extend(eq_lows)
            
            # Sort by strength
            levels.sort(key=lambda x: x['strength'], reverse=True)
            
            self.logger.debug(f"Found {len(levels)} equal levels on {timeframe}")
            return levels
            
        except Exception as e:
            self.logger.error(f"Error finding equal levels: {e}")
            return []
    
    def _find_equal_points(self, prices: List[float], point_type: str, 
                          timeframe: str) -> List[Dict]:
        """
        Find equal price points (highs or lows).
        """
        levels = []
        
        if len(prices) < self.MIN_TOUCHES:
            return levels
        
        # Use recent data for analysis
        recent_prices = prices[-self.MAX_LOOKBACK:] if len(prices) > self.MAX_LOOKBACK else prices
        
        # Group similar prices
        price_groups = self._group_similar_prices(recent_prices)
        
        for group_price, indices in price_groups.items():
            if len(indices) >= self.MIN_TOUCHES:
                # Calculate strength based on touches and recency
                strength = min(5, len(indices))  # Max strength of 5
                
                # Boost strength for recent touches
                recent_touches = sum(1 for idx in indices if idx >= len(recent_prices) - 20)
                if recent_touches >= 2:
                    strength = min(5, strength + 1)
                
                levels.append({
                    'price': group_price,
                    'type': f'eq_{point_type}s',
                    'strength': strength,
                    'timeframe': timeframe,
                    'touches': len(indices),
                    'indices': indices
                })
        
        return levels
    
    def _group_similar_prices(self, prices: List[float]) -> Dict[float, List[int]]:
        """
        Group prices that are within tolerance of each other.
        """
        groups = {}
        
        for i, price in enumerate(prices):
            # Find existing group this price belongs to
            assigned = False
            
            for group_price in groups.keys():
                if abs(price - group_price) / group_price <= self.EQUAL_LEVEL_TOLERANCE:
                    groups[group_price].append(i)
                    assigned = True
                    break
            
            # Create new group if not assigned
            if not assigned:
                groups[price] = [i]
        
        # Filter groups with minimum touches
        return {price: indices for price, indices in groups.items() 
                if len(indices) >= self.MIN_TOUCHES}
    
    def find_fair_value_gaps(self, ohlc_data: Dict[str, List[float]], 
                           timeframe: str = "H1") -> List[Dict]:
        """
        Find Fair Value Gaps (FVGs) - areas of imbalance in price action.
        
        Args:
            ohlc_data: Dictionary with OHLC data
            timeframe: Timeframe identifier
            
        Returns:
            List of FVG dictionaries
        """
        fvgs = []
        
        try:
            highs = ohlc_data.get('high', [])
            lows = ohlc_data.get('low', [])
            opens = ohlc_data.get('open', [])
            closes = ohlc_data.get('close', [])
            
            if len(highs) < 3:
                return fvgs
            
            # Look for 3-candle FVG patterns
            for i in range(2, len(highs)):
                # Bullish FVG: gap between candle 1 high and candle 3 low
                if (lows[i] > highs[i-2] and 
                    closes[i-1] > opens[i-1]):  # Middle candle is bullish
                    
                    gap_size = lows[i] - highs[i-2]
                    if gap_size >= self.FVG_MIN_SIZE / 10000:  # Convert pips to price
                        fvgs.append({
                            'type': 'fvg',
                            'direction': 'bullish',
                            'top': lows[i],
                            'bottom': highs[i-2],
                            'price': (lows[i] + highs[i-2]) / 2,
                            'size': gap_size,
                            'timeframe': timeframe,
                            'candle_index': i,
                            'strength': self._calculate_fvg_strength(gap_size, timeframe)
                        })
                
                # Bearish FVG: gap between candle 1 low and candle 3 high
                elif (highs[i] < lows[i-2] and 
                      closes[i-1] < opens[i-1]):  # Middle candle is bearish
                    
                    gap_size = lows[i-2] - highs[i]
                    if gap_size >= self.FVG_MIN_SIZE / 10000:  # Convert pips to price
                        fvgs.append({
                            'type': 'fvg',
                            'direction': 'bearish',
                            'top': lows[i-2],
                            'bottom': highs[i],
                            'price': (lows[i-2] + highs[i]) / 2,
                            'size': gap_size,
                            'timeframe': timeframe,
                            'candle_index': i,
                            'strength': self._calculate_fvg_strength(gap_size, timeframe)
                        })
            
            # Sort by strength and recency
            fvgs.sort(key=lambda x: (x['strength'], x['candle_index']), reverse=True)
            
            self.logger.debug(f"Found {len(fvgs)} FVGs on {timeframe}")
            return fvgs[:10]  # Return top 10 FVGs
            
        except Exception as e:
            self.logger.error(f"Error finding FVGs: {e}")
            return []
    
    def _calculate_fvg_strength(self, gap_size: float, timeframe: str) -> int:
        """
        Calculate FVG strength based on size and timeframe.
        """
        # Base strength on gap size
        if gap_size >= 50 / 10000:  # 50+ pips
            strength = 5
        elif gap_size >= 30 / 10000:  # 30+ pips
            strength = 4
        elif gap_size >= 20 / 10000:  # 20+ pips
            strength = 3
        elif gap_size >= 15 / 10000:  # 15+ pips
            strength = 2
        else:
            strength = 1
        
        # Boost for higher timeframes
        if timeframe in ['H4', 'D1']:
            strength = min(5, strength + 1)
        
        return strength
    
    def detect_liquidity_sweeps(self, ohlc_data: Dict[str, List[float]], 
                               liquidity_levels: List[Dict]) -> List[Dict]:
        """
        Detect when price has swept through liquidity levels.
        
        Args:
            ohlc_data: Current OHLC data
            liquidity_levels: Previously identified liquidity levels
            
        Returns:
            List of sweep events
        """
        sweeps = []
        
        try:
            if not liquidity_levels or not ohlc_data:
                return sweeps
            
            highs = ohlc_data.get('high', [])
            lows = ohlc_data.get('low', [])
            
            if not highs or not lows:
                return sweeps
            
            current_high = highs[-1]
            current_low = lows[-1]
            
            for level in liquidity_levels:
                level_price = level['price']
                level_type = level['type']
                
                # Check for sweep based on level type
                if level_type == 'eq_highs' and current_high > level_price:
                    # High swept
                    sweeps.append({
                        'type': 'sweep',
                        'direction': 'bullish_sweep',
                        'level_price': level_price,
                        'sweep_price': current_high,
                        'level_type': level_type,
                        'strength': level['strength'],
                        'pips_beyond': (current_high - level_price) * 10000
                    })
                
                elif level_type == 'eq_lows' and current_low < level_price:
                    # Low swept
                    sweeps.append({
                        'type': 'sweep',
                        'direction': 'bearish_sweep',
                        'level_price': level_price,
                        'sweep_price': current_low,
                        'level_type': level_type,
                        'strength': level['strength'],
                        'pips_beyond': (level_price - current_low) * 10000
                    })
            
            self.logger.debug(f"Detected {len(sweeps)} liquidity sweeps")
            return sweeps
            
        except Exception as e:
            self.logger.error(f"Error detecting sweeps: {e}")
            return []
    
    def find_order_blocks(self, ohlc_data: Dict[str, List[float]], 
                         timeframe: str = "H1") -> List[Dict]:
        """
        Find order blocks - areas where smart money likely placed orders.
        
        Args:
            ohlc_data: OHLC data dictionary
            timeframe: Timeframe identifier
            
        Returns:
            List of order block dictionaries
        """
        order_blocks = []
        
        try:
            highs = ohlc_data.get('high', [])
            lows = ohlc_data.get('low', [])
            opens = ohlc_data.get('open', [])
            closes = ohlc_data.get('close', [])
            
            if len(highs) < 5:
                return order_blocks
            
            # Look for order block patterns
            for i in range(2, len(highs) - 2):
                # Bullish order block: strong up move after consolidation
                if (closes[i] > opens[i] and  # Bullish candle
                    closes[i] - opens[i] > (highs[i] - lows[i]) * 0.7 and  # Strong body
                    closes[i] > max(closes[i-2:i]) and  # Breaking recent highs
                    lows[i] > min(lows[i-2:i])):  # Higher low
                    
                    order_blocks.append({
                        'type': 'order_block',
                        'direction': 'bullish',
                        'top': highs[i],
                        'bottom': opens[i],
                        'price': (highs[i] + opens[i]) / 2,
                        'timeframe': timeframe,
                        'candle_index': i,
                        'strength': self._calculate_ob_strength(ohlc_data, i, 'bullish')
                    })
                
                # Bearish order block: strong down move after consolidation
                elif (closes[i] < opens[i] and  # Bearish candle
                      opens[i] - closes[i] > (highs[i] - lows[i]) * 0.7 and  # Strong body
                      closes[i] < min(closes[i-2:i]) and  # Breaking recent lows
                      highs[i] < max(highs[i-2:i])):  # Lower high
                    
                    order_blocks.append({
                        'type': 'order_block',
                        'direction': 'bearish',
                        'top': opens[i],
                        'bottom': lows[i],
                        'price': (opens[i] + lows[i]) / 2,
                        'timeframe': timeframe,
                        'candle_index': i,
                        'strength': self._calculate_ob_strength(ohlc_data, i, 'bearish')
                    })
            
            # Sort by strength and recency
            order_blocks.sort(key=lambda x: (x['strength'], x['candle_index']), reverse=True)
            
            self.logger.debug(f"Found {len(order_blocks)} order blocks on {timeframe}")
            return order_blocks[:5]  # Return top 5 order blocks
            
        except Exception as e:
            self.logger.error(f"Error finding order blocks: {e}")
            return []
    
    def _calculate_ob_strength(self, ohlc_data: Dict[str, List[float]], 
                              index: int, direction: str) -> int:
        """
        Calculate order block strength based on various factors.
        """
        try:
            highs = ohlc_data.get('high', [])
            lows = ohlc_data.get('low', [])
            opens = ohlc_data.get('open', [])
            closes = ohlc_data.get('close', [])
            
            strength = 1
            
            # Factor 1: Candle body size
            body_size = abs(closes[index] - opens[index])
            candle_range = highs[index] - lows[index]
            
            if body_size / candle_range > 0.8:  # Strong body
                strength += 1
            
            # Factor 2: Volume (if available)
            volumes = ohlc_data.get('volume', [])
            if volumes and len(volumes) > index:
                avg_volume = np.mean(volumes[max(0, index-10):index])
                if volumes[index] > avg_volume * 1.5:  # High volume
                    strength += 1
            
            # Factor 3: Follow-through
            if index < len(closes) - 2:
                if direction == 'bullish' and closes[index + 1] > closes[index]:
                    strength += 1
                elif direction == 'bearish' and closes[index + 1] < closes[index]:
                    strength += 1
            
            return min(5, strength)  # Cap at 5
            
        except Exception as e:
            self.logger.error(f"Error calculating OB strength: {e}")
            return 1
    
    def get_active_levels(self, current_price: float, 
                         all_levels: List[Dict], 
                         distance_threshold: float = 0.01) -> List[Dict]:
        """
        Get liquidity levels that are close to current price.
        
        Args:
            current_price: Current market price
            all_levels: All detected liquidity levels
            distance_threshold: Maximum distance as percentage of price
            
        Returns:
            List of nearby active levels
        """
        active_levels = []
        
        try:
            for level in all_levels:
                level_price = level['price']
                distance_pct = abs(current_price - level_price) / current_price
                
                if distance_pct <= distance_threshold:
                    # Add distance info
                    level_copy = level.copy()
                    level_copy['distance_pct'] = distance_pct
                    level_copy['distance_pips'] = abs(current_price - level_price) * 10000
                    active_levels.append(level_copy)
            
            # Sort by distance (closest first)
            active_levels.sort(key=lambda x: x['distance_pct'])
            
            return active_levels
            
        except Exception as e:
            self.logger.error(f"Error getting active levels: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    # Mock OHLC data
    test_data = {
        'high': [2020, 2025, 2030, 2025, 2020, 2025, 2030, 2035, 2030, 2025],
        'low': [2010, 2015, 2020, 2015, 2010, 2015, 2020, 2025, 2020, 2015],
        'open': [2015, 2020, 2025, 2020, 2015, 2020, 2025, 2030, 2025, 2020],
        'close': [2020, 2025, 2030, 2015, 2020, 2025, 2030, 2025, 2020, 2025]
    }
    
    # Initialize detector
    detector = LiquidityDetector()
    
    # Test equal levels detection
    equal_levels = detector.find_equal_levels(test_data, "H1")
    print(f"Found {len(equal_levels)} equal levels")
    
    # Test FVG detection
    fvgs = detector.find_fair_value_gaps(test_data, "H1")
    print(f"Found {len(fvgs)} FVGs")
    
    # Test order blocks
    order_blocks = detector.find_order_blocks(test_data, "H1")
    print(f"Found {len(order_blocks)} order blocks")
    
    # Test sweep detection
    sweeps = detector.detect_liquidity_sweeps(test_data, equal_levels)
    print(f"Found {len(sweeps)} sweeps")