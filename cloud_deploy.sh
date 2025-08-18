#!/bin/bash

# TradeBot Sentinel - Universal Cloud Deployment Script
# Supports: AWS, GCP, DigitalOcean, Contabo, Vast.ai

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Default values
PROVIDER=""
INSTANCE_TYPE=""
REGION=""
DRY_RUN=false
USE_DOCKER=true
SSL_ENABLED=false
MONITORING_ENABLED=true
AUTO_SCALING=false
DEPLOYMENT_ID="tradebot-$(date +%s)"

# Function to show usage
show_usage() {
    cat << EOF
TradeBot Sentinel - Universal Cloud Deployment Script

Usage: $0 [OPTIONS]

Options:
    --provider PROVIDER         Cloud provider (aws|gcp|digitalocean|contabo|vast)
    --instance-type TYPE        Instance type/size
    --region REGION            Deployment region
    --dry-run                  Validate configuration only
    --no-docker                Deploy without Docker
    --enable-ssl               Enable SSL/TLS
    --enable-monitoring        Enable monitoring stack (default: true)
    --enable-auto-scaling      Enable auto-scaling
    --deployment-id ID         Custom deployment ID
    --help                     Show this help message

Examples:
    $0 --provider aws --instance-type t3.medium --region us-east-1
    $0 --provider gcp --instance-type e2-medium --region us-central1-a
    $0 --provider digitalocean --instance-type s-2vcpu-4gb --region nyc1
    $0 --provider contabo --instance-type vps-s
    $0 --provider vast --instance-type rtx3080

Environment Variables Required:
    AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_KEY_PAIR, AWS_SSH_KEY_PATH
    GCP: GOOGLE_APPLICATION_CREDENTIALS, GCP_PROJECT_ID, GCP_SSH_KEY_PATH
    DigitalOcean: DO_API_TOKEN, DO_SSH_KEY_PATH
    Contabo: CONTABO_SSH_KEY, CONTABO_VPS_IP
    Vast.ai: VAST_API_KEY, VAST_SSH_KEY_PATH

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --instance-type)
            INSTANCE_TYPE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-docker)
            USE_DOCKER=false
            shift
            ;;
        --enable-ssl)
            SSL_ENABLED=true
            shift
            ;;
        --enable-monitoring)
            MONITORING_ENABLED=true
            shift
            ;;
        --enable-auto-scaling)
            AUTO_SCALING=true
            shift
            ;;
        --deployment-id)
            DEPLOYMENT_ID="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PROVIDER" ]]; then
    log_error "Provider is required. Use --provider to specify."
    show_usage
    exit 1
fi

# Validate provider
case $PROVIDER in
    aws|gcp|digitalocean|contabo|vast)
        log_info "Using provider: $PROVIDER"
        ;;
    *)
        log_error "Unsupported provider: $PROVIDER"
        exit 1
        ;;
esac

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("curl" "jq" "git")
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        tools+=("docker" "docker-compose")
    fi
    
    case $PROVIDER in
        aws)
            tools+=("aws")
            ;;
        gcp)
            tools+=("gcloud")
            ;;
        digitalocean)
            tools+=("doctl")
            ;;
    esac
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    log_success "All required tools are available"
}

# Function to validate credentials
validate_credentials() {
    log_info "Validating cloud provider credentials..."
    
    case $PROVIDER in
        aws)
            if ! aws sts get-caller-identity &> /dev/null; then
                log_error "AWS credentials validation failed"
                exit 1
            fi
            ;;
        gcp)
            if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
                log_error "GCP credentials validation failed"
                exit 1
            fi
            ;;
        digitalocean)
            if [[ -z "$DO_API_TOKEN" ]]; then
                log_error "DO_API_TOKEN environment variable is required"
                exit 1
            fi
            if ! curl -s -H "Authorization: Bearer $DO_API_TOKEN" "https://api.digitalocean.com/v2/account" | jq -e '.account' &> /dev/null; then
                log_error "DigitalOcean credentials validation failed"
                exit 1
            fi
            ;;
        contabo)
            if [[ -z "$CONTABO_SSH_KEY" ]] || [[ ! -f "$CONTABO_SSH_KEY" ]]; then
                log_error "CONTABO_SSH_KEY environment variable must point to a valid SSH key file"
                exit 1
            fi
            ;;
        vast)
            if [[ -z "$VAST_API_KEY" ]]; then
                log_error "VAST_API_KEY environment variable is required"
                exit 1
            fi
            if ! curl -s -H "Authorization: Bearer $VAST_API_KEY" "https://console.vast.ai/api/v0/users/current/" | jq -e '.success' &> /dev/null; then
                log_error "Vast.ai credentials validation failed"
                exit 1
            fi
            ;;
    esac
    
    log_success "Credentials validated successfully"
}

