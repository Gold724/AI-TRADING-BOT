# region imports
from AlgorithmImports import *
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict
import math

# Import configuration and dynamic mode system
try:
    from bulenox_strategy_config import CONFIG
except ImportError:
    # Fallback configuration if config file not available
    class FallbackConfig:
        DAILY_PROFIT_TARGET = 535.71
        DAILY_MAX_DRAWDOWN = 267.00
        MAX_TRADES_PER_DAY = 9
        MAX_CONTRACTS = 3
        DEFAULT_CONTRACTS = 1
        FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]
        TRADING_SESSIONS = {
            'morning': {'start': time(3, 0), 'end': time(6, 0), 'name': 'Morning Session'},
            'midday': {'start': time(8, 20), 'end': time(11, 30), 'name': 'Midday Session'},
            'afternoon': {'start': time(13, 0), 'end': time(15, 30), 'name': 'Afternoon Session'}
        }
        MIN_RISK_REWARD_RATIO = 2.5
        BASE_TAKE_PROFIT_PERCENT = 0.15
        BASE_STOP_LOSS_PERCENT = 0.02
        MAX_CONSECUTIVE_LOSSES = 3
        ENABLE_TRAILING_STOP = True
        TRAILING_STOP_ACTIVATION = 0.5
        FULL_SYMBOL = "GCZ25"
    CONFIG = FallbackConfig()

# Import dynamic trading mode system
try:
    from backend_mode_config import TRADING_MODE, get_contracts_for_setup, get_daily_targets, get_mode_info
except ImportError:
    # Fallback if mode config not available
    class MockTradingMode:
        def get_current_mode(self): return "safe"
        def get_contracts_for_setup(self, is_high_confidence=False): return 1
        def get_daily_profit_target(self): return 535.71
        def get_daily_max_drawdown(self): return 267.00
        def get_mode_display_name(self): return "🛡 Safe Mode"
        def get_mode_summary(self): return {"mode": "safe", "contracts": {"default": 1}}
    
    TRADING_MODE = MockTradingMode()
    get_contracts_for_setup = lambda is_high_confidence=False: 1
    get_daily_targets = lambda: {"profit_target": 535.71, "max_drawdown": 267.00}
    get_mode_info = lambda: {"mode": "safe", "display_name": "🛡 Safe Mode"}

# endregion

