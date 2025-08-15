#!/bin/bash
# auto_news_cron.sh - Daily cron job to fetch and save upcoming economic news

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set up logging
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/news_fetch_$(date +%Y%m%d).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log start time
echo "[$(date)] Starting news fetch job" >> "$LOG_FILE"

# Run the news fetcher
python fetch_news.py >> "$LOG_FILE" 2>&1
FETCH_STATUS=$?

# Update banned periods based on fetched news
python -c "from news_filter import update_banned_periods; update_banned_periods()" >> "$LOG_FILE" 2>&1
BANNED_STATUS=$?

# Log completion status
if [ $FETCH_STATUS -eq 0 ] && [ $BANNED_STATUS -eq 0 ]; then
    echo "[$(date)] News fetch job completed successfully" >> "$LOG_FILE"
    
    # Send Slack notification if SLACK_WEBHOOK_URL is configured
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        # Count high impact events
        HIGH_IMPACT_COUNT=$(python -c "import json; f=open('data/forex_news.json'); events=json.load(f); f.close(); print(len([e for e in events if e.get('impact')=='high']))")
        
        # Send notification
        curl -s -X POST -H "Content-type: application/json" \
            --data "{\"text\":\"📅 *ECONOMIC CALENDAR UPDATED* 📅\n• Calendar data refreshed successfully\n• Found $HIGH_IMPACT_COUNT high-impact events\n• Trading filters updated\"}" \
            "$SLACK_WEBHOOK_URL" > /dev/null
    fi
else
    echo "[$(date)] News fetch job failed" >> "$LOG_FILE"
    
    # Send failure notification if SLACK_WEBHOOK_URL is configured
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -s -X POST -H "Content-type: application/json" \
            --data "{\"text\":\"⚠️ *ECONOMIC CALENDAR UPDATE FAILED* ⚠️\nThe scheduled news data update failed. Please check the logs.\"}" \
            "$SLACK_WEBHOOK_URL" > /dev/null
    fi
fi

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi

exit 0