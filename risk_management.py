#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradeBot Sentinel - Advanced Risk Management System
Daily limits, position size limits, stop-loss logic, and portfolio protection
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class TradePosition:
    symbol: str
    side: str  # 'BUY' or 'SELL'
    amount: float
    entry_price: float
    current_price: float
    timestamp: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def pnl(self) -> float:
        """Calculate current PnL"""
        if self.side == 'BUY':
            return (self.current_price - self.entry_price) * self.amount
        else:
            return (self.entry_price - self.current_price) * self.amount
            
    @property
    def pnl_percentage(self) -> float:
        """Calculate PnL percentage"""
        return (self.pnl / (self.entry_price * self.amount)) * 100

class RiskManager:
    def __init__(self):
        self.config = self._load_risk_config()
        self.positions_file = Path('logs/positions.json')
        self.risk_log_file = Path('logs/risk_management.log')
        self.daily_stats_file = Path('logs/daily_stats.json')
        
        # Ensure directories exist
        Path('logs').mkdir(exist_ok=True)
        
        # Initialize daily stats
        self.daily_stats = self._load_daily_stats()
        
    def _load_risk_config(self) -> Dict[str, Any]:
        """Load risk management configuration"""
        return {
            # Daily limits
            'daily_loss_limit': float(os.getenv('DAILY_LOSS_LIMIT', '1000.0')),
            'daily_trade_limit': int(os.getenv('DAILY_TRADE_LIMIT', '10')),
            'daily_volume_limit': float(os.getenv('DAILY_VOLUME_LIMIT', '10000.0')),
            
            # Position limits
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '1000.0')),
            'max_positions': int(os.getenv('MAX_POSITIONS', '5')),
            'position_size_percentage': float(os.getenv('POSITION_SIZE_PERCENTAGE', '2.0')),  # % of portfolio
            
            # Stop-loss settings
            'default_stop_loss_percentage': float(os.getenv('DEFAULT_STOP_LOSS_PERCENTAGE', '2.0')),
            'trailing_stop_enabled': os.getenv('TRAILING_STOP_ENABLED', 'True').lower() == 'true',
            'trailing_stop_percentage': float(os.getenv('TRAILING_STOP_PERCENTAGE', '1.5')),
            
            # Risk ratios
            'max_risk_per_trade': float(os.getenv('MAX_RISK_PER_TRADE', '100.0')),
            'risk_reward_ratio': float(os.getenv('RISK_REWARD_RATIO', '2.0')),
            
            # Portfolio limits
            'max_portfolio_risk': float(os.getenv('MAX_PORTFOLIO_RISK', '5.0')),  # % of total portfolio
            'max_correlation_exposure': float(os.getenv('MAX_CORRELATION_EXPOSURE', '30.0')),  # % in correlated assets
            
            # Emergency settings
            'emergency_stop_loss': float(os.getenv('EMERGENCY_STOP_LOSS', '5000.0')),
            'circuit_breaker_enabled': os.getenv('CIRCUIT_BREAKER_ENABLED', 'True').lower() == 'true',
            'circuit_breaker_threshold': float(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '10.0')),  # % portfolio loss
        }
        
    def _load_daily_stats(self) -> Dict[str, Any]:
        """Load or initialize daily statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if self.daily_stats_file.exists():
            with open(self.daily_stats_file, 'r') as f:
                stats = json.load(f)
                
            # Reset if new day
            if stats.get('date') != today:
                stats = self._initialize_daily_stats(today)
        else:
            stats = self._initialize_daily_stats(today)
            
        return stats
        
    def _initialize_daily_stats(self, date: str) -> Dict[str, Any]:
        """Initialize daily statistics"""
        return {
            'date': date,
            'trades_count': 0,
            'total_volume': 0.0,
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'max_drawdown': 0.0,
            'trades': [],
            'risk_events': []
        }
        
    def _save_daily_stats(self):
        """Save daily statistics to file"""
        with open(self.daily_stats_file, 'w') as f:
            json.dump(self.daily_stats, f, indent=2, default=str)
            
    def can_place_trade(self, trade_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if trade can be placed based on risk rules"""
        try:
            # Extract trade information
            symbol = trade_data.get('symbol', '')
            side = trade_data.get('side', '')
            amount = float(trade_data.get('amount', 0))
            price = float(trade_data.get('price', 0))
            
            # Check daily trade limit
            if self.daily_stats['trades_count'] >= self.config['daily_trade_limit']:
                return False, f"Daily trade limit reached ({self.config['daily_trade_limit']})"
                
            # Check daily loss limit
            if self.daily_stats['realized_pnl'] <= -self.config['daily_loss_limit']:
                return False, f"Daily loss limit reached (-${self.config['daily_loss_limit']})"
                
            # Check daily volume limit
            trade_volume = amount * price
            if self.daily_stats['total_volume'] + trade_volume > self.config['daily_volume_limit']:
                return False, f"Daily volume limit would be exceeded (${self.config['daily_volume_limit']})"
                
            # Check position size limit
            if trade_volume > self.config['max_position_size']:
                return False, f"Position size too large (max: ${self.config['max_position_size']})"
                
            # Check maximum positions
            current_positions = self._get_current_positions()
            if len(current_positions) >= self.config['max_positions']:
                return False, f"Maximum positions reached ({self.config['max_positions']})"
                
            # Check risk per trade
            risk_amount = trade_volume * (self.config['default_stop_loss_percentage'] / 100)
            if risk_amount > self.config['max_risk_per_trade']:
                return False, f"Risk per trade too high (${risk_amount:.2f} > ${self.config['max_risk_per_trade']})"
                
            # Check circuit breaker
            if self.config['circuit_breaker_enabled']:
                total_pnl = self.daily_stats['realized_pnl'] + self.daily_stats['unrealized_pnl']
                portfolio_loss_percentage = abs(total_pnl) / 10000 * 100  # Assuming $10k portfolio
                
                if portfolio_loss_percentage > self.config['circuit_breaker_threshold']:
                    return False, f"Circuit breaker triggered ({portfolio_loss_percentage:.2f}% loss)"
                    
            return True, "Trade approved"
            
        except Exception as e:
            logger.error(f"Error checking trade approval: {e}")
            return False, f"Risk check error: {e}"
            
    def record_trade(self, trade_data: Dict[str, Any]):
        """Record a new trade"""
        try:
            symbol = trade_data.get('symbol', '')
            side = trade_data.get('side', '')
            amount = float(trade_data.get('amount', 0))
            price = float(trade_data.get('price', 0))
            timestamp = datetime.now()
            
            # Calculate stop-loss
            stop_loss = self._calculate_stop_loss(price, side)
            
            # Create position
            position = TradePosition(
                symbol=symbol,
                side=side,
                amount=amount,
                entry_price=price,
                current_price=price,
                timestamp=timestamp,
                stop_loss=stop_loss
            )
            
            # Update daily stats
            self.daily_stats['trades_count'] += 1
            self.daily_stats['total_volume'] += amount * price
            self.daily_stats['trades'].append({
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'timestamp': timestamp.isoformat(),
                'stop_loss': stop_loss
            })
            
            # Save position
            self._save_position(position)
            self._save_daily_stats()
            
            logger.info(f"✅ Trade recorded: {symbol} {side} {amount} @ {price}")
            
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            
    def _calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop-loss price"""
        stop_loss_percentage = self.config['default_stop_loss_percentage'] / 100
        
        if side == 'BUY':
            return entry_price * (1 - stop_loss_percentage)
        else:
            return entry_price * (1 + stop_loss_percentage)
            
    def _save_position(self, position: TradePosition):
        """Save position to file"""
        positions = self._get_current_positions()
        positions.append({
            'symbol': position.symbol,
            'side': position.side,
            'amount': position.amount,
            'entry_price': position.entry_price,
            'current_price': position.current_price,
            'timestamp': position.timestamp.isoformat(),
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit
        })
        
        with open(self.positions_file, 'w') as f:
            json.dump(positions, f, indent=2)
            
    def _get_current_positions(self) -> List[Dict[str, Any]]:
        """Get current positions from file"""
        if self.positions_file.exists():
            with open(self.positions_file, 'r') as f:
                return json.load(f)
        return []
        
    def check_stop_losses(self, current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check for stop-loss triggers"""
        triggered_stops = []
        positions = self._get_current_positions()
        
        for position in positions:
            symbol = position['symbol']
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            stop_loss = position.get('stop_loss')
            
            if not stop_loss:
                continue
                
            # Check if stop-loss is triggered
            triggered = False
            if position['side'] == 'BUY' and current_price <= stop_loss:
                triggered = True
            elif position['side'] == 'SELL' and current_price >= stop_loss:
                triggered = True
                
            if triggered:
                triggered_stops.append({
                    'symbol': symbol,
                    'side': position['side'],
                    'amount': position['amount'],
                    'entry_price': position['entry_price'],
                    'stop_price': stop_loss,
                    'current_price': current_price,
                    'reason': 'stop_loss_triggered'
                })
                
        return triggered_stops
        
    def update_trailing_stops(self, current_prices: Dict[str, float]):
        """Update trailing stop-losses"""
        if not self.config['trailing_stop_enabled']:
            return
            
        positions = self._get_current_positions()
        updated_positions = []
        
        for position in positions:
            symbol = position['symbol']
            if symbol not in current_prices:
                updated_positions.append(position)
                continue
                
            current_price = current_prices[symbol]
            trailing_percentage = self.config['trailing_stop_percentage'] / 100
            
            # Update trailing stop for profitable positions
            if position['side'] == 'BUY':
                if current_price > position['entry_price']:
                    new_stop = current_price * (1 - trailing_percentage)
                    if new_stop > position.get('stop_loss', 0):
                        position['stop_loss'] = new_stop
                        logger.info(f"📈 Trailing stop updated for {symbol}: {new_stop:.4f}")
                        
            elif position['side'] == 'SELL':
                if current_price < position['entry_price']:
                    new_stop = current_price * (1 + trailing_percentage)
                    if new_stop < position.get('stop_loss', float('inf')):
                        position['stop_loss'] = new_stop
                        logger.info(f"📉 Trailing stop updated for {symbol}: {new_stop:.4f}")
                        
            updated_positions.append(position)
            
        # Save updated positions
        with open(self.positions_file, 'w') as f:
            json.dump(updated_positions, f, indent=2)
            
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        positions = self._get_current_positions()
        
        total_exposure = sum(pos['amount'] * pos['entry_price'] for pos in positions)
        total_risk = sum(pos['amount'] * pos['entry_price'] * (self.config['default_stop_loss_percentage'] / 100) for pos in positions)
        
        return {
            'daily_stats': self.daily_stats,
            'current_positions': len(positions),
            'total_exposure': total_exposure,
            'total_risk': total_risk,
            'risk_limits': self.config,
            'risk_utilization': {
                'daily_trades': f"{self.daily_stats['trades_count']}/{self.config['daily_trade_limit']}",
                'daily_volume': f"${self.daily_stats['total_volume']:.2f}/${self.config['daily_volume_limit']}",
                'positions': f"{len(positions)}/{self.config['max_positions']}",
                'daily_pnl': f"${self.daily_stats['realized_pnl']:.2f}"
            }
        }
        
    def reset_daily_stats(self):
        """Reset daily statistics (called at start of new day)"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_stats = self._initialize_daily_stats(today)
        self._save_daily_stats()
        logger.info(f"📊 Daily stats reset for {today}")
        
if __name__ == "__main__":
    # Test risk management
    risk_manager = RiskManager()
    
    # Test trade approval
    test_trade = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'amount': '0.001',
        'price': '45000'
    }
    
    can_trade, reason = risk_manager.can_place_trade(test_trade)
    print(f"Can place trade: {can_trade} - {reason}")
    
    if can_trade:
        risk_manager.record_trade(test_trade)
        
    # Print risk summary
    summary = risk_manager.get_risk_summary()
    print(json.dumps(summary, indent=2, default=str))