#!/usr/bin/env python3
"""
Fibonacci Multi-Level Take Profit Strategy
==========================================

Solves the dual requirements:
1. Take profit at EVERY Fibonacci level (partial position closing)
2. Dynamic profit targets (not hardcoded)

This implementation allows for:
- Multiple take profit levels based on Fibonacci sequence
- Partial position closing at each level
- Dynamic contract allocation across levels
- Risk management with trailing stops
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bulenox_strategy_config import *
except ImportError:
    # Fallback configuration
    class CONFIG:
        FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]
        FULL_SYMBOL = "F.US.GCE"
        DEFAULT_CONTRACTS = 1
        MAX_CONTRACTS = 3
        DAILY_PROFIT_TARGET = 535.71
        MORNING_SESSION = ("09:30", "11:30")
        MIDDAY_SESSION = ("11:30", "14:30")
        AFTERNOON_SESSION = ("14:30", "16:30")

class FibonacciMultiTPStrategy:
    """
    Multi-level Take Profit Strategy using Fibonacci sequence
    
    Key Features:
    1. Distributes contracts across multiple TP levels
    2. Partial position closing at each Fibonacci level
    3. Dynamic profit targets based on session and market conditions
    4. Risk management with trailing stops after first TP hit
    """
    
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
        
        # Multi-TP specific attributes
        self.active_positions = {}
        self.tp_levels_hit = {}
        self.remaining_contracts = {}
        
        print(f"[INIT] Multi-TP Fibonacci Strategy initialized")
        print(f"[INIT] Fibonacci sequence: {self.fibonacci_sequence}")
        print(f"[INIT] Max contracts: {CONFIG.MAX_CONTRACTS}")
    
    def calculate_multi_tp_levels(self, session, entry_price, is_long=True, total_contracts=3):
        """
        Calculate multiple take profit levels based on Fibonacci sequence
        
        Args:
            session: Current trading session
            entry_price: Entry price for the trade
            is_long: True for long positions, False for short
            total_contracts: Total contracts to distribute across TP levels
            
        Returns:
            dict: TP levels with contract allocation
        """
        current_fib_index = self.session_fib_index[session]
        
        # Get next 3-5 Fibonacci levels for multi-TP
        tp_levels = {}
        contracts_per_level = self.distribute_contracts(total_contracts)
        
        # Calculate Gold futures pricing
        points_per_dollar = 0.01  # $1 = 0.01 points for GC
        
        for i, contracts in enumerate(contracts_per_level):
            if contracts == 0:
                continue
                
            # Get Fibonacci target for this level
            fib_index = min(current_fib_index + i, len(self.fibonacci_sequence) - 1)
            profit_target_usd = self.fibonacci_sequence[fib_index]
            profit_target_points = profit_target_usd * points_per_dollar
            
            if is_long:
                tp_price = round(entry_price + profit_target_points, 1)
            else:
                tp_price = round(entry_price - profit_target_points, 1)
            
            tp_levels[f"TP{i+1}"] = {
                'price': tp_price,
                'contracts': contracts,
                'profit_usd': profit_target_usd,
                'fib_level': fib_index,
                'fib_value': self.fibonacci_sequence[fib_index],
                'hit': False
            }
        
        return tp_levels
    
    def distribute_contracts(self, total_contracts):
        """
        Distribute contracts across multiple TP levels
        
        Strategy:
        - 1 contract: All on first TP
        - 2 contracts: 1 on TP1, 1 on TP2
        - 3 contracts: 1 on TP1, 1 on TP2, 1 on TP3
        
        Returns:
            list: Contracts per TP level
        """
        if total_contracts == 1:
            return [1, 0, 0, 0, 0]
        elif total_contracts == 2:
            return [1, 1, 0, 0, 0]
        elif total_contracts == 3:
            return [1, 1, 1, 0, 0]
        else:
            # For more than 3 contracts, distribute evenly
            base = total_contracts // 3
            remainder = total_contracts % 3
            distribution = [base, base, base, 0, 0]
            for i in range(remainder):
                distribution[i] += 1
            return distribution
    
    def create_multi_tp_order(self, session, entry_price, is_long=True, total_contracts=None):
        """
        Create a multi-level take profit order structure
        
        Returns:
            dict: Complete order structure with multiple TP levels
        """
        if total_contracts is None:
            total_contracts = self.get_fibonacci_contract_size(session)
        
        # Calculate TP levels
        tp_levels = self.calculate_multi_tp_levels(session, entry_price, is_long, total_contracts)
        
        # Calculate stop loss (2.5:1 risk/reward based on first TP)
        first_tp = list(tp_levels.values())[0]
        profit_points = abs(first_tp['price'] - entry_price)
        stop_loss_points = profit_points * 0.4  # 2.5:1 R:R
        
        if is_long:
            stop_loss = round(entry_price - stop_loss_points, 1)
        else:
            stop_loss = round(entry_price + stop_loss_points, 1)
        
        order_structure = {
            'entry_price': entry_price,
            'direction': 'LONG' if is_long else 'SHORT',
            'total_contracts': total_contracts,
            'stop_loss': stop_loss,
            'tp_levels': tp_levels,
            'session': session,
            'fib_start_index': self.session_fib_index[session],
            'timestamp': None,  # Would be set when order is placed
            'status': 'pending'
        }
        
        return order_structure
    
    def simulate_tp_hit(self, order_id, tp_level, current_price):
        """
        Simulate a take profit level being hit
        
        Args:
            order_id: Unique order identifier
            tp_level: TP level hit (TP1, TP2, etc.)
            current_price: Current market price
        """
        if order_id not in self.active_positions:
            print(f"[ERROR] Order {order_id} not found in active positions")
            return
        
        order = self.active_positions[order_id]
        tp_info = order['tp_levels'][tp_level]
        
        if tp_info['hit']:
            print(f"[WARNING] {tp_level} already hit for order {order_id}")
            return
        
        # Mark TP as hit
        tp_info['hit'] = True
        contracts_closed = tp_info['contracts']
        profit_realized = tp_info['profit_usd']
        
        # Update tracking
        self.daily_pnl += profit_realized
        
        # Check if this completes the Fibonacci level
        if tp_level == 'TP1':  # First TP hit advances Fibonacci
            self.advance_fibonacci(order['session'], True)
        
        print(f"\n🎯 {tp_level} HIT - Order {order_id}")
        print(f"   Contracts Closed: {contracts_closed}")
        print(f"   Profit Realized: ${profit_realized}")
        print(f"   Price: ${current_price} (Target: ${tp_info['price']})")
        print(f"   Fibonacci Level: {tp_info['fib_level']} (${tp_info['fib_value']})")
        print(f"   Daily P&L: ${self.daily_pnl:.2f}")
        
        # Check if all TPs are hit
        remaining_tps = [tp for tp in order['tp_levels'].values() if not tp['hit'] and tp['contracts'] > 0]
        
        if not remaining_tps:
            print(f"[COMPLETE] All TP levels hit for order {order_id}")
            order['status'] = 'completed'
            # Implement trailing stop for any remaining position
        else:
            print(f"[ACTIVE] {len(remaining_tps)} TP levels remaining")
            # Move stop loss to breakeven or implement trailing stop
            self.implement_trailing_stop(order_id, current_price)
    
    def implement_trailing_stop(self, order_id, current_price):
        """
        Implement trailing stop after first TP is hit
        """
        order = self.active_positions[order_id]
        entry_price = order['entry_price']
        is_long = order['direction'] == 'LONG'
        
        # Move stop to breakeven + small buffer
        buffer_points = 0.1  # $10 buffer
        
        if is_long:
            new_stop = entry_price + buffer_points
        else:
            new_stop = entry_price - buffer_points
        
        order['stop_loss'] = new_stop
        print(f"[TRAILING] Stop moved to breakeven+: ${new_stop}")
    
    def get_fibonacci_contract_size(self, session):
        """Calculate contract size based on Fibonacci level"""
        target = self.get_current_fibonacci_target(session)
        if target <= 20:
            return CONFIG.DEFAULT_CONTRACTS
        elif target <= 50:
            return min(2, CONFIG.MAX_CONTRACTS)
        else:
            return CONFIG.MAX_CONTRACTS
    
    def get_current_fibonacci_target(self, session):
        """Get current Fibonacci profit target for session"""
        index = self.session_fib_index[session]
        if index < len(self.fibonacci_sequence):
            return self.fibonacci_sequence[index]
        return self.fibonacci_sequence[-1]
    
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
    
    def demo_multi_tp_strategy(self):
        """
        Demonstrate the multi-TP strategy with realistic scenarios
        """
        print("\n" + "=" * 60)
        print("🎯 FIBONACCI MULTI-TP STRATEGY DEMONSTRATION")
        print("=" * 60)
        
        # Scenario 1: 3-contract trade with multiple TP levels
        print("\n📊 SCENARIO 1: 3-Contract Multi-TP Trade")
        print("-" * 40)
        
        entry_price = 2650.0
        order_structure = self.create_multi_tp_order('morning', entry_price, True, 3)
        order_id = "DEMO_001"
        self.active_positions[order_id] = order_structure
        
        print(f"Entry Price: ${entry_price}")
        print(f"Direction: {order_structure['direction']}")
        print(f"Total Contracts: {order_structure['total_contracts']}")
        print(f"Stop Loss: ${order_structure['stop_loss']}")
        print("\nTake Profit Levels:")
        
        for tp_name, tp_info in order_structure['tp_levels'].items():
            if tp_info['contracts'] > 0:
                print(f"  {tp_name}: ${tp_info['price']} ({tp_info['contracts']} contracts) - ${tp_info['profit_usd']} profit")
        
        # Simulate TP hits
        print("\n🎯 Simulating TP Hits:")
        self.simulate_tp_hit(order_id, 'TP1', 2650.1)  # First TP hit
        self.simulate_tp_hit(order_id, 'TP2', 2650.1)  # Second TP hit
        self.simulate_tp_hit(order_id, 'TP3', 2650.2)  # Third TP hit
        
        print(f"\n📈 Final Results:")
        print(f"  Total Profit: ${self.daily_pnl:.2f}")
        print(f"  Fibonacci Progression: Level {self.session_fib_index['morning']}")
        
        # Scenario 2: Compare with single TP approach
        print("\n📊 SCENARIO 2: Single TP vs Multi-TP Comparison")
        print("-" * 50)
        
        single_tp_profit = 10  # Single $10 target
        multi_tp_profit = 10 + 10 + 20  # $40 total from multi-TP
        
        print(f"Single TP Approach: ${single_tp_profit} (1 level)")
        print(f"Multi-TP Approach: ${multi_tp_profit} (3 levels)")
        print(f"Profit Improvement: {((multi_tp_profit - single_tp_profit) / single_tp_profit * 100):.1f}%")
        
        print("\n✅ ADVANTAGES OF MULTI-TP APPROACH:")
        print("  1. Captures more profit from strong moves")
        print("  2. Reduces risk after first TP hit (trailing stop)")
        print("  3. Maintains Fibonacci progression logic")
        print("  4. Allows for partial position management")
        print("  5. Better risk/reward optimization")

def main():
    print("[DEMO] Fibonacci Multi-TP Strategy Test")
    print("=" * 50)
    
    strategy = FibonacciMultiTPStrategy()
    strategy.demo_multi_tp_strategy()
    
    print("\n" + "=" * 50)
    print("[COMPLETE] Multi-TP Strategy Demonstration Complete!")
    print("\n💡 IMPLEMENTATION NOTES:")
    print("  - This solves both hardcoded targets AND multi-level TP")
    print("  - Fibonacci sequence drives dynamic profit targets")
    print("  - Partial position closing maximizes profit potential")
    print("  - Risk management through trailing stops")
    print("  - Compatible with existing Playwright automation")

if __name__ == "__main__":
    main()