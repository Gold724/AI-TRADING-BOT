#!/bin/bash

# 🔐 SSH Troubleshooting & Auto-Setup Script for AI Trading Sentinel
# Usage: ./ssh_troubleshoot.sh [target_ip] [username]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TARGET_IP="${1:-161.97.112.146}"
USERNAME="${2:-root}"
SSH_KEY_PATH="$HOME/.ssh/id_rsa"

echo -e "${BLUE}🔐 AI Trading Sentinel - SSH Troubleshooter${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Target: ${YELLOW}$USERNAME@$TARGET_IP${NC}"
echo ""

# Function to log messages
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

# Step 1: Basic connectivity test
log_info "Step 1: Testing basic connectivity..."
if ping -c 3 "$TARGET_IP" > /dev/null 2>&1; then
    log_success "Server is reachable via ping"
else
    log_error "Server is not reachable via ping"
    exit 1
fi

# Step 2: Check SSH port
log_info "Step 2: Checking SSH port 22..."
if nc -z "$TARGET_IP" 22 2>/dev/null; then
    log_success "SSH port 22 is open"
else
    log_error "SSH port 22 is not accessible"
    log_info "Trying alternative SSH ports..."
    for port in 2222 22022 2200; do
        if nc -z "$TARGET_IP" "$port" 2>/dev/null; then
            log_success "SSH found on port $port"
            SSH_PORT="$port"
            break
        fi
    done
fi

# Step 3: Check existing SSH keys
log_info "Step 3: Checking SSH keys..."
if [ -f "$SSH_KEY_PATH" ]; then
    log_success "SSH private key found: $SSH_KEY_PATH"
else
    log_warning "No SSH key found. Generating new key pair..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "trae-deployment@$(hostname)"
    log_success "New SSH key pair generated"
fi

# Step 4: Test SSH connection methods
log_info "Step 4: Testing SSH connection methods..."

# Method 1: Key-based authentication
log_info "Testing key-based authentication..."
SSH_CMD="ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
if [ -n "$SSH_PORT" ]; then
    SSH_CMD="$SSH_CMD -p $SSH_PORT"
fi

if $SSH_CMD "$USERNAME@$TARGET_IP" "echo 'SSH key auth successful'" 2>/dev/null; then
    log_success "SSH key authentication works!"
    SSH_AUTH_METHOD="key"
else
    log_warning "SSH key authentication failed"
    
    # Method 2: Try to copy SSH key
    log_info "Attempting to copy SSH key to server..."
    if command -v ssh-copy-id >/dev/null 2>&1; then
        log_info "Please enter the password for $USERNAME@$TARGET_IP when prompted:"
        if ssh-copy-id -i "$SSH_KEY_PATH.pub" "$USERNAME@$TARGET_IP" 2>/dev/null; then
            log_success "SSH key copied successfully!"
            SSH_AUTH_METHOD="key"
        else
            log_warning "Failed to copy SSH key automatically"
        fi
    fi
fi

# Step 5: Alternative connection methods
if [ "$SSH_AUTH_METHOD" != "key" ]; then
    log_info "Step 5: Trying alternative authentication methods..."
    
    # Try different usernames
    for user in ubuntu admin user debian; do
        log_info "Trying username: $user"
        if $SSH_CMD "$user@$TARGET_IP" "echo 'Connected as $user'" 2>/dev/null; then
            log_success "Successfully connected as $user"
            USERNAME="$user"
            SSH_AUTH_METHOD="key"
            break
        fi
    done
fi

# Step 6: Generate deployment commands
log_info "Step 6: Generating deployment commands..."

if [ "$SSH_AUTH_METHOD" = "key" ]; then
    log_success "SSH access established! Generating deployment commands..."
    
    cat > "ssh_deploy_commands.sh" << EOF
#!/bin/bash
# Auto-generated SSH deployment commands

# SSH connection command
SSH_CMD="ssh $USERNAME@$TARGET_IP"
if [ -n "$SSH_PORT" ]; then
    SSH_CMD="ssh -p $SSH_PORT $USERNAME@$TARGET_IP"
fi

# Deploy AI Trading Sentinel
echo "Deploying AI Trading Sentinel..."
\$SSH_CMD << 'REMOTE_COMMANDS'
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip nodejs npm git docker.io docker-compose curl

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker \$USER

# Clone repository
if [ ! -d "ai-trading-sentinel" ]; then
    git clone https://github.com/your-username/ai-trading-sentinel.git
fi

cd ai-trading-sentinel

# Make scripts executable
chmod +x deploy/deploy-production.sh
chmod +x quick-deploy.sh

# Run deployment
./deploy/deploy-production.sh

echo "Deployment completed! Services starting..."
REMOTE_COMMANDS

echo "Deployment script completed!"
EOF

    chmod +x "ssh_deploy_commands.sh"
    log_success "Deployment script created: ssh_deploy_commands.sh"
    
else
    log_error "Could not establish SSH connection"
    log_info "Manual steps required:"
    echo ""
    echo "1. Contact Contabo support for console access"
    echo "2. Reset root password via control panel"
    echo "3. Add your SSH key manually:"
    echo "   cat $SSH_KEY_PATH.pub"
    echo "   # Copy the output and add to ~/.ssh/authorized_keys on target server"
    echo ""
    echo "4. Or deploy on current server instead:"
    echo "   ./quick-deploy.sh localhost"
fi

# Step 7: Create connection helper
log_info "Step 7: Creating connection helper..."

cat > "connect_server.sh" << EOF
#!/bin/bash
# Quick connection script

if [ "\$1" = "deploy" ]; then
    echo "Running deployment..."
    ./ssh_deploy_commands.sh
elif [ "\$1" = "logs" ]; then
    echo "Viewing logs..."
    ssh $USERNAME@$TARGET_IP "tail -f ai-trading-sentinel/logs/trading.log"
elif [ "\$1" = "status" ]; then
    echo "Checking status..."
    ssh $USERNAME@$TARGET_IP "cd ai-trading-sentinel && python3 deployment_validator.py"
else
    echo "Connecting to server..."
    ssh $USERNAME@$TARGET_IP
fi
EOF

chmod +x "connect_server.sh"
log_success "Connection helper created: connect_server.sh"

echo ""
log_success "SSH troubleshooting completed!"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
if [ "$SSH_AUTH_METHOD" = "key" ]; then
    echo "1. Run deployment: ./ssh_deploy_commands.sh"
    echo "2. Connect to server: ./connect_server.sh"
    echo "3. Check status: ./connect_server.sh status"
    echo "4. View logs: ./connect_server.sh logs"
else
    echo "1. Resolve SSH access issues (see manual steps above)"
    echo "2. Or deploy locally: ./quick-deploy.sh localhost"
fi
echo ""
echo -e "${GREEN}🚀 Ready for AI Trading Sentinel deployment!${NC}"