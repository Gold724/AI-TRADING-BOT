#!/bin/bash

# TRAE AI Trading Sentinel - Contabo VPS Deployment Script
# This script deploys the TRAE AI Trading Sentinel to a Contabo VPS
# It sets up the environment, installs dependencies, configures security,
# and ensures startup persistence

set -e

# Configuration
APP_DIR="/opt/trae-ai-sentinel"
GIT_REPO="https://github.com/yourusername/ai-trading-sentinel.git"
BRANCH="main"
USER="trae"
GROUP="trae"
PORT=5000
SSL_PORT=5443

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║             TRAE AI TRADING SENTINEL DEPLOYMENT            ║"
echo "║                                                            ║"
echo "║                  CONTABO VPS DEPLOYMENT                    ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    exit 1
fi

# Function to print section header
print_section() {
    echo -e "\n${YELLOW}==== $1 ====${NC}\n"
}

# Function to print status
print_status() {
    echo -e "${GREEN}[✓] $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}[i] $1${NC}"
}

# Update system
print_section "Updating System"
echo "Updating package lists..."
apt-get update
echo "Upgrading packages..."
apt-get upgrade -y
print_status "System updated"

# Install dependencies
print_section "Installing Dependencies"
echo "Installing system dependencies..."
apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    unzip \
    wget \
    curl \
    supervisor \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    chromium-browser \
    chromium-chromedriver
print_status "System dependencies installed"

# Create user if it doesn't exist
print_section "Setting up User"
if id "$USER" &>/dev/null; then
    print_info "User $USER already exists"
else
    echo "Creating user $USER..."
    useradd -m -s /bin/bash "$USER"
    print_status "User $USER created"
fi

# Create app directory
print_section "Setting up Application Directory"
if [ -d "$APP_DIR" ]; then
    print_info "Directory $APP_DIR already exists"
else
    echo "Creating directory $APP_DIR..."
    mkdir -p "$APP_DIR"
    print_status "Directory $APP_DIR created"
fi

# Set ownership
echo "Setting ownership of $APP_DIR to $USER:$GROUP..."
chown -R "$USER:$GROUP" "$APP_DIR"
print_status "Ownership set"

# Clone or update repository
print_section "Setting up Repository"
if [ -d "$APP_DIR/.git" ]; then
    print_info "Repository already exists, updating..."
    cd "$APP_DIR"
    sudo -u "$USER" git fetch
    sudo -u "$USER" git checkout "$BRANCH"
    sudo -u "$USER" git pull
    print_status "Repository updated"
else
    echo "Cloning repository..."
    sudo -u "$USER" git clone -b "$BRANCH" "$GIT_REPO" "$APP_DIR"
    print_status "Repository cloned"
fi

# Set up Python virtual environment
print_section "Setting up Python Virtual Environment"
if [ -d "$APP_DIR/venv" ]; then
    print_info "Virtual environment already exists"
else
    echo "Creating virtual environment..."
    cd "$APP_DIR"
    sudo -u "$USER" python3 -m venv venv
    print_status "Virtual environment created"
fi

# Install Python dependencies
print_section "Installing Python Dependencies"
echo "Installing Python dependencies..."
cd "$APP_DIR"
sudo -u "$USER" bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pip install undetected-chromedriver selenium gunicorn"
print_status "Python dependencies installed"

# Create necessary directories
print_section "Creating Necessary Directories"
echo "Creating log directories..."
sudo -u "$USER" mkdir -p "$APP_DIR/logs/bulenox"
sudo -u "$USER" mkdir -p "$APP_DIR/logs/trae_ai"
sudo -u "$USER" mkdir -p "$APP_DIR/logs/dreamer"
sudo -u "$USER" mkdir -p "$APP_DIR/logs/control_panel"
print_status "Log directories created"

# Create configuration directory if it doesn't exist
echo "Creating configuration directory..."
sudo -u "$USER" mkdir -p "$APP_DIR/config"
print_status "Configuration directory created"

# Generate API key if it doesn't exist
print_section "Setting up API Key"
API_KEY_FILE="$APP_DIR/config/api_key.txt"
if [ -f "$API_KEY_FILE" ]; then
    print_info "API key already exists"
else
    echo "Generating API key..."
    API_KEY=$(openssl rand -hex 32)
    sudo -u "$USER" bash -c "echo $API_KEY > $API_KEY_FILE"
    print_status "API key generated"
fi

# Create Bulenox controller config if it doesn't exist
print_section "Setting up Bulenox Controller Config"
BULENOX_CONFIG_FILE="$APP_DIR/config/bulenox_controller_config.json"
if [ -f "$BULENOX_CONFIG_FILE" ]; then
    print_info "Bulenox controller config already exists"
else
    echo "Creating Bulenox controller config..."
    API_KEY=$(cat "$API_KEY_FILE")
    sudo -u "$USER" bash -c "cat > $BULENOX_CONFIG_FILE << EOL
{
    \"dreamer_mode\": {
        \"enabled\": false,
        \"simulation_id\": \"sim_$(date +%s)\"
    },
    \"session\": {
        \"auto_login\": true,
        \"headless\": true,
        \"debug\": true,
        \"session_timeout\": 3600
    },
    \"trading\": {
        \"default_quantity\": 1,
        \"default_tp_pips\": 50,
        \"default_sl_pips\": 30,
        \"max_trades_per_day\": 10,
        \"allowed_symbols\": [\"EURUSD\", \"GBPUSD\", \"USDJPY\", \"XAUUSD\", \"ES\"]
    },
    \"security\": {
        \"api_key_required\": true,
        \"api_key\": \"$API_KEY\"
    }
}
EOL"
    print_status "Bulenox controller config created"
