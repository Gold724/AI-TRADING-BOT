#!/bin/bash

# AI Trading Sentinel - Cloud Deployment Script
# Automated deployment to Contabo VPS or any cloud provider

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-trading-sentinel"
GIT_REPO="https://github.com/yourusername/ai-trading-sentinel.git"
VPS_USER="root"
VPS_HOST=""
SSH_KEY_PATH="~/.ssh/id_rsa"
DOMAIN=""
EMAIL=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get user input
get_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        eval "$var_name='${input:-$default}'"
    else
        read -p "$prompt: " input
        eval "$var_name='$input'"
    fi
}

# Function to validate inputs
validate_inputs() {
    if [ -z "$VPS_HOST" ]; then
        print_error "VPS host is required"
        exit 1
    fi
    
    if [ -z "$GIT_REPO" ]; then
        print_error "Git repository URL is required"
        exit 1
    fi
}

# Function to test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection to $VPS_USER@$VPS_HOST..."
    
    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o BatchMode=yes "$VPS_USER@$VPS_HOST" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        print_success "SSH connection established"
        return 0
    else
        print_error "SSH connection failed"
        print_warning "Please ensure:"
        echo "  1. SSH key is properly configured: $SSH_KEY_PATH"
        echo "  2. VPS is accessible: $VPS_HOST"
        echo "  3. User has proper permissions: $VPS_USER"
        return 1
    fi
}

# Function to setup VPS environment
setup_vps_environment() {
    print_status "Setting up VPS environment..."
    
    ssh -i "$SSH_KEY_PATH" "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        set -e
        
        echo "🔄 Updating system packages..."
        apt update && apt upgrade -y
        
        echo "📦 Installing essential packages..."
        apt install -y \
            curl \
            wget \
            git \
            htop \
            screen \
            tmux \
            ufw \
            fail2ban \
            python3 \
            python3-pip \
            python3-venv \
            nodejs \
            npm
        
        echo "🐳 Installing Docker..."
        if ! command -v docker >/dev/null 2>&1; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            usermod -aG docker $USER
            systemctl enable docker
            systemctl start docker
        fi
        
        echo "🐙 Installing Docker Compose..."
        if ! command -v docker-compose >/dev/null 2>&1; then
            curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
        fi
        
        echo "🔒 Configuring firewall..."
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8080/tcp
        
        echo "🛡️ Configuring Fail2Ban..."
        systemctl enable fail2ban
        systemctl start fail2ban
        
        echo "✅ VPS environment setup completed"
ENDSSH
    
    print_success "VPS environment setup completed"
}

# Function to deploy application
deploy_application() {
    print_status "Deploying AI Trading Sentinel..."
    
    ssh -i "$SSH_KEY_PATH" "$VPS_USER@$VPS_HOST" << ENDSSH
        set -e
        
        echo "📥 Cloning repository..."
        if [ -d "$PROJECT_NAME" ]; then
            cd $PROJECT_NAME
            git pull origin main
        else
            git clone $GIT_REPO $PROJECT_NAME
            cd $PROJECT_NAME
        fi
        
        echo "🔧 Setting up environment..."
        cat > .env << EOF
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=XujhMzFf6K
ENVIRONMENT=production
HEADLESS=true
LOG_LEVEL=INFO
REDIS_PASSWORD=\$(openssl rand -hex 16)
DASHBOARD_SECRET=\$(openssl rand -hex 16)
TZ=UTC
EOF
        
        chmod 600 .env
        
        echo "🏗️ Building and starting containers..."
        docker-compose down --remove-orphans || true
        docker-compose build --no-cache
        docker-compose up -d
        
        echo "⏳ Waiting for services to start..."
        sleep 30
        
        echo "🔍 Checking service status..."
        docker-compose ps
        
        echo "📊 Checking logs..."
        docker-compose logs --tail=20
        
        echo "✅ Application deployment completed"
ENDSSH
    
    print_success "Application deployed successfully"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring and health checks..."
    
    ssh -i "$SSH_KEY_PATH" "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        set -e
        
        cd ai-trading-sentinel
        
        echo "📊 Creating monitoring script..."
        cat > monitor_trading_bot.sh << 'EOF'
#!/bin/bash

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️ Some containers are not running, restarting..."
    docker-compose restart
fi

# Check application health
if ! curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "⚠️ Application health check failed, restarting..."
    docker-compose restart trading-bot
fi

# Clean up old logs
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Clean up old screenshots
find screenshots/ -name "*.png" -mtime +3 -delete 2>/dev/null || true

echo "✅ Health check completed at $(date)"
EOF
        
        chmod +x monitor_trading_bot.sh
        
        echo "⏰ Setting up cron job for monitoring..."
        (crontab -l 2>/dev/null; echo "*/5 * * * * /root/ai-trading-sentinel/monitor_trading_bot.sh >> /root/ai-trading-sentinel/logs/monitor.log 2>&1") | crontab -
        
        echo "🔄 Creating auto-update script..."
        cat > auto_update.sh << 'EOF'
#!/bin/bash
set -e

cd /root/ai-trading-sentinel

echo "🔍 Checking for updates..."
git fetch origin

LATEST_COMMIT=$(git rev-parse origin/main)
CURRENT_COMMIT=$(git rev-parse HEAD)

if [ "$LATEST_COMMIT" != "$CURRENT_COMMIT" ]; then
    echo "📥 New updates found, deploying..."
    
    # Pull updates
    git pull origin main
    
    # Rebuild and restart
    docker-compose build --no-cache
    docker-compose up -d
    
    echo "✅ Update completed successfully!"
    
    # Send notification (if configured)
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="🚀 AI Trading Sentinel updated successfully on $(hostname)" >/dev/null
    fi
else
    echo "✅ Already up to date!"
fi
EOF
        
        chmod +x auto_update.sh
        
        echo "⏰ Setting up cron job for auto-updates..."
        (crontab -l 2>/dev/null; echo "0 */6 * * * /root/ai-trading-sentinel/auto_update.sh >> /root/ai-trading-sentinel/logs/update.log 2>&1") | crontab -
        
        echo "✅ Monitoring setup completed"
ENDSSH
    
    print_success "Monitoring and auto-update configured"
}

