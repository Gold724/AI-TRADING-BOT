#!/usr/bin/env python3
# Trae API Connection Test Script
# This script tests the connection to the Trae API and verifies that it's functioning correctly

import argparse
import json
import sys
import time
from urllib.parse import urlparse

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description="Test the connection to the Trae API")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host of the Trae API (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port of the Trae API (default: 5000)",
    )
    parser.add_argument(
        "--protocol",
        default="http",
        choices=["http", "https"],
        help="Protocol to use (default: http)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    return parser.parse_args()


def test_health_endpoint(base_url, timeout=10, verbose=False):
    url = f"{base_url}/api/health"
    try:
        if verbose:
            print(f"Testing health endpoint at {url}...")

        response = requests.get(url, timeout=timeout)

        if verbose:
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")

        if response.status_code != 200:
            return False, f"Health endpoint returned status code {response.status_code}"

        try:
            data = response.json()
        except json.JSONDecodeError:
            return False, "Health endpoint returned invalid JSON"

        if data.get("status") != "ok":
            return False, f"Health endpoint returned unexpected status: {data.get('status')}"

        return True, "Health endpoint is functioning correctly"
    except requests.exceptions.RequestException as e:
        return False, f"Request to health endpoint failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error testing health endpoint: {str(e)}"


def test_strategies_endpoint(base_url, timeout=10, verbose=False):
    url = f"{base_url}/api/strategies"
    try:
        if verbose:
            print(f"Testing strategies endpoint at {url}...")

        response = requests.get(url, timeout=timeout)

        if verbose:
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")

        if response.status_code != 200:
            return False, f"Strategies endpoint returned status code {response.status_code}"

        try:
            data = response.json()
        except json.JSONDecodeError:
            return False, "Strategies endpoint returned invalid JSON"

        if not isinstance(data.get("strategies"), list):
            return False, "Strategies endpoint did not return a list of strategies"

        return True, "Strategies endpoint is functioning correctly"
    except requests.exceptions.RequestException as e:
        return False, f"Request to strategies endpoint failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error testing strategies endpoint: {str(e)}"


def main():
    args = parse_arguments()
    host = args.host
    port = args.port
    protocol = args.protocol
    timeout = args.timeout
    verbose = args.verbose

    base_url = f"{protocol}://{host}:{port}"

    if verbose:
        print(f"Testing connection to Trae API at {base_url}")

    # Test health endpoint
    health_success, health_message = test_health_endpoint(base_url, timeout, verbose)
    print(f"Health endpoint: {'✅ PASS' if health_success else '❌ FAIL'} - {health_message}")

    # Test strategies endpoint
    strategies_success, strategies_message = test_strategies_endpoint(base_url, timeout, verbose)
    print(f"Strategies endpoint: {'✅ PASS' if strategies_success else '❌ FAIL'} - {strategies_message}")

    # Overall result
    if health_success and strategies_success:
        print("\n✅ All tests passed - Trae API is functioning correctly")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - Trae API is not functioning correctly")
        sys.exit(1)


if __name__ == "__main__":
    main()