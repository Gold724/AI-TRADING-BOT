#!/bin/bash

echo "Bulenox cURL Command Capture Tool"
echo "===================================="

echo "Setting environment variables..."
export BX64883=your_username
export XujhMzFf6K=XujhMzFf6K

echo "Installing dependencies..."
npm install

echo ""
echo "Running Playwright script to capture cURL command..."
# Use full path to node if available in Windows environment
if command -v node >/dev/null 2>&1; then
    node bulenox_trade.js
else
    # Try to find node in common Windows locations
    if [ -f "/c/Program Files/nodejs/node.exe" ]; then
        "/c/Program Files/nodejs/node.exe" bulenox_trade.js
    elif [ -f "/c/Program Files (x86)/nodejs/node.exe" ]; then
        "/c/Program Files (x86)/nodejs/node.exe" bulenox_trade.js
    else
        echo "Error: Node.js not found. Please install Node.js or add it to your PATH."
        exit 1
    fi
fi

echo ""
if [ -f "trade.sh" ]; then
    echo "cURL command captured successfully!"
    echo "The command has been saved to trade.sh and trade_request.py"
    echo ""
    echo "You can run the command with: bash trade.sh"
    
    # Make the trade.sh file executable
    chmod +x trade.sh
    echo "Made trade.sh executable"
else
    echo "Failed to capture cURL command."
    echo "Please check the console output for errors."
fi