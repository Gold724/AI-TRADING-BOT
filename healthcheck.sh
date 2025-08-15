#!/bin/bash
# Trae AI Trading Bot Health Check Script
# This script checks if the trae service is running and sends Slack notifications if it fails

# Default values
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-""}
SERVICE_NAME="trae"
RESTART_ON_FAILURE=false
MAX_RETRIES=3
RETRY_DELAY=30  # seconds

# Colors for console output
NC='\033[0m'        # No Color
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --webhook-url)
      SLACK_WEBHOOK_URL="$2"
      shift 2
      ;;
    --service)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --restart)
      RESTART_ON_FAILURE=true
      shift
      ;;
    --max-retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --retry-delay)
      RETRY_DELAY="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --webhook-url URL   Slack webhook URL for notifications"
      echo "  --service NAME      Service name to check (default: trae)"
      echo "  --restart           Restart service on failure"
      echo "  --max-retries N     Maximum restart attempts (default: 3)"
      echo "  --retry-delay N     Seconds between restart attempts (default: 30)"
      echo "  --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Function to send Slack notification
send_slack_notification() {
    local message="$1"
    local status="$2"  # "success", "failure", "warning"
    
    if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
        echo -e "${YELLOW}Slack webhook URL not provided. Skipping notification.${NC}"
        return 1
    fi
    
    # Get hostname and timestamp
    local hostname=$(hostname)
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Set emoji based on status
    local emoji
    case "$status" in
        "success")
            emoji=":white_check_mark:"
            ;;
        "warning")
            emoji=":warning:"
            ;;
        "failure")
            emoji=":x:"
            ;;
        *)
            emoji=":information_source:"
            ;;
    esac
    
    # Format message
    local formatted_message="$emoji *Trae AI Trading Bot Health Check* $emoji\n"
    formatted_message+="*Status:* $status\n"
    formatted_message+="*Host:* $hostname\n"
    formatted_message+="*Time:* $timestamp\n"
    formatted_message+="*Message:* $message"
    
    # Prepare payload
    local payload="{\"text\":\"$formatted_message\"}"
    
    # Send to Slack
    curl -s -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" > /dev/null
    
    if [[ $? -eq 0 ]]; then
        echo -e "${CYAN}Slack notification sent.${NC}"
        return 0
    else
        echo -e "${RED}Error sending Slack notification.${NC}"
        return 1
    fi
}

# Function to check service status
check_service_status() {
    local service_name="$1"
    
    if ! systemctl list-unit-files | grep -q "$service_name.service"; then
        echo -e "${RED}Service '$service_name' not found. Please check if it's installed correctly.${NC}"
        return 1
    fi
    
    local status=$(systemctl is-active "$service_name")
    echo "$status"
    return 0
}

# Function to restart service
restart_service() {
    local service_name="$1"
    local max_retries="$2"
    local retry_delay="$3"
    
    for ((i=1; i<=max_retries; i++)); do
        echo -e "${CYAN}Attempting to restart service (Attempt $i of $max_retries)...${NC}"
        
        sudo systemctl restart "$service_name"
        sleep 5  # Wait for service to start
        
        local status=$(systemctl is-active "$service_name")
        if [[ "$status" == "active" ]]; then
            echo -e "${GREEN}Service restarted successfully.${NC}"
            return 0
        else
            echo -e "${YELLOW}Service failed to restart. Status: $status${NC}"
        fi
        
        if [[ $i -lt $max_retries ]]; then
            echo -e "${CYAN}Waiting $retry_delay seconds before next retry...${NC}"
            sleep "$retry_delay"
        fi
    done
    
    echo -e "${RED}Failed to restart service after $max_retries attempts.${NC}"
    return 1
}

# Main health check logic
echo -e "${CYAN}Starting Trae AI Trading Bot health check...${NC}"

# Check if service exists and get its status
STATUS=$(check_service_status "$SERVICE_NAME")

if [[ $? -ne 0 ]]; then
    ERROR_MESSAGE="Service '$SERVICE_NAME' not found. Please check if it's installed correctly."
    echo -e "${RED}$ERROR_MESSAGE${NC}"
    send_slack_notification "$ERROR_MESSAGE" "failure"
    exit 1
fi

# Check service status
if [[ "$STATUS" == "active" ]]; then
    SUCCESS_MESSAGE="Service '$SERVICE_NAME' is running normally."
    echo -e "${GREEN}$SUCCESS_MESSAGE${NC}"
    # Uncomment to send success notifications (may be noisy for scheduled tasks)
    # send_slack_notification "$SUCCESS_MESSAGE" "success"
    exit 0
else
    ERROR_MESSAGE="Service '$SERVICE_NAME' is not running. Current status: $STATUS"
    echo -e "${RED}$ERROR_MESSAGE${NC}"
    
    # Send notification
    send_slack_notification "$ERROR_MESSAGE" "failure"
    
    # Attempt to restart if enabled
    if [[ "$RESTART_ON_FAILURE" == true ]]; then
        echo -e "${CYAN}Attempting to restart service...${NC}"
        if restart_service "$SERVICE_NAME" "$MAX_RETRIES" "$RETRY_DELAY"; then
            RECOVERY_MESSAGE="Service '$SERVICE_NAME' was successfully restarted."
            echo -e "${GREEN}$RECOVERY_MESSAGE${NC}"
            send_slack_notification "$RECOVERY_MESSAGE" "success"
            exit 0
        else
            FATAL_MESSAGE="Failed to restart service '$SERVICE_NAME' after multiple attempts. Manual intervention required."
            echo -e "${RED}$FATAL_MESSAGE${NC}"
            send_slack_notification "$FATAL_MESSAGE" "failure"
            exit 2
        fi
    else
        echo -e "${CYAN}Automatic restart is disabled. Use --restart to enable.${NC}"
        exit 1
    fi
fi