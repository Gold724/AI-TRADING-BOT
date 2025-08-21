#!/bin/bash

# Contabo SSH Setup and Deployment Script
# This script sets up SSH keys and deploys the AI Trading Sentinel

set -e

echo "🔐 AI Trading Sentinel - SSH Setup & Deployment"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TARGET_IP="161.97.112.146"
USER="root"
SSH_KEY_PATH="$HOME/.ssh/id_rsa"
REPO_URL="https://github.com/your-username/ai-trading-sentinel.git"
DEPLOY_DIR="/opt/ai-trading-sentinel"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Generate SSH Key if not exists
setup_ssh_key() {
    log_info "Setting up SSH key..."
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        log_info "Generating new SSH key pair..."
        ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "ai-trading-sentinel@contabo"
        log_success "SSH key generated at $SSH_KEY_PATH"
    else
        log_info "SSH key already exists at $SSH_KEY_PATH"
    fi
    
    # Set proper permissions
    chmod 600 "$SSH_KEY_PATH"
    chmod 644 "${SSH_KEY_PATH}.pub"
}

# Step 2: Copy SSH key to target server
setup_ssh_access() {
    log_info "Setting up SSH access to $TARGET_IP..."
    
    # Check if we can already connect
    if ssh -o ConnectTimeout=5 -o BatchMode=yes "$USER@$TARGET_IP" exit 2>/dev/null; then
        log_success "SSH key authentication already working"
        return 0
    fi
    
    log_info "Copying SSH key to target server..."
    log_warning "You will be prompted for the root password"
    
    # Copy SSH key using ssh-copy-id
    if command -v ssh-copy-id >/dev/null 2>&1; then
        ssh-copy-id -i "${SSH_KEY_PATH}.pub" "$USER@$TARGET_IP"
    else
        # Manual method if ssh-copy-id is not available
        cat "${SSH_KEY_PATH}.pub" | ssh "$USER@$TARGET_IP" "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"
    fi
    
    # Test SSH connection
    if ssh -o ConnectTimeout=5 "$USER@$TARGET_IP" "echo 'SSH connection successful'"; then
        log_success "SSH key authentication configured successfully"
    else
        log_error "Failed to setup SSH key authentication"
        exit 1
    fi
}

