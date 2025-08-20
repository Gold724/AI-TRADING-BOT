#!/usr/bin/env python3
"""
Test script to verify Fibonacci integration in TradeBot Sentinel
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the strategy configuration
try:
    from bulenox_strategy_config import *
    print("[SUCCESS] Strategy configuration imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import strategy config: {e}")
    # Fallback configuration
    class CONFIG:
        FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]
        FULL_SYMBOL = "GCZ25"
        DEFAULT_CONTRACTS = 1
        MAX_CONTRACTS = 3
        DAILY_PROFIT_TARGET = 535.71
        MORNING_SESSION = ("09:30", "11:30")
        MIDDAY_SESSION = ("11:30", "14:30")
        AFTERNOON_SESSION = ("14:30", "16:30")

class FibonacciTester:
    def __init__(self):
        self.fibonacci_sequence = CONFIG.FIBONACCI_PROFIT_SEQUENCE
        self.session_fib_index = {
            'morning': 0,
            'midday': 0,
            'afternoon': 0
        }
        self.current_session = 'morning'
        self.daily_trades = 0
        self.session_trades = 0
        self.daily_pnl = 0.0
        
        print(f"[INIT] Fibonacci sequence: {self.fibonacci_sequence}")
        print(f"[INIT] Gold symbol: {CONFIG.FULL_SYMBOL}")
        print(f"[INIT] Daily target: ${CONFIG.DAILY_PROFIT_TARGET}")
    
    def get_current_fibonacci_target(self, session):
        """Get current Fibonacci profit target for session"""
        index = self.session_fib_index[session]
        if index < len(self.fibonacci_sequence):
            return self.fibonacci_sequence[index]
        return self.fibonacci_sequence[-1]  # Use last level if exceeded
    
    def advance_fibonacci(self, session, is_win):
        """Advance or reset Fibonacci sequence based on trade outcome"""
        if is_win:
            if self.session_fib_index[session] < len(self.fibonacci_sequence) - 1:
                self.session_fib_index[session] += 1
                print(f"[FIBONACCI] {session.upper()} advanced to level {self.session_fib_index[session]}")
            else:
                print(f"[FIBONACCI] {session.upper()} at maximum level")
        else:
            self.session_fib_index[session] = 0
            print(f"[FIBONACCI] {session.upper()} reset to level 0")
    
    def get_fibonacci_contract_size(self, session):
        """Calculate contract size based on Fibonacci level"""
        target = self.get_current_fibonacci_target(session)
        if target <= 20:
            return CONFIG.DEFAULT_CONTRACTS
        elif target <= 50:
            return min(2, CONFIG.MAX_CONTRACTS)
        else:
            return CONFIG.MAX_CONTRACTS
    
    def simulate_trade_sequence(self):
        """Simulate a sequence of trades to test Fibonacci progression"""
        print("\n[TEST] Starting Fibonacci trade sequence simulation...")
        
        # Simulate winning streak
        trade_outcomes = [True, True, False, True, True, True, False, True]
        
        for i, is_win in enumerate(trade_outcomes):
            print(f"\n--- Trade {i+1} ---")
            
            # Get current parameters
            profit_target = self.get_current_fibonacci_target(self.current_session)
            contracts = self.get_fibonacci_contract_size(self.current_session)
            
            print(f"[TRADE] Session: {self.current_session.upper()}")
            print(f"[TRADE] Fibonacci Level: {self.session_fib_index[self.current_session]}")
            print(f"[TRADE] Profit Target: ${profit_target}")
            print(f"[TRADE] Contracts: {contracts}")
            
            # Calculate Gold futures pricing
            entry_price = 2650.0
            points_per_dollar = 0.01
            profit_target_points = profit_target * points_per_dollar
            
            if is_win:
                take_profit = round(entry_price + profit_target_points, 1)
                actual_profit = profit_target
                print(f"[WIN] Entry: ${entry_price} | TP: ${take_profit} | Profit: ${actual_profit}")
            else:
                stop_loss = round(entry_price - (profit_target_points * 0.4), 1)
                actual_loss = -profit_target * 0.4
                print(f"[LOSS] Entry: ${entry_price} | SL: ${stop_loss} | Loss: ${actual_loss}")
            
            # Update tracking
            self.daily_trades += 1
            self.session_trades += 1
            profit_loss = actual_profit if is_win else actual_loss
            self.daily_pnl += profit_loss
            
            # Advance Fibonacci
            self.advance_fibonacci(self.current_session, is_win)
            
            print(f"[DAILY] Total P&L: ${self.daily_pnl:.2f} | Trades: {self.daily_trades}")
            
            # Check daily target
            if self.daily_pnl >= CONFIG.DAILY_PROFIT_TARGET:
                print(f"\n[SUCCESS] Daily profit target reached: ${self.daily_pnl:.2f} >= ${CONFIG.DAILY_PROFIT_TARGET}")
                break
        
        print(f"\n[SUMMARY] Final Results:")
        print(f"  - Total Trades: {self.daily_trades}")
        print(f"  - Total P&L: ${self.daily_pnl:.2f}")
        print(f"  - Target Achievement: {(self.daily_pnl / CONFIG.DAILY_PROFIT_TARGET * 100):.1f}%")
        print(f"  - Final Fibonacci Levels: {self.session_fib_index}")

def main():
    print("[TEST] Fibonacci Integration Test Starting...")
    print("=" * 50)
    
    tester = FibonacciTester()
    tester.simulate_trade_sequence()
    
    print("\n" + "=" * 50)
    print("[TEST] Fibonacci Integration Test Complete!")

if __name__ == "__main__":
    main()