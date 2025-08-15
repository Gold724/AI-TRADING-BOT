#!/bin/bash
# Deployment script for TRAE AI Trading Bot with Adaptive Intelligence

set -e  # Exit on error

# Display banner
echo "=== TRAE AI Trading Bot Deployment Script ==="
echo "This script will set up the TRAE AI Trading Bot with Adaptive Intelligence"
echo ""

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Get the absolute path to the project directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
echo "Project directory: $PROJECT_DIR"

# Step 1: Copy the service file
echo "\nStep 1: Copying trae-bot.service to /etc/systemd/system/"
cp "$PROJECT_DIR/trae-bot.service" /etc/systemd/system/
echo "Service file copied successfully"

# Step 2: Reload systemd
echo "\nStep 2: Reloading systemd daemon"
systemctl daemon-reload
echo "Systemd daemon reloaded successfully"

# Step 3: Enable the service
echo "\nStep 3: Enabling trae-bot service"
systemctl enable trae-bot
echo "Service enabled successfully"

# Step 4: Start the service
echo "\nStep 4: Starting trae-bot service"
systemctl start trae-bot
echo "Service started successfully"

# Check service status
echo "\nChecking service status:"
systemctl status trae-bot --no-pager

# Step 5: Set up cron jobs
echo "\nStep 5: Setting up Adaptive Intelligence cron jobs"
chmod +x "$PROJECT_DIR/setup_adaptive_intelligence_cron.sh"
chmod +x "$PROJECT_DIR/activate_adaptive_intelligence.sh"
"$PROJECT_DIR/setup_adaptive_intelligence_cron.sh"
echo "Cron jobs set up successfully"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Final verification
echo "\nVerifying deployment:"
echo "1. Service status:"
systemctl is-active trae-bot
echo "2. Cron jobs:"
crontab -l | grep "activate_adaptive_intelligence"
echo "3. Log file:"
if [ -f "/root/AI-TRADING-BOT/trae_output.log" ]; then
    echo "Log file exists"
    tail -n 5 "/root/AI-TRADING-BOT/trae_output.log"
else
    echo "Log file not found yet, it will be created when the service runs"
fi

echo "\n=== Deployment Complete ==="
echo "The TRAE AI Trading Bot with Adaptive Intelligence has been deployed successfully"
echo "You can monitor the bot using:"
echo "  - systemctl status trae-bot"
echo "  - tail -f /root/AI-TRADING-BOT/trae_output.log"
echo "  - Check the logs directory for Adaptive Intelligence logs"