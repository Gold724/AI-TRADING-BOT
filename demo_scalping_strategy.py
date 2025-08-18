#!/usr/bin/env python3
"""
Scalping Strategy Demo - AI Trading Sentinel
==========================================

Demonstrates scalping functionality using simulation mode (Dreamer Mode)
for safe testing without real broker connections.

Features:
- Gold (XAUUSD) scalping with tight spreads
- Tesla 3-6-9 trade rhythm
- Fibonacci position sizing
- Risk management controls
- Real-time simulation

Author: TRAE-SentinelOps
Version: 1.0.0
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, time as dt_time
from typing import Dict, Any, List

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'liveops'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import configuration
try:
    from bulenox_strategy_config import BulenoxStrategyConfig as CONFIG
except ImportError:
    # Fallback configuration
    class CONFIG:
        DAILY_PROFIT_TARGET = 535.71
        FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]
        TRADES_PER_SESSION = 3
        BASE_TAKE_PROFIT_PERCENT = 0.15
        BASE_STOP_LOSS_PERCENT = 0.02
        TRADING_SESSIONS = {
            'morning': {'start': dt_time(3, 0), 'end': dt_time(6, 0), 'name': 'Morning Session'},
            'midday': {'start': dt_time(8, 20), 'end': dt_time(11, 30), 'name': 'Midday Session'},
            'afternoon': {'start': dt_time(13, 0), 'end': dt_time(15, 30), 'name': 'Afternoon Session'}
        }

# Import Dreamer Mode for simulation
try:
    from dreamer_mode import DreamerMode
except ImportError:
    print("⚠️  Dreamer Mode not available. Creating mock simulation...")
    class DreamerMode:
        def __init__(self, config):
            self.config = config
            self.simulated_trades = []
            self.balance = 10000.0
            
        def simulate_trade(self, account_id, broker, symbol, action, lot_size, take_profit=None, stop_loss=None):
            trade_id = f"DEMO_{int(time.time())}"
            current_price = 2400.0 if symbol == "XAUUSD" else 1.1000
            
            return {
                "status": "success",
                "trade_id": trade_id,
                "symbol": symbol,
                "action": action,
                "lot_size": lot_size,
                "open_price": current_price,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "timestamp": datetime.now().isoformat(),
                "simulated": True
            }
            
        def get_account_summary(self, account_id):
            return {
                "account_id": account_id,
                "balance": self.balance,
                "equity": self.balance,
                "open_trades": len(self.simulated_trades),
                "total_profit": 0.0
            }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScalpingStrategyDemo:
    """Scalping Strategy Demonstration using Dreamer Mode"""
    
    def __init__(self):
        """Initialize the scalping demo"""
        self.config = {
            "governance": {
                "allowed_symbols": ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
            }
        }
        
        # Initialize Dreamer Mode for simulation
        self.dreamer = DreamerMode(self.config)
        self.account_id = "SCALPING_DEMO"
        self.broker = "bulenox_simulation"
        
        # Trading state
        self.current_session = None
        self.trades_in_session = 0
        self.fibonacci_level = 0
        self.daily_profit = 0.0
        
        logger.info("🚀 Scalping Strategy Demo initialized")
        logger.info(f"📊 Target: ${CONFIG.DAILY_PROFIT_TARGET}/day")
        logger.info(f"🎯 Fibonacci Sequence: {CONFIG.FIBONACCI_PROFIT_SEQUENCE}")
    
    def get_current_session(self) -> str:
        """Determine current trading session"""
        current_time = datetime.now().time()
        
        for session_name, session_info in CONFIG.TRADING_SESSIONS.items():
            if session_info['start'] <= current_time <= session_info['end']:
                return session_name
        
        return None
    
    def calculate_position_size(self, confidence_level: str = "medium") -> float:
        """Calculate position size based on Fibonacci sequence and confidence"""
        base_size = 0.01  # Base lot size
        
        # Fibonacci multiplier
        fib_multiplier = 1
        if self.fibonacci_level < len(CONFIG.FIBONACCI_PROFIT_SEQUENCE):
            fib_multiplier = CONFIG.FIBONACCI_PROFIT_SEQUENCE[self.fibonacci_level] / 10
        
        # Confidence multiplier
        confidence_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5
        }
        
        confidence_mult = confidence_multipliers.get(confidence_level, 1.0)
        
        return round(base_size * fib_multiplier * confidence_mult, 2)
    
    def calculate_scalping_levels(self, symbol: str, current_price: float, action: str) -> Dict[str, float]:
        """Calculate tight scalping levels for take profit and stop loss"""
        
        if symbol == "XAUUSD":
            # Gold scalping - tight levels
            tp_pips = 3.0  # $30 profit (3 points)
            sl_pips = 2.0  # $20 risk (2 points)
            pip_size = 0.1
        else:
            # Forex scalping
            tp_pips = 8.0  # 8 pips profit
            sl_pips = 5.0  # 5 pips risk
            pip_size = 0.0001 if "JPY" not in symbol else 0.01
        
        if action.upper() == "BUY":
            take_profit = current_price + (tp_pips * pip_size)
            stop_loss = current_price - (sl_pips * pip_size)
        else:  # SELL
            take_profit = current_price - (tp_pips * pip_size)
            stop_loss = current_price + (sl_pips * pip_size)
        
        return {
            "take_profit": round(take_profit, 5),
            "stop_loss": round(stop_loss, 5),
            "risk_reward_ratio": tp_pips / sl_pips
        }
    
    def execute_scalping_trade(self, symbol: str = "XAUUSD", action: str = "BUY", confidence: str = "medium") -> Dict[str, Any]:
        """Execute a scalping trade using simulation"""
        
        # Check session limits
        current_session = self.get_current_session()
        if not current_session:
            return {"status": "error", "message": "Outside trading hours"}
        
        if current_session != self.current_session:
            # New session - reset counters
            self.current_session = current_session
            self.trades_in_session = 0
            self.fibonacci_level = 0
            logger.info(f"📅 New session: {CONFIG.TRADING_SESSIONS[current_session]['name']}")
        
        if self.trades_in_session >= CONFIG.TRADES_PER_SESSION:
            return {"status": "error", "message": f"Session limit reached ({CONFIG.TRADES_PER_SESSION} trades)"}
        
        # Calculate position size
        lot_size = self.calculate_position_size(confidence)
        
        # Simulate current price
        current_price = 2400.0 + (time.time() % 100) / 100  # Simulate price movement
        
        # Calculate scalping levels
        levels = self.calculate_scalping_levels(symbol, current_price, action)
        
        # Execute simulated trade
        trade_result = self.dreamer.simulate_trade(
            account_id=self.account_id,
            broker=self.broker,
            symbol=symbol,
            action=action,
            lot_size=lot_size,
            take_profit=levels["take_profit"],
            stop_loss=levels["stop_loss"]
        )
        
        if trade_result.get("success"):
            self.trades_in_session += 1
            self.fibonacci_level += 1
            
            # Calculate expected profit
            if symbol == "XAUUSD":
                expected_profit = abs(levels["take_profit"] - current_price) * 100 * lot_size
            else:
                expected_profit = abs(levels["take_profit"] - current_price) * 100000 * lot_size
            
            logger.info(f"✅ Scalping trade executed:")
            logger.info(f"   Symbol: {symbol} | Action: {action} | Size: {lot_size}")
            logger.info(f"   Entry: {current_price:.5f}")
            logger.info(f"   TP: {levels['take_profit']:.5f} | SL: {levels['stop_loss']:.5f}")
            logger.info(f"   Expected Profit: ${expected_profit:.2f}")
            logger.info(f"   Risk/Reward: 1:{levels['risk_reward_ratio']:.2f}")
            logger.info(f"   Session Progress: {self.trades_in_session}/{CONFIG.TRADES_PER_SESSION}")
            
            return {
                "status": "success",
                "trade_id": trade_result["trade_id"],
                "symbol": symbol,
                "action": action,
                "lot_size": lot_size,
                "entry_price": current_price,
                "take_profit": levels["take_profit"],
                "stop_loss": levels["stop_loss"],
                "expected_profit": expected_profit,
                "risk_reward_ratio": levels["risk_reward_ratio"],
                "fibonacci_level": self.fibonacci_level,
                "session": current_session,
                "trades_in_session": self.trades_in_session
            }
        
        return trade_result
    
    def run_scalping_demo(self, num_trades: int = 5):
        """Run a demonstration of scalping trades"""
        logger.info(f"🎯 Starting Scalping Demo - {num_trades} trades")
        logger.info("=" * 60)
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD"]
        actions = ["BUY", "SELL"]
        confidence_levels = ["medium", "high", "medium", "high", "medium"]
        
        successful_trades = 0
        total_expected_profit = 0.0
        
        for i in range(num_trades):
            logger.info(f"\n📈 Trade {i+1}/{num_trades}")
            
            # Vary parameters for demonstration
            symbol = symbols[i % len(symbols)]
            action = actions[i % len(actions)]
            confidence = confidence_levels[i % len(confidence_levels)]
            
            result = self.execute_scalping_trade(symbol, action, confidence)
            
            if result["status"] == "success":
                successful_trades += 1
                total_expected_profit += result["expected_profit"]
            else:
                logger.warning(f"❌ Trade failed: {result.get('message')}")
            
            # Simulate time between trades
            time.sleep(2)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 SCALPING DEMO SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful Trades: {successful_trades}/{num_trades}")
        logger.info(f"💰 Total Expected Profit: ${total_expected_profit:.2f}")
        logger.info(f"🎯 Daily Target Progress: {(total_expected_profit/CONFIG.DAILY_PROFIT_TARGET)*100:.1f}%")
        
        # Account summary
        account_summary = self.dreamer.get_account_summary(self.account_id)
        logger.info(f"💼 Account Balance: ${account_summary.get('balance', 0):.2f}")
        logger.info(f"📈 Open Positions: {account_summary.get('open_trades', 0)}")
        
        return {
            "successful_trades": successful_trades,
            "total_trades": num_trades,
            "expected_profit": total_expected_profit,
            "success_rate": (successful_trades / num_trades) * 100,
            "account_summary": account_summary
        }

def main():
    """Main function to run the scalping demo"""
    print("🚀 AI Trading Sentinel - Scalping Strategy Demo")
    print("=" * 50)
    print("📋 Features:")
    print("   • Gold (XAUUSD) scalping simulation")
    print("   • Tesla 3-6-9 trade rhythm")
    print("   • Fibonacci position sizing")
    print("   • Tight risk management")
    print("   • Real-time simulation (Dreamer Mode)")
    print("\n⚠️  This is a SIMULATION - no real trades are executed")
    print("=" * 50)
    
    # Initialize and run demo
    demo = ScalpingStrategyDemo()
    
    try:
        # Run the demo
        result = demo.run_scalping_demo(num_trades=6)
        
        print("\n🎉 Demo completed successfully!")
        print(f"📊 Success Rate: {result['success_rate']:.1f}%")
        print(f"💰 Expected Profit: ${result['expected_profit']:.2f}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo stopped by user")
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()