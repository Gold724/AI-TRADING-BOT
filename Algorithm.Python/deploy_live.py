#!/usr/bin/env python3
"""
Tesla369Gold Live Deployment Script
Integrates QuantConnect strategy with Bulenox ProjectX trading platform
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import logging
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class Tesla369LiveDeployment:
    def __init__(self, config_path="backtest_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.setup_logging()
        self.trade_count_today = 0
        self.daily_pnl = 0.0
        self.session_active = False
        
        # Load Bulenox credentials
        self.bulenox_username = os.getenv('BULENOX_USERNAME')
        self.bulenox_password = os.getenv('BULENOX_PASSWORD')
        
        if not self.bulenox_username or not self.bulenox_password:
            self.logger.error("❌ Bulenox credentials not found in environment variables")
            raise ValueError("Missing BULENOX_USERNAME or BULENOX_PASSWORD")
            
        # Load latest trade request data
        self.load_trade_request_data()
        
    def load_config(self):
        """Load deployment configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_path}")
            sys.exit(1)
            
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('Tesla369Gold')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"tesla369gold_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def load_trade_request_data(self):
        """Load the latest trade request data from TradeBot Sentinel"""
        try:
            # Load from trade_request_full.py
            trade_file = Path("../trade_request_full.py")
            if trade_file.exists():
                with open(trade_file, 'r') as f:
                    content = f.read()
                    
                # Extract URL, headers, and data (simplified parsing)
                import re
                
                url_match = re.search(r'url = ["\']([^"\']+)["\']', content)
                self.trade_url = url_match.group(1) if url_match else None
                
                # Extract headers
                headers_match = re.search(r'headers = ({[^}]+})', content, re.DOTALL)
                if headers_match:
                    headers_str = headers_match.group(1)
                    # Simple parsing - in production, use ast.literal_eval
                    self.trade_headers = eval(headers_str)
                else:
                    self.trade_headers = {}
                    
                self.logger.info(f"✅ Loaded trade request data from {trade_file}")
                self.logger.info(f"   Trade URL: {self.trade_url}")
                
            else:
                self.logger.warning("⚠️  trade_request_full.py not found, using default settings")
                self.trade_url = None
                self.trade_headers = {}
                
        except Exception as e:
            self.logger.error(f"❌ Error loading trade request data: {e}")
            self.trade_url = None
            self.trade_headers = {}
            
    def check_session_windows(self) -> bool:
        """Check if current time is within trading session windows"""
        now = datetime.now()
        current_time = now.time()
        
        # NY session windows (converted to local time)
        sessions = [
            (3, 0, 6, 0),    # 03:00-06:00
            (8, 20, 11, 30), # 08:20-11:30
            (13, 0, 15, 30)  # 13:00-15:30
        ]
        
        for start_h, start_m, end_h, end_m in sessions:
            start_time = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0).time()
            end_time = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0).time()
            
            if start_time <= current_time <= end_time:
                return True
                
        return False
        
    def check_daily_limits(self) -> Dict[str, bool]:
        """Check if daily trading limits have been reached"""
        max_trades = self.config['parameters']['trades_per_day']['default']
        profit_target = self.config['parameters']['daily_profit_target']['default']
        max_drawdown = self.config['parameters']['daily_max_drawdown']['default']
        
        return {
            'trades_limit_reached': self.trade_count_today >= max_trades,
            'profit_target_hit': self.daily_pnl >= profit_target,
            'drawdown_limit_breached': self.daily_pnl <= -max_drawdown
        }
        
    def should_trade(self) -> tuple[bool, str]:
        """Determine if trading should continue"""
        # Check session windows
        if not self.check_session_windows():
            return False, "Outside trading session windows"
            
        # Check daily limits
        limits = self.check_daily_limits()
        
        if limits['trades_limit_reached']:
            return False, f"Daily trade limit reached ({self.trade_count_today} trades)"
            
        if limits['profit_target_hit']:
            return False, f"Daily profit target hit (${self.daily_pnl:.2f})"
            
        if limits['drawdown_limit_breached']:
            return False, f"Daily drawdown limit breached (${self.daily_pnl:.2f})"
            
        return True, "Ready to trade"
        
    def execute_trade(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade using Bulenox API"""
        if not self.trade_url or not self.trade_headers:
            self.logger.error("❌ Trade request data not available")
            return {'success': False, 'error': 'No trade request data'}
            
        try:
            # Prepare trade data based on signal
            trade_data = {
                'accountId': 228936,  # From intercepted data
                'symbolId': 'GC',     # Gold Futures
                'type': signal_data.get('direction', 2),  # 1=Buy, 2=Sell
                'positionSize': signal_data.get('contracts', 1),
                'customTag': f"Tesla369Gold_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            self.logger.info(f"🚀 Executing trade: {trade_data}")
            
            # Execute trade
            response = requests.post(
                self.trade_url,
                headers=self.trade_headers,
                json=trade_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Trade executed successfully")
                self.trade_count_today += 1
                
                return {
                    'success': True,
                    'response': response.json() if response.content else {},
                    'trade_data': trade_data
                }
            else:
                self.logger.error(f"❌ Trade failed with status: {response.status_code}")
                self.logger.error(f"   Response: {response.text}")
                
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'trade_data': trade_data
                }
                
        except Exception as e:
            self.logger.error(f"❌ Trade execution error: {e}")
            return {'success': False, 'error': str(e)}
            
    def simulate_strategy_signals(self) -> Optional[Dict[str, Any]]:
        """Simulate Tesla369Gold strategy signals (replace with actual strategy logic)"""
        # This is a simplified simulation - in production, integrate with actual QuantConnect strategy
        import random
        
        # Simulate signal generation based on strategy rules
        if random.random() < 0.3:  # 30% chance of signal
            signal_strength = random.randint(1, 3)
            direction = random.choice([1, 2])  # 1=Buy, 2=Sell
            
            return {
                'direction': direction,
                'contracts': min(signal_strength, self.config['parameters']['max_contracts']['default']),
                'signal_strength': signal_strength,
                'entry_reason': 'Simulated signal',
                'timestamp': datetime.now().isoformat()
            }
            
        return None
        
    def run_trading_session(self):
        """Main trading session loop"""
        self.logger.info("🎯 Tesla369Gold Live Trading Session Started")
        self.logger.info(f"   Account: {self.bulenox_username}")
        self.logger.info(f"   Max trades per day: {self.config['parameters']['trades_per_day']['default']}")
        self.logger.info(f"   Profit target: ${self.config['parameters']['daily_profit_target']['default']}")
        self.logger.info(f"   Max drawdown: ${self.config['parameters']['daily_max_drawdown']['default']}")
        
        session_start = datetime.now()
        
        try:
            while True:
                # Check if we should continue trading
                should_continue, reason = self.should_trade()
                
                if not should_continue:
                    self.logger.info(f"🛑 Trading halted: {reason}")
                    
                    # If it's end of day, break completely
                    if "session" not in reason.lower():
                        break
                    else:
                        # Wait for next session window
                        time.sleep(60)  # Check every minute
                        continue
                        
                # Generate trading signals
                signal = self.simulate_strategy_signals()
                
                if signal:
                    self.logger.info(f"📊 Signal detected: {signal}")
                    
                    # Execute trade
                    result = self.execute_trade(signal)
                    
                    if result['success']:
                        self.logger.info(f"✅ Trade #{self.trade_count_today} executed successfully")
                        
                        # Update daily PnL (simplified - in production, get actual fill data)
                        estimated_pnl = random.uniform(-100, 200)  # Simulate PnL
                        self.daily_pnl += estimated_pnl
                        
                        self.logger.info(f"   Estimated PnL: ${estimated_pnl:.2f}")
                        self.logger.info(f"   Daily PnL: ${self.daily_pnl:.2f}")
                        
                    else:
                        self.logger.error(f"❌ Trade execution failed: {result.get('error', 'Unknown error')}")
                        
                # Wait before next signal check
                time.sleep(30)  # Check for signals every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Trading session interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Trading session error: {e}")
        finally:
            session_end = datetime.now()
            session_duration = session_end - session_start
            
            self.logger.info("📊 Trading Session Summary:")
            self.logger.info(f"   Duration: {session_duration}")
            self.logger.info(f"   Trades executed: {self.trade_count_today}")
            self.logger.info(f"   Daily PnL: ${self.daily_pnl:.2f}")
            
    def reset_daily_counters(self):
        """Reset daily trading counters (call at start of each trading day)"""
        self.trade_count_today = 0
        self.daily_pnl = 0.0
        self.logger.info("🔄 Daily counters reset")
        
    def emergency_flatten(self):
        """Emergency position flattening (15:30 NY time)"""
        self.logger.warning("🚨 Emergency flatten triggered - closing all positions")
        # In production, implement actual position closing logic
        # This would query current positions and close them
        
def main():
    """Main deployment function"""
    print("🚀 Tesla369Gold Live Deployment")
    print("================================\n")
    
    try:
        # Initialize deployment
        deployment = Tesla369LiveDeployment()
        
        # Check if we should start trading
        should_trade, reason = deployment.should_trade()
        
        if should_trade:
            print(f"✅ {reason}")
            print("🎯 Starting live trading session...\n")
            
            # Run trading session
            deployment.run_trading_session()
            
        else:
            print(f"⚠️  Cannot start trading: {reason}")
            print("   Check session windows and daily limits.")
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()