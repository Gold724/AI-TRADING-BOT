#!/usr/bin/env python3
"""
AI Trading Sentinel - News Guard
TRAE-SentinelOps: Economic news and event-based trading restrictions

Manages:
1. Economic calendar integration
2. High-impact news detection
3. Pre/post-event trading restrictions
4. Volatility spike protection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import requests
from pathlib import Path

class EventImpact(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventStatus(Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    PASSED = "passed"

@dataclass
class EconomicEvent:
    id: str
    title: str
    country: str
    currency: str
    impact: EventImpact
    datetime_utc: datetime
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    description: Optional[str] = None
    source: str = "manual"

@dataclass
class NewsGuardStatus:
    is_restricted: bool
    restriction_reason: str
    active_events: List[EconomicEvent]
    upcoming_events: List[EconomicEvent]
    restriction_until: Optional[datetime]
    risk_level: str  # low, medium, high, critical
    notes: str

class NewsGuard:
    """
    Comprehensive news and economic event guard system.
    Prevents trading during high-impact news events.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.ENABLED = self.config.get('enabled', True)
        self.HIGH_IMPACT_BUFFER_MINUTES = self.config.get('high_impact_buffer_minutes', 30)
        self.MEDIUM_IMPACT_BUFFER_MINUTES = self.config.get('medium_impact_buffer_minutes', 15)
        self.CRITICAL_IMPACT_BUFFER_MINUTES = self.config.get('critical_impact_buffer_minutes', 60)
        self.MONITORED_CURRENCIES = self.config.get('monitored_currencies', ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'])
        self.AUTO_UPDATE_INTERVAL = self.config.get('auto_update_interval_hours', 6)
        
        # Data storage
        self.events_cache = []
        self.last_update = None
        self.cache_file = Path(self.config.get('cache_file', 'data/economic_events.json'))
        
        # High-impact event keywords
        self.HIGH_IMPACT_KEYWORDS = [
            'NFP', 'Non-Farm Payrolls', 'Employment', 'Unemployment Rate',
            'FOMC', 'Federal Reserve', 'Interest Rate', 'Rate Decision',
            'GDP', 'Gross Domestic Product', 'Inflation', 'CPI', 'Consumer Price Index',
            'PPI', 'Producer Price Index', 'Retail Sales', 'Manufacturing PMI',
            'Services PMI', 'Trade Balance', 'Current Account', 'Central Bank',
            'ECB', 'Bank of England', 'Bank of Japan', 'RBA', 'SNB', 'BoC'
        ]
        
        # Initialize
        self._load_cached_events()
        
    def _load_cached_events(self):
        """
        Load cached economic events from file.
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    
                self.events_cache = []
                for event_data in data.get('events', []):
                    event = EconomicEvent(
                        id=event_data['id'],
                        title=event_data['title'],
                        country=event_data['country'],
                        currency=event_data['currency'],
                        impact=EventImpact(event_data['impact']),
                        datetime_utc=datetime.fromisoformat(event_data['datetime_utc']),
                        forecast=event_data.get('forecast'),
                        previous=event_data.get('previous'),
                        actual=event_data.get('actual'),
                        description=event_data.get('description'),
                        source=event_data.get('source', 'cached')
                    )
                    self.events_cache.append(event)
                
                self.last_update = datetime.fromisoformat(data.get('last_update', datetime.utcnow().isoformat()))
                self.logger.info(f"Loaded {len(self.events_cache)} cached events")
            else:
                self.logger.info("No cached events found, will fetch fresh data")
                
        except Exception as e:
            self.logger.error(f"Error loading cached events: {e}")
            self.events_cache = []
            self.last_update = None
    
    def _save_events_cache(self):
        """
        Save economic events to cache file.
        """
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'last_update': datetime.utcnow().isoformat(),
                'events': []
            }
            
            for event in self.events_cache:
                event_data = {
                    'id': event.id,
                    'title': event.title,
                    'country': event.country,
                    'currency': event.currency,
                    'impact': event.impact.value,
                    'datetime_utc': event.datetime_utc.isoformat(),
                    'forecast': event.forecast,
                    'previous': event.previous,
                    'actual': event.actual,
                    'description': event.description,
                    'source': event.source
                }
                data['events'].append(event_data)
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved {len(self.events_cache)} events to cache")
            
        except Exception as e:
            self.logger.error(f"Error saving events cache: {e}")
    
    def update_economic_calendar(self, force: bool = False) -> bool:
        """
        Update economic calendar from external sources.
        
        Args:
            force: Force update even if recently updated
            
        Returns:
            True if update was successful
        """
        if not self.ENABLED:
            return True
        
        try:
            # Check if update is needed
            if not force and self.last_update:
                time_since_update = datetime.utcnow() - self.last_update
                if time_since_update.total_seconds() < (self.AUTO_UPDATE_INTERVAL * 3600):
                    self.logger.debug("Economic calendar recently updated, skipping")
                    return True
            
            # Try multiple sources
            success = False
            
            # Source 1: ForexFactory (if API available)
            if not success:
                success = self._fetch_from_forexfactory()
            
            # Source 2: Investing.com (if API available)
            if not success:
                success = self._fetch_from_investing()
            
            # Source 3: Manual/Static events (fallback)
            if not success:
                success = self._load_static_events()
            
            if success:
                self.last_update = datetime.utcnow()
                self._save_events_cache()
                self.logger.info(f"Economic calendar updated with {len(self.events_cache)} events")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating economic calendar: {e}")
            return False
    
    def _fetch_from_forexfactory(self) -> bool:
        """
        Fetch events from ForexFactory (placeholder - requires API key).
        """
        try:
            # This would require ForexFactory API access
            # For now, return False to use fallback
            self.logger.debug("ForexFactory API not configured")
            return False
            
        except Exception as e:
            self.logger.error(f"Error fetching from ForexFactory: {e}")
            return False
    
    def _fetch_from_investing(self) -> bool:
        """
        Fetch events from Investing.com (placeholder - requires API key).
        """
        try:
            # This would require Investing.com API access
            # For now, return False to use fallback
            self.logger.debug("Investing.com API not configured")
            return False
            
        except Exception as e:
            self.logger.error(f"Error fetching from Investing.com: {e}")
            return False
    
    def _load_static_events(self) -> bool:
        """
        Load static/manual economic events as fallback.
        """
        try:
            # Generate some common recurring events
            now = datetime.utcnow()
            static_events = []
            
            # NFP - First Friday of each month at 13:30 UTC
            for month_offset in range(3):  # Next 3 months
                target_month = now.replace(day=1) + timedelta(days=32 * month_offset)
                target_month = target_month.replace(day=1)
                
                # Find first Friday
                first_friday = target_month
                while first_friday.weekday() != 4:  # Friday = 4
                    first_friday += timedelta(days=1)
                
                nfp_time = first_friday.replace(hour=13, minute=30, second=0, microsecond=0)
                
                if nfp_time > now:
                    static_events.append(EconomicEvent(
                        id=f"nfp_{nfp_time.strftime('%Y%m%d')}",
                        title="Non-Farm Payrolls",
                        country="US",
                        currency="USD",
                        impact=EventImpact.HIGH,
                        datetime_utc=nfp_time,
                        description="US employment data release",
                        source="static"
                    ))
            
            # FOMC meetings (8 times per year, roughly every 6 weeks)
            fomc_dates = [
                "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
                "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18"
            ]
            
            for date_str in fomc_dates:
                try:
                    fomc_date = datetime.strptime(date_str, "%Y-%m-%d")
                    fomc_time = fomc_date.replace(hour=19, minute=0)  # 7 PM UTC
                    
                    if fomc_time > now:
                        static_events.append(EconomicEvent(
                            id=f"fomc_{fomc_time.strftime('%Y%m%d')}",
                            title="FOMC Rate Decision",
                            country="US",
                            currency="USD",
                            impact=EventImpact.CRITICAL,
                            datetime_utc=fomc_time,
                            description="Federal Reserve interest rate decision",
                            source="static"
                        ))
                except:
                    continue
            
            # Add events to cache
            self.events_cache.extend(static_events)
            
            # Remove duplicates and sort
            seen_ids = set()
            unique_events = []
            for event in self.events_cache:
                if event.id not in seen_ids:
                    unique_events.append(event)
                    seen_ids.add(event.id)
            
            self.events_cache = sorted(unique_events, key=lambda x: x.datetime_utc)
            
            self.logger.info(f"Loaded {len(static_events)} static events")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading static events: {e}")
            return False
    
    def get_news_guard_status(self, target_time: Optional[datetime] = None) -> NewsGuardStatus:
        """
        Get current news guard status.
        
        Args:
            target_time: Time to check (defaults to now)
            
        Returns:
            NewsGuardStatus with restriction information
        """
        if not self.ENABLED:
            return NewsGuardStatus(
                is_restricted=False,
                restriction_reason="News guard disabled",
                active_events=[],
                upcoming_events=[],
                restriction_until=None,
                risk_level="low",
                notes="News guard is disabled in configuration"
            )
        
        if target_time is None:
            target_time = datetime.utcnow()
        
        try:
            # Update calendar if needed
            self.update_economic_calendar()
            
            # Find relevant events
            active_events = []
            upcoming_events = []
            restriction_until = None
            max_risk_level = "low"
            
            for event in self.events_cache:
                # Skip events for non-monitored currencies
                if event.currency not in self.MONITORED_CURRENCIES:
                    continue
                
                # Calculate buffer time based on impact
                if event.impact == EventImpact.CRITICAL:
                    buffer_minutes = self.CRITICAL_IMPACT_BUFFER_MINUTES
                elif event.impact == EventImpact.HIGH:
                    buffer_minutes = self.HIGH_IMPACT_BUFFER_MINUTES
                elif event.impact == EventImpact.MEDIUM:
                    buffer_minutes = self.MEDIUM_IMPACT_BUFFER_MINUTES
                else:
                    continue  # Skip low impact events
                
                event_start = event.datetime_utc - timedelta(minutes=buffer_minutes)
                event_end = event.datetime_utc + timedelta(minutes=buffer_minutes)
                
                # Check if event is active (within buffer window)
                if event_start <= target_time <= event_end:
                    active_events.append(event)
                    
                    # Update restriction end time
                    if restriction_until is None or event_end > restriction_until:
                        restriction_until = event_end
                    
                    # Update risk level
                    if event.impact == EventImpact.CRITICAL:
                        max_risk_level = "critical"
                    elif event.impact == EventImpact.HIGH and max_risk_level != "critical":
                        max_risk_level = "high"
                    elif event.impact == EventImpact.MEDIUM and max_risk_level not in ["critical", "high"]:
                        max_risk_level = "medium"
                
                # Check if event is upcoming (within next 4 hours)
                elif event.datetime_utc > target_time and event.datetime_utc <= target_time + timedelta(hours=4):
                    upcoming_events.append(event)
            
            # Determine restriction status
            is_restricted = len(active_events) > 0
            
            if is_restricted:
                event_titles = [event.title for event in active_events]
                restriction_reason = f"High-impact news events active: {', '.join(event_titles)}"
                notes = f"Trading restricted due to {len(active_events)} active event(s)"
            else:
                restriction_reason = "No active high-impact events"
                if upcoming_events:
                    next_event = min(upcoming_events, key=lambda x: x.datetime_utc)
                    time_to_next = next_event.datetime_utc - target_time
                    notes = f"Next event: {next_event.title} in {time_to_next}"
                else:
                    notes = "No upcoming high-impact events in next 4 hours"
            
            return NewsGuardStatus(
                is_restricted=is_restricted,
                restriction_reason=restriction_reason,
                active_events=active_events,
                upcoming_events=upcoming_events[:5],  # Limit to next 5 events
                restriction_until=restriction_until,
                risk_level=max_risk_level,
                notes=notes
            )
            
        except Exception as e:
            self.logger.error(f"Error getting news guard status: {e}")
            return self._get_default_news_status()
    
    def _get_default_news_status(self) -> NewsGuardStatus:
        """
        Return default news status for error cases.
        """
        return NewsGuardStatus(
            is_restricted=True,  # Err on the side of caution
            restriction_reason="News guard system error",
            active_events=[],
            upcoming_events=[],
            restriction_until=None,
            risk_level="high",
            notes="News guard system encountered an error - trading restricted as precaution"
        )
    
    def is_trading_allowed(self, target_time: Optional[datetime] = None) -> bool:
        """
        Simple check if trading is allowed based on news events.
        
        Args:
            target_time: Time to check (defaults to now)
            
        Returns:
            True if trading is allowed
        """
        status = self.get_news_guard_status(target_time)
        return not status.is_restricted
    
    def add_manual_event(self, event: EconomicEvent) -> bool:
        """
        Add a manual economic event.
        
        Args:
            event: EconomicEvent to add
            
        Returns:
            True if event was added successfully
        """
        try:
            # Check for duplicates
            existing_ids = [e.id for e in self.events_cache]
            if event.id in existing_ids:
                self.logger.warning(f"Event {event.id} already exists")
                return False
            
            self.events_cache.append(event)
            self.events_cache.sort(key=lambda x: x.datetime_utc)
            
            self._save_events_cache()
            self.logger.info(f"Added manual event: {event.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding manual event: {e}")
            return False
    
    def get_upcoming_events(self, hours: int = 24) -> List[EconomicEvent]:
        """
        Get upcoming economic events in the next N hours.
        
        Args:
            hours: Number of hours to look ahead
            
        Returns:
            List of upcoming events
        """
        try:
            now = datetime.utcnow()
            end_time = now + timedelta(hours=hours)
            
            upcoming = []
            for event in self.events_cache:
                if now <= event.datetime_utc <= end_time:
                    if event.currency in self.MONITORED_CURRENCIES:
                        upcoming.append(event)
            
            return sorted(upcoming, key=lambda x: x.datetime_utc)
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming events: {e}")
            return []
    
    def get_event_summary(self) -> Dict:
        """
        Get summary of economic events and news guard status.
        
        Returns:
            Dictionary with event summary
        """
        try:
            status = self.get_news_guard_status()
            upcoming = self.get_upcoming_events(24)
            
            return {
                'enabled': self.ENABLED,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'total_events_cached': len(self.events_cache),
                'current_status': {
                    'is_restricted': status.is_restricted,
                    'risk_level': status.risk_level,
                    'active_events': len(status.active_events),
                    'restriction_until': status.restriction_until.isoformat() if status.restriction_until else None,
                    'notes': status.notes
                },
                'upcoming_24h': {
                    'total': len(upcoming),
                    'high_impact': len([e for e in upcoming if e.impact in [EventImpact.HIGH, EventImpact.CRITICAL]]),
                    'next_event': {
                        'title': upcoming[0].title,
                        'time': upcoming[0].datetime_utc.isoformat(),
                        'impact': upcoming[0].impact.value,
                        'currency': upcoming[0].currency
                    } if upcoming else None
                },
                'monitored_currencies': self.MONITORED_CURRENCIES,
                'buffer_settings': {
                    'critical': self.CRITICAL_IMPACT_BUFFER_MINUTES,
                    'high': self.HIGH_IMPACT_BUFFER_MINUTES,
                    'medium': self.MEDIUM_IMPACT_BUFFER_MINUTES
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating event summary: {e}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    # Initialize news guard
    config = {
        'enabled': True,
        'high_impact_buffer_minutes': 30,
        'medium_impact_buffer_minutes': 15,
        'critical_impact_buffer_minutes': 60,
        'monitored_currencies': ['USD', 'EUR', 'GBP', 'JPY'],
        'auto_update_interval_hours': 6,
        'cache_file': 'data/economic_events.json'
    }
    
    news_guard = NewsGuard(config)
    
    # Update calendar
    success = news_guard.update_economic_calendar(force=True)
    print(f"Calendar update success: {success}")
    
    # Get current status
    status = news_guard.get_news_guard_status()
    print(f"Trading restricted: {status.is_restricted}")
    print(f"Risk level: {status.risk_level}")
    print(f"Active events: {len(status.active_events)}")
    print(f"Notes: {status.notes}")
    
    # Check if trading is allowed
    can_trade = news_guard.is_trading_allowed()
    print(f"Can trade now: {can_trade}")
    
    # Get upcoming events
    upcoming = news_guard.get_upcoming_events(24)
    print(f"Upcoming events (24h): {len(upcoming)}")
    
    # Get summary
    summary = news_guard.get_event_summary()
    print(f"Summary: {json.dumps(summary, indent=2)}")