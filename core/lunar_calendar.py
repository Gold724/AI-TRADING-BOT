#!/usr/bin/env python3
"""
AI Trading Sentinel - Lunar Calendar Module
TRAE-SentinelOps: Optional lunar timing for volatility and risk modulation

Provides:
1. Moon phase calculations and tracking
2. Volatility expectations based on lunar cycles
3. Risk adjustment recommendations
4. Market timing insights (optional enhancement)
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class MoonPhase(Enum):
    NEW_MOON = "new"
    WAXING_CRESCENT = "waxing_crescent"
    FIRST_QUARTER = "first_quarter"
    WAXING_GIBBOUS = "waxing_gibbous"
    FULL_MOON = "full"
    WANING_GIBBOUS = "waning_gibbous"
    LAST_QUARTER = "last_quarter"
    WANING_CRESCENT = "waning_crescent"

@dataclass
class LunarData:
    phase: MoonPhase
    illumination: float  # 0.0 to 1.0
    age_days: float  # Days since new moon
    distance_km: float  # Distance to moon
    angular_diameter: float  # Angular size in degrees
    next_new_moon: datetime
    next_full_moon: datetime

@dataclass
class MarketExpectation:
    volatility_bias: str  # "expansion", "contraction", "neutral"
    risk_adjustment: float  # -0.15 to +0.15 (percentage adjustment)
    confidence: float  # 0.0 to 1.0
    notes: str

class LunarCalendar:
    """
    Lunar calendar for market timing and volatility analysis.
    Based on astronomical calculations and market observation patterns.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.WINDOW_DAYS = self.config.get('lunar_window_days', 1)  # ±1 day around events
        self.MAX_ADJUSTMENT = self.config.get('max_adjustment', 0.15)  # ±15%
        self.ENABLE_DISTANCE_FACTOR = self.config.get('enable_distance_factor', True)
        
        # Known lunar constants
        self.SYNODIC_MONTH = 29.530588853  # Average lunar cycle length
        self.KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14)  # Reference new moon
        
    def get_current_phase(self, target_date: Optional[datetime] = None) -> Dict[str, any]:
        """
        Get current moon phase and related data.
        
        Args:
            target_date: Date to analyze (defaults to now)
            
        Returns:
            Dictionary with phase information
        """
        if target_date is None:
            target_date = datetime.utcnow()
        
        try:
            lunar_data = self._calculate_lunar_data(target_date)
            market_expectation = self._get_market_expectation(lunar_data, target_date)
            
            # Determine if we're in a significant window
            window_info = self._get_window_info(lunar_data, target_date)
            
            return {
                'phase': lunar_data.phase.value,
                'illumination': lunar_data.illumination,
                'age_days': lunar_data.age_days,
                'window': window_info['window'],
                'adjustment': f"{market_expectation.risk_adjustment:+.0%}",
                'volatility_bias': market_expectation.volatility_bias,
                'confidence': market_expectation.confidence,
                'notes': market_expectation.notes,
                'next_events': {
                    'new_moon': lunar_data.next_new_moon.isoformat(),
                    'full_moon': lunar_data.next_full_moon.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating lunar phase: {e}")
            return self._get_neutral_phase()
    
    def _calculate_lunar_data(self, target_date: datetime) -> LunarData:
        """
        Calculate detailed lunar data for the target date.
        """
        # Calculate days since known new moon
        delta = target_date - self.KNOWN_NEW_MOON
        days_since_reference = delta.total_seconds() / 86400.0
        
        # Calculate current lunar age
        lunar_age = days_since_reference % self.SYNODIC_MONTH
        
        # Calculate illumination (0 = new moon, 0.5 = full moon)
        illumination_cycle = lunar_age / self.SYNODIC_MONTH
        if illumination_cycle <= 0.5:
            illumination = illumination_cycle * 2  # Waxing
        else:
            illumination = 2 - (illumination_cycle * 2)  # Waning
        
        # Determine phase
        phase = self._get_phase_from_age(lunar_age)
        
        # Calculate next events
        next_new_moon = self._get_next_new_moon(target_date)
        next_full_moon = self._get_next_full_moon(target_date)
        
        # Calculate distance (simplified - varies ~356,500 to 406,700 km)
        distance_variation = math.sin(illumination_cycle * 2 * math.pi) * 25000
        distance_km = 384400 + distance_variation  # Average distance ± variation
        
        # Angular diameter (inversely related to distance)
        angular_diameter = 0.5181 * (384400 / distance_km)  # degrees
        
        return LunarData(
            phase=phase,
            illumination=illumination,
            age_days=lunar_age,
            distance_km=distance_km,
            angular_diameter=angular_diameter,
            next_new_moon=next_new_moon,
            next_full_moon=next_full_moon
        )
    
    def _get_phase_from_age(self, lunar_age: float) -> MoonPhase:
        """
        Determine moon phase from lunar age in days.
        """
        # Normalize to 0-1 range
        phase_fraction = lunar_age / self.SYNODIC_MONTH
        
        if phase_fraction < 0.0625:  # 0-1.84 days
            return MoonPhase.NEW_MOON
        elif phase_fraction < 0.1875:  # 1.84-5.53 days
            return MoonPhase.WAXING_CRESCENT
        elif phase_fraction < 0.3125:  # 5.53-9.22 days
            return MoonPhase.FIRST_QUARTER
        elif phase_fraction < 0.4375:  # 9.22-12.91 days
            return MoonPhase.WAXING_GIBBOUS
        elif phase_fraction < 0.5625:  # 12.91-16.61 days
            return MoonPhase.FULL_MOON
        elif phase_fraction < 0.6875:  # 16.61-20.30 days
            return MoonPhase.WANING_GIBBOUS
        elif phase_fraction < 0.8125:  # 20.30-23.99 days
            return MoonPhase.LAST_QUARTER
        else:  # 23.99-29.53 days
            return MoonPhase.WANING_CRESCENT
    
    def _get_next_new_moon(self, from_date: datetime) -> datetime:
        """
        Calculate next new moon date.
        """
        delta = from_date - self.KNOWN_NEW_MOON
        days_since_reference = delta.total_seconds() / 86400.0
        
        # Find next new moon cycle
        current_cycle = int(days_since_reference / self.SYNODIC_MONTH)
        next_cycle = current_cycle + 1
        
        days_to_next = next_cycle * self.SYNODIC_MONTH
        return self.KNOWN_NEW_MOON + timedelta(days=days_to_next)
    
    def _get_next_full_moon(self, from_date: datetime) -> datetime:
        """
        Calculate next full moon date.
        """
        next_new = self._get_next_new_moon(from_date)
        
        # Full moon is approximately 14.76 days after new moon
        full_moon_offset = self.SYNODIC_MONTH / 2
        
        # Check if full moon is before or after next new moon
        potential_full = next_new - timedelta(days=full_moon_offset)
        
        if potential_full > from_date:
            return potential_full
        else:
            return next_new + timedelta(days=full_moon_offset)
    
    def _get_market_expectation(self, lunar_data: LunarData, 
                               target_date: datetime) -> MarketExpectation:
        """
        Generate market expectations based on lunar data.
        
        Based on observed patterns:
        - New moon periods: Tend toward expansion/breakouts
        - Full moon periods: Tend toward mean reversion/consolidation
        - Distance effects: Closer moon = stronger gravitational effects
        """
        phase = lunar_data.phase
        illumination = lunar_data.illumination
        
        # Base expectations by phase
        if phase in [MoonPhase.NEW_MOON, MoonPhase.WAXING_CRESCENT]:
            volatility_bias = "expansion"
            base_adjustment = 0.10  # +10% bias toward expansion
            confidence = 0.7
            notes = "New moon window: expect breakouts and trend continuation"
            
        elif phase in [MoonPhase.FULL_MOON, MoonPhase.WANING_GIBBOUS]:
            volatility_bias = "contraction"
            base_adjustment = -0.10  # -10% bias toward mean reversion
            confidence = 0.7
            notes = "Full moon window: expect mean reversion and consolidation"
            
        elif phase in [MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER]:
            volatility_bias = "neutral"
            base_adjustment = 0.05 if phase == MoonPhase.FIRST_QUARTER else -0.05
            confidence = 0.4
            notes = f"{phase.value.replace('_', ' ').title()}: moderate directional bias"
            
        else:  # Transitional phases
            volatility_bias = "neutral"
            base_adjustment = 0.0
            confidence = 0.3
            notes = "Transitional lunar phase: minimal bias"
        
        # Adjust for lunar distance (perigee/apogee effects)
        if self.ENABLE_DISTANCE_FACTOR:
            # Closer moon = stronger effects
            distance_factor = (406700 - lunar_data.distance_km) / (406700 - 356500)
            distance_multiplier = 0.5 + (distance_factor * 0.5)  # 0.5 to 1.0
            base_adjustment *= distance_multiplier
            confidence *= (0.7 + distance_factor * 0.3)  # Boost confidence for closer moon
        
        # Cap adjustment at maximum
        final_adjustment = max(-self.MAX_ADJUSTMENT, 
                              min(self.MAX_ADJUSTMENT, base_adjustment))
        
        return MarketExpectation(
            volatility_bias=volatility_bias,
            risk_adjustment=final_adjustment,
            confidence=min(1.0, confidence),
            notes=notes
        )
    
    def _get_window_info(self, lunar_data: LunarData, target_date: datetime) -> Dict[str, str]:
        """
        Determine if we're in a significant lunar window.
        """
        # Check distance to new moon
        days_to_new = (lunar_data.next_new_moon - target_date).total_seconds() / 86400
        days_from_last_new = lunar_data.age_days
        
        # Check distance to full moon
        days_to_full = (lunar_data.next_full_moon - target_date).total_seconds() / 86400
        days_from_last_full = abs(lunar_data.age_days - self.SYNODIC_MONTH / 2)
        
        # Determine window
        if days_from_last_new <= self.WINDOW_DAYS or days_to_new <= self.WINDOW_DAYS:
            if days_from_last_new <= self.WINDOW_DAYS:
                return {'window': 'post', 'event': 'new_moon'}
            else:
                return {'window': 'pre', 'event': 'new_moon'}
                
        elif days_from_last_full <= self.WINDOW_DAYS or days_to_full <= self.WINDOW_DAYS:
            if days_from_last_full <= self.WINDOW_DAYS:
                return {'window': 'post', 'event': 'full_moon'}
            else:
                return {'window': 'pre', 'event': 'full_moon'}
        
        return {'window': 'none', 'event': 'none'}
    
    def _get_neutral_phase(self) -> Dict[str, any]:
        """
        Return neutral phase data for error cases.
        """
        return {
            'phase': 'none',
            'illumination': 0.5,
            'age_days': 14.76,
            'window': 'none',
            'adjustment': '0%',
            'volatility_bias': 'neutral',
            'confidence': 0.0,
            'notes': 'Lunar data unavailable',
            'next_events': {
                'new_moon': (datetime.utcnow() + timedelta(days=15)).isoformat(),
                'full_moon': (datetime.utcnow() + timedelta(days=15)).isoformat()
            }
        }
    
    def get_lunar_calendar(self, start_date: datetime, days: int = 30) -> List[Dict]:
        """
        Generate lunar calendar for a date range.
        
        Args:
            start_date: Starting date
            days: Number of days to generate
            
        Returns:
            List of daily lunar data
        """
        calendar = []
        
        try:
            for i in range(days):
                current_date = start_date + timedelta(days=i)
                phase_data = self.get_current_phase(current_date)
                
                calendar.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'phase': phase_data['phase'],
                    'illumination': phase_data['illumination'],
                    'volatility_bias': phase_data['volatility_bias'],
                    'adjustment': phase_data['adjustment'],
                    'window': phase_data['window']
                })
            
            return calendar
            
        except Exception as e:
            self.logger.error(f"Error generating lunar calendar: {e}")
            return []
    
    def is_significant_lunar_event(self, target_date: Optional[datetime] = None) -> bool:
        """
        Check if the target date is during a significant lunar event.
        
        Args:
            target_date: Date to check (defaults to now)
            
        Returns:
            True if within window of new/full moon
        """
        phase_data = self.get_current_phase(target_date)
        return phase_data['window'] != 'none'
    
    def get_risk_multiplier(self, target_date: Optional[datetime] = None) -> float:
        """
        Get risk multiplier based on lunar phase.
        
        Args:
            target_date: Date to analyze (defaults to now)
            
        Returns:
            Risk multiplier (0.85 to 1.15)
        """
        phase_data = self.get_current_phase(target_date)
        adjustment_str = phase_data['adjustment'].rstrip('%')
        adjustment_pct = float(adjustment_str) / 100.0
        
        return 1.0 + adjustment_pct

# Example usage and testing
if __name__ == "__main__":
    # Initialize lunar calendar
    lunar = LunarCalendar({
        'lunar_window_days': 1,
        'max_adjustment': 0.15,
        'enable_distance_factor': True
    })
    
    # Get current phase
    current_phase = lunar.get_current_phase()
    print(f"Current lunar phase: {current_phase['phase']}")
    print(f"Volatility bias: {current_phase['volatility_bias']}")
    print(f"Risk adjustment: {current_phase['adjustment']}")
    print(f"Window: {current_phase['window']}")
    print(f"Notes: {current_phase['notes']}")
    
    # Check if significant event
    is_significant = lunar.is_significant_lunar_event()
    print(f"Significant lunar event: {is_significant}")
    
    # Get risk multiplier
    risk_multiplier = lunar.get_risk_multiplier()
    print(f"Risk multiplier: {risk_multiplier:.3f}")
    
    # Generate 7-day calendar
    calendar = lunar.get_lunar_calendar(datetime.utcnow(), 7)
    print("\n7-Day Lunar Calendar:")
    for day in calendar:
        print(f"{day['date']}: {day['phase']} ({day['volatility_bias']}, {day['adjustment']})")