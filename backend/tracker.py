import json
import os
import datetime
from typing import Dict, List, Optional, Tuple, Union

# Constants for the compounding tracker
INITIAL_ACCOUNT_SIZE = 250000.0
MAX_PROFIT_TARGET = 15000.0
MAX_TRAILING_DRAWDOWN = 5500.0
MAX_CONTRACTS = 25
MAX_TRADES_PER_DAY = 5
DAILY_LOSS_LIMIT = 550.0  # 10% of buffer
ACCOUNT_ID = "BX64883-11"

# Trading modes
MODE_FAST = "fast"
MODE_SAFE = "safe"

# Fast Pass Mode (Evaluation) - Targets $15K in 5-10 days using aggressive trades (30-50% daily)
FAST_PASS_TARGETS = {
    1: 1000,   # Day 1: $1,000
    2: 1000,   # Day 2: $1,000
    3: 1500,   # Day 3: $1,500
    4: 2000,   # Day 4: $2,000
    5: 2500,   # Day 5: $2,500
    6: 3500,   # Day 6: $3,500
    7: 3500,   # Day 7: $3,500
}

# Safe Growth Mode (Post-Evaluation) - Targets $14.5K+ in 20 days using conservative compounding (5-15% daily)
SAFE_GROWTH_TARGETS = {
    1: 50,     # Day 1: $50 (10% of $500)
    2: 55,     # Day 2: $55 (10% of $550)
    3: 91,     # Day 3: $91 (15% of $605)
    4: 100,    # Day 4: $100
    5: 110,    # Day 5: $110
    6: 120,    # Day 6: $120
    7: 130,    # Day 7: $130
    8: 140,    # Day 8: $140
    9: 150,    # Day 9: $150
    10: 200,   # Day 10: $200
    11: 220,   # Day 11: $220
    12: 240,   # Day 12: $240
    13: 260,   # Day 13: $260
    14: 280,   # Day 14: $280
    15: 300,   # Day 15: $300
    16: 350,   # Day 16: $350
    17: 400,   # Day 17: $400
    18: 450,   # Day 18: $450
    19: 500,   # Day 19: $500
    20: 2500,  # Day 20: $2,500
}

# Default to the original compounding table for backward compatibility
DAILY_TARGETS = {
    1: 400,    # Day 1: $400
    2: 500,    # Day 2: $500
    3: 600,    # Day 3: $600
    4: 750,    # Day 4: $750
    5: 950,    # Day 5: $950
    6: 1100,   # Day 6: $1,100
    7: 1250,   # Day 7: $1,250
    8: 1400,   # Day 8: $1,400
    9: 1550,   # Day 9: $1,550
    10: 1700,  # Day 10: $1,700
    11: 1850,  # Day 11: $1,850
    12: 2000,  # Day 12: $2,000
    13: 2150,  # Day 13: $2,150
    14: 2300,  # Day 14: $2,300
    15: 2450,  # Day 15: $2,450
    16: 2600,  # Day 16: $2,600
    17: 2750,  # Day 17: $2,750
    18: 2900,  # Day 18: $2,900
    19: 3050,  # Day 19: $3,050
    20: 3100,  # Day 20: $3,100
}

