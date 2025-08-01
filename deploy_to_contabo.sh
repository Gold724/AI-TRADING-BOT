#!/bin/bash

echo "===================================="
echo "AI Trading Sentinel - Contabo VPS Deployment"
echo "===================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.7 or higher."
    echo
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import paramiko" &> /dev/null; then
    echo "Installing required packages..."
    if [ -f "deployment_requirements.txt" ]; then
        pip3 install -r deployment_requirements.txt
    else
        pip3 install paramiko cryptography pysftp tqdm
    fi
    if [ $? -ne 0 ]; then
        echo "Failed to install required packages. Please check your internet connection."
        echo
        echo "Press Enter to exit..."
        read
        exit 1
    fi
fi

echo
echo "Please enter your Contabo VPS details:"
echo "--------------------------------"

read -p "VPS IP Address: " VPS_IP
read -s -p "VPS Password: " VPS_PASSWORD
echo
read -p "SSH Port (default 22): " SSH_PORT

if [ -z "$SSH_PORT" ]; then
    SSH_PORT=22
fi

echo
echo "Select .env file to upload:"
echo "--------------------------------"
echo "1. Use .env.example (default)"
echo "2. Use existing .env file"
echo "3. Create new .env file"

read -p "Choice (1-3): " ENV_CHOICE

if [ "$ENV_CHOICE" = "1" ]; then
    ENV_FILE=".env.example"
elif [ "$ENV_CHOICE" = "2" ]; then
    if [ -f ".env" ]; then
        ENV_FILE=".env"
    else
        echo ".env file not found. Using .env.example instead."
        ENV_FILE=".env.example"
    fi
elif [ "$ENV_CHOICE" = "3" ]; then
    echo
    echo "Creating new .env file..."
    echo
    read -p "Bulenox Username: " BULENOX_USERNAME
    read -s -p "Bulenox Password: " BULENOX_PASSWORD
    echo
    read -p "Slack Webhook URL: " SLACK_WEBHOOK_URL
    read -p "Max Daily Trades (default 5): " MAX_DAILY_TRADES
    read -p "Trade Interval in Seconds (default 60): " TRADE_INTERVAL_SECONDS
    
    if [ -z "$MAX_DAILY_TRADES" ]; then
        MAX_DAILY_TRADES=5
    fi
    if [ -z "$TRADE_INTERVAL_SECONDS" ]; then
        TRADE_INTERVAL_SECONDS=60
    fi
    
    cat > .env.temp << EOF
BULENOX_USERNAME=$BULENOX_USERNAME
BULENOX_PASSWORD=$BULENOX_PASSWORD
SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL
MAX_DAILY_TRADES=$MAX_DAILY_TRADES
TRADE_INTERVAL_SECONDS=$TRADE_INTERVAL_SECONDS
SIGNAL_SOURCE=webhook
EOF
    
    ENV_FILE=".env.temp"
else
    echo "Invalid choice. Using .env.example."
    ENV_FILE=".env.example"
fi

echo
echo "Do you want to upload a Chrome profile? (y/n)"
read -p "Choice: " CHROME_PROFILE_CHOICE

if [ "${CHROME_PROFILE_CHOICE,,}" = "y" ]; then
    echo
    echo "Enter the path to your Chrome profile directory:"
    echo "(e.g. ~/.config/google-chrome/Default or ~/Library/Application\ Support/Google/Chrome/Default)"
    read -p "Path: " CHROME_PROFILE_PATH
    
    if [ ! -d "$CHROME_PROFILE_PATH" ]; then
        echo "Chrome profile directory not found. Continuing without it."
        CHROME_PROFILE_PARAM=""
    else
        CHROME_PROFILE_PARAM="--chrome-profile \"$CHROME_PROFILE_PATH\""
    fi
else
    CHROME_PROFILE_PARAM=""
fi

echo
echo "Starting deployment..."
echo "--------------------------------"

python3 deploy_to_contabo.py --ip "$VPS_IP" --password "$VPS_PASSWORD" --port "$SSH_PORT" --env-file "$ENV_FILE" $CHROME_PROFILE_PARAM

if [ $? -ne 0 ]; then
    echo
    echo "Deployment failed. Please check the error messages above."
else
    echo
    echo "Deployment completed successfully!"
    echo "Your AI Trading Sentinel is now running on your Contabo VPS."
    echo
    echo "To monitor the application:"
    echo "1. SSH into your VPS: ssh root@$VPS_IP"
    echo "2. Attach to the tmux session: tmux attach -t trading_sentinel"
    echo "3. To detach from the session: Press Ctrl+B, then D"
fi

if [ "$ENV_FILE" = ".env.temp" ]; then
    rm .env.temp
fi

echo
echo "Press Enter to exit..."
read