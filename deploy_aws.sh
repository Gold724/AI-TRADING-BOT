#!/bin/bash

# TradeBot Sentinel - AWS Deployment Script
# Automated deployment to Amazon Web Services

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="tradebot-sentinel"
REGION="us-east-1"
INSTANCE_TYPE="t3.medium"
KEY_NAME="tradebot-key"
SECURITY_GROUP="tradebot-sg"
AMI_ID="ami-0c02fb55956c7d316"  # Ubuntu 20.04 LTS
VOLUME_SIZE="50"
DOMAIN_NAME=""
SSL_EMAIL=""

# Functions
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

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install it first."
        exit 1
    fi
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

load_config() {
    log_info "Loading configuration..."
    
    # Load from .env file if exists
    if [ -f ".env" ]; then
        source .env
        log_info "Configuration loaded from .env file"
    fi
    
    # Override with command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --region)
                REGION="$2"
                shift 2
                ;;
            --instance-type)
                INSTANCE_TYPE="$2"
                shift 2
                ;;
            --key-name)
                KEY_NAME="$2"
                shift 2
                ;;
            --domain)
                DOMAIN_NAME="$2"
                shift 2
                ;;
            --ssl-email)
                SSL_EMAIL="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "Region: $REGION"
    log_info "Instance Type: $INSTANCE_TYPE"
    log_info "Key Name: $KEY_NAME"
}

show_help() {
    echo "TradeBot Sentinel AWS Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --region REGION          AWS region (default: us-east-1)"
    echo "  --instance-type TYPE     EC2 instance type (default: t3.medium)"
    echo "  --key-name NAME          EC2 key pair name (default: tradebot-key)"
    echo "  --domain DOMAIN          Domain name for SSL certificate"
    echo "  --ssl-email EMAIL        Email for Let's Encrypt SSL certificate"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --region us-west-2 --instance-type t3.large"
    echo "  $0 --domain tradebot.example.com --ssl-email admin@example.com"
}

create_key_pair() {
    log_info "Creating EC2 key pair..."
    
    # Check if key pair already exists
    if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &> /dev/null; then
        log_warning "Key pair '$KEY_NAME' already exists"
        return 0
    fi
    
    # Create new key pair
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$REGION" \
        --query 'KeyMaterial' \
        --output text > "${KEY_NAME}.pem"
    
    chmod 600 "${KEY_NAME}.pem"
    log_success "Key pair created and saved to ${KEY_NAME}.pem"
}

create_security_group() {
    log_info "Creating security group..."
    
    # Check if security group already exists
    if aws ec2 describe-security-groups --group-names "$SECURITY_GROUP" --region "$REGION" &> /dev/null; then
        log_warning "Security group '$SECURITY_GROUP' already exists"
        return 0
    fi
    
    # Create security group
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP" \
        --description "TradeBot Sentinel Security Group" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text)
    
    # Add rules
    # SSH access
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    # HTTP access
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    # HTTPS access
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    # Application port
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    log_success "Security group created with ID: $SECURITY_GROUP_ID"
}

create_user_data_script() {
    log_info "Creating user data script..."
    
    cat > user-data.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install other dependencies
apt-get install -y git nginx certbot python3-certbot-nginx htop curl wget unzip

# Create application directory
mkdir -p /opt/tradebot
cd /opt/tradebot

# Clone repository (replace with your repository URL)
# git clone https://github.com/yourusername/ai-trading-sentinel.git .

# Create directories
mkdir -p logs screenshots data
chown -R ubuntu:ubuntu /opt/tradebot

# Install Python dependencies
apt-get install -y python3-pip
pip3 install playwright requests psutil schedule python-telegram-bot curlconverter

# Install Playwright browsers
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

# Setup systemd service
cat > /etc/systemd/system/tradebot.service << 'EOFSERVICE'
[Unit]
Description=TradeBot Sentinel
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/tradebot
Environment=PYTHONPATH=/opt/tradebot
ExecStart=/usr/bin/python3 /opt/tradebot/tradebot_sentinel.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSERVICE

# Enable and start service
systemctl daemon-reload
systemctl enable tradebot

# Setup log rotation
cat > /etc/logrotate.d/tradebot << 'EOFLOGROTATE'
/opt/tradebot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload tradebot
    endscript
}
EOFLOGROTATE

# Setup firewall
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 8000

# Setup automatic updates
echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create health check endpoint
cat > /opt/tradebot/health_endpoint.py << 'EOFHEALTH'
#!/usr/bin/env python3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from health_check import TradeBotHealthChecker

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                checker = TradeBotHealthChecker()
                report = checker.run_health_check()
                
                self.send_response(200 if report['overall_status'] == 'healthy' else 503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(report).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8001), HealthHandler)
    server.serve_forever()
EOFHEALTH

chmod +x /opt/tradebot/health_endpoint.py

# Setup health check service
cat > /etc/systemd/system/tradebot-health.service << 'EOFHEALTHSERVICE'
[Unit]
Description=TradeBot Health Check Endpoint
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/tradebot
ExecStart=/usr/bin/python3 /opt/tradebot/health_endpoint.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOFHEALTHSERVICE

systemctl daemon-reload
systemctl enable tradebot-health
systemctl start tradebot-health

