# examples/multi_agent_example.py

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SentinelDecider
from sentinel_decider import SentinelDecider

def main():
    # Initialize the SentinelDecider with Phase 5
    print("Initializing SentinelDecider with Phase 5...")
    decider = SentinelDecider(phase=5)
    
    # Check if multi-agent mode is enabled
    if not decider.multi_agent_mode:
        print("Error: Multi-agent mode is not enabled. Make sure phase-5.md is properly configured.")
        return
    
    print(f"Multi-agent mode enabled with {len(decider.voting_system.agents)} agents")
    print(f"Voting method: {decider.voting_system.voting_method}")
    print(f"Governance mode: {decider.voting_system.governance_mode}")
    print("\nRegistered agents:")
    for agent_name, agent in decider.voting_system.agents.items():
        print(f"- {agent_name}: {agent.__class__.__name__} (weight: {agent.weight})")
    
    # Create a sample signal
    print("\nCreating sample trade signal...")
    signal = {
        "market_data": {
            "price": 1.1234,
            "open": 1.1220,
            "high": 1.1250,
            "low": 1.1200,
            "close": 1.1234,
            "volume": 10000,
            "ema50": 1.1210,
            "ema200": 1.1180,
            "rsi": 65,
            "macd": 0.0025,
            "macd_signal": 0.0010,
            "atr": 0.0050,
            "atr_change": 0.10,
            "adx": 28
        },
        "strategy": "trend_following",
        "type": "entry",
        "indicators": {
            "trend_direction": "up",
            "momentum": "increasing",
            "volatility": "moderate"
        },
        "news": {
            "impact": "low",
            "title": "Minor economic data release",
            "timestamp": datetime.now().isoformat()
        },
        "account_info": {
            "balance": 10000,
            "equity": 10200,
            "margin": 1000,
            "free_margin": 9200,
            "margin_level": 1020,
            "open_positions": 2
        }
    }
    
    # Get decision from multi-agent system
    print("\nGetting decision from multi-agent system...")
    decision = decider.decide_trade(signal)
    
    # Print decision details
    print("\nDecision:")
    print(f"Action: {decision['action']}")
    print(f"Confidence: {decision['confidence']}%")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Voting method: {decision.get('voting_method', 'N/A')}")
    
    # Print individual votes if available
    if 'votes' in decision:
        print("\nIndividual agent votes:")
        for vote in decision['votes']:
            print(f"- {vote['agent']}: {vote['vote']} with {vote['confidence']}% confidence")
            if 'reason' in vote:
                print(f"  Reason: {vote['reason']}")
    
    # Save decision to log file
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'multi_agent_example.json')
    with open(log_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "signal": signal,
            "decision": decision
        }, f, indent=2)
    
    print(f"\nDecision saved to {log_file}")

if __name__ == "__main__":
    main()