#!/usr/bin/env python3
"""
Debug Risk/Reward Ratio Calculation
"""

def calculate_risk_reward(entry_price, position_type, sl_pct, tp_pct):
    """Calculate risk/reward ratio for debugging"""
    print(f"\nTesting: {position_type} position at {entry_price}")
    print(f"Stop Loss: {sl_pct}%, Take Profit: {tp_pct}%")
    
    if position_type == "buy":
        expected_sl = entry_price * (1 - sl_pct / 100)
        expected_tp = entry_price * (1 + tp_pct / 100)
        print(f"Buy: SL = {expected_sl:.4f}, TP = {expected_tp:.4f}")
        
        risk = entry_price - expected_sl
        reward = expected_tp - entry_price
    else:  # sell
        expected_sl = entry_price * (1 + sl_pct / 100)
        expected_tp = entry_price * (1 - tp_pct / 100)
        print(f"Sell: SL = {expected_sl:.4f}, TP = {expected_tp:.4f}")
        
        risk = expected_sl - entry_price
        reward = entry_price - expected_tp
    
    print(f"Risk: {risk:.4f}, Reward: {reward:.4f}")
    
    risk_reward_ratio = reward / risk if risk > 0 else 0
    print(f"Risk/Reward Ratio: {risk_reward_ratio:.2f}")
    
    return risk_reward_ratio

# Test the same cases as in the verification script
test_cases = [
    {"entry": 1.1000, "type": "buy", "sl_pct": 1.0, "tp_pct": 2.0},
    {"entry": 1.1000, "type": "sell", "sl_pct": 1.0, "tp_pct": 2.0},
    {"entry": 110.50, "type": "buy", "sl_pct": 1.0, "tp_pct": 2.0},
]

print("=== Risk/Reward Ratio Debug ===")
print("Minimum required ratio: 2.0")

for i, case in enumerate(test_cases, 1):
    print(f"\n--- Test Case {i} ---")
    ratio = calculate_risk_reward(
        case["entry"], case["type"], case["sl_pct"], case["tp_pct"]
    )
    
    if ratio >= 2.0:
        print(f"✅ PASS: Ratio {ratio:.2f} >= 2.0")
    else:
        print(f"❌ FAIL: Ratio {ratio:.2f} < 2.0")

print("\n=== Analysis Complete ===")