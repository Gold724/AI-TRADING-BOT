from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

@dataclass
class TrailingStopConfig:
    """Configuration for trailing stop loss"""
    initial_stop_atr_multiplier: float = 2.0
    trail_start_profit_atr: float = 1.5  # Start trailing after this profit
    trail_step_atr: float = 0.5  # Move stop by this amount
    min_trail_distance_atr: float = 1.0  # Minimum distance from current price
    max_trail_distance_atr: float = 3.0  # Maximum distance from current price

@dataclass
class PartialProfitConfig:
    """Configuration for partial profit taking"""
    first_target_atr: float = 2.0  # First profit target
    first_target_percentage: float = 0.3  # Take 30% profit at first target
    second_target_atr: float = 4.0  # Second profit target
    second_target_percentage: float = 0.5  # Take 50% of remaining at second target
    final_target_atr: float = 6.0  # Final target for remaining position

@dataclass
class TimeBasedExitConfig:
    """Configuration for time-based exits"""
    london_session_exit_minutes: int = 240  # Exit after 4 hours in London
    ny_session_exit_minutes: int = 300  # Exit after 5 hours in NY
    overlap_session_exit_minutes: int = 180  # Exit after 3 hours in overlap
    max_trade_duration_hours: int = 8  # Maximum trade duration
    friday_exit_hour: int = 15  # Exit all positions by 3 PM on Friday

@dataclass
class ExitSignal:
    """Represents an exit signal"""
    signal_type: str  # 'trailing_stop', 'partial_profit', 'time_based', 'emergency'
    action: str  # 'close_partial', 'close_all', 'update_stop'
    percentage: float = 1.0  # Percentage of position to close
    price: Optional[float] = None  # Specific exit price
    reason: str = ""  # Detailed reason for exit
    urgency: str = "normal"  # 'low', 'normal', 'high', 'emergency'

@dataclass
class PositionTracker:
    """Tracks position state for exit strategies"""
    entry_time: datetime
    entry_price: float
    position_size: float
    original_size: float
    direction: str  # 'long' or 'short'
    session: str  # 'london', 'ny', 'overlap', 'other'
    current_stop: Optional[float] = None
    highest_profit: float = 0.0
    lowest_profit: float = 0.0
    partial_exits: List[Dict] = None
    trailing_active: bool = False
    
    def __post_init__(self):
        if self.partial_exits is None:
            self.partial_exits = []

