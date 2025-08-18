import os
from dotenv import load_dotenv
from bulenox_trade_request import execute_bulenox_trade

# Load environment variables (if you store your token in .env file)
load_dotenv()

def main():
    # Get token from environment variable or input
    token = os.getenv("BULENOX_TOKEN")
    
    if not token:
        print("\n[⚠️] No BULENOX_TOKEN found in environment variables.")
        token = input("Enter your Bulenox authorization token: ")
    
    # Get trade parameters with defaults
    symbol = input("Enter symbol (default: EURUSD): ") or "EURUSD"
    
    volume_input = input("Enter volume (default: 0.01): ") or "0.01"
    volume = float(volume_input)
    
    side = input("Enter side - buy/sell (default: buy): ").lower() or "buy"
    if side not in ["buy", "sell"]:
        print(f"Invalid side '{side}', defaulting to 'buy'")
        side = "buy"
    
    # Execute the trade
    print(f"\n[🚀] Executing {side} order for {volume} {symbol}...")
    
    try:
        result = execute_bulenox_trade(token, symbol, volume, side)
        
        # Check if the response contains an error
        if isinstance(result, dict) and result.get("error"):
            print(f"\n[❌] Trade failed: {result.get('error')}")
        else:
            print("\n[✅] Trade executed successfully!")
            print("Response:")
            print(result)
    except Exception as e:
        print(f"\n[❌] Error executing trade: {e}")

if __name__ == "__main__":
    print("=== Bulenox Trade Executor ===\n")
    main()