import os
import sys
import json
import time
import argparse
import requests

def load_signals(file_path):
    """
    Load sample signals from JSON file
    """
    try:
        with open(file_path, 'r') as f:
            signals = json.load(f)
        return signals
    except Exception as e:
        print(f"Error loading signals: {e}")
        return []

def call_fibonacci_api(signal, api_url="http://localhost:5000/api/trade/fibonacci"):
    """
    Call the Fibonacci strategy API endpoint
    """
    try:
        # Make API request
        print(f"\n🚀 Calling Fibonacci API at {api_url}")
        print(f"📊 Signal: {json.dumps(signal, indent=2)}")
        
        # Send POST request
        response = requests.post(api_url, json=signal)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API call successful: {result}")
            return True, result
        else:
            print(f"\n❌ API call failed with status code {response.status_code}: {response.text}")
            return False, response.text
    
    except Exception as e:
        print(f"\n❌ Error calling API: {e}")
        return False, str(e)

def run_fibonacci_api(signal_index=0, signals_file="sample_fibonacci_signals.json", api_url="http://localhost:5000/api/trade/fibonacci"):
    """
    Run the Fibonacci strategy via the API endpoint
    """
    # Load signals
    signals = load_signals(signals_file)
    
    if not signals:
        print("No signals found. Please check the signals file.")
        return False, None
    
    # Validate signal index
    if signal_index < 0 or signal_index >= len(signals):
        print(f"Invalid signal index. Please choose an index between 0 and {len(signals)-1}")
        return False, None
    
    # Get signal
    signal = signals[signal_index]
    
    # Call API
    start_time = time.time()
    success, result = call_fibonacci_api(signal, api_url)
    end_time = time.time()
    
    # Print result
    if success:
        print(f"\n✅ Fibonacci strategy API call completed in {end_time - start_time:.2f} seconds!")
    else:
        print(f"\n❌ Fibonacci strategy API call failed after {end_time - start_time:.2f} seconds!")
    
    return success, result

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Fibonacci Strategy via API")
    parser.add_argument("--index", type=int, default=0, help="Index of the signal to use from the signals file")
    parser.add_argument("--file", type=str, default="sample_fibonacci_signals.json", help="Path to the signals file")
    parser.add_argument("--url", type=str, default="http://localhost:5000/api/trade/fibonacci", help="API endpoint URL")
    parser.add_argument("--list", action="store_true", help="List all available signals")
    
    args = parser.parse_args()
    
    # List signals if requested
    if args.list:
        signals = load_signals(args.file)
        if signals:
            print(f"\nAvailable Signals ({len(signals)}):\n")
            for i, signal in enumerate(signals):
                print(f"[{i}] {signal.get('symbol')} {signal.get('side')} - {signal.get('description')}")
            print("\nRun with: python api_fibonacci_strategy.py --index <signal_index>")
        return
    
    # Run API call
    run_fibonacci_api(args.index, args.file, args.url)

if __name__ == "__main__":
    main()