class BulenoxGoldScalpingStrategy(QCAlgorithm):
    """
    Bulenox Gold Scalping Strategy - Tesla 3-6-9 Rhythm + Fibonacci Growth Model
    
    Target: $15,000 profit in 28 days (~$535.71/day)
    Structure: 3 sessions × 3 trades = max 9 trades/day
    Risk: Stop at +$535.71 profit or -$267 loss per day
    """
    
    def Initialize(self):
        """Initialize the algorithm with configuration parameters"""
        
        # Load configuration
        self.config = CONFIG
        
        # Initialize dynamic trading mode system
        self.trading_mode = TRADING_MODE
        self.current_mode_info = get_mode_info()
        
        # === STRATEGY PARAMETERS ===
        # Dynamic profit and loss limits based on current mode
        mode_targets = get_daily_targets()
        self.daily_profit_target = mode_targets['profit_target']
        self.daily_max_drawdown = mode_targets['max_drawdown']
        self.max_contracts = self.config.MAX_CONTRACTS
        self.default_contracts = self.config.DEFAULT_CONTRACTS
        self.trades_per_session = 3  # Fixed: 3 trades per session
        self.max_trades_per_day = self.config.MAX_TRADES_PER_DAY
        
        # Fibonacci sequence for profit targets and position sizing
        self.fib_sequence = self.config.FIBONACCI_PROFIT_SEQUENCE
        
        # Risk management parameters
        self.min_risk_reward_ratio = getattr(self.config, 'MIN_RISK_REWARD_RATIO', 2.5)
        self.base_take_profit_percent = getattr(self.config, 'BASE_TAKE_PROFIT_PERCENT', 0.15)
        self.base_stop_loss_percent = getattr(self.config, 'BASE_STOP_LOSS_PERCENT', 0.02)
        self.max_consecutive_losses = getattr(self.config, 'MAX_CONSECUTIVE_LOSSES', 3)
        
        # Technical indicators
        self.vwap_period = getattr(self.config, 'VWAP_PERIOD', 20)
        self.volume_spike_threshold = getattr(self.config, 'VOLUME_SPIKE_THRESHOLD', 2.0)
        self.min_volume_ratio = getattr(self.config, 'MIN_VOLUME_RATIO', 1.5)
        
        # === TRADING SESSIONS (NY TIME) ===
        self.trading_sessions = self.config.TRADING_SESSIONS
        
        # === ALGORITHM SETUP ===
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2024, 12, 31)
        self.SetCash(100000)  # Starting capital
        self.SetTimeZone(TimeZones.NewYork)
        
        # Add Gold Futures (GC) - Use specific contract if configured
        if hasattr(self.config, 'FULL_SYMBOL') and self.config.FULL_SYMBOL:
            self.gold_symbol = self.AddFuture(Futures.Metals.Gold, Resolution.Minute, 
                                            contractFilter=lambda x: x.Symbol.Value == self.config.FULL_SYMBOL).Symbol
        else:
            self.gold_symbol = self.AddFuture(Futures.Metals.Gold, Resolution.Minute).Symbol
        
        # === STATE VARIABLES ===
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.current_session = None
        self.session_trades = 0
        self.last_trade_date = None
        self.stop_trading_today = False
        
        # Fibonacci progression tracking
        self.session_fib_index = {'morning': 0, 'midday': 0, 'afternoon': 0}
        self.daily_fib_completions = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
        # Technical indicators
        self.vwap = None
        self.volume_sma = None
        self.session_high = {'morning': 0, 'midday': 0, 'afternoon': 0}
        self.session_low = {'morning': float('inf'), 'midday': float('inf'), 'afternoon': float('inf')}
        
        # Order management
        self.active_orders = {}
        self.position_entry_price = 0
        self.current_trade_info = None
        
        # Enhanced logging
        self.trade_log = []
        self.session_stats = {'morning': [], 'midday': [], 'afternoon': []}
        self.fibonacci_progression_log = []
        
        # Schedule daily reset
        self.Schedule.On(
            self.DateRules.EveryDay(self.gold_symbol),
            self.TimeRules.At(0, 0),
            self.ResetDailyCounters
        )
      # Log initialization with current mode
        mode_display = self.trading_mode.get_mode_display_name()
        self.Log(f"Tesla 3-6-9 Strategy initialized - {mode_display}")
        self.Log(f"Target: ${self.daily_profit_target}/day, Max Loss: ${self.daily_max_drawdown}/day")
        self.Log(f"Mode Config: {self.current_mode_info}")
    
    def RefreshTradingMode(self):
        """Refresh trading mode configuration to allow dynamic adjustments"""
        try:
            # Update mode info
            self.current_mode_info = get_mode_info()
            
            # Update daily targets based on current mode
            mode_targets = get_daily_targets()
            old_profit_target = self.daily_profit_target
            old_max_drawdown = self.daily_max_drawdown
            
            self.daily_profit_target = mode_targets['profit_target']
            self.daily_max_drawdown = mode_targets['max_drawdown']
            
            # Log changes if targets have been updated
            if (old_profit_target != self.daily_profit_target or 
                old_max_drawdown != self.daily_max_drawdown):
                
                mode_display = self.trading_mode.get_mode_display_name()
                self.Log(f"[MODE UPDATE] {mode_display}")
                self.Log(f"   Profit Target: ${old_profit_target} → ${self.daily_profit_target}")
                self.Log(f"   Max Drawdown: ${old_max_drawdown} → ${self.daily_max_drawdown}")
                
        except Exception as e:
            self.Log(f"[WARNING] Failed to refresh trading mode: {str(e)}")
    
    def OnData(self, data):
        """Main trading logic executed on each data point"""
        
        # Refresh trading mode configuration periodically (every hour)
        if self.Time.minute == 0:
            self.RefreshTradingMode()
        
        # Skip if no gold data
        if not data.ContainsKey(self.gold_symbol):
            return
            
        current_time = self.Time.time()
        current_date = self.Time.date()
        
        # Reset counters if new day
        if self.last_trade_date != current_date:
            self.ResetDailyCounters()
            self.last_trade_date = current_date
        
        # Stop trading if daily limits reached
        if self.stop_trading_today:
            return
            
        # Enhanced risk management checks
        if not self.CheckRiskLimits():
            return
        
        # Determine current trading session
        session = self.GetCurrentSession(current_time)
        
        if session != self.current_session:
            # New session started
            if session:
                self.StartNewSession(session)
            self.current_session = session
        
        # Tesla 3-6-9 rhythm validation: Skip if not in trading session or max trades reached
        tesla_max_trades = 9
        if not session or self.session_trades >= self.trades_per_session or self.daily_trades >= tesla_max_trades:
            return
        
        # Update technical indicators
        self.UpdateIndicators(data)
        
        # Check for entry signals (only if no position)
        if not self.Portfolio[self.gold_symbol].Invested:
            self.CheckEntrySignals(data)
        else:
            self.ManagePosition(data)
    
    def CheckRiskLimits(self):
        """Comprehensive risk management checks with Tesla 3-6-9 rhythm validation"""
        
        # Daily profit target check
        if self.daily_pnl >= self.daily_profit_target:
            if not self.stop_trading_today:
                self.stop_trading_today = True
                mode_display = self.trading_mode.get_mode_display_name()
                self.Log(f"[TESLA 3-6-9] {mode_display} - Daily profit target achieved!")
                self.Log(f"[RISK] Daily profit target reached: ${self.daily_pnl:.2f} >= ${self.daily_profit_target:.2f}")
                self.LogDailySummary("PROFIT_TARGET_REACHED")
            return False
            
        # Daily max drawdown check
        if self.daily_pnl <= -self.daily_max_drawdown:
            if not self.stop_trading_today:
                self.stop_trading_today = True
                mode_display = self.trading_mode.get_mode_display_name()
                self.Log(f"[TESLA 3-6-9] {mode_display} - Max drawdown hit, stopping trades")
                self.Log(f"[RISK] Daily max drawdown reached: ${self.daily_pnl:.2f} <= -${self.daily_max_drawdown:.2f}")
                self.LogDailySummary("MAX_DRAWDOWN_REACHED")
            return False
            
        # Tesla 3-6-9 rhythm: Maximum 9 trades per day validation
        tesla_max_trades = 9
        if self.daily_trades >= tesla_max_trades:
            if not self.stop_trading_today:
                self.stop_trading_today = True
                mode_display = self.trading_mode.get_mode_display_name()
                self.Log(f"[TESLA 3-6-9] {mode_display} - Daily rhythm complete: {self.daily_trades}/9 trades")
                self.LogDailySummary("MAX_TRADES_REACHED")
            return False
            
        # Check for excessive consecutive losses
        if self.consecutive_losses >= 3:
            self.Log(f"[RISK] Warning: {self.consecutive_losses} consecutive losses - consider reducing position size")
            
        # Portfolio heat check (total exposure)
        current_position = self.Portfolio[self.gold_symbol]
        if abs(current_position.Quantity) > self.max_contracts:
            self.Log(f"[RISK] Position size exceeds maximum: {abs(current_position.Quantity)} > {self.max_contracts}")
            return False
            
        return True
    
    def LogDailySummary(self, reason):
        """Log comprehensive daily summary when trading stops with advanced analytics"""
        total_sessions = len([s for s in self.session_stats.values() if s])
        total_trades = len(self.trade_log)
        
        # Calculate basic statistics
        winning_trades = sum(1 for trade in self.trade_log if trade.get('pnl', 0) > 0)
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate advanced metrics
        profits = [trade.get('pnl', 0) for trade in self.trade_log if trade.get('pnl', 0) > 0]
        losses = [trade.get('pnl', 0) for trade in self.trade_log if trade.get('pnl', 0) < 0]
        
        avg_win = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = abs(sum(profits) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
        
        # Risk metrics
        max_consecutive_losses = self.CalculateMaxConsecutiveLosses()
        sharpe_ratio = self.CalculateSharpeRatio()
        
        summary = {
            'timestamp': self.Time,
            'reason': reason,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'daily_fib_completions': self.daily_fib_completions,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'sessions_traded': total_sessions,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_consecutive_losses': max_consecutive_losses,
            'sharpe_ratio': sharpe_ratio,
            'session_breakdown': {}
        }
        
        # Header
        self.Log(f"\n{'='*60}")
        self.Log(f"=== DAILY SUMMARY {self.Time.strftime('%Y-%m-%d')} - {reason} ===")
        self.Log(f"{'='*60}")
        
        # Performance Overview
        self.Log(f"📊 PERFORMANCE OVERVIEW:")
        self.Log(f"   Total Trades: {total_trades} | Wins: {winning_trades} | Losses: {losing_trades}")
        self.Log(f"   Win Rate: {win_rate:.1f}% | Daily PnL: ${self.daily_pnl:.2f}")
        self.Log(f"   Target: ${self.daily_profit_target} | Max DD: ${self.daily_max_drawdown}")
        self.Log(f"   Progress: {(self.daily_pnl/self.daily_profit_target*100):.1f}% of daily target")
        
        # Risk Metrics
        self.Log(f"\n📈 RISK METRICS:")
        self.Log(f"   Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
        self.Log(f"   Profit Factor: {profit_factor:.2f} | Sharpe Ratio: {sharpe_ratio:.2f}")
        self.Log(f"   Max Consecutive Losses: {max_consecutive_losses}")
        
        # Session Analysis
        self.Log(f"\n🕐 SESSION BREAKDOWN:")
        for session_name, session_trades in self.session_stats.items():
            if session_trades:
                session_pnl = sum(trade.get('pnl', 0) for trade in session_trades if 'pnl' in trade)
                session_wins = len([t for t in session_trades if t.get('result') == 'WIN'])
                session_losses = len([t for t in session_trades if t.get('result') == 'LOSS'])
                session_win_rate = (session_wins / len(session_trades) * 100) if session_trades else 0
                
                summary['session_breakdown'][session_name] = {
                    'trades': len(session_trades),
                    'pnl': session_pnl,
                    'wins': session_wins,
                    'losses': session_losses,
                    'win_rate': session_win_rate,
                    'fib_index': self.session_fib_index[session_name]
                }
                
                self.Log(f"   {session_name.upper()}: {len(session_trades)} trades | PnL: ${session_pnl:.2f} | "
                        f"Win Rate: {session_win_rate:.1f}% | Fib: {self.session_fib_index[session_name]}")
            else:
                self.Log(f"   {session_name.upper()}: No trades")
        
        # Fibonacci Analysis
        self.Log(f"\n🔢 FIBONACCI ANALYSIS:")
        self.Log(f"   Total Sequence Completions: {self.daily_fib_completions}")
        for session in ['morning', 'midday', 'afternoon']:
            fib_index = self.session_fib_index.get(session, 0)
            current_target = self.fib_sequence[min(fib_index, len(self.fib_sequence)-1)]
            self.Log(f"   {session.upper()}: Index {fib_index} | Target ${current_target}")
        
        self.trade_log.append(summary)
        self.Log(f"{'='*60}\n")
    
    def GetCurrentSession(self, current_time):
        """Determine which trading session we're currently in"""
        for session_name, times in self.trading_sessions.items():
            if times['start'] <= current_time <= times['end']:
                return session_name
        return None
    
    def CalculateMaxConsecutiveLosses(self):
        """Calculate maximum consecutive losses"""
        if not self.trade_log:
            return 0
            
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in self.trade_log:
            if trade.get('pnl', 0) < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
                
        return max_consecutive
    
    def CalculateSharpeRatio(self):
        """Calculate simplified Sharpe ratio for daily performance"""
        if len(self.trade_log) < 2:
            return 0.0
            
        returns = [trade.get('pnl', 0) for trade in self.trade_log]
        avg_return = sum(returns) / len(returns)
        
        # Calculate standard deviation
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
            
        # Simplified Sharpe (assuming risk-free rate = 0)
        return avg_return / std_dev
    
    def reset_session_fibonacci(self, session_name):
        """Reset Fibonacci index for a specific session with enhanced logging"""
        if session_name in self.session_fib_index:
            old_index = self.session_fib_index[session_name]
            self.session_fib_index[session_name] = 0
            
            # Log Fibonacci reset
            self.fibonacci_progression_log.append({
                'timestamp': self.Time,
                'session': session_name,
                'action': 'reset',
                'old_index': old_index,
                'new_index': 0,
                'reason': 'session_start'
            })
            
            self.Log(f"🔢 [FIBONACCI] Reset {session_name} session: index {old_index} → 0")
    
    def advance_fibonacci(self, session_name, win=True):
        """Advance or reset Fibonacci sequence based on trade outcome"""
        if session_name not in self.session_fib_index:
            return
            
        old_index = self.session_fib_index[session_name]
        
        if win:
            # Advance to next Fibonacci level (max at sequence length - 1)
            self.session_fib_index[session_name] = min(old_index + 1, len(self.fib_sequence) - 1)
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            reason = 'winning_trade'
        else:
            # Reset to beginning on loss
            self.session_fib_index[session_name] = 0
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            reason = 'losing_trade'
        
        new_index = self.session_fib_index[session_name]
        
        # Log Fibonacci progression
        self.fibonacci_progression_log.append({
            'timestamp': self.Time,
            'session': session_name,
            'action': 'advance' if win else 'reset',
            'old_index': old_index,
            'new_index': new_index,
            'reason': reason,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses
        })
        
        # Check for sequence completion
        if old_index == len(self.fib_sequence) - 1 and win:
            self.daily_fib_completions += 1
            self.Log(f"[FIBONACCI] Completed sequence in {session_name}! Total completions today: {self.daily_fib_completions}")
        
        self.Log(f"[FIBONACCI] {session_name} progression: index {old_index} → {new_index} ({reason})")
    
    def get_current_fibonacci_target(self, session_name):
        """Get current Fibonacci profit target for the session"""
        if session_name not in self.session_fib_index:
            return self.fib_sequence[0]
        
        index = self.session_fib_index[session_name]
        return self.fib_sequence[index]
    
    def get_fibonacci_contract_size(self, session_name):
        """Calculate contract size based on Fibonacci progression"""
        fib_target = self.get_current_fibonacci_target(session_name)
        
        # Scale contract size based on Fibonacci target (keeping within limits)
        if fib_target <= 20:
            return self.default_contracts  # 1 contract
        elif fib_target <= 50:
            return min(2, self.max_contracts)  # 2 contracts
        else:
            return self.max_contracts  # 3 contracts
    
    def StartNewSession(self, session_name):
        """Initialize new trading session"""
        self.current_session = session_name
        self.session_trades = 0
        
        # Reset Fibonacci sequence for new session
        self.reset_session_fibonacci(session_name)
        
        # Reset session highs/lows
        self.session_high[session_name] = 0
        self.session_low[session_name] = float('inf')
        
        # Get current Fibonacci target and contract size
        fib_target = self.get_current_fibonacci_target(session_name)
        contract_size = self.get_fibonacci_contract_size(session_name)
        
        self.Log(f"[SESSION] Starting {session_name} session - Fib target: ${fib_target}, Contracts: {contract_size}")
        
        # Log session start with enhanced info
        session_log = {
            'timestamp': self.Time,
            'action': 'session_start',
            'session': session_name,
            'fib_index': self.session_fib_index[session_name],
            'fib_target': fib_target,
            'contract_size': contract_size,
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'daily_fib_completions': self.daily_fib_completions
        }
        
        self.trade_log.append(session_log)
        self.session_stats[session_name].append(session_log)
    
    def UpdateIndicators(self, data):
        """Update technical indicators"""
        if not data.ContainsKey(self.gold_symbol) or self.current_session is None:
            return
            
        bar = data[self.gold_symbol]
        
        # Update session-specific high/low
        self.session_high[self.current_session] = max(self.session_high[self.current_session], bar.High)
        self.session_low[self.current_session] = min(self.session_low[self.current_session], bar.Low)
        
        # Calculate session range
        session_range = self.session_high[self.current_session] - self.session_low[self.current_session]
        
        # Initialize VWAP if needed
        if self.vwap is None:
            self.vwap = self.VWAP(self.gold_symbol, 20)
            self.volume_sma = self.SMA(self.gold_symbol, 20, Resolution.Minute, Field.Volume)
        
        # Log indicator updates (every 5 minutes to avoid excessive logging)
        if self.Time.minute % 5 == 0 and self.Time.second == 0:
            self.Log(f"[INDICATORS] Session: {self.current_session}, Price: ${bar.Close:.2f}, " +
                     f"Range: ${session_range:.2f}, VWAP: ${self.vwap.Current.Value:.2f}")
    
    def CheckEntrySignals(self, data):
        """Check for entry signals based on VWAP confluence + volume spike + session sweep"""
        if not data.ContainsKey(self.gold_symbol) or self.current_session is None:
            return
            
        if self.session_trades >= self.trades_per_session:
            return  # Max trades per session reached
            
        bar = data[self.gold_symbol]
        
        # Check if we have valid indicators
        if not self.vwap.IsReady or not self.volume_sma.IsReady:
            return
            
        # Entry conditions
        price = bar.Close
        vwap_value = self.vwap.Current.Value
        volume = bar.Volume
        avg_volume = self.volume_sma.Current.Value
        
        # Get current session data
        session_high = self.session_high[self.current_session]
        session_low = self.session_low[self.current_session]
        session_range = session_high - session_low
        
        # Skip if session range is too small (avoid choppy markets)
        min_range = 5.0  # Minimum $5 range
        if session_range < min_range:
            return
        
        # Volume spike detection (configurable multiplier)
        volume_spike = volume > (avg_volume * 2.0)
        
        # VWAP confluence (price near VWAP with configurable tolerance)
        vwap_confluence = abs(price - vwap_value) / vwap_value < 0.001
        
        # Session high/low sweep detection with rejection
        sweep_high_rejection = (price > session_high * 0.998 and 
                               bar.Close < bar.Open)  # Rejection candle
        sweep_low_rejection = (price < session_low * 1.002 and 
                              bar.Close > bar.Open)   # Rejection candle
        
        # Additional confluence factors
        price_momentum = (bar.Close - bar.Open) / bar.Open
        strong_momentum = abs(price_momentum) > 0.0005  # 0.05% minimum momentum
        
        # Entry signals with enhanced logic
        long_signal = (vwap_confluence and volume_spike and 
                      sweep_low_rejection and strong_momentum and price_momentum > 0)
        short_signal = (vwap_confluence and volume_spike and 
                       sweep_high_rejection and strong_momentum and price_momentum < 0)
        
        # High-confidence setup detection (all three conditions must be met)
        is_high_confidence = (vwap_confluence and volume_spike and 
                             (sweep_high_rejection or sweep_low_rejection))
        
        # Get position sizing based on confidence level
        fib_target = self.get_current_fibonacci_target(self.current_session)
        contract_size = get_contracts_for_setup(is_high_confidence)
        
        if long_signal:
            confidence_label = "HIGH-CONF" if is_high_confidence else "STANDARD"
            self.Log(f"[ENTRY] Long signal [{confidence_label}] - Fib target: ${fib_target}, Contracts: {contract_size}")
            self.ExecuteTrade(True, price, is_high_confidence)
        elif short_signal:
            confidence_label = "HIGH-CONF" if is_high_confidence else "STANDARD"
            self.Log(f"[ENTRY] Short signal [{confidence_label}] - Fib target: ${fib_target}, Contracts: {contract_size}")
            self.ExecuteTrade(False, price, is_high_confidence)
    
    def ExecuteTrade(self, is_long, entry_price, is_high_confidence=False):
        """Execute trade with Fibonacci-based position sizing and bracket orders"""
        
        # Get dynamic contract sizing based on mode and confidence
        contracts = get_contracts_for_setup(is_high_confidence)
        profit_target_usd = self.get_current_fibonacci_target(self.current_session)
        
        # Log mode and contract allocation
        mode_display = self.trading_mode.get_mode_display_name()
        confidence_type = "HIGH-CONFIDENCE" if is_high_confidence else "STANDARD"
        self.Log(f"[TRADE EXEC] {mode_display} - {confidence_type} setup - Contracts: {contracts}")
        
        # Enhanced price level calculations for Gold futures
        # GC futures: $100 per full point (1.0), minimum tick = 0.1 ($10)
        points_per_dollar = 0.01  # More precise: $1 = 0.01 points for GC
        profit_target_points = profit_target_usd * points_per_dollar
        
        # Dynamic stop loss based on session volatility and Fibonacci level
        base_stop_points = profit_target_points * 0.4  # 2.5:1 reward/risk ratio
        volatility_adjustment = self.GetSessionVolatilityAdjustment()
        stop_loss_points = base_stop_points * volatility_adjustment
        
        # Calculate precise entry and exit levels
        if is_long:
            take_profit = round(entry_price + profit_target_points, 1)  # Round to nearest tick
            stop_loss = round(entry_price - stop_loss_points, 1)
            quantity = contracts
        else:
            take_profit = round(entry_price - profit_target_points, 1)
            stop_loss = round(entry_price + stop_loss_points, 1)
            quantity = -contracts
        
        # Execute bracket order strategy
        try:
            # Primary market entry order
            entry_ticket = self.MarketOrder(self.gold_symbol, quantity)
            
            if entry_ticket:
                # Create bracket orders with proper order management
                profit_ticket = self.LimitOrder(self.gold_symbol, -quantity, take_profit)
                stop_ticket = self.StopMarketOrder(self.gold_symbol, -quantity, stop_loss)
                
                # Store order tickets for management
                self.active_orders = {
                    'entry': entry_ticket,
                    'profit': profit_ticket,
                    'stop': stop_ticket,
                    'entry_time': self.Time
                }
                
                # Update counters
                self.daily_trades += 1
                self.session_trades += 1
                self.position_entry_price = entry_price
                
                # Store comprehensive trade info
                self.current_trade_info = {
                    'time': self.Time,
                    'direction': 'LONG' if is_long else 'SHORT',
                    'contracts': contracts,
                    'entry_price': entry_price,
                    'target_profit': profit_target_usd,
                    'fib_index': self.session_fib_index[self.current_session],
                    'session': self.current_session,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'risk_reward_ratio': profit_target_points / stop_loss_points,
                    'volatility_adjustment': volatility_adjustment,
                    'order_tickets': {
                        'entry': entry_ticket.OrderId if entry_ticket else None,
                        'profit': profit_ticket.OrderId if profit_ticket else None,
                        'stop': stop_ticket.OrderId if stop_ticket else None
                    }
                }
                
                # Enhanced logging
                direction = "LONG" if is_long else "SHORT"
                rr_ratio = profit_target_points / stop_loss_points
                
                # Enhanced trade entry logging
                self.Log(f"\n🎯 TRADE ENTRY #{self.daily_trades}:")
                self.Log(f"   Direction: {direction} | Contracts: {contracts} | Price: ${entry_price:.1f}")
                self.Log(f"   TP: ${take_profit:.1f} (+${profit_target_usd}) | SL: ${stop_loss:.1f}")
                self.Log(f"   R:R {rr_ratio:.1f}:1 | Session: {self.current_session.upper()}")
                self.Log(f"   Time: {self.Time.strftime('%H:%M:%S')} | Daily Trades: {self.daily_trades}/{self.max_trades_per_day}")
                
                # Store current trade info for later use
                self.current_trade_info = {
                    'entry_time': self.Time,
                    'entry_price': entry_price,
                    'direction': 'LONG' if is_long else 'SHORT',
                    'contracts': contracts,
                    'session': self.current_session,
                    'fibonacci_level': self.session_fib_index[self.current_session],
                    'trading_mode': self.trading_mode.get_current_mode(),
                    'mode_display': self.trading_mode.get_mode_display_name(),
                    'is_high_confidence': is_high_confidence,
                    'confidence_type': 'HIGH-CONFIDENCE' if is_high_confidence else 'STANDARD'
                }
                
            else:
                direction = "LONG" if is_long else "SHORT"
                self.Log(f"[ERROR] Failed to place entry order for {direction} trade")
                
        except Exception as e:
            self.Log(f"[ERROR] Trade execution failed: {str(e)}")
    
    def GetSessionVolatilityAdjustment(self):
        """Calculate volatility adjustment for stop loss based on session conditions"""
        if self.current_session is None:
            return 1.0
            
        # Get session range
        session_high = self.session_high[self.current_session]
        session_low = self.session_low[self.current_session]
        session_range = session_high - session_low
        
        # Base volatility adjustment
        if session_range < 5.0:  # Low volatility
            return 0.8  # Tighter stops
        elif session_range > 15.0:  # High volatility
            return 1.3  # Wider stops
        else:
            return 1.0  # Normal stops
    
    def ManageExitOrders(self):
        """Advanced exit order management and trailing stops"""
        if not self.current_trade_info or not self.active_orders:
            return
            
        current_position = self.Portfolio[self.gold_symbol]
        if current_position.Quantity == 0:
            return  # No position to manage
            
        current_price = self.Securities[self.gold_symbol].Price
        entry_price = self.current_trade_info['entry_price']
        is_long = self.current_trade_info['direction'] == 'LONG'
        
        # Calculate current unrealized PnL
        if is_long:
            unrealized_pnl = (current_price - entry_price) * abs(current_position.Quantity) * 100
        else:
            unrealized_pnl = (entry_price - current_price) * abs(current_position.Quantity) * 100
            
        # Implement trailing stop logic for profitable trades
        fib_target = self.current_trade_info['target_profit']
        
        if unrealized_pnl > fib_target * 0.5:  # 50% of target reached
            self.ImplementTrailingStop(current_price, is_long)
            
        # Enhanced position status logging every minute
        if self.Time.second == 0:
            pnl_percentage = (unrealized_pnl / fib_target * 100) if fib_target > 0 else 0
            entry_price = self.current_trade_info.get('actual_entry_price', self.current_trade_info['entry_price'])
            
            self.Log(f"📊 POSITION: {self.current_trade_info['direction']} {abs(current_position.Quantity)} @ "
                    f"${entry_price:.1f} → ${current_price:.1f} | Unrealized: ${unrealized_pnl:.2f} "
                    f"({pnl_percentage:.1f}% of ${fib_target} target)")
    
    def ImplementTrailingStop(self, current_price, is_long):
        """Implement trailing stop logic for profitable positions"""
        if 'trailing_stop_activated' not in self.current_trade_info:
            self.current_trade_info['trailing_stop_activated'] = True
            self.current_trade_info['highest_profit_price'] = current_price
            self.Log(f"[TRAILING] Trailing stop activated at ${current_price:.1f}")
            return
            
        # Update trailing levels
        if is_long and current_price > self.current_trade_info['highest_profit_price']:
            self.current_trade_info['highest_profit_price'] = current_price
            # Update stop loss order (implementation would depend on broker API)
            
        elif not is_long and current_price < self.current_trade_info['highest_profit_price']:
            self.current_trade_info['highest_profit_price'] = current_price
            # Update stop loss order (implementation would depend on broker API)
    
    def CalculatePositionSize(self):
        """Calculate position size based on Fibonacci sequence and risk limits (deprecated - use get_fibonacci_contract_size)"""
        
        # This method is kept for compatibility but should use session-specific sizing
        if self.current_session:
            return self.get_fibonacci_contract_size(self.current_session)
        
        # Fallback to default
        return self.default_contracts
    
    def ManagePosition(self, data):
        """Manage existing positions with advanced exit logic"""
        # Call advanced exit order management
        self.ManageExitOrders()
        
        # Additional position management logic can be added here
        # Such as partial profit taking, dynamic stop adjustments, etc.
        pass
    
    def OnOrderEvent(self, orderEvent):
        """Enhanced order event handling with comprehensive trade tracking"""
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        if orderEvent.Status == OrderStatus.Filled:
            self.HandleOrderFill(order, orderEvent)
        elif orderEvent.Status == OrderStatus.Canceled:
            self.Log(f"[ORDER] Order canceled: {order.Type} {order.Quantity} @ {order.LimitPrice if hasattr(order, 'LimitPrice') else 'Market'}")
        elif orderEvent.Status == OrderStatus.Invalid:
            self.Log(f"[ERROR] Invalid order: {order.Type} {order.Quantity} - {orderEvent.Message}")
    
    def HandleOrderFill(self, order, orderEvent):
        """Handle different types of order fills with detailed tracking"""
        fill_price = orderEvent.FillPrice
        fill_quantity = orderEvent.FillQuantity
        
        if order.Type == OrderType.Market:
            # Entry order filled
            self.HandleEntryFill(order, orderEvent)
            
        elif order.Type == OrderType.Limit:
            # Take profit order filled
            self.HandleTakeProfitFill(order, orderEvent)
            
        elif order.Type == OrderType.StopMarket:
            # Stop loss order filled
            self.HandleStopLossFill(order, orderEvent)
            
        else:
            self.Log(f"[ORDER] Unknown order type filled: {order.Type} {fill_quantity} @ ${fill_price:.1f}")
    
    def HandleEntryFill(self, order, orderEvent):
        """Handle entry order fills"""
        fill_price = orderEvent.FillPrice
        fill_quantity = orderEvent.FillQuantity
        direction = "LONG" if fill_quantity > 0 else "SHORT"
        
        # Update current trade info with actual fill price
        if self.current_trade_info:
            self.current_trade_info['actual_entry_price'] = fill_price
            self.current_trade_info['actual_quantity'] = abs(fill_quantity)
            self.current_trade_info['entry_fill_time'] = self.Time
            
        self.Log(f"[ENTRY FILLED] {direction} {abs(fill_quantity)} contracts @ ${fill_price:.1f} | "
                f"Session: {self.current_session} | Trade #{self.daily_trades}")
    
    def HandleTakeProfitFill(self, order, orderEvent):
        """Handle take profit order fills - winning trades"""
        if not self.current_trade_info:
            self.Log(f"[WARNING] Take profit filled but no current trade info")
            return
            
        fill_price = orderEvent.FillPrice
        fill_quantity = abs(orderEvent.FillQuantity)
        entry_price = self.current_trade_info.get('actual_entry_price', self.current_trade_info['entry_price'])
        
        # Calculate actual profit
        if self.current_trade_info['direction'] == 'LONG':
            profit_per_contract = (fill_price - entry_price) * 100  # $100 per point for GC
        else:
            profit_per_contract = (entry_price - fill_price) * 100
            
        total_profit = profit_per_contract * fill_quantity
        self.daily_pnl += total_profit
        
        # Update Fibonacci progression for winning trade
        session = self.current_trade_info['session']
        self.advance_fibonacci(session, True)
        
        # Enhanced logging
        fib_target = self.current_trade_info['target_profit']
        actual_vs_target = (total_profit / fib_target) * 100 if fib_target > 0 else 0
        
        self.Log(f"\n✅ PROFIT TAKEN:")
        self.Log(f"   Amount: +${total_profit:.2f} ({actual_vs_target:.1f}% of ${fib_target} target)")
        self.Log(f"   Daily PnL: ${self.daily_pnl:.2f} | Session: {session.upper()}")
        self.Log(f"   Fibonacci Advanced | Consecutive Wins: {self.consecutive_wins}")
        
        # Update session statistics with mode information
        if session in self.session_stats:
            win_record = {
                'pnl': total_profit,
                'result': 'WIN',
                'close_time': self.Time,
                'close_price': fill_price,
                'trading_mode': self.trading_mode.get_current_mode(),
                'mode_display': self.trading_mode.get_mode_display_name(),
                **self.current_trade_info
            }
            self.session_stats[session].append(win_record)
        
        # Cancel remaining stop loss order
        self.CancelRemainingOrders()
        
        # Clear current trade
        self.current_trade_info = None
        self.active_orders = None
    
    def HandleStopLossFill(self, order, orderEvent):
        """Handle stop loss order fills - losing trades"""
        if not self.current_trade_info:
            self.Log(f"[WARNING] Stop loss filled but no current trade info")
            return
            
        fill_price = orderEvent.FillPrice
        fill_quantity = abs(orderEvent.FillQuantity)
        entry_price = self.current_trade_info.get('actual_entry_price', self.current_trade_info['entry_price'])
        
        # Calculate actual loss
        if self.current_trade_info['direction'] == 'LONG':
            loss_per_contract = (fill_price - entry_price) * 100  # Will be negative
        else:
            loss_per_contract = (entry_price - fill_price) * 100  # Will be negative
            
        total_loss = loss_per_contract * fill_quantity
        self.daily_pnl += total_loss
        
        # Reset Fibonacci progression for losing trade
        session = self.current_trade_info['session']
        self.advance_fibonacci(session, False)
        
        # Enhanced logging
        expected_stop = self.current_trade_info['stop_loss']
        slippage = abs(fill_price - expected_stop)
        
        self.Log(f"\n❌ STOP LOSS HIT:")
        self.Log(f"   Loss: ${total_loss:.2f} (Slippage: ${slippage:.1f})")
        self.Log(f"   Daily PnL: ${self.daily_pnl:.2f} | Session: {session.upper()}")
        self.Log(f"   Fibonacci Reset | Consecutive Losses: {self.consecutive_losses}")
        
        # Update session statistics with mode information
        if session in self.session_stats:
            loss_record = {
                'pnl': total_loss,
                'result': 'LOSS',
                'close_time': self.Time,
                'close_price': fill_price,
                'trading_mode': self.trading_mode.get_current_mode(),
                'mode_display': self.trading_mode.get_mode_display_name(),
                **self.current_trade_info
            }
            self.session_stats[session].append(loss_record)
        
        # Cancel remaining take profit order
        self.CancelRemainingOrders()
        
        # Clear current trade
        self.current_trade_info = None
        self.active_orders = None
    
    def CancelRemainingOrders(self):
        """Cancel any remaining bracket orders when one leg is filled"""
        if not self.active_orders:
            return
            
        try:
            # Cancel profit and stop orders that haven't been filled
            for order_type, ticket in self.active_orders.items():
                if order_type != 'entry' and ticket and ticket.Status not in [OrderStatus.Filled, OrderStatus.Canceled]:
                    ticket.Cancel()
                    self.Log(f"[ORDER] Canceled remaining {order_type} order")
        except Exception as e:
            self.Log(f"[ERROR] Failed to cancel remaining orders: {str(e)}")
    
    def CalculateTradePnL(self, orderEvent):
        """Calculate PnL for a completed trade"""
        # Simplified PnL calculation
        # In practice, this would be more sophisticated
        return orderEvent.FillQuantity * (orderEvent.FillPrice - self.position_entry_price) * 100
    
    def ResetDailyCounters(self):
        """Reset daily counters at start of new day"""
        if self.daily_trades > 0:  # Log previous day's results
            self.Log(f"Daily Summary - Trades: {self.daily_trades} | PnL: ${self.daily_pnl:.2f} | "
                    f"Fib Completions: {self.daily_fib_completions}")
        
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.stop_trading_today = False
        self.session_trades = 0
        self.current_session = None
        self.daily_fib_completions = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
        # Reset all session Fibonacci indices
        for session_name in self.session_fib_index:
            self.session_fib_index[session_name] = 0
        
        # Reset session highs/lows
        for session_name in self.session_high:
            self.session_high[session_name] = 0
            self.session_low[session_name] = float('inf')
        
        self.Log(f"New trading day started - Reset all counters and Fibonacci sequences")
    
    def OnEndOfAlgorithm(self):
        """Final logging and cleanup"""
        total_trades = len(self.trade_log)
        if total_trades > 0:
            self.Log(f"Strategy completed - Total trades: {total_trades}")
            self.Log(f"Final portfolio value: ${self.Portfolio.TotalPortfolioValue}")
            
            # Log trade statistics
            winning_trades = sum(1 for trade in self.trade_log if 'pnl' in trade and trade['pnl'] > 0)
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            self.Log(f"Win rate: {win_rate:.1f}% ({winning_trades}/{total_trades})")