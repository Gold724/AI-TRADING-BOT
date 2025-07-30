#!/bin/bash

echo "AI Trading Sentinel - Remote UI Test"
echo "====================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if requests module is installed
if ! python3 -c "import requests" &> /dev/null; then
    echo "Installing requests module..."
    pip3 install requests || {
        echo "Error: Failed to install requests module"
        exit 1
    }
fi

# Get the remote API URL
API_URL="http://localhost:5000"

if [ -f ".env" ]; then
    VAST_IP=$(grep VAST_INSTANCE_IP .env | cut -d '=' -f2)
    
    if [ ! -z "$VAST_IP" ]; then
        API_URL="http://$VAST_IP:5000"
    fi
fi

echo ""
echo "1. Test local API (http://localhost:5000)"
echo "2. Test remote API ($API_URL)"
echo "3. Test custom API URL"
echo ""

read -p "Enter your choice (1-3): " CHOICE

case $CHOICE in
    1)
        python3 test_remote_ui.py --url http://localhost:5000
        ;;
    2)
        python3 test_remote_ui.py --url "$API_URL"
        ;;
    3)
        read -p "Enter custom API URL: " CUSTOM_URL
        python3 test_remote_ui.py --url "$CUSTOM_URL"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Test completed."
echo ""