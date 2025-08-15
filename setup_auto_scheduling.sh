#!/bin/bash
# TRAE AUTO-SCHEDULING & CI/CD INTEGRATION SCRIPT

# Step 1: Define Script Locations
DEPLOY_SCRIPT="/opt/trae/trae_deploy.sh"
NEWS_SCRIPT="/opt/trae/auto_news_cron.sh"
SSH_KEY="/root/.ssh/trae_vps"
LOG_FILE="/var/log/trae_cron.log"
NEWS_LOG_FILE="/var/log/trae_news.log"

# Step 2: Install crontab jobs for daily auto-redeployment (3:00 AM UTC) and news fetching (00:00 AM UTC)
echo "Setting up cron auto-deployment..."
( crontab -l 2>/dev/null | grep -v "$DEPLOY_SCRIPT\|$NEWS_SCRIPT" ; echo "0 3 * * * /bin/bash $DEPLOY_SCRIPT --ssh-key $SSH_KEY >> $LOG_FILE 2>&1" ; echo "0 0 * * * /bin/bash $NEWS_SCRIPT >> $NEWS_LOG_FILE 2>&1" ) | crontab -

# Step 3: Ensure log files exist and have proper permissions
mkdir -p $(dirname "$LOG_FILE")
touch "$LOG_FILE"
touch "$NEWS_LOG_FILE"
chmod 644 "$LOG_FILE"
chmod 644 "$NEWS_LOG_FILE"

# Step 4: Copy news fetching script to destination
echo "Installing news fetching script..."
cp "$(dirname "$0")/auto_news_cron.sh" "$NEWS_SCRIPT"
chmod +x "$NEWS_SCRIPT"

# Step 5: Verify crontab installation
echo "Verifying cron job installation..."
DEPLOY_JOB_INSTALLED=$(crontab -l | grep -c "$DEPLOY_SCRIPT")
NEWS_JOB_INSTALLED=$(crontab -l | grep -c "$NEWS_SCRIPT")

if [ $DEPLOY_JOB_INSTALLED -gt 0 ] && [ $NEWS_JOB_INSTALLED -gt 0 ]; then
    echo "✅ All cron jobs have been successfully installed."
else
    echo "❌ Failed to install cron jobs. Please check your crontab configuration."
    exit 1
fi

echo "✅ Auto-scheduling setup complete."
echo "👉 The system will automatically redeploy daily at 3:00 AM UTC."
echo "👉 Economic news data will be fetched daily at 00:00 AM UTC."
echo "👉 Deployment logs will be written to $LOG_FILE"
echo "👉 News fetching logs will be written to $NEWS_LOG_FILE"

# Step 6: Run initial news fetch
echo "Performing initial news data fetch..."
"$NEWS_SCRIPT"