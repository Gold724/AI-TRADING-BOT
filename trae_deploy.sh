#!/bin/bash
# Trae AI Trading Sentinel Deployment Script for Linux/macOS
# This script automates the deployment process to a Contabo VPS

set -e

# Default values
VPS_IP="161.97.112.146"
VPS_USER="root"
SSH_PORT="22"
NOTIFY_SLACK=false
SLACK_WEBHOOK_URL=""
AUTO_MODE=false

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
    --auto)
      AUTO_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Parameters are now optional with defaults
if [ "$AUTO_MODE" = "true" ]; then
  echo "Running in AUTO mode"
  # Set up logging for auto mode
  LOG_DIR="/var/log/trae"
  mkdir -p "$LOG_DIR"
  LOG_FILE="$LOG_DIR/auto_deploy_$(date +%Y%m%d_%H%M%S).log"
  exec > >(tee -a "$LOG_FILE") 2>&1
  echo "[$(date)] Starting auto-deployment"
fi

echo "Using VPS IP: $VPS_IP"
echo "Using VPS User: $VPS_USER"
echo "Using SSH Port: $SSH_PORT"

# Record start time
DEPLOYMENT_START_TIME=$(date +%s)

# Function to send Slack notifications
send_slack_notification() {
  local message="$1"
  local status="${2:-info}" # info, success, error
  
  if [ "$NOTIFY_SLACK" != "true" ] || [ -z "$SLACK_WEBHOOK_URL" ]; then
    return
  fi
  
  case "$status" in
    success)
      color="good"
      ;;
    error)
      color="danger"
      ;;
    *)
      color="#0000FF" # info - blue
      ;;
  esac
  
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  local payload='{"attachments":[{"fallback":"'"$message"'","color":"'"$color"'","text":"'"$message"'","fields":[{"title":"Environment","value":"Production","short":true},{"title":"Timestamp","value":"'"$timestamp"'","short":true}]}]}'
  
  curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$SLACK_WEBHOOK_URL" > /dev/null
  echo "Slack notification sent: $message"
}

# Prepare SSH parameters
SSH_PARAMS="-p $SSH_PORT -o StrictHostKeyChecking=no"
if [ ! -z "$SSH_KEY_PATH" ]; then
  if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "SSH key file not found at: $SSH_KEY_PATH"
    send_slack_notification "⚠️ SSH key file not found at: $SSH_KEY_PATH" "error"
    exit 1
  fi
  SSH_PARAMS="-i \"$SSH_KEY_PATH\" $SSH_PARAMS"
fi

try_command() {
  "$@" || {
    local exit_code=$?
    echo "Command failed: $@"
    send_slack_notification "❌ Deployment failed: Command '$@' exited with code $exit_code" "error"
    exit $exit_code
  }
}

# Start deployment
echo "Starting deployment to $VPS_IP..."
send_slack_notification "🚀 Starting deployment of Trae AI Trading Sentinel to $VPS_IP"

# Create remote directory structure
echo "Creating remote directory structure..."
try_command ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "mkdir -p ~/ai-trading-sentinel/logs"

# Transfer files
echo "Transferring files to VPS..."
if command -v rsync > /dev/null; then
  # Using rsync for efficient file transfer
  EXCLUDE_PARAMS="--exclude '.git' --exclude '__pycache__' --exclude 'venv' --exclude 'node_modules'"
  try_command rsync -avz $EXCLUDE_PARAMS -e "ssh $SSH_PARAMS" . "$VPS_USER@$VPS_IP:~/ai-trading-sentinel/"
else
  # Fallback to scp
  echo "rsync not found. Using scp for file transfer."
  try_command scp $SSH_PARAMS -r ./* "$VPS_USER@$VPS_IP:~/ai-trading-sentinel/"
fi

# Transfer environment file if specified
if [ ! -z "$ENV_FILE_PATH" ]; then
  if [ -f "$ENV_FILE_PATH" ]; then
    echo "Transferring environment file..."
    try_command scp $SSH_PARAMS "$ENV_FILE_PATH" "$VPS_USER@$VPS_IP:~/ai-trading-sentinel/.env"
  else
    echo "Environment file not found at: $ENV_FILE_PATH"
    send_slack_notification "⚠️ Environment file not found at: $ENV_FILE_PATH" "error"
  fi
fi

# Setup virtual environment and install dependencies
echo "Setting up virtual environment and installing dependencies..."
try_command ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "cd ~/ai-trading-sentinel && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Setup frontend dependencies
echo "Setting up frontend dependencies..."
try_command ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "cd ~/ai-trading-sentinel/frontend && npm install"

# Create systemd service file
echo "Creating systemd service file..."
# Adjust home directory based on user
if [ "$VPS_USER" = "root" ]; then
  HOME_DIR="/root"
else
  HOME_DIR="/home/$VPS_USER"
fi

SERVICE_FILE_CONTENT="[Unit]\nDescription=Trae AI Trading Bot\nAfter=network.target\n\n[Service]\nUser=$VPS_USER\nWorkingDirectory=$HOME_DIR/ai-trading-sentinel\nExecStart=$HOME_DIR/ai-trading-sentinel/venv/bin/python main.py\nRestart=always\nRestartSec=10\nEnvironment=PYTHONUNBUFFERED=1\n\n[Install]\nWantedBy=multi-user.target"

echo "$SERVICE_FILE_CONTENT" | try_command ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "cat > ~/trae.service"
try_command ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "sudo mv ~/trae.service /etc/systemd/system/trae.service"

# Enable and start the service
echo "Enabling and starting the service..."
try_command ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "sudo systemctl daemon-reload && sudo systemctl enable trae && sudo systemctl restart trae"

# Check service status
echo "Checking service status..."
ssh $SSH_PARAMS "$VPS_USER@$VPS_IP" "sudo systemctl status trae"

# Deployment completed
DEPLOYMENT_END_TIME=$(date +%s)
DEPLOYMENT_DURATION=$((DEPLOYMENT_END_TIME - DEPLOYMENT_START_TIME))
DURATION_MINUTES=$((DEPLOYMENT_DURATION / 60))
DURATION_SECONDS=$((DEPLOYMENT_DURATION % 60))
DURATION_MESSAGE="Deployment completed in $DURATION_MINUTES minutes and $DURATION_SECONDS seconds"

echo "✅ Deployment completed successfully!"
echo "$DURATION_MESSAGE"
send_slack_notification "✅ Trae AI Trading Sentinel deployed successfully to $VPS_IP! $DURATION_MESSAGE" "success"