# Function to create cloud instance
create_instance() {
    log_info "Creating cloud instance..."
    
    case $PROVIDER in
        aws)
            create_aws_instance
            ;;
        gcp)
            create_gcp_instance
            ;;
        digitalocean)
            create_digitalocean_instance
            ;;
        contabo)
            create_contabo_instance
            ;;
        vast)
            create_vast_instance
            ;;
    esac
}

# AWS instance creation
create_aws_instance() {
    local instance_type=${INSTANCE_TYPE:-"t3.medium"}
    local region=${REGION:-"us-east-1"}
    
    log_info "Creating AWS EC2 instance: $instance_type in $region"
    
    # Create security group
    local sg_id=$(aws ec2 create-security-group \
        --group-name "$DEPLOYMENT_ID-sg" \
        --description "TradeBot Sentinel Security Group" \
        --region "$region" \
        --query 'GroupId' --output text)
    
    # Add security group rules
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp --port 22 --cidr 0.0.0.0/0 \
        --region "$region"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 \
        --region "$region"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 \
        --region "$region"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp --port 5000 --cidr 0.0.0.0/0 \
        --region "$region"
    
    # Launch instance
    local instance_id=$(aws ec2 run-instances \
        --image-id ami-0c02fb55956c7d316 \
        --instance-type "$instance_type" \
        --key-name "$AWS_KEY_PAIR" \
        --security-group-ids "$sg_id" \
        --region "$region" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$DEPLOYMENT_ID}]" \
        --query 'Instances[0].InstanceId' --output text)
    
    log_info "Instance created: $instance_id"
    
    # Wait for instance to be running
    log_info "Waiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids "$instance_id" --region "$region"
    
    # Get public IP
    local public_ip=$(aws ec2 describe-instances \
        --instance-ids "$instance_id" \
        --region "$region" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    
    log_success "Instance is running at: $public_ip"
    
    # Save instance info
    cat > "deployment_${DEPLOYMENT_ID}.json" << EOF
{
    "provider": "aws",
    "deployment_id": "$DEPLOYMENT_ID",
    "instance_id": "$instance_id",
    "public_ip": "$public_ip",
    "ssh_user": "ubuntu",
    "ssh_key": "$AWS_SSH_KEY_PATH",
    "region": "$region",
    "instance_type": "$instance_type",
    "security_group": "$sg_id",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    INSTANCE_IP="$public_ip"
    SSH_USER="ubuntu"
    SSH_KEY="$AWS_SSH_KEY_PATH"
}

# GCP instance creation
create_gcp_instance() {
    local machine_type=${INSTANCE_TYPE:-"e2-medium"}
    local zone=${REGION:-"us-central1-a"}
    
    log_info "Creating GCP Compute Engine instance: $machine_type in $zone"
    
    # Create firewall rules
    gcloud compute firewall-rules create "$DEPLOYMENT_ID-firewall" \
        --allow tcp:22,tcp:80,tcp:443,tcp:5000 \
        --source-ranges 0.0.0.0/0 \
        --description "TradeBot Sentinel firewall rules" || true
    
    # Create instance
    gcloud compute instances create "$DEPLOYMENT_ID" \
        --zone="$zone" \
        --machine-type="$machine_type" \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=20GB \
        --tags=tradebot-sentinel
    
    # Get external IP
    local public_ip=$(gcloud compute instances describe "$DEPLOYMENT_ID" \
        --zone="$zone" \
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    
    log_success "Instance is running at: $public_ip"
    
    # Save instance info
    cat > "deployment_${DEPLOYMENT_ID}.json" << EOF
{
    "provider": "gcp",
    "deployment_id": "$DEPLOYMENT_ID",
    "instance_id": "$DEPLOYMENT_ID",
    "public_ip": "$public_ip",
    "ssh_user": "ubuntu",
    "ssh_key": "$GCP_SSH_KEY_PATH",
    "zone": "$zone",
    "machine_type": "$machine_type",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    INSTANCE_IP="$public_ip"
    SSH_USER="ubuntu"
    SSH_KEY="$GCP_SSH_KEY_PATH"
}

# DigitalOcean droplet creation
create_digitalocean_instance() {
    local size=${INSTANCE_TYPE:-"s-2vcpu-4gb"}
    local region=${REGION:-"nyc1"}
    
    log_info "Creating DigitalOcean droplet: $size in $region"
    
    # Get SSH key ID
    local ssh_key_id=$(curl -s -H "Authorization: Bearer $DO_API_TOKEN" \
        "https://api.digitalocean.com/v2/account/keys" | \
        jq -r '.ssh_keys[0].id')
    
    # Create droplet
    local droplet_data=$(cat << EOF
{
    "name": "$DEPLOYMENT_ID",
    "region": "$region",
    "size": "$size",
    "image": "ubuntu-22-04-x64",
    "ssh_keys": ["$ssh_key_id"],
    "monitoring": true,
    "tags": ["tradebot-sentinel"]
}
EOF
    )
    
    local response=$(curl -s -X POST \
        -H "Authorization: Bearer $DO_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$droplet_data" \
        "https://api.digitalocean.com/v2/droplets")
    
    local droplet_id=$(echo "$response" | jq -r '.droplet.id')
    
    log_info "Droplet created: $droplet_id"
    
    # Wait for droplet to be active
    log_info "Waiting for droplet to be active..."
    while true; do
        local status=$(curl -s -H "Authorization: Bearer $DO_API_TOKEN" \
            "https://api.digitalocean.com/v2/droplets/$droplet_id" | \
            jq -r '.droplet.status')
        
        if [[ "$status" == "active" ]]; then
            break
        fi
        
        sleep 10
    done
    
    # Get public IP
    local public_ip=$(curl -s -H "Authorization: Bearer $DO_API_TOKEN" \
        "https://api.digitalocean.com/v2/droplets/$droplet_id" | \
        jq -r '.droplet.networks.v4[] | select(.type=="public") | .ip_address')
    
    log_success "Droplet is active at: $public_ip"
    
    # Save instance info
    cat > "deployment_${DEPLOYMENT_ID}.json" << EOF
{
    "provider": "digitalocean",
    "deployment_id": "$DEPLOYMENT_ID",
    "instance_id": "$droplet_id",
    "public_ip": "$public_ip",
    "ssh_user": "root",
    "ssh_key": "$DO_SSH_KEY_PATH",
    "region": "$region",
    "size": "$size",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    INSTANCE_IP="$public_ip"
    SSH_USER="root"
    SSH_KEY="$DO_SSH_KEY_PATH"
}

# Contabo VPS setup (manual)
create_contabo_instance() {
    log_info "Contabo VPS setup requires manual creation through their control panel"
    
    if [[ -z "$CONTABO_VPS_IP" ]]; then
        log_warning "Please create a VPS instance in Contabo control panel"
        read -p "Enter your Contabo VPS IP address: " CONTABO_VPS_IP
    fi
    
    # Save instance info
    cat > "deployment_${DEPLOYMENT_ID}.json" << EOF
{
    "provider": "contabo",
    "deployment_id": "$DEPLOYMENT_ID",
    "instance_id": "contabo-manual",
    "public_ip": "$CONTABO_VPS_IP",
    "ssh_user": "root",
    "ssh_key": "$CONTABO_SSH_KEY",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    INSTANCE_IP="$CONTABO_VPS_IP"
    SSH_USER="root"
    SSH_KEY="$CONTABO_SSH_KEY"
}

# Vast.ai instance creation
create_vast_instance() {
    local gpu_type=${INSTANCE_TYPE:-"RTX 3080"}
    
    log_info "Creating Vast.ai instance with GPU: $gpu_type"
    
    # Search for available instances
    local offers=$(curl -s -H "Authorization: Bearer $VAST_API_KEY" \
        "https://console.vast.ai/api/v0/bundles/?verified=true&external=false&rentable=true&gpu_name=$gpu_type&order=score-")
    
    local best_offer_id=$(echo "$offers" | jq -r '.offers[0].id')
    
    if [[ "$best_offer_id" == "null" ]]; then
        log_error "No available Vast.ai instances found for GPU: $gpu_type"
        exit 1
    fi
    
    # Create instance
    local create_data=$(cat << EOF
{
    "client_id": "me",
    "image": "pytorch/pytorch:latest",
    "args": [],
    "env": {},
    "price": 0.5,
    "disk": 10,
    "label": "$DEPLOYMENT_ID"
}
EOF
    )
    
    local response=$(curl -s -X PUT \
        -H "Authorization: Bearer $VAST_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$create_data" \
        "https://console.vast.ai/api/v0/asks/$best_offer_id/")
    
    local instance_id=$(echo "$response" | jq -r '.new_contract')
    
    log_info "Instance created: $instance_id"
    
    # Wait for instance to be running
    log_info "Waiting for instance to be running..."
    while true; do
        local status_response=$(curl -s -H "Authorization: Bearer $VAST_API_KEY" \
            "https://console.vast.ai/api/v0/instances/$instance_id/")
        
        local status=$(echo "$status_response" | jq -r '.instances[0].actual_status')
        
        if [[ "$status" == "running" ]]; then
            local public_ip=$(echo "$status_response" | jq -r '.instances[0].public_ipaddr')
            local ssh_port=$(echo "$status_response" | jq -r '.instances[0].ssh_port')
            break
        fi
        
        sleep 15
    done
    
    log_success "Instance is running at: $public_ip:$ssh_port"
    
    # Save instance info
    cat > "deployment_${DEPLOYMENT_ID}.json" << EOF
{
    "provider": "vast",
    "deployment_id": "$DEPLOYMENT_ID",
    "instance_id": "$instance_id",
    "public_ip": "$public_ip",
    "ssh_user": "root",
    "ssh_key": "$VAST_SSH_KEY_PATH",
    "ssh_port": "$ssh_port",
    "gpu_type": "$gpu_type",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    INSTANCE_IP="$public_ip"
    SSH_USER="root"
    SSH_KEY="$VAST_SSH_KEY_PATH"
    SSH_PORT="$ssh_port"
}

# Function to wait for SSH
wait_for_ssh() {
    log_info "Waiting for SSH to be available..."
    
    local ssh_cmd="ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i $SSH_KEY"
    
    if [[ -n "$SSH_PORT" ]]; then
        ssh_cmd="$ssh_cmd -p $SSH_PORT"
    fi
    
    ssh_cmd="$ssh_cmd $SSH_USER@$INSTANCE_IP 'echo SSH is ready'"
    
    local attempts=0
    local max_attempts=30
    
    while [[ $attempts -lt $max_attempts ]]; do
        if eval "$ssh_cmd" &> /dev/null; then
            log_success "SSH is now available"
            return 0
        fi
        
        attempts=$((attempts + 1))
        log_info "SSH attempt $attempts/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
    done
    
    log_error "SSH connection timeout after $max_attempts attempts"
    return 1
}

# Function to deploy application
deploy_application() {
    log_info "Deploying TradeBot Sentinel..."
    
    local ssh_cmd="ssh -o StrictHostKeyChecking=no -i $SSH_KEY"
    local scp_cmd="scp -o StrictHostKeyChecking=no -i $SSH_KEY"
    
    if [[ -n "$SSH_PORT" ]]; then
        ssh_cmd="$ssh_cmd -p $SSH_PORT"
        scp_cmd="$scp_cmd -P $SSH_PORT"
    fi
    
    # Update system
    log_info "Updating system packages..."
    eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'sudo apt-get update && sudo apt-get upgrade -y'"
    
    # Install Docker if needed
    if [[ "$USE_DOCKER" == "true" ]]; then
        log_info "Installing Docker..."
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $SSH_USER'"
        
        # Install Docker Compose
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose'"
    fi
    
    # Clone repository
    log_info "Cloning repository..."
    eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'git clone https://github.com/Gold724/AI-TRADING-BOT.git tradebot-sentinel && cd tradebot-sentinel'"
    
    # Copy environment file
    if [[ -f ".env" ]]; then
        log_info "Copying environment configuration..."
        eval "$scp_cmd .env $SSH_USER@$INSTANCE_IP:~/tradebot-sentinel/.env"
    fi
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        # Deploy with Docker
        log_info "Deploying with Docker Compose..."
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'cd tradebot-sentinel && docker-compose -f docker-compose.cloud.yml up -d'"
    else
        # Deploy directly
        log_info "Installing Python dependencies..."
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'cd tradebot-sentinel && sudo apt-get install -y python3 python3-pip && pip3 install -r requirements.txt'"
        
        # Install Chrome
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add - && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list && sudo apt-get update && sudo apt-get install -y google-chrome-stable'"
        
        # Create systemd service
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'sudo tee /etc/systemd/system/tradebot-sentinel.service > /dev/null << EOF
[Unit]
Description=TradeBot Sentinel
After=network.target

[Service]
Type=simple
User=$SSH_USER
WorkingDirectory=/home/$SSH_USER/tradebot-sentinel
Environment=DISPLAY=:99
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
ExecStart=/usr/bin/python3 tradebot_sentinel_final.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF'"
        
        # Start service
        eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'sudo systemctl daemon-reload && sudo systemctl enable tradebot-sentinel && sudo systemctl start tradebot-sentinel'"
    fi
    
    log_success "Deployment completed successfully!"
}

# Function to setup monitoring
setup_monitoring() {
    if [[ "$MONITORING_ENABLED" != "true" ]]; then
        return 0
    fi
    
    log_info "Setting up monitoring..."
    
    local ssh_cmd="ssh -o StrictHostKeyChecking=no -i $SSH_KEY"
    
    if [[ -n "$SSH_PORT" ]]; then
        ssh_cmd="$ssh_cmd -p $SSH_PORT"
    fi
    
    # Install monitoring tools
    eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'sudo apt-get install -y htop iotop nethogs'"
    
    log_success "Monitoring setup completed"
}

# Function to setup SSL
setup_ssl() {
    if [[ "$SSL_ENABLED" != "true" ]]; then
        return 0
    fi
    
    log_info "Setting up SSL/TLS..."
    
    local ssh_cmd="ssh -o StrictHostKeyChecking=no -i $SSH_KEY"
    
    if [[ -n "$SSH_PORT" ]]; then
        ssh_cmd="$ssh_cmd -p $SSH_PORT"
    fi
    
    # Install Certbot
    eval "$ssh_cmd $SSH_USER@$INSTANCE_IP 'sudo apt-get install -y certbot python3-certbot-nginx'"
    
    log_success "SSL setup completed"
}

# Function to show deployment summary
show_deployment_summary() {
    log_success "\n" + "="*60
    log_success "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    log_success "="*60
    log_info "Provider: $PROVIDER"
    log_info "Deployment ID: $DEPLOYMENT_ID"
    log_info "Instance IP: $INSTANCE_IP"
    log_info "SSH User: $SSH_USER"
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        log_info "TradeBot URL: http://$INSTANCE_IP"
        log_info "Grafana: http://$INSTANCE_IP:3000"
        log_info "Portainer: http://$INSTANCE_IP:9000"
    else
        log_info "TradeBot URL: http://$INSTANCE_IP:5000"
    fi
    
    log_info "SSH Command: ssh -i $SSH_KEY $SSH_USER@$INSTANCE_IP"
    log_info "Deployment Info: deployment_${DEPLOYMENT_ID}.json"
    log_success "="*60
}

# Main execution
main() {
    log_info "Starting TradeBot Sentinel cloud deployment..."
    log_info "Provider: $PROVIDER"
    log_info "Deployment ID: $DEPLOYMENT_ID"
    
    # Check prerequisites
    check_prerequisites
    
    # Validate credentials
    validate_credentials
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_success "Dry run completed successfully. Configuration is valid."
        exit 0
    fi
    
    # Create instance
    create_instance
    
    # Wait for SSH
    wait_for_ssh
    
    # Deploy application
    deploy_application
    
    # Setup monitoring
    setup_monitoring
    
    # Setup SSL
    setup_ssl
    
    # Show summary
    show_deployment_summary
}

# Run main function
main "$@"