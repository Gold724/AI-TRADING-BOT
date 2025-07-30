#!/bin/bash

echo "======================================"
echo "AI Trading Sentinel - Remote UI Deployment"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please create a .env file with the required variables"
    exit 1
fi

echo ""
echo "Choose deployment option:"
echo "1. Deploy both backend and frontend"
echo "2. Deploy backend API only"
echo "3. Deploy frontend UI only"
echo "4. Dry run (validate configuration only)"
echo ""

read -p "Enter option (1-4): " OPTION

case $OPTION in
    1)
        echo "Deploying both backend and frontend..."
        python3 deploy_remote_ui.py
        ;;
    2)
        echo "Deploying backend API only..."
        python3 deploy_remote_ui.py --backend-only
        ;;
    3)
        echo "Deploying frontend UI only..."
        python3 deploy_remote_ui.py --frontend-only
        ;;
    4)
        echo "Running in dry-run mode..."
        python3 deploy_remote_ui.py --dry-run
        ;;
    *)
        echo "Invalid option selected"
        exit 1
        ;;
esac

echo ""
echo "Deployment script completed"
echo ""