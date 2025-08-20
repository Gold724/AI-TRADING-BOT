#!/usr/bin/env python3
"""
AI Trading Sentinel - Session Manager
TRAE-SentinelOps: Trading session validation and timing controls

Manages:
1. Market session detection (FX, Futures, Crypto)
2. Session-based trading rules and restrictions
3. Rollover and gap risk management
4. Holiday and low-liquidity period detection
"""

import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pytz

class MarketType(Enum):
    FOREX = "FX"
    FUTURES = "FUTURES"
    CRYPTO = "CRYPTO"
    STOCKS = "STOCKS"

class SessionType(Enum):
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    SYDNEY = "sydney"
    OVERLAP_LONDON_NY = "london_ny_overlap"
    OVERLAP_ASIAN_LONDON = "asian_london_overlap"

@dataclass
class TradingSession:
    name: str
    start_time: time
    end_time: time
    timezone: str
    market_type: MarketType
    liquidity_score: int  # 1-10 (10 = highest liquidity)
    volatility_score: int  # 1-10 (10 = highest volatility)
    enabled: bool = True

@dataclass
class SessionStatus:
    is_active: bool
    current_session: Optional[SessionType]
    next_session: Optional[SessionType]
    time_to_next: Optional[timedelta]
    liquidity_score: int
    volatility_score: int
    rollover_risk: bool
    notes: str