# Function to setup SSL (optional)
setup_ssl() {
    if [ -n "$DOMAIN" ] && [ -n "$EMAIL" ]; then
        print_status "Setting up SSL certificate for $DOMAIN..."
        
        ssh -i "$SSH_KEY_PATH" "$VPS_USER@$VPS_HOST" << ENDSSH
            set -e
            
            echo "🔒 Installing Certbot..."
            apt install -y certbot python3-certbot-nginx
            
            echo "📜 Obtaining SSL certificate..."
            certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive
            
            echo "⏰ Setting up auto-renewal..."
            (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
            
            echo "✅ SSL setup completed"
ENDSSH
        
        print_success "SSL certificate configured for $DOMAIN"
    else
        print_warning "Skipping SSL setup (domain and email not provided)"
    fi
}

# Function to display final information
display_final_info() {
    print_success "🎉 AI Trading Sentinel deployment completed!"
    echo ""
    echo "📋 Deployment Summary:"
    echo "  • VPS Host: $VPS_HOST"
    echo "  • Application URL: http://$VPS_HOST:8080"
    if [ -n "$DOMAIN" ]; then
        echo "  • Domain: https://$DOMAIN"
    fi
    echo "  • Dashboard: http://$VPS_HOST:3000"
    echo ""
    echo "🔧 Management Commands:"
    echo "  • SSH to VPS: ssh -i $SSH_KEY_PATH $VPS_USER@$VPS_HOST"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Restart services: docker-compose restart"
    echo "  • Update application: ./auto_update.sh"
    echo "  • Monitor health: ./monitor_trading_bot.sh"
    echo ""
    echo "📊 Monitoring:"
    echo "  • Health checks run every 5 minutes"
    echo "  • Auto-updates check every 6 hours"
    echo "  • Logs are automatically rotated"
    echo ""
    print_warning "⚠️ Important: Save your VPS credentials and SSH keys securely!"
}

# Main deployment function
main() {
    echo "🚀 AI Trading Sentinel - Cloud Deployment Script"
    echo "================================================"
    echo ""
    
    # Get deployment configuration
    print_status "Please provide deployment configuration:"
    get_input "VPS Host/IP" "VPS_HOST"
    get_input "VPS Username" "VPS_USER" "root"
    get_input "SSH Key Path" "SSH_KEY_PATH" "~/.ssh/id_rsa"
    get_input "Git Repository URL" "GIT_REPO" "https://github.com/yourusername/ai-trading-sentinel.git"
    get_input "Domain (optional)" "DOMAIN"
    get_input "Email for SSL (optional)" "EMAIL"
    
    echo ""
    
    # Validate inputs
    validate_inputs
    
    # Test SSH connection
    if ! test_ssh_connection; then
        exit 1
    fi
    
    # Confirm deployment
    echo ""
    print_warning "⚠️ This will deploy AI Trading Sentinel to $VPS_HOST"
    read -p "Do you want to continue? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi
    
    echo ""
    
    # Execute deployment steps
    setup_vps_environment
    deploy_application
    setup_monitoring
    setup_ssl
    
    # Display final information
    display_final_info
}

# Check prerequisites
if ! command_exists ssh; then
    print_error "SSH client is required but not installed"
    exit 1
fi

if ! command_exists git; then
    print_error "Git is required but not installed"
    exit 1
fi

# Run main function
main "$@"