class CompoundingTracker:
    def __init__(self, log_file_path: str = "logs/trade_log.json"):
        self.log_file_path = log_file_path
        self.ensure_log_file_exists()
        self.current_state = self.load_current_state()
    
    def ensure_log_file_exists(self) -> None:
        """Ensure the log file directory and file exist"""
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w') as f:
                json.dump({
                    "account_id": ACCOUNT_ID,
                    "initial_account_size": INITIAL_ACCOUNT_SIZE,
                    "max_profit_target": MAX_PROFIT_TARGET,
                    "max_trailing_drawdown": MAX_TRAILING_DRAWDOWN,
                    "daily_loss_limit": DAILY_LOSS_LIMIT,
                    "days": [],
                    "current_day": 1,
                    "total_pnl": 0.0,
                    "remaining_drawdown": MAX_TRAILING_DRAWDOWN,
                    "last_updated": datetime.datetime.now().isoformat()
                }, f, indent=2)
    
    def load_current_state(self) -> Dict:
        """Load the current state from the log file"""
        try:
            with open(self.log_file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or doesn't exist, create a new one
            self.ensure_log_file_exists()
            with open(self.log_file_path, 'r') as f:
                return json.load(f)
    
    def save_current_state(self) -> None:
        """Save the current state to the log file"""
        self.current_state["last_updated"] = datetime.datetime.now().isoformat()
        with open(self.log_file_path, 'w') as f:
            json.dump(self.current_state, f, indent=2)
    
    def calculate_daily_target(self, day: int, mode: str = MODE_SAFE) -> float:
        """Calculate the daily target for a given day based on the trading mode"""
        if mode == MODE_FAST:
            # Fast Pass Mode - aggressive targets
            return FAST_PASS_TARGETS.get(day, 3500)  # Default to the last day's target if out of range
        elif mode == MODE_SAFE:
            # Safe Growth Mode - conservative targets
            return SAFE_GROWTH_TARGETS.get(day, 2500)  # Default to the last day's target if out of range
        else:
            # Default to original targets for backward compatibility
            return DAILY_TARGETS.get(day, 3100)  # Default to the last day's target if out of range
    
    def calculate_contracts(self, day: int, remaining_drawdown: Optional[float] = None, mode: str = MODE_SAFE) -> int:
        """Calculate the suggested number of contracts based on day, remaining drawdown, and trading mode"""
        if remaining_drawdown is None:
            remaining_drawdown = self.current_state["remaining_drawdown"]
        
        # Base contract calculation on day number and remaining drawdown
        drawdown_factor = remaining_drawdown / MAX_TRAILING_DRAWDOWN
        
        if mode == MODE_FAST:
            # Fast Pass Mode - more aggressive contract sizing
            day_factor = min(day / 5, 1.0)  # Scales up faster, reaching max at day 5
            aggression_multiplier = 1.2  # 20% more aggressive
            
            # Calculate base contracts with aggression multiplier
            base_contracts = round(MAX_CONTRACTS * day_factor * drawdown_factor * aggression_multiplier)
        else:
            # Safe Growth Mode - more conservative contract sizing
            day_factor = min(day / 15, 1.0)  # Scales up slower, reaching max at day 15
            
            # Calculate base contracts
            base_contracts = round(MAX_CONTRACTS * day_factor * drawdown_factor * 0.8)  # 20% more conservative
        
        # Ensure we stay within limits
        return max(1, min(base_contracts, MAX_CONTRACTS))
    
    def log_trade(self, pnl: float, contracts_used: int, timestamp: Optional[str] = None) -> Dict:
        """Log a trade and update the current state"""
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        current_day = self.current_state["current_day"]
        day_data = self._get_or_create_day_data(current_day)
        
        # Update day's trades
        trade = {
            "pnl": pnl,
            "contracts": contracts_used,
            "timestamp": timestamp
        }
        day_data["trades"].append(trade)
        
        # Update day's PnL
        day_data["actual_pnl"] += pnl
        
        # Update overall state
        self.current_state["total_pnl"] += pnl
        self.current_state["remaining_drawdown"] = min(
            MAX_TRAILING_DRAWDOWN,
            MAX_TRAILING_DRAWDOWN - abs(min(0, self.current_state["total_pnl"]))
        )
        
        # Check if we've hit the daily target
        if day_data["actual_pnl"] >= day_data["daily_target"]:
            day_data["status"] = "target_hit"
        elif day_data["actual_pnl"] < 0 and abs(day_data["actual_pnl"]) >= DAILY_LOSS_LIMIT:
            day_data["status"] = "overdrawn"
        else:
            day_data["status"] = "in_progress"
        
        self.save_current_state()
        return day_data
    
    def _get_or_create_day_data(self, day: int) -> Dict:
        """Get or create data for a specific day"""
        # Find the day data if it exists
        for day_data in self.current_state["days"]:
            if day_data["day"] == day:
                return day_data
        
        # Create new day data if it doesn't exist
        daily_target = self.calculate_daily_target(day)
        suggested_contracts = self.calculate_contracts(day)
        
        new_day_data = {
            "day": day,
            "daily_target": daily_target,
            "actual_pnl": 0.0,
            "suggested_contracts": suggested_contracts,
            "trades": [],
            "status": "in_progress",
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        
        self.current_state["days"].append(new_day_data)
        self.save_current_state()
        return new_day_data
    
    def check_drawdown_limit(self) -> bool:
        """Check if we've hit the drawdown limit"""
        return self.current_state["remaining_drawdown"] <= 0
    
    def calculate_per_trade_targets(self, daily_target: float, num_trades: int = 3) -> float:
        """Calculate per-trade profit targets by dividing the daily target by the number of trades"""
        return round(daily_target / num_trades, 2)
    
    def generate_trade_plan(self, day: Optional[int] = None, num_trades: int = 4, mode: str = MODE_SAFE) -> Dict:
        """Generate a trade plan for the day with specified number of trades and trading mode"""
        if day is None:
            day = self.current_state["current_day"]
        
        day_data = self._get_or_create_day_data(day)
        
        # Use mode-specific daily target
        daily_target = self.calculate_daily_target(day, mode)
        
        # Use mode-specific contract calculation
        suggested_contracts = self.calculate_contracts(day, self.current_state["remaining_drawdown"], mode)
        
        remaining_drawdown = self.current_state["remaining_drawdown"]
        
        # Calculate per-trade target based on specified number of trades
        per_trade_target = self.calculate_per_trade_targets(daily_target, num_trades)
        
        # Adjust risk-reward ratio based on mode
        if mode == MODE_FAST:
            # Fast Pass Mode - more aggressive (1:1.5 risk-reward)
            risk_reward_ratio = 1.5
            max_daily_loss_factor = 0.15  # 15% of buffer for more aggressive approach
        else:
            # Safe Growth Mode - more conservative (1:2 risk-reward)
            risk_reward_ratio = 2.0
            max_daily_loss_factor = 0.1  # 10% of buffer for more conservative approach
        
        # Calculate recommended stop loss based on risk-reward ratio
        recommended_sl = round(per_trade_target / risk_reward_ratio, 2)
        
        # Calculate max daily loss based on mode
        max_daily_loss = min(DAILY_LOSS_LIMIT * max_daily_loss_factor, remaining_drawdown)
        
        return {
            "day": day,
            "daily_target": daily_target,
            "suggested_contracts": suggested_contracts,
            "trades_taken": len(day_data["trades"]),
            "trades_remaining": MAX_TRADES_PER_DAY - len(day_data["trades"]),
            "trades_planned": num_trades,
            "per_trade_target": per_trade_target,
            "recommended_sl": recommended_sl,
            "recommended_tp": per_trade_target,
            "stop_loss_per_contract": min(100, max(55, remaining_drawdown * 0.01 * (0.8 if mode == MODE_SAFE else 1.2))),
            "take_profit_per_contract": min(100, max(55, remaining_drawdown * 0.01 * (0.8 if mode == MODE_SAFE else 1.2))) * risk_reward_ratio,
            "max_daily_loss": max_daily_loss,
            "current_pnl": day_data["actual_pnl"],
            "remaining_drawdown": remaining_drawdown,
            "status": day_data["status"],
            "mode": mode,
            "max_days": 20 if mode == MODE_SAFE else 7
        }
    
    def reset_day(self, day: Optional[int] = None) -> Dict:
        """Reset a specific day's data"""
        if day is None:
            day = self.current_state["current_day"]
        
        # Find and remove the day's data
        day_index = None
        for i, day_data in enumerate(self.current_state["days"]):
            if day_data["day"] == day:
                day_index = i
                break
        
        if day_index is not None:
            # Calculate PnL to remove
            day_data = self.current_state["days"][day_index]
            pnl_to_remove = day_data["actual_pnl"]
            
            # Remove the day's data
            self.current_state["days"].pop(day_index)
            
            # Update total PnL
            self.current_state["total_pnl"] -= pnl_to_remove
            
            # Recalculate remaining drawdown
            self.current_state["remaining_drawdown"] = min(
                MAX_TRAILING_DRAWDOWN,
                MAX_TRAILING_DRAWDOWN - abs(min(0, self.current_state["total_pnl"]))
            )
            
            self.save_current_state()
        
        # Create a fresh day
        return self._get_or_create_day_data(day)
    
    def advance_day(self) -> Dict:
        """Advance to the next trading day"""
        current_day = self.current_state["current_day"]
        self.current_state["current_day"] = current_day + 1
        self.save_current_state()
        return self._get_or_create_day_data(current_day + 1)
    
    def get_day_status(self, day: Optional[int] = None) -> Dict:
        """Get the status for a specific day"""
        if day is None:
            day = self.current_state["current_day"]
        
        for day_data in self.current_state["days"]:
            if day_data["day"] == day:
                return day_data
        
        # If day doesn't exist yet, create it
        return self._get_or_create_day_data(day)
    
    def get_all_days(self) -> List[Dict]:
        """Get data for all days"""
        return sorted(self.current_state["days"], key=lambda x: x["day"])
    
    def get_summary(self) -> Dict:
        """Get a summary of the current progress"""
        days = self.get_all_days()
        completed_days = [d for d in days if d["status"] == "target_hit"]
        overdrawn_days = [d for d in days if d["status"] == "overdrawn"]
        
        return {
            "account_id": ACCOUNT_ID,
            "current_day": self.current_state["current_day"],
            "total_pnl": self.current_state["total_pnl"],
            "remaining_drawdown": self.current_state["remaining_drawdown"],
            "progress_percentage": min(100, (self.current_state["total_pnl"] / MAX_PROFIT_TARGET) * 100),
            "completed_days": len(completed_days),
            "overdrawn_days": len(overdrawn_days),
            "total_days": len(days),
            "last_updated": self.current_state["last_updated"]
        }

# Singleton instance
tracker = CompoundingTracker()

# Helper functions for API endpoints
def calculate_daily_target(day: int) -> float:
    return tracker.calculate_daily_target(day)

def calculate_contracts(day: int) -> int:
    return tracker.calculate_contracts(day)

def calculate_per_trade_targets(daily_target: float, num_trades: int = 3) -> float:
    return tracker.calculate_per_trade_targets(daily_target, num_trades)

def log_trade(pnl: float, contracts_used: int = 1) -> Dict:
    return tracker.log_trade(pnl, contracts_used)

def check_drawdown_limit() -> bool:
    return tracker.check_drawdown_limit()

def generate_trade_plan(day: Optional[int] = None, num_trades: int = 4, mode: str = MODE_SAFE) -> Dict:
    return tracker.generate_trade_plan(day, num_trades, mode)

def reset_day(day: Optional[int] = None) -> Dict:
    return tracker.reset_day(day)

def advance_day() -> Dict:
    return tracker.advance_day()

def get_day_status(day: Optional[int] = None) -> Dict:
    return tracker.get_day_status(day)

def get_all_days() -> List[Dict]:
    return tracker.get_all_days()

def get_summary() -> Dict:
    return tracker.get_summary()