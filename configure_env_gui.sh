#!/bin/bash

# AI Trading Sentinel - GUI Environment Configuration Script
# This script helps configure the .env file using gedit in VNC environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$HOME/ai-trading-sentinel"
ENV_FILE="$PROJECT_DIR/.env"
TEMPLATE_FILE="$PROJECT_DIR/env_template_vnc.txt"

echo -e "${BLUE}🔧 AI Trading Sentinel - VNC Environment Configuration${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Function to show notification
show_notification() {
    local message="$1"
    local type="$2"
    
    if command -v notify-send &> /dev/null; then
        notify-send "Trading Bot Setup" "$message" --icon=dialog-information
    fi
    
    case $type in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        *)
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if we're in a GUI environment
check_gui_environment() {
    if [ -z "$DISPLAY" ]; then
        show_notification "No GUI environment detected. Setting DISPLAY=:1" "warning"
        export DISPLAY=:1
    fi
    
    if ! command -v gedit &> /dev/null; then
        show_notification "Installing gedit text editor..." "info"
        sudo apt update
        sudo apt install -y gedit
    fi
}

# Create project directory if it doesn't exist
setup_project_directory() {
    if [ ! -d "$PROJECT_DIR" ]; then
        show_notification "Creating project directory: $PROJECT_DIR" "info"
        mkdir -p "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        
        # Clone repository if it doesn't exist
        if [ ! -f "main.py" ]; then
            show_notification "Cloning AI Trading Sentinel repository..." "info"
            git clone https://github.com/your-username/ai-trading-sentinel.git .
        fi
    else
        cd "$PROJECT_DIR"
    fi
}

# Create .env file from template
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$TEMPLATE_FILE" ]; then
            show_notification "Creating .env file from template..." "info"
            cp "$TEMPLATE_FILE" "$ENV_FILE"
        else
            show_notification "Creating basic .env file..." "info"
            cat > "$ENV_FILE" << 'EOF'
# AI Trading Sentinel Configuration
# Configure these values for your setup

# Broker Configuration
BROKER_USERNAME=your_broker_username
BROKER_PASSWORD=your_broker_password
BROKER_URL=https://your-broker-platform.com

# Trading Parameters
TRADE_AMOUNT=100
MAX_DAILY_TRADES=10
RISK_PERCENTAGE=2

# VPS Configuration
VPS_MODE=true
HEADLESS_BROWSER=true
VNC_DISPLAY=:1

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/ubuntu/ai-trading-sentinel/logs/trae.log

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EMAIL_NOTIFICATIONS=true

# Security
API_SECRET_KEY=your-super-secret-api-key-here

# Environment
ENVIRONMENT=production
TEST_MODE=false
EOF
        fi
    fi
}

# Show configuration instructions
show_instructions() {
    local instruction_file="/tmp/env_instructions.txt"
    
    cat > "$instruction_file" << 'EOF'
🔧 AI Trading Sentinel - Environment Configuration Instructions

📋 REQUIRED CONFIGURATIONS:

1. BROKER CREDENTIALS (CRITICAL):
   - BROKER_USERNAME: Your trading platform username
   - BROKER_PASSWORD: Your trading platform password  
   - BROKER_URL: Your broker's trading platform URL

2. TRADING PARAMETERS:
   - TRADE_AMOUNT: Amount per trade (e.g., 100)
   - MAX_DAILY_TRADES: Maximum trades per day (e.g., 10)
   - RISK_PERCENTAGE: Risk per trade (e.g., 2)

3. NOTIFICATIONS:
   - SLACK_WEBHOOK_URL: For trade alerts
   - EMAIL settings for notifications

4. SECURITY:
   - API_SECRET_KEY: Generate a strong secret key
   - Change all default passwords

⚠️  SECURITY NOTES:
   - Never share your .env file
   - Use strong, unique passwords
   - Enable 2FA on your broker account
   - Test in demo mode first

✅ AFTER CONFIGURATION:
   - Save the file (Ctrl+S)
   - Close gedit
   - The script will validate your configuration

🔍 VALIDATION CHECKLIST:
   □ Broker credentials entered
   □ Trading parameters set
   □ Notification URLs configured
   □ Security keys generated
   □ File saved successfully
EOF

    # Show instructions in a separate gedit window
    gedit "$instruction_file" &
    sleep 2
}

