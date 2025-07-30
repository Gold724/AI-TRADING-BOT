#!/bin/bash

echo "🚀 AI Trading Sentinel - Vast.ai Deployment"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if the deployment script exists
if [ ! -f "deploy_to_vast.py" ]; then
    echo "❌ Error: deploy_to_vast.py not found."
    echo "Please ensure you are in the correct directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found."
    echo "Please create a .env file with the required environment variables."
    exit 1
fi

echo "📡 Running deployment script..."
echo

python3 deploy_to_vast.py

echo
echo "🔍 Deployment process completed."
echo