class SmartExitManager:
    """Manages smart exit strategies for trading positions"""
    
    def __init__(self, 
                 trailing_config: TrailingStopConfig = None,
                 partial_config: PartialProfitConfig = None,
                 time_config: TimeBasedExitConfig = None):
        
        self.trailing_config = trailing_config or TrailingStopConfig()
        self.partial_config = partial_config or PartialProfitConfig()
        self.time_config = time_config or TimeBasedExitConfig()
        
        # Track active positions
        self.active_positions: Dict[str, PositionTracker] = {}
        
        # Performance tracking
        self.trailing_stop_exits = 0
        self.partial_profit_exits = 0
        self.time_based_exits = 0
        self.emergency_exits = 0
        
        # Exit statistics
        self.total_profit_from_partials = 0.0
        self.total_profit_from_trailing = 0.0
        self.avg_hold_time_minutes = 0.0
        
    def add_position(self, symbol: str, entry_time: datetime, entry_price: float,
                    position_size: float, direction: str, session: str) -> None:
        """Add a new position to track"""
        self.active_positions[symbol] = PositionTracker(
            entry_time=entry_time,
            entry_price=entry_price,
            position_size=position_size,
            original_size=position_size,
            direction=direction,
            session=session
        )
    
    def update_position(self, symbol: str, current_price: float, atr: float, 
                       current_time: datetime) -> List[ExitSignal]:
        """Update position and generate exit signals"""
        if symbol not in self.active_positions:
            return []
        
        position = self.active_positions[symbol]
        exit_signals = []
        
        # Calculate current profit/loss
        if position.direction == 'long':
            current_pnl = (current_price - position.entry_price) / position.entry_price
            profit_atr = (current_price - position.entry_price) / atr
        else:
            current_pnl = (position.entry_price - current_price) / position.entry_price
            profit_atr = (position.entry_price - current_price) / atr
        
        # Update profit tracking
        position.highest_profit = max(position.highest_profit, profit_atr)
        position.lowest_profit = min(position.lowest_profit, profit_atr)
        
        # Check for exit signals in priority order
        
        # 1. Emergency time-based exits (highest priority)
        emergency_signal = self._check_emergency_exits(position, current_time)
        if emergency_signal:
            exit_signals.append(emergency_signal)
            return exit_signals
        
        # 2. Partial profit taking
        partial_signals = self._check_partial_profits(position, current_price, atr, profit_atr)
        exit_signals.extend(partial_signals)
        
        # 3. Trailing stop updates
        trailing_signal = self._check_trailing_stop(position, current_price, atr, profit_atr)
        if trailing_signal:
            exit_signals.append(trailing_signal)
        
        # 4. Regular time-based exits
        time_signal = self._check_time_based_exits(position, current_time)
        if time_signal:
            exit_signals.append(time_signal)
        
        return exit_signals
    
    def _check_emergency_exits(self, position: PositionTracker, current_time: datetime) -> Optional[ExitSignal]:
        """Check for emergency exit conditions"""
        # Friday close-out
        if current_time.weekday() == 4 and current_time.hour >= self.time_config.friday_exit_hour:
            return ExitSignal(
                signal_type='time_based',
                action='close_all',
                reason='Friday market close approach',
                urgency='high'
            )
        
        # Maximum trade duration
        trade_duration = current_time - position.entry_time
        if trade_duration.total_seconds() / 3600 > self.time_config.max_trade_duration_hours:
            return ExitSignal(
                signal_type='time_based',
                action='close_all',
                reason=f'Maximum trade duration ({self.time_config.max_trade_duration_hours}h) exceeded',
                urgency='high'
            )
        
        return None
    
    def _check_partial_profits(self, position: PositionTracker, current_price: float, 
                              atr: float, profit_atr: float) -> List[ExitSignal]:
        """Check for partial profit taking opportunities"""
        signals = []
        
        # Only take profits on winning trades
        if profit_atr <= 0:
            return signals
        
        # First target
        if (profit_atr >= self.partial_config.first_target_atr and 
            not any(exit['target'] == 'first' for exit in position.partial_exits)):
            
            signals.append(ExitSignal(
                signal_type='partial_profit',
                action='close_partial',
                percentage=self.partial_config.first_target_percentage,
                reason=f'First profit target reached ({self.partial_config.first_target_atr:.1f} ATR)',
                urgency='normal'
            ))
            
            position.partial_exits.append({
                'target': 'first',
                'percentage': self.partial_config.first_target_percentage,
                'profit_atr': profit_atr
            })
        
        # Second target
        if (profit_atr >= self.partial_config.second_target_atr and 
            not any(exit['target'] == 'second' for exit in position.partial_exits)):
            
            signals.append(ExitSignal(
                signal_type='partial_profit',
                action='close_partial',
                percentage=self.partial_config.second_target_percentage,
                reason=f'Second profit target reached ({self.partial_config.second_target_atr:.1f} ATR)',
                urgency='normal'
            ))
            
            position.partial_exits.append({
                'target': 'second',
                'percentage': self.partial_config.second_target_percentage,
                'profit_atr': profit_atr
            })
        
        # Final target
        if (profit_atr >= self.partial_config.final_target_atr and 
            not any(exit['target'] == 'final' for exit in position.partial_exits)):
            
            signals.append(ExitSignal(
                signal_type='partial_profit',
                action='close_all',
                reason=f'Final profit target reached ({self.partial_config.final_target_atr:.1f} ATR)',
                urgency='normal'
            ))
            
            position.partial_exits.append({
                'target': 'final',
                'percentage': 1.0,
                'profit_atr': profit_atr
            })
        
        return signals
    
    def _check_trailing_stop(self, position: PositionTracker, current_price: float, 
                            atr: float, profit_atr: float) -> Optional[ExitSignal]:
        """Check and update trailing stop"""
        # Start trailing after reaching profit threshold
        if profit_atr >= self.trailing_config.trail_start_profit_atr:
            position.trailing_active = True
        
        if not position.trailing_active:
            return None
        
        # Calculate new trailing stop
        if position.direction == 'long':
            new_stop = current_price - (self.trailing_config.min_trail_distance_atr * atr)
            # Only move stop up for long positions
            if position.current_stop is None or new_stop > position.current_stop:
                position.current_stop = new_stop
                return ExitSignal(
                    signal_type='trailing_stop',
                    action='update_stop',
                    price=new_stop,
                    reason=f'Trailing stop updated to {new_stop:.4f}',
                    urgency='low'
                )
        else:
            new_stop = current_price + (self.trailing_config.min_trail_distance_atr * atr)
            # Only move stop down for short positions
            if position.current_stop is None or new_stop < position.current_stop:
                position.current_stop = new_stop
                return ExitSignal(
                    signal_type='trailing_stop',
                    action='update_stop',
                    price=new_stop,
                    reason=f'Trailing stop updated to {new_stop:.4f}',
                    urgency='low'
                )
        
        return None
    
    def _check_time_based_exits(self, position: PositionTracker, current_time: datetime) -> Optional[ExitSignal]:
        """Check for time-based exit conditions"""
        trade_duration_minutes = (current_time - position.entry_time).total_seconds() / 60
        
        # Session-specific time limits
        if position.session == 'london' and trade_duration_minutes >= self.time_config.london_session_exit_minutes:
            return ExitSignal(
                signal_type='time_based',
                action='close_all',
                reason=f'London session time limit reached ({self.time_config.london_session_exit_minutes} min)',
                urgency='normal'
            )
        
        if position.session == 'ny' and trade_duration_minutes >= self.time_config.ny_session_exit_minutes:
            return ExitSignal(
                signal_type='time_based',
                action='close_all',
                reason=f'NY session time limit reached ({self.time_config.ny_session_exit_minutes} min)',
                urgency='normal'
            )
        
        if position.session == 'overlap' and trade_duration_minutes >= self.time_config.overlap_session_exit_minutes:
            return ExitSignal(
                signal_type='time_based',
                action='close_all',
                reason=f'Overlap session time limit reached ({self.time_config.overlap_session_exit_minutes} min)',
                urgency='normal'
            )
        
        return None
    
    def execute_exit_signal(self, symbol: str, signal: ExitSignal, execution_price: float) -> Dict:
        """Execute an exit signal and update tracking"""
        if symbol not in self.active_positions:
            return {'success': False, 'reason': 'Position not found'}
        
        position = self.active_positions[symbol]
        result = {
            'success': True,
            'signal_type': signal.signal_type,
            'action': signal.action,
            'percentage': signal.percentage,
            'execution_price': execution_price,
            'reason': signal.reason
        }
        
        # Update statistics
        if signal.signal_type == 'trailing_stop':
            self.trailing_stop_exits += 1
        elif signal.signal_type == 'partial_profit':
            self.partial_profit_exits += 1
        elif signal.signal_type == 'time_based':
            self.time_based_exits += 1
        
        # Handle different actions
        if signal.action == 'close_all':
            # Remove position from tracking
            del self.active_positions[symbol]
        elif signal.action == 'close_partial':
            # Reduce position size
            position.position_size *= (1 - signal.percentage)
        elif signal.action == 'update_stop':
            # Stop loss updated, no position size change
            pass
        
        return result
    
    def get_position_status(self, symbol: str) -> Optional[Dict]:
        """Get current status of a position"""
        if symbol not in self.active_positions:
            return None
        
        position = self.active_positions[symbol]
        return {
            'entry_time': position.entry_time,
            'entry_price': position.entry_price,
            'current_size': position.position_size,
            'original_size': position.original_size,
            'direction': position.direction,
            'session': position.session,
            'current_stop': position.current_stop,
            'highest_profit': position.highest_profit,
            'partial_exits_count': len(position.partial_exits),
            'trailing_active': position.trailing_active
        }
    
    def get_exit_statistics(self) -> Dict:
        """Get comprehensive exit strategy statistics"""
        total_exits = (self.trailing_stop_exits + self.partial_profit_exits + 
                      self.time_based_exits + self.emergency_exits)
        
        return {
            'total_exits': total_exits,
            'trailing_stop_exits': self.trailing_stop_exits,
            'partial_profit_exits': self.partial_profit_exits,
            'time_based_exits': self.time_based_exits,
            'emergency_exits': self.emergency_exits,
            'trailing_stop_percentage': (self.trailing_stop_exits / max(total_exits, 1)) * 100,
            'partial_profit_percentage': (self.partial_profit_exits / max(total_exits, 1)) * 100,
            'time_based_percentage': (self.time_based_exits / max(total_exits, 1)) * 100,
            'active_positions': len(self.active_positions),
            'total_profit_from_partials': self.total_profit_from_partials,
            'total_profit_from_trailing': self.total_profit_from_trailing
        }
    
    def cleanup_expired_positions(self, current_time: datetime) -> List[str]:
        """Remove positions that should have been closed"""
        expired_symbols = []
        
        for symbol, position in list(self.active_positions.items()):
            trade_duration = current_time - position.entry_time
            
            # Remove positions older than max duration
            if trade_duration.total_seconds() / 3600 > self.time_config.max_trade_duration_hours:
                expired_symbols.append(symbol)
                del self.active_positions[symbol]
        
        return expired_symbols