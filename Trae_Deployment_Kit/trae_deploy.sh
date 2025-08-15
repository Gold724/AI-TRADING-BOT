#!/bin/bash

# Bash script for deploying Trae AI Trading Sentinel to a VPS

# Default values
VPS_IP="161.97.112.146"
VPS_USER="root"
SSH_PORT="22"
NOTIFY_SLACK=false
SLACK_WEBHOOK_URL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --vps-ip)
      VPS_IP="$2"
      shift 2
      ;;
    --vps-user)
      VPS_USER="$2"
      shift 2
      ;;
    --ssh-port)
      SSH_PORT="$2"
      shift 2
      ;;
    --ssh-key)
      SSH_KEY_PATH="$2"
      shift 2
      ;;
    --env)
      ENV_FILE_PATH="$2"
      shift 2
      ;;
    --notify-slack)
      NOTIFY_SLACK=true
      shift
      ;;
    --slack-webhook)
      SLACK_WEBHOOK_URL="$2"
      NOTIFY_SLACK=true
      shift 2
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Validate parameters (now with defaults)
if [ -z "$VPS_IP" ]; then
  echo "Using default VPS IP: 161.97.112.146"
  VPS_IP="161.97.112.146"
fi

if [ -z "$VPS_USER" ]; then
  echo "Using default VPS user: root"
  VPS_USER="root"
fi

if [ -z "$SSH_PORT" ]; then
  echo "Using default SSH port: 22"
  SSH_PORT="22"
fi

# Colors for console output
COLOR_SUCCESS="\033[0;32m"
COLOR_ERROR="\033[0;31m"
COLOR_INFO="\033[0;36m"
COLOR_WARNING="\033[0;33m"
COLOR_RESET="\033[0m"

# Function to display colored messages
function print_message() {
  local message="$1"
  local color="$2"
  
  echo -e "${color}${message}${COLOR_RESET}"
}

# Function to send Slack notifications
function send_slack_notification() {
  local message="$1"
  local status="$2"
  local webhook_url="$SLACK_WEBHOOK_URL"
  
  if [ "$NOTIFY_SLACK" != "true" ] || [ -z "$webhook_url" ]; then
    return
  fi
  
  # Determine color based on status
  local color
  case "$status" in
    "success")
      color="good"
      ;;
    "error")
      color="danger"
      ;;
    *)
      color="#0000FF" # Blue for info
      ;;
  esac
  
  local payload='{"attachments":[{"color":"'"$color"'","text":"'"$message"'","fields":[{"title":"Environment","value":"Production","short":true},{"title":"Time","value":"'"$(date +"%Y-%m-%d %H:%M:%S")"'","short":true}]}]}'
  
  curl -s -X POST -H "Content-type: application/json" -d "$payload" "$webhook_url" > /dev/null
}

# Validate SSH parameters
if [ -z "$SSH_KEY_PATH" ]; then
  print_message "No SSH key path provided. Will attempt to use password authentication or default key." "$COLOR_WARNING"
  SSH_KEY_PARAM=""
else
  if [ ! -f "$SSH_KEY_PATH" ]; then
    print_message "SSH key file not found at path: $SSH_KEY_PATH" "$COLOR_ERROR"
    exit 1
  fi
  SSH_KEY_PARAM="-i \"$SSH_KEY_PATH\""
fi

# Function to try a command and send notification on failure
function try_command() {
  local command="$1"
  local error_message="$2"
  
  eval "$command"
  local exit_code=$?
  
  if [ $exit_code -ne 0 ]; then
    print_message "$error_message" "$COLOR_ERROR"
    send_slack_notification "$error_message" "error"
    exit 1
  fi
}

# Start deployment
print_message "Starting deployment to VPS: $VPS_IP" "$COLOR_INFO"
send_slack_notification "Starting deployment to VPS: $VPS_IP" "info"

# Record start time
START_TIME=$(date +%s)

# Create remote directory structure
print_message "Creating remote directory structure..." "$COLOR_INFO"
try_command "ssh -p $SSH_PORT $SSH_KEY_PARAM $VPS_USER@$VPS_IP \"mkdir -p ~/ai-trading-sentinel\"" "Failed to create remote directory structure"

# Check if rsync is available
if command -v rsync > /dev/null; then
  RSYNC_AVAILABLE=true
else
  RSYNC_AVAILABLE=false
fi

# Transfer files
print_message "Transferring files to VPS..." "$COLOR_INFO"
if [ "$RSYNC_AVAILABLE" = true ]; then
  # Use rsync for file transfer (more efficient)
  try_command "rsync -avz --exclude '.git' --exclude '__pycache__' --exclude 'venv' --exclude 'node_modules' -e \"ssh -p $SSH_PORT $SSH_KEY_PARAM\" ./ $VPS_USER@$VPS_IP:~/ai-trading-sentinel" "Failed to transfer files"
else
  # Fallback to scp
  print_message "rsync not found, falling back to scp (slower)" "$COLOR_WARNING"
  try_command "scp -P $SSH_PORT $SSH_KEY_PARAM -r ./* $VPS_USER@$VPS_IP:~/ai-trading-sentinel" "Failed to transfer files"
fi

# Transfer environment file if specified
if [ -n "$ENV_FILE_PATH" ]; then
  print_message "Transferring environment file..." "$COLOR_INFO"
  try_command "scp -P $SSH_PORT $SSH_KEY_PARAM \"$ENV_FILE_PATH\" $VPS_USER@$VPS_IP:~/ai-trading-sentinel/.env" "Failed to transfer environment file"
fi

# Set up Python environment and install dependencies
print_message "Setting up Python environment and installing dependencies..." "$COLOR_INFO"
try_command "ssh -p $SSH_PORT $SSH_KEY_PARAM $VPS_USER@$VPS_IP \"cd ~/ai-trading-sentinel && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt\"" "Failed to set up Python environment"

# Set up frontend dependencies
print_message "Setting up frontend dependencies..." "$COLOR_INFO"
try_command "ssh -p $SSH_PORT $SSH_KEY_PARAM $VPS_USER@$VPS_IP \"cd ~/ai-trading-sentinel/frontend && npm install\"" "Failed to set up frontend dependencies"

# Create and move systemd service file
print_message "Setting up systemd service..." "$COLOR_INFO"
try_command "ssh -p $SSH_PORT $SSH_KEY_PARAM $VPS_USER@$VPS_IP \"sudo cp ~/ai-trading-sentinel/trae.service /etc/systemd/system/\"" "Failed to set up systemd service"

# Enable and start the service
print_message "Enabling and starting the service..." "$COLOR_INFO"
try_command "ssh -p $SSH_PORT $SSH_KEY_PARAM $VPS_USER@$VPS_IP \"sudo systemctl daemon-reload && sudo systemctl enable trae && sudo systemctl restart trae\"" "Failed to enable and start the service"

# Check service status
print_message "Checking service status..." "$COLOR_INFO"
SERVICE_STATUS=$(ssh -p $SSH_PORT $SSH_KEY_PARAM $VPS_USER@$VPS_IP "sudo systemctl status trae")
echo "$SERVICE_STATUS"

# Calculate deployment duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

# Deployment successful
SUCCESS_MESSAGE="Deployment to VPS $VPS_IP completed successfully in ${DURATION_MIN}m ${DURATION_SEC}s!"
print_message "$SUCCESS_MESSAGE" "$COLOR_SUCCESS"
send_slack_notification "$SUCCESS_MESSAGE" "success"