import json
import datetime
from backend.strategies.lunar_trader import LunarTraderStrategy
from backend.utils.lunar_phase import get_lunar_phase

def test_lunar_trader():
    print("\n🌙 Testing LUNAR TRADER Module")
    print("================================\n")
    
    # Get current lunar phase
    lunar_phase = get_lunar_phase()
    print(f"Current Lunar Phase: {lunar_phase}\n")
    
    # Initialize strategy
    strategy = LunarTraderStrategy()
    
    # Test with sample market data
    market_data = {
        "symbol": "GOLD_FUTURES",
        "current": 2342.50,
        "high": 2350.00,
        "low": 2335.00,
        "session": "NY"
    }
    
    # Generate signal
    signal = strategy.generate_signal(market_data, account_balance=10000)
    
    if signal:
        print("Generated Signal:")
        print(json.dumps(signal, indent=2))
        print("\nLunar Phase Bias:")
        phase_bias = strategy.calculate_phase_bias(lunar_phase)
        print(f"Buy Bias: {phase_bias['buy']:.2f}")
        print(f"Sell Bias: {phase_bias['sell']:.2f}")
    else:
        print("No signal generated")

if __name__ == "__main__":
    test_lunar_trader()