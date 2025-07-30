import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime

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

def save_test_results(results, file_path="logs/fibonacci_test_results.json"):
    """
    Save test results to a JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving test results: {e}")
        return False

def run_test(test_type, signal_index, signals_file, **kwargs):
    """
    Run a single test with the specified parameters
    """
    # Build command based on test type
    if test_type == "simulation":
        cmd = [
            "python", "simulate_fibonacci_strategy.py",
            "--index", str(signal_index),
            "--file", signals_file,
            "--time", str(kwargs.get("time", 60)),
            "--interval", str(kwargs.get("interval", 1)),
            "--output", f"logs/simulated_fibonacci_trades_{signal_index}.json"
        ]
    elif test_type == "api":
        cmd = [
            "python", "api_fibonacci_strategy.py",
            "--index", str(signal_index),
            "--file", signals_file,
            "--url", kwargs.get("url", "http://localhost:5000/api/trade/fibonacci")
        ]
    elif test_type == "executor":
        cmd = [
            "python", "test_fibonacci_executor.py",
            "--symbol", kwargs.get("symbol", "EURUSD"),
            "--side", kwargs.get("side", "buy"),
            "--quantity", str(kwargs.get("quantity", 0.1)),
            "--entry", str(kwargs.get("entry", 1.0850)),
            "--fib_low", str(kwargs.get("fib_low", 1.0800)),
            "--fib_high", str(kwargs.get("fib_high", 1.0900)),
            "--stealth_level", str(kwargs.get("stealth_level", 2))
        ]
        
        # Add optional parameters if provided
        if "stop_loss" in kwargs:
            cmd.extend(["--stop_loss", str(kwargs["stop_loss"])])
        if "take_profit" in kwargs:
            cmd.extend(["--take_profit", str(kwargs["take_profit"])])
    else:
        print(f"Unknown test type: {test_type}")
        return False, None
    
    # Run command
    try:
        print(f"\n🚀 Running {test_type} test for signal {signal_index}")
        print(f"📊 Command: {' '.join(cmd)}")
        
        # Start time
        start_time = time.time()
        
        # Run process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        # End time
        end_time = time.time()
        
        # Check result
        if process.returncode == 0:
            print(f"\n✅ Test completed successfully in {end_time - start_time:.2f} seconds!")
            success = True
        else:
            print(f"\n❌ Test failed with return code {process.returncode} after {end_time - start_time:.2f} seconds!")
            success = False
        
        # Return result
        result = {
            "success": success,
            "return_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration": end_time - start_time
        }
        return success, result
    
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        return False, {"error": str(e)}

def run_batch_tests(test_type, signals_file="sample_fibonacci_signals.json", indices=None, **kwargs):
    """
    Run a batch of tests with the specified parameters
    """
    # Load signals
    signals = load_signals(signals_file)
    
    if not signals:
        print("No signals found. Please check the signals file.")
        return False
    
    # Determine indices to test
    if indices is None:
        indices = list(range(len(signals)))
    else:
        # Validate indices
        indices = [i for i in indices if 0 <= i < len(signals)]
        if not indices:
            print(f"No valid indices provided. Please choose indices between 0 and {len(signals)-1}")
            return False
    
    # Initialize results
    results = {
        "test_type": test_type,
        "signals_file": signals_file,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tests": []
    }
    
    # Run tests
    success_count = 0
    for i, signal_index in enumerate(indices):
        print(f"\n📌 Running test {i+1} of {len(indices)} (Signal {signal_index})")
        
        # Get signal
        signal = signals[signal_index]
        
        # Run test
        success, result = run_test(test_type, signal_index, signals_file, **kwargs)
        
        # Update success count
        if success:
            success_count += 1
        
        # Add result to results
        test_result = {
            "signal_index": signal_index,
            "signal": signal,
            "success": success,
            "result": result
        }
        results["tests"].append(test_result)
    
    # Save results
    results_file = f"logs/fibonacci_{test_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if save_test_results(results, results_file):
        print(f"\n📁 Test results saved to: {results_file}")
    
    # Print summary
    print(f"\n📊 Batch Test Summary:")
    print(f"  - Test Type: {test_type}")
    print(f"  - Signals File: {signals_file}")
    print(f"  - Total Tests: {len(indices)}")
    print(f"  - Successful Tests: {success_count}")
    print(f"  - Failed Tests: {len(indices) - success_count}")
    print(f"  - Success Rate: {success_count / len(indices) * 100:.2f}%")
    
    return success_count == len(indices)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Batch Fibonacci Strategy Tests")
    parser.add_argument("--type", type=str, default="simulation", choices=["simulation", "api", "executor"], help="Test type")
    parser.add_argument("--file", type=str, default="sample_fibonacci_signals.json", help="Path to the signals file")
    parser.add_argument("--indices", type=str, help="Comma-separated list of signal indices to test")
    parser.add_argument("--time", type=int, default=60, help="Simulation time in seconds (for simulation tests)")
    parser.add_argument("--interval", type=int, default=1, help="Simulation interval in seconds (for simulation tests)")
    parser.add_argument("--url", type=str, default="http://localhost:5000/api/trade/fibonacci", help="API endpoint URL (for API tests)")
    parser.add_argument("--stealth_level", type=int, default=2, choices=[1, 2, 3], help="Stealth level (for executor tests)")
    parser.add_argument("--list", action="store_true", help="List all available signals")
    
    args = parser.parse_args()
    
    # List signals if requested
    if args.list:
        signals = load_signals(args.file)
        if signals:
            print(f"\nAvailable Signals ({len(signals)}):\n")
            for i, signal in enumerate(signals):
                print(f"[{i}] {signal.get('symbol')} {signal.get('side')} - {signal.get('description')}")
            print("\nRun with: python batch_fibonacci_tests.py --indices <comma_separated_indices>")
        return
    
    # Parse indices
    indices = None
    if args.indices:
        try:
            indices = [int(i.strip()) for i in args.indices.split(",")]
        except:
            print(f"Invalid indices format. Please use comma-separated integers.")
            return
    
    # Run batch tests
    kwargs = {
        "time": args.time,
        "interval": args.interval,
        "url": args.url,
        "stealth_level": args.stealth_level
    }
    run_batch_tests(args.type, args.file, indices, **kwargs)

if __name__ == "__main__":
    main()