class SessionManager:
    """
    Comprehensive trading session manager with multi-market support.
    Handles session detection, liquidity assessment, and risk controls.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.MARKET_TYPE = MarketType(self.config.get('market_type', 'FX'))
        self.ENABLED_SESSIONS = self.config.get('enabled_sessions', ['london', 'new_york'])
        self.MIN_LIQUIDITY_SCORE = self.config.get('min_liquidity_score', 6)
        self.ROLLOVER_BUFFER_MINUTES = self.config.get('rollover_buffer_minutes', 30)
        self.WEEKEND_TRADING = self.config.get('weekend_trading', False)
        
        # Initialize sessions
        self.sessions = self._initialize_sessions()
        self.holidays = self._load_market_holidays()
        
    def _initialize_sessions(self) -> Dict[SessionType, TradingSession]:
        """
        Initialize trading sessions based on market type.
        """
        sessions = {}
        
        if self.MARKET_TYPE == MarketType.FOREX:
            sessions.update({
                SessionType.SYDNEY: TradingSession(
                    name="Sydney",
                    start_time=time(22, 0),  # 10 PM UTC (Sydney open)
                    end_time=time(7, 0),     # 7 AM UTC (Sydney close)
                    timezone="Australia/Sydney",
                    market_type=MarketType.FOREX,
                    liquidity_score=4,
                    volatility_score=3
                ),
                SessionType.ASIAN: TradingSession(
                    name="Tokyo",
                    start_time=time(0, 0),   # 12 AM UTC (Tokyo open)
                    end_time=time(9, 0),     # 9 AM UTC (Tokyo close)
                    timezone="Asia/Tokyo",
                    market_type=MarketType.FOREX,
                    liquidity_score=6,
                    volatility_score=5
                ),
                SessionType.LONDON: TradingSession(
                    name="London",
                    start_time=time(8, 0),   # 8 AM UTC (London open)
                    end_time=time(17, 0),    # 5 PM UTC (London close)
                    timezone="Europe/London",
                    market_type=MarketType.FOREX,
                    liquidity_score=9,
                    volatility_score=8
                ),
                SessionType.NEW_YORK: TradingSession(
                    name="New York",
                    start_time=time(13, 0),  # 1 PM UTC (NY open)
                    end_time=time(22, 0),    # 10 PM UTC (NY close)
                    timezone="America/New_York",
                    market_type=MarketType.FOREX,
                    liquidity_score=10,
                    volatility_score=9
                ),
                SessionType.OVERLAP_LONDON_NY: TradingSession(
                    name="London-NY Overlap",
                    start_time=time(13, 0),  # 1 PM UTC
                    end_time=time(17, 0),    # 5 PM UTC
                    timezone="UTC",
                    market_type=MarketType.FOREX,
                    liquidity_score=10,
                    volatility_score=10
                )
            })
            
        elif self.MARKET_TYPE == MarketType.FUTURES:
            sessions.update({
                SessionType.ASIAN: TradingSession(
                    name="Asian Futures",
                    start_time=time(0, 0),
                    end_time=time(9, 0),
                    timezone="Asia/Tokyo",
                    market_type=MarketType.FUTURES,
                    liquidity_score=7,
                    volatility_score=6
                ),
                SessionType.LONDON: TradingSession(
                    name="European Futures",
                    start_time=time(7, 0),
                    end_time=time(16, 0),
                    timezone="Europe/London",
                    market_type=MarketType.FUTURES,
                    liquidity_score=8,
                    volatility_score=7
                ),
                SessionType.NEW_YORK: TradingSession(
                    name="US Futures",
                    start_time=time(14, 30),  # CME open
                    end_time=time(21, 0),     # CME close
                    timezone="America/Chicago",
                    market_type=MarketType.FUTURES,
                    liquidity_score=9,
                    volatility_score=8
                )
            })
            
        elif self.MARKET_TYPE == MarketType.CRYPTO:
            # Crypto trades 24/7, but we can still define high-activity periods
            sessions.update({
                SessionType.ASIAN: TradingSession(
                    name="Asian Crypto",
                    start_time=time(0, 0),
                    end_time=time(8, 0),
                    timezone="UTC",
                    market_type=MarketType.CRYPTO,
                    liquidity_score=7,
                    volatility_score=6
                ),
                SessionType.LONDON: TradingSession(
                    name="European Crypto",
                    start_time=time(8, 0),
                    end_time=time(16, 0),
                    timezone="UTC",
                    market_type=MarketType.CRYPTO,
                    liquidity_score=8,
                    volatility_score=7
                ),
                SessionType.NEW_YORK: TradingSession(
                    name="US Crypto",
                    start_time=time(16, 0),
                    end_time=time(0, 0),
                    timezone="UTC",
                    market_type=MarketType.CRYPTO,
                    liquidity_score=9,
                    volatility_score=8
                )
            })
        
        # Filter by enabled sessions
        enabled_sessions = {}
        for session_type, session in sessions.items():
            if session.name.lower().replace(' ', '_').replace('-', '_') in [s.lower() for s in self.ENABLED_SESSIONS]:
                enabled_sessions[session_type] = session
        
        return enabled_sessions
    
    def _load_market_holidays(self) -> List[datetime]:
        """
        Load market holidays for the current year.
        """
        # This would typically load from a database or API
        # For now, return major holidays
        current_year = datetime.now().year
        
        holidays = [
            datetime(current_year, 1, 1),   # New Year's Day
            datetime(current_year, 12, 25), # Christmas
            datetime(current_year, 7, 4),   # US Independence Day
            # Add more holidays as needed
        ]
        
        return holidays
    
    def get_current_session_status(self, target_time: Optional[datetime] = None) -> SessionStatus:
        """
        Get current trading session status.
        
        Args:
            target_time: Time to check (defaults to now)
            
        Returns:
            SessionStatus with current session information
        """
        if target_time is None:
            target_time = datetime.utcnow()
        
        try:
            # Check if it's a weekend and weekend trading is disabled
            if not self.WEEKEND_TRADING and target_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return SessionStatus(
                    is_active=False,
                    current_session=None,
                    next_session=self._get_next_session(target_time),
                    time_to_next=self._get_time_to_next_session(target_time),
                    liquidity_score=0,
                    volatility_score=0,
                    rollover_risk=False,
                    notes="Weekend - markets closed"
                )
            
            # Check for holidays
            if self._is_holiday(target_time):
                return SessionStatus(
                    is_active=False,
                    current_session=None,
                    next_session=self._get_next_session(target_time),
                    time_to_next=self._get_time_to_next_session(target_time),
                    liquidity_score=0,
                    volatility_score=0,
                    rollover_risk=False,
                    notes="Market holiday"
                )
            
            # Find active sessions
            active_sessions = self._get_active_sessions(target_time)
            
            if not active_sessions:
                return SessionStatus(
                    is_active=False,
                    current_session=None,
                    next_session=self._get_next_session(target_time),
                    time_to_next=self._get_time_to_next_session(target_time),
                    liquidity_score=0,
                    volatility_score=0,
                    rollover_risk=False,
                    notes="No active trading sessions"
                )
            
            # Get the best session (highest liquidity)
            best_session = max(active_sessions, key=lambda x: x[1].liquidity_score)
            session_type, session = best_session
            
            # Check rollover risk
            rollover_risk = self._check_rollover_risk(target_time)
            
            # Check if liquidity meets minimum requirements
            meets_liquidity = session.liquidity_score >= self.MIN_LIQUIDITY_SCORE
            
            return SessionStatus(
                is_active=meets_liquidity and not rollover_risk,
                current_session=session_type,
                next_session=self._get_next_session(target_time),
                time_to_next=self._get_time_to_next_session(target_time),
                liquidity_score=session.liquidity_score,
                volatility_score=session.volatility_score,
                rollover_risk=rollover_risk,
                notes=f"Active: {session.name}" + (" (rollover risk)" if rollover_risk else "")
            )
            
        except Exception as e:
            self.logger.error(f"Error getting session status: {e}")
            return self._get_default_session_status()
    
    def _get_active_sessions(self, target_time: datetime) -> List[Tuple[SessionType, TradingSession]]:
        """
        Get all currently active sessions.
        """
        active = []
        current_time = target_time.time()
        
        for session_type, session in self.sessions.items():
            if self._is_session_active(session, current_time):
                active.append((session_type, session))
        
        return active
    
    def _is_session_active(self, session: TradingSession, current_time: time) -> bool:
        """
        Check if a session is currently active.
        """
        start = session.start_time
        end = session.end_time
        
        # Handle sessions that cross midnight
        if start > end:
            return current_time >= start or current_time <= end
        else:
            return start <= current_time <= end
    
    def _check_rollover_risk(self, target_time: datetime) -> bool:
        """
        Check if we're in a rollover risk period.
        """
        if self.MARKET_TYPE != MarketType.FOREX:
            return False
        
        # FX rollover typically happens around 5 PM EST (22:00 UTC)
        rollover_time = time(22, 0)  # 10 PM UTC
        buffer_minutes = self.ROLLOVER_BUFFER_MINUTES
        
        current_time = target_time.time()
        
        # Create rollover window
        rollover_start = (datetime.combine(datetime.today(), rollover_time) - 
                         timedelta(minutes=buffer_minutes)).time()
        rollover_end = (datetime.combine(datetime.today(), rollover_time) + 
                       timedelta(minutes=buffer_minutes)).time()
        
        # Handle midnight crossing
        if rollover_start > rollover_end:
            return current_time >= rollover_start or current_time <= rollover_end
        else:
            return rollover_start <= current_time <= rollover_end
    
    def _is_holiday(self, target_time: datetime) -> bool:
        """
        Check if the target time falls on a market holiday.
        """
        target_date = target_time.date()
        return any(holiday.date() == target_date for holiday in self.holidays)
    
    def _get_next_session(self, target_time: datetime) -> Optional[SessionType]:
        """
        Get the next trading session.
        """
        if not self.sessions:
            return None
        
        current_time = target_time.time()
        next_sessions = []
        
        for session_type, session in self.sessions.items():
            # Calculate time until session starts
            if current_time < session.start_time:
                # Session starts today
                time_diff = datetime.combine(datetime.today(), session.start_time) - \
                           datetime.combine(datetime.today(), current_time)
            else:
                # Session starts tomorrow
                tomorrow = datetime.today() + timedelta(days=1)
                time_diff = datetime.combine(tomorrow, session.start_time) - \
                           datetime.combine(datetime.today(), current_time)
            
            next_sessions.append((session_type, time_diff))
        
        # Return the session that starts soonest
        if next_sessions:
            return min(next_sessions, key=lambda x: x[1])[0]
        
        return None
    
    def _get_time_to_next_session(self, target_time: datetime) -> Optional[timedelta]:
        """
        Get time until next trading session.
        """
        next_session_type = self._get_next_session(target_time)
        
        if not next_session_type or next_session_type not in self.sessions:
            return None
        
        next_session = self.sessions[next_session_type]
        current_time = target_time.time()
        
        if current_time < next_session.start_time:
            # Session starts today
            return datetime.combine(datetime.today(), next_session.start_time) - \
                   datetime.combine(datetime.today(), current_time)
        else:
            # Session starts tomorrow
            tomorrow = datetime.today() + timedelta(days=1)
            return datetime.combine(tomorrow, next_session.start_time) - \
                   datetime.combine(datetime.today(), current_time)
    
    def _get_default_session_status(self) -> SessionStatus:
        """
        Return default session status for error cases.
        """
        return SessionStatus(
            is_active=False,
            current_session=None,
            next_session=None,
            time_to_next=None,
            liquidity_score=0,
            volatility_score=0,
            rollover_risk=False,
            notes="Session data unavailable"
        )
    
    def is_trading_session(self, target_time: Optional[datetime] = None) -> bool:
        """
        Simple check if trading is allowed at the target time.
        
        Args:
            target_time: Time to check (defaults to now)
            
        Returns:
            True if trading is allowed
        """
        status = self.get_current_session_status(target_time)
        return status.is_active
    
    def get_session_schedule(self, days: int = 7) -> List[Dict]:
        """
        Get trading session schedule for the next N days.
        
        Args:
            days: Number of days to generate schedule for
            
        Returns:
            List of daily session schedules
        """
        schedule = []
        start_date = datetime.utcnow().date()
        
        try:
            for i in range(days):
                current_date = start_date + timedelta(days=i)
                daily_sessions = []
                
                for session_type, session in self.sessions.items():
                    daily_sessions.append({
                        'name': session.name,
                        'type': session_type.value,
                        'start': session.start_time.strftime('%H:%M'),
                        'end': session.end_time.strftime('%H:%M'),
                        'timezone': session.timezone,
                        'liquidity': session.liquidity_score,
                        'volatility': session.volatility_score
                    })
                
                schedule.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.strftime('%A'),
                    'is_weekend': current_date.weekday() >= 5,
                    'is_holiday': self._is_holiday(datetime.combine(current_date, time())),
                    'sessions': daily_sessions
                })
            
            return schedule
            
        except Exception as e:
            self.logger.error(f"Error generating session schedule: {e}")
            return []
    
    def get_optimal_trading_windows(self, hours: int = 24) -> List[Dict]:
        """
        Get optimal trading windows for the next N hours.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            List of optimal trading windows
        """
        windows = []
        start_time = datetime.utcnow()
        
        try:
            for i in range(hours):
                check_time = start_time + timedelta(hours=i)
                status = self.get_current_session_status(check_time)
                
                if status.is_active and status.liquidity_score >= 8:  # High liquidity
                    windows.append({
                        'start': check_time.strftime('%Y-%m-%d %H:%M UTC'),
                        'session': status.current_session.value if status.current_session else 'unknown',
                        'liquidity': status.liquidity_score,
                        'volatility': status.volatility_score,
                        'notes': status.notes
                    })
            
            return windows
            
        except Exception as e:
            self.logger.error(f"Error finding optimal windows: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    # Initialize session manager for FX
    config = {
        'market_type': 'FX',
        'enabled_sessions': ['london', 'new_york', 'london_ny_overlap'],
        'min_liquidity_score': 7,
        'rollover_buffer_minutes': 30,
        'weekend_trading': False
    }
    
    session_manager = SessionManager(config)
    
    # Get current session status
    status = session_manager.get_current_session_status()
    print(f"Trading active: {status.is_active}")
    print(f"Current session: {status.current_session}")
    print(f"Liquidity score: {status.liquidity_score}")
    print(f"Rollover risk: {status.rollover_risk}")
    print(f"Notes: {status.notes}")
    
    # Check if trading is allowed
    can_trade = session_manager.is_trading_session()
    print(f"Can trade now: {can_trade}")
    
    # Get session schedule
    schedule = session_manager.get_session_schedule(3)
    print(f"\n3-day schedule: {len(schedule)} days")
    
    # Get optimal windows
    windows = session_manager.get_optimal_trading_windows(12)
    print(f"Optimal windows in next 12h: {len(windows)}")