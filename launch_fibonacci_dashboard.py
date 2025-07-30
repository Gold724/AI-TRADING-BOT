#!/usr/bin/env python
"""
Fibonacci Strategy Dashboard Launcher

This script provides a simple way to launch the Fibonacci Strategy Dashboard
with default or custom settings.
"""

import os
import sys
import argparse
import subprocess

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Launch Fibonacci Strategy Dashboard")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5001, help="Server port")
    parser.add_argument("--history", type=str, default="logs/fibonacci_trades.json", help="Trade history file")
    parser.add_argument("--signals", type=str, default="sample_fibonacci_signals.json", help="Signals file")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Construct the command
    dashboard_script = os.path.join("backend", "fibonacci_strategy_dashboard.py")
    
    # Check if the dashboard script exists
    if not os.path.exists(dashboard_script):
        print(f"Error: Dashboard script not found at {dashboard_script}")
        sys.exit(1)
    
    # Build command arguments
    cmd = [
        sys.executable,
        dashboard_script,
        "--host", args.host,
        "--port", str(args.port),
        "--history", args.history,
        "--signals", args.signals
    ]
    
    # Add no-browser flag if specified
    if args.no_browser:
        cmd.append("--no-browser")
    
    # Print startup message
    print("\n🧠 AI Trading Sentinel - Fibonacci Strategy Dashboard")
    print(f"\nLaunching dashboard at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Launch the dashboard
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️ Dashboard stopped")
    except Exception as e:
        print(f"\nError launching dashboard: {e}")

if __name__ == "__main__":
    main()