# Step 3: Deploy AI Trading Sentinel
deploy_trading_bot() {
    log_info "Deploying AI Trading Sentinel to $TARGET_IP..."
    
    # Create deployment script
    cat > /tmp/deploy_script.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting AI Trading Sentinel deployment..."

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nodejs npm git curl wget unzip

# Install Docker
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose
if ! command -v docker-compose >/dev/null 2>&1; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create deployment directory
mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Clone or update repository
if [ -d ".git" ]; then
    echo "Updating existing repository..."
    git pull origin main
else
    echo "Cloning repository..."
    git clone https://github.com/your-username/ai-trading-sentinel.git .
fi

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install Node.js dependencies
if [ -f "package.json" ]; then
    npm install
fi

# Set up environment file
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "# AI Trading Sentinel Environment" > .env
    echo "Please configure .env file with your credentials"
fi

# Set up systemd service
if [ -f "trae.service" ]; then
    cp trae.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable trae
fi

# Set up Nginx (if config exists)
if [ -f "nginx.conf" ] && command -v nginx >/dev/null 2>&1; then
    cp nginx.conf /etc/nginx/sites-available/ai-trading-sentinel
    ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
fi

# Set proper permissions
chown -R root:root /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/*.sh

echo "✅ AI Trading Sentinel deployed successfully!"
echo "📍 Location: /opt/ai-trading-sentinel"
echo "🔧 Configure .env file and start services"
EOF

    # Copy and execute deployment script
    scp /tmp/deploy_script.sh "$USER@$TARGET_IP:/tmp/"
    ssh "$USER@$TARGET_IP" "chmod +x /tmp/deploy_script.sh && /tmp/deploy_script.sh"
    
    log_success "Deployment completed successfully!"
}

# Step 4: Configure environment and start services
configure_and_start() {
    log_info "Configuring environment and starting services..."
    
    # Create environment configuration script
    cat > /tmp/configure_env.sh << 'EOF'
#!/bin/bash
cd /opt/ai-trading-sentinel

# Check if .env exists and has basic configuration
if [ ! -s ".env" ]; then
    echo "Creating basic .env configuration..."
    cat > .env << 'ENVEOF'
# AI Trading Sentinel Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=5000
FRONTEND_PORT=3000

# Database
DATABASE_URL=sqlite:///data/trading.db

# Trading Configuration
TRADING_MODE=live
RISK_LEVEL=medium
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0

# Broker Configuration (Update with your credentials)
BROKER_USERNAME=your_username
BROKER_PASSWORD=your_password
BROKER_URL=https://your-broker.com

# Monitoring
MONITORING_ENABLED=true
ALERT_EMAIL=your-email@example.com

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENVEOF
    echo "⚠️  Please update .env with your actual credentials!"
fi

# Create data directories
mkdir -p data/{accounts,backtest,emergency,historical,memory,signals,simulations}
mkdir -p logs

# Start services using systemd if available
if systemctl is-enabled trae >/dev/null 2>&1; then
    echo "Starting trae service..."
    systemctl start trae
    systemctl status trae --no-pager
else
    echo "Systemd service not configured. You can start manually with:"
    echo "cd /opt/ai-trading-sentinel && python3 main.py"
fi

echo "🎯 Configuration completed!"
echo "📊 Access dashboard at: http://$(curl -s ifconfig.me):5000"
echo "📝 Logs: tail -f /opt/ai-trading-sentinel/logs/trading.log"
echo "🔧 Edit config: nano /opt/ai-trading-sentinel/.env"
EOF

    # Execute configuration script
    scp /tmp/configure_env.sh "$USER@$TARGET_IP:/tmp/"
    ssh "$USER@$TARGET_IP" "chmod +x /tmp/configure_env.sh && /tmp/configure_env.sh"
    
    log_success "Configuration completed!"
}

# Step 5: Validation and status check
validate_deployment() {
    log_info "Validating deployment..."
    
    ssh "$USER@$TARGET_IP" << 'EOF'
echo "🔍 Deployment Validation Report"
echo "=============================="

# Check if directory exists
if [ -d "/opt/ai-trading-sentinel" ]; then
    echo "✅ Deployment directory exists"
    cd /opt/ai-trading-sentinel
    
    # Check Python environment
    if [ -d "venv" ]; then
        echo "✅ Python virtual environment created"
    else
        echo "❌ Python virtual environment missing"
    fi
    
    # Check configuration
    if [ -f ".env" ]; then
        echo "✅ Environment configuration exists"
    else
        echo "❌ Environment configuration missing"
    fi
    
    # Check service status
    if systemctl is-active trae >/dev/null 2>&1; then
        echo "✅ Trading service is running"
    else
        echo "⚠️  Trading service not running (may need manual start)"
    fi
    
    # Check ports
    if netstat -tlnp | grep -q ":5000"; then
        echo "✅ Backend service listening on port 5000"
    else
        echo "⚠️  Backend service not listening on port 5000"
    fi
    
    # Show system info
    echo ""
    echo "📊 System Information:"
    echo "CPU: $(nproc) cores"
    echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
    echo "Disk: $(df -h / | awk 'NR==2 {print $4}') available"
    echo "IP: $(curl -s ifconfig.me)"
    
else
    echo "❌ Deployment directory not found"
fi
EOF

    log_success "Validation completed!"
}

# Main execution
main() {
    echo
    log_info "Starting SSH setup and deployment process..."
    echo
    
    setup_ssh_key
    setup_ssh_access
    deploy_trading_bot
    configure_and_start
    validate_deployment
    
    echo
    log_success "🎉 AI Trading Sentinel deployment completed successfully!"
    echo
    echo "📋 Next Steps:"
    echo "1. SSH into server: ssh root@$TARGET_IP"
    echo "2. Configure credentials: nano /opt/ai-trading-sentinel/.env"
    echo "3. Start trading: systemctl start trae"
    echo "4. Monitor logs: tail -f /opt/ai-trading-sentinel/logs/trading.log"
    echo "5. Access dashboard: http://$TARGET_IP:5000"
    echo
}

# Execute main function
main "$@"