#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for verifying remote UI functionality.
This script tests the connection to a remote AI Trading Sentinel instance.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import requests


def test_api_connection(base_url):
    """Test connection to the remote API."""
    print(f"\n🔍 Testing connection to {base_url}...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connection successful! API version: {data.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ Connection failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def test_strategy_endpoint(base_url):
    """Test the strategy endpoint."""
    print(f"\n🔍 Testing strategy endpoint...")
    try:
        response = requests.get(f"{base_url}/api/strategy", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategy endpoint working! Current strategy: {data.get('name', 'unknown')}")
            return True
        else:
            print(f"❌ Strategy endpoint failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Strategy endpoint error: {e}")
        return False


def test_logs_endpoint(base_url):
    """Test the logs endpoint."""
    print(f"\n🔍 Testing logs endpoint...")
    try:
        response = requests.get(
            f"{base_url}/api/logs?log_type=main&line_count=5", timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logs endpoint working! Retrieved {len(data.get('lines', []))} log lines")
            return True
        else:
            print(f"❌ Logs endpoint failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Logs endpoint error: {e}")
        return False


def run_all_tests(base_url):
    """Run all tests and return overall status."""
    print(f"\n🚀 Starting Remote UI Tests for {base_url}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    tests = [
        ("API Connection", test_api_connection(base_url)),
        ("Strategy Endpoint", test_strategy_endpoint(base_url)),
        ("Logs Endpoint", test_logs_endpoint(base_url)),
    ]
    
    print("\n" + "-" * 50)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        if not result:
            all_passed = False
        print(f"{status} - {name}")
    
    print("-" * 50)
    overall = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    print(f"\n{overall}")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Test Remote UI functionality")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:5000",
        help="Base URL of the remote API (default: http://localhost:5000)",
    )
    args = parser.parse_args()
    
    success = run_all_tests(args.url)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())