#!/bin/bash
# Setup cron jobs for the TRAE Adaptive Intelligence System

# Get the absolute path to the project directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Display banner
echo "=== Setting up TRAE Adaptive Intelligence Cron Jobs ==="
echo "Project directory: $PROJECT_DIR"
echo ""

# Create temporary crontab file
TEMP_CRONTAB=$(mktemp)

# Export current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null

# Add daily evaluation job (runs at 00:15 every day)
if ! grep -q "activate_adaptive_intelligence.sh --mode evaluate" "$TEMP_CRONTAB"; then
    echo "Adding daily evaluation job..."
    echo "15 0 * * * cd $PROJECT_DIR && ./activate_adaptive_intelligence.sh --mode evaluate >> $PROJECT_DIR/logs/adaptive_intelligence_daily.log 2>&1" >> "$TEMP_CRONTAB"
fi

# Add weekly report job (runs at 01:00 every Sunday)
if ! grep -q "activate_adaptive_intelligence.sh --mode report" "$TEMP_CRONTAB"; then
    echo "Adding weekly report job..."
    echo "0 1 * * 0 cd $PROJECT_DIR && ./activate_adaptive_intelligence.sh --mode report >> $PROJECT_DIR/logs/adaptive_intelligence_weekly.log 2>&1" >> "$TEMP_CRONTAB"
fi

# Add monthly full run job (runs at 02:00 on the 1st of each month)
if ! grep -q "activate_adaptive_intelligence.sh --mode full" "$TEMP_CRONTAB"; then
    echo "Adding monthly full run job..."
    echo "0 2 1 * * cd $PROJECT_DIR && ./activate_adaptive_intelligence.sh --mode full >> $PROJECT_DIR/logs/adaptive_intelligence_monthly.log 2>&1" >> "$TEMP_CRONTAB"
fi

# Install new crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Make the activation script executable
chmod +x "$PROJECT_DIR/activate_adaptive_intelligence.sh"

# Verify crontab installation
echo "Verifying crontab installation..."
crontab -l | grep "activate_adaptive_intelligence"

echo ""
echo "Cron jobs for TRAE Adaptive Intelligence System have been set up successfully."
echo "Logs will be written to the logs directory."