fi

# Set up environment variables
print_section "Setting up Environment Variables"
ENV_FILE="$APP_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    print_info "Environment file already exists"
else
    echo "Creating environment file..."
    API_KEY=$(cat "$API_KEY_FILE")
    sudo -u "$USER" bash -c "cat > $ENV_FILE << EOL
# TRAE AI Trading Sentinel Environment Variables
TRAE_API_KEY=$API_KEY
TRAE_ENV=production
TRAE_DEBUG=false
TRAE_LOG_LEVEL=INFO
TRAE_PORT=$PORT
TRAE_SSL_PORT=$SSL_PORT

# Bulenox Credentials
# Replace with actual credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
BULENOX_PROFILE_PATH=/home/$USER/.config/chromium
EOL"
    print_status "Environment file created"
fi

# Set up Supervisor configuration
print_section "Setting up Supervisor"
SUPERVISOR_CONF="/etc/supervisor/conf.d/trae-ai-sentinel.conf"
echo "Creating Supervisor configuration..."
cat > "$SUPERVISOR_CONF" << EOL
[program:trae-api]
command=/opt/trae-ai-sentinel/venv/bin/gunicorn -w 4 -b 0.0.0.0:$PORT app:app
directory=/opt/trae-ai-sentinel
user=$USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stdout_logfile=/opt/trae-ai-sentinel/logs/control_panel/gunicorn.log
stderr_logfile=/opt/trae-ai-sentinel/logs/control_panel/gunicorn.error.log
environment=PATH="/opt/trae-ai-sentinel/venv/bin"

[program:trae-ai-agent]
command=/opt/trae-ai-sentinel/venv/bin/python trae_ai.py
directory=/opt/trae-ai-sentinel
user=$USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stdout_logfile=/opt/trae-ai-sentinel/logs/trae_ai/agent.log
stderr_logfile=/opt/trae-ai-sentinel/logs/trae_ai/agent.error.log
environment=PATH="/opt/trae-ai-sentinel/venv/bin"

[group:trae]
programs=trae-api,trae-ai-agent
priority=999
EOL
print_status "Supervisor configuration created"

# Set up Nginx configuration
print_section "Setting up Nginx"
NGINX_CONF="/etc/nginx/sites-available/trae-ai-sentinel"
echo "Creating Nginx configuration..."
cat > "$NGINX_CONF" << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
print_status "Nginx configuration created"

# Enable Nginx site
echo "Enabling Nginx site..."
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
print_status "Nginx site enabled"

# Set up SSL with Certbot (optional)
print_section "Setting up SSL (Optional)"
echo -e "${YELLOW}Do you want to set up SSL with Certbot? (y/n)${NC}"
read -r setup_ssl
if [ "$setup_ssl" = "y" ]; then
    echo "Enter your domain name:"
    read -r domain_name
    echo "Setting up SSL for $domain_name..."
    certbot --nginx -d "$domain_name" --non-interactive --agree-tos --email admin@"$domain_name"
    print_status "SSL set up for $domain_name"
else
    print_info "Skipping SSL setup"
fi

# Restart services
print_section "Restarting Services"
echo "Restarting Supervisor..."
supervisorctl reread
supervisorctl update
supervisorctl restart trae:
print_status "Supervisor restarted"

echo "Restarting Nginx..."
systemctl restart nginx
print_status "Nginx restarted"

# Set up cron job for auto-scheduling
print_section "Setting up Cron Job for Auto-Scheduling"
CRON_FILE="/etc/cron.d/trae-ai-sentinel"
echo "Creating cron job..."
cat > "$CRON_FILE" << EOL
# TRAE AI Trading Sentinel Cron Jobs

# Run TRAE AI Agent every hour during market hours (Mon-Fri)
0 * * * 1-5 $USER cd $APP_DIR && $APP_DIR/venv/bin/python trae_ai.py --auto-run >> $APP_DIR/logs/trae_ai/cron.log 2>&1

# Clean up logs weekly
0 0 * * 0 $USER find $APP_DIR/logs -type f -name "*.log" -mtime +7 -delete
EOL
chmod 0644 "$CRON_FILE"
print_status "Cron job created"

# Print summary
print_section "Deployment Summary"
echo -e "${GREEN}TRAE AI Trading Sentinel has been deployed successfully!${NC}"
echo ""
echo -e "${BLUE}Application Directory:${NC} $APP_DIR"
echo -e "${BLUE}API URL:${NC} http://your-server-ip:$PORT/api"
echo -e "${BLUE}Dashboard URL:${NC} http://your-server-ip/"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "1. Update the Bulenox credentials in $APP_DIR/.env"
echo "2. The API key is stored in $API_KEY_FILE"
echo "3. Logs are stored in $APP_DIR/logs"
echo "4. To monitor the application, use: supervisorctl status trae:"
echo ""
echo -e "${GREEN}Thank you for using TRAE AI Trading Sentinel!${NC}"