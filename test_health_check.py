#!/usr/bin/env python3
# Trae AI Trading Bot Health Check Test Script
# This script tests the health check endpoint and returns an appropriate exit code

import argparse
import json
import sys
import time
from urllib.parse import urlparse

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description="Test the Trae API health check endpoint")
    parser.add_argument(
        "--url",
        default="http://localhost:5000/api/health",
        help="URL of the health check endpoint (default: http://localhost:5000/api/health)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts (default: 3)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Delay between retries in seconds (default: 5)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--slack-webhook",
        help="Slack webhook URL for notifications",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    return parser.parse_args()


def send_slack_notification(webhook_url, message, status="info"):
    if not webhook_url:
        return

    color = {
        "success": "good",
        "error": "danger",
        "info": "#0000FF",
    }.get(status, "#0000FF")

    payload = {
        "attachments": [
            {
                "fallback": message,
                "color": color,
                "text": message,
                "fields": [
                    {"title": "Environment", "value": "Production", "short": True},
                    {
                        "title": "Timestamp",
                        "value": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "short": True,
                    },
                ],
            }
        ]
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Slack notification: {e}")
        return False


def check_health(url, timeout=10, verbose=False):
    try:
        if verbose:
            print(f"Checking health at {url}...")

        response = requests.get(url, timeout=timeout)

        if verbose:
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")

        if response.status_code != 200:
            return False, f"Unexpected status code: {response.status_code}"

        try:
            data = response.json()
        except json.JSONDecodeError:
            return False, "Invalid JSON response"

        if data.get("status") != "ok":
            return False, f"Unexpected status: {data.get('status')}"

        return True, "Health check passed"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    args = parse_arguments()
    url = args.url
    retries = args.retries
    delay = args.delay
    timeout = args.timeout
    webhook_url = args.slack_webhook
    verbose = args.verbose

    # Parse URL to check if it's valid
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            print(f"Invalid URL: {url}")
            sys.exit(1)
    except Exception as e:
        print(f"Error parsing URL: {e}")
        sys.exit(1)

    # Try to connect to the health check endpoint with retries
    for attempt in range(retries):
        if verbose and attempt > 0:
            print(f"Retry attempt {attempt + 1}/{retries}")

        success, message = check_health(url, timeout, verbose)

        if success:
            print(f"Health check passed: {message}")
            if webhook_url:
                send_slack_notification(
                    webhook_url, "✅ Trae API health check passed", "success"
                )
            sys.exit(0)

        print(f"Health check failed: {message}")

        if attempt < retries - 1:
            if verbose:
                print(f"Waiting {delay} seconds before retrying...")
            time.sleep(delay)

    # All retries failed
    error_message = f"❌ Health check failed after {retries} attempts"
    print(error_message)

    if webhook_url:
        send_slack_notification(webhook_url, error_message, "error")

    sys.exit(1)


if __name__ == "__main__":
    main()