# Open .env file in gedit
open_env_editor() {
    show_notification "Opening .env file in gedit editor..." "info"
    show_notification "Please configure your trading bot settings" "info"
    
    # Show instructions first
    show_instructions
    
    # Open .env file in gedit
    gedit "$ENV_FILE"
    
    show_notification "Environment file editor closed" "info"
}

# Validate .env configuration
validate_env_config() {
    show_notification "Validating .env configuration..." "info"
    
    local errors=0
    local warnings=0
    
    # Check required fields
    required_fields=(
        "BROKER_USERNAME"
        "BROKER_PASSWORD"
        "BROKER_URL"
        "TRADE_AMOUNT"
        "API_SECRET_KEY"
    )
    
    for field in "${required_fields[@]}"; do
        if ! grep -q "^$field=" "$ENV_FILE" || grep -q "^$field=your_" "$ENV_FILE" || grep -q "^$field=$" "$ENV_FILE"; then
            show_notification "Missing or default value for: $field" "error"
            ((errors++))
        fi
    done
    
    # Check for common issues
    if grep -q "your_broker_username" "$ENV_FILE"; then
        show_notification "Please replace 'your_broker_username' with actual username" "warning"
        ((warnings++))
    fi
    
    if grep -q "your-super-secret-api-key-here" "$ENV_FILE"; then
        show_notification "Please generate a strong API secret key" "warning"
        ((warnings++))
    fi
    
    # Show validation results
    if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
        show_notification "✅ Configuration validation passed!" "success"
        return 0
    elif [ $errors -eq 0 ]; then
        show_notification "⚠️  Configuration has $warnings warnings but is usable" "warning"
        return 0
    else
        show_notification "❌ Configuration has $errors errors - please fix before proceeding" "error"
        return 1
    fi
}

# Generate secure API key
generate_api_key() {
    if command -v openssl &> /dev/null; then
        local api_key=$(openssl rand -hex 32)
        show_notification "Generated secure API key: ${api_key:0:16}..." "success"
        
        # Ask if user wants to auto-update the .env file
        if command -v zenity &> /dev/null; then
            if zenity --question --text="Auto-update API_SECRET_KEY in .env file?"; then
                sed -i "s/API_SECRET_KEY=.*/API_SECRET_KEY=$api_key/" "$ENV_FILE"
                show_notification "API key updated in .env file" "success"
            fi
        else
            echo "To update manually, replace API_SECRET_KEY value with: $api_key"
        fi
    fi
}

# Create logs directory
setup_logs_directory() {
    local logs_dir="$PROJECT_DIR/logs"
    if [ ! -d "$logs_dir" ]; then
        show_notification "Creating logs directory..." "info"
        mkdir -p "$logs_dir"
        touch "$logs_dir/trae.log"
        chmod 664 "$logs_dir/trae.log"
    fi
}

# Main configuration flow
main() {
    echo -e "${BLUE}Starting GUI environment configuration...${NC}"
    
    # Setup steps
    check_gui_environment
    setup_project_directory
    create_env_file
    setup_logs_directory
    
    # Generate API key option
    if command -v zenity &> /dev/null; then
        if zenity --question --text="Generate a secure API key?"; then
            generate_api_key
        fi
    else
        read -p "Generate a secure API key? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            generate_api_key
        fi
    fi
    
    # Open editor
    open_env_editor
    
    # Validate configuration
    if validate_env_config; then
        show_notification "🎉 Environment configuration completed successfully!" "success"
        
        # Ask if user wants to proceed to service setup
        if command -v zenity &> /dev/null; then
            if zenity --question --text="Configuration complete! Start the trading bot service now?"; then
                echo -e "${GREEN}Proceeding to service startup...${NC}"
                # This will be handled by the next script
                exit 0
            fi
        else
            read -p "Configuration complete! Start the trading bot service now? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${GREEN}Proceeding to service startup...${NC}"
                exit 0
            fi
        fi
    else
        show_notification "Please fix configuration errors and run this script again" "error"
        
        # Ask if user wants to re-edit
        if command -v zenity &> /dev/null; then
            if zenity --question --text="Re-open .env file for editing?"; then
                open_env_editor
                validate_env_config
            fi
        fi
    fi
    
    echo -e "${BLUE}Environment configuration script completed.${NC}"
}

# Run main function
main "$@"