# Setup Nginx reverse proxy
cat > /etc/nginx/sites-available/tradebot << 'EOFNGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOFNGINX

ln -s /etc/nginx/sites-available/tradebot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Log completion
echo "$(date): TradeBot Sentinel installation completed" >> /var/log/tradebot-install.log
EOF

    log_success "User data script created"
}

launch_instance() {
    log_info "Launching EC2 instance..."
    
    # Get security group ID
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
        --group-names "$SECURITY_GROUP" \
        --region "$REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    # Launch instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --count 1 \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SECURITY_GROUP_ID" \
        --user-data file://user-data.sh \
        --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_SIZE,VolumeType=gp3}" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$APP_NAME},{Key=Environment,Value=production}]" \
        --region "$REGION" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    log_success "Instance launched with ID: $INSTANCE_ID"
    
    # Wait for instance to be running
    log_info "Waiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    log_success "Instance is running at IP: $PUBLIC_IP"
    
    # Save instance information
    cat > deployment-info.json << EOF
{
    "instance_id": "$INSTANCE_ID",
    "public_ip": "$PUBLIC_IP",
    "region": "$REGION",
    "key_name": "$KEY_NAME",
    "security_group": "$SECURITY_GROUP",
    "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log_info "Deployment information saved to deployment-info.json"
}

setup_ssl() {
    if [ -z "$DOMAIN_NAME" ] || [ -z "$SSL_EMAIL" ]; then
        log_warning "Domain name or SSL email not provided, skipping SSL setup"
        return 0
    fi
    
    log_info "Setting up SSL certificate for $DOMAIN_NAME..."
    
    # Wait for instance to be fully ready
    sleep 60
    
    # SSH and setup SSL
    ssh -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no ubuntu@"$PUBLIC_IP" << EOF
sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email $SSL_EMAIL
sudo systemctl reload nginx
EOF
    
    log_success "SSL certificate configured for $DOMAIN_NAME"
}

upload_files() {
    log_info "Uploading application files..."
    
    # Wait for instance to be ready
    sleep 30
    
    # Create tar archive of application files
    tar -czf tradebot-app.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='screenshots/*.png' \
        *.py *.yml *.yaml *.txt *.md *.env.template Dockerfile* docker-compose* requirements.txt 2>/dev/null || true
    
    # Upload files
    scp -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no tradebot-app.tar.gz ubuntu@"$PUBLIC_IP":/tmp/
    
    # Extract and setup files on server
    ssh -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no ubuntu@"$PUBLIC_IP" << 'EOF'
sudo mkdir -p /opt/tradebot
cd /opt/tradebot
sudo tar -xzf /tmp/tradebot-app.tar.gz
sudo chown -R ubuntu:ubuntu /opt/tradebot
sudo chmod +x *.py

# Create environment file from template
if [ -f ".env.template" ] && [ ! -f ".env" ]; then
    cp .env.template .env
    echo "Environment template copied to .env - please configure it"
fi

# Start services
sudo systemctl start tradebot
sudo systemctl start tradebot-health
EOF
    
    # Cleanup
    rm -f tradebot-app.tar.gz
    
    log_success "Application files uploaded and services started"
}

show_deployment_summary() {
    log_success "\n=== TradeBot Sentinel Deployment Complete ==="
    echo ""
    echo "Instance ID: $INSTANCE_ID"
    echo "Public IP: $PUBLIC_IP"
    echo "Region: $REGION"
    echo "SSH Command: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
    echo ""
    echo "Application URLs:"
    echo "  Main App: http://$PUBLIC_IP:8000"
    echo "  Health Check: http://$PUBLIC_IP/health"
    
    if [ -n "$DOMAIN_NAME" ]; then
        echo "  Domain: https://$DOMAIN_NAME"
    fi
    
    echo ""
    echo "Next Steps:"
    echo "1. SSH to the server and configure .env file with your credentials"
    echo "2. Restart the TradeBot service: sudo systemctl restart tradebot"
    echo "3. Monitor logs: sudo journalctl -u tradebot -f"
    echo "4. Check health: curl http://$PUBLIC_IP/health"
    echo ""
    echo "Important Files:"
    echo "  - SSH Key: ${KEY_NAME}.pem"
    echo "  - Deployment Info: deployment-info.json"
    echo ""
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    
    if [ -n "$INSTANCE_ID" ]; then
        log_info "Terminating instance $INSTANCE_ID..."
        aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$REGION" || true
    fi
    
    # Remove temporary files
    rm -f user-data.sh tradebot-app.tar.gz
    
    exit 1
}

# Main deployment function
main() {
    log_info "Starting TradeBot Sentinel AWS deployment..."
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Load configuration
    load_config "$@"
    
    # Check dependencies
    check_dependencies
    
    # Create AWS resources
    create_key_pair
    create_security_group
    create_user_data_script
    
    # Launch instance
    launch_instance
    
    # Upload application files
    upload_files
    
    # Setup SSL if domain provided
    setup_ssl
    
    # Show deployment summary
    show_deployment_summary
    
    # Cleanup temporary files
    rm -f user-data.sh
    
    log_success "TradeBot Sentinel deployed successfully!"
}

# Run main function with all arguments
main "$@"