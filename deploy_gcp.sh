#!/bin/bash

# TradeBot Sentinel - Google Cloud Platform Deployment Script
# Automated deployment to Google Cloud Platform

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="tradebot-sentinel"
PROJECT_ID=""
REGION="us-central1"
ZONE="us-central1-a"
MACHINE_TYPE="e2-medium"
BOOT_DISK_SIZE="50GB"
IMAGE_FAMILY="ubuntu-2004-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
NETWORK_NAME="tradebot-network"
SUBNET_NAME="tradebot-subnet"
FIREWALL_NAME="tradebot-firewall"
INSTANCE_NAME="tradebot-instance"
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
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI not found. Please install it first."
        log_info "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install it first."
        exit 1
    fi
    
    # Verify gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "Not authenticated with gcloud. Run 'gcloud auth login' first."
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
            --project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            --region)
                REGION="$2"
                ZONE="${2}-a"
                shift 2
                ;;
            --zone)
                ZONE="$2"
                shift 2
                ;;
            --machine-type)
                MACHINE_TYPE="$2"
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
    
    # Validate required parameters
    if [ -z "$PROJECT_ID" ]; then
        log_error "Project ID is required. Use --project-id or set GCP_PROJECT_ID in .env"
        exit 1
    fi
    
    log_info "Project ID: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Zone: $ZONE"
    log_info "Machine Type: $MACHINE_TYPE"
}

show_help() {
    echo "TradeBot Sentinel GCP Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --project-id ID          GCP project ID (required)"
    echo "  --region REGION          GCP region (default: us-central1)"
    echo "  --zone ZONE              GCP zone (default: us-central1-a)"
    echo "  --machine-type TYPE      VM machine type (default: e2-medium)"
    echo "  --domain DOMAIN          Domain name for SSL certificate"
    echo "  --ssl-email EMAIL        Email for Let's Encrypt SSL certificate"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --project-id my-project --region us-west1"
    echo "  $0 --project-id my-project --machine-type e2-standard-2"
    echo "  $0 --project-id my-project --domain tradebot.example.com --ssl-email admin@example.com"
}

setup_project() {
    log_info "Setting up GCP project..."
    
    # Set current project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required APIs..."
    gcloud services enable compute.googleapis.com
    gcloud services enable dns.googleapis.com
    gcloud services enable logging.googleapis.com
    gcloud services enable monitoring.googleapis.com
    
    log_success "Project setup completed"
}

create_network() {
    log_info "Creating VPC network..."
    
    # Check if network already exists
    if gcloud compute networks describe "$NETWORK_NAME" --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Network '$NETWORK_NAME' already exists"
    else
        # Create VPC network
        gcloud compute networks create "$NETWORK_NAME" \
            --project="$PROJECT_ID" \
            --subnet-mode=custom \
            --bgp-routing-mode=regional
        
        log_success "VPC network created"
    fi
    
    # Check if subnet already exists
    if gcloud compute networks subnets describe "$SUBNET_NAME" --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Subnet '$SUBNET_NAME' already exists"
    else
        # Create subnet
        gcloud compute networks subnets create "$SUBNET_NAME" \
            --project="$PROJECT_ID" \
            --network="$NETWORK_NAME" \
            --region="$REGION" \
            --range="10.0.0.0/24"
        
        log_success "Subnet created"
    fi
}

create_firewall_rules() {
    log_info "Creating firewall rules..."
    
    # Check if firewall rule already exists
    if gcloud compute firewall-rules describe "$FIREWALL_NAME" --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Firewall rule '$FIREWALL_NAME' already exists"
        return 0
    fi
    
    # Create firewall rule
    gcloud compute firewall-rules create "$FIREWALL_NAME" \
        --project="$PROJECT_ID" \
        --network="$NETWORK_NAME" \
        --allow=tcp:22,tcp:80,tcp:443,tcp:8000,tcp:8001 \
        --source-ranges=0.0.0.0/0 \
        --description="TradeBot Sentinel firewall rule"
    
    log_success "Firewall rules created"
}

create_startup_script() {
    log_info "Creating startup script..."
    
    cat > startup-script.sh << 'EOF'
#!/bin/bash

# Logging
exec > >(tee /var/log/startup-script.log)
exec 2>&1

echo "$(date): Starting TradeBot Sentinel installation"

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
apt-get install -y git nginx certbot python3-certbot-nginx htop curl wget unzip jq

# Install Google Cloud Ops Agent for monitoring
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Create application directory
mkdir -p /opt/tradebot
cd /opt/tradebot

# Create directories
mkdir -p logs screenshots data config
chown -R ubuntu:ubuntu /opt/tradebot

# Install Python dependencies
apt-get install -y python3-pip python3-venv
python3 -m venv /opt/tradebot/venv
source /opt/tradebot/venv/bin/activate
pip install playwright requests psutil schedule python-telegram-bot curlconverter google-cloud-logging google-cloud-monitoring

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
Group=ubuntu
WorkingDirectory=/opt/tradebot
Environment=PYTHONPATH=/opt/tradebot
Environment=PATH=/opt/tradebot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/tradebot/venv/bin/python /opt/tradebot/tradebot_sentinel.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOFSERVICE

# Enable service
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
ufw allow 8001

# Setup automatic updates
echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create health check endpoint
cat > /opt/tradebot/health_endpoint.py << 'EOFHEALTH'
#!/usr/bin/env python3
import json
import sys
import os
sys.path.append('/opt/tradebot')
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
Group=ubuntu
WorkingDirectory=/opt/tradebot
Environment=PYTHONPATH=/opt/tradebot
Environment=PATH=/opt/tradebot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/tradebot/venv/bin/python /opt/tradebot/health_endpoint.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

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
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /health {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        access_log off;
    }
    
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
EOFNGINX

ln -s /etc/nginx/sites-available/tradebot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Setup Google Cloud Logging
cat > /etc/google-cloud-ops-agent/config.yaml << 'EOFLOGGING'
logging:
  receivers:
    tradebot_logs:
      type: files
      include_paths:
        - /opt/tradebot/logs/*.log
        - /var/log/tradebot-*.log
      exclude_paths:
        - /opt/tradebot/logs/*.gz
    nginx_access:
      type: files
      include_paths:
        - /var/log/nginx/access.log
    nginx_error:
      type: files
      include_paths:
        - /var/log/nginx/error.log
    syslog:
      type: files
      include_paths:
        - /var/log/syslog
  processors:
    tradebot_parser:
      type: parse_json
  service:
    pipelines:
      default_pipeline:
        receivers: [tradebot_logs, nginx_access, nginx_error, syslog]
        processors: [tradebot_parser]

metrics:
  receivers:
    hostmetrics:
      type: hostmetrics
      collection_interval: 60s
    nginx:
      type: nginx
      stub_status_url: http://localhost/nginx_status
  service:
    pipelines:
      default_pipeline:
        receivers: [hostmetrics, nginx]
EOFLOGGING

systemctl restart google-cloud-ops-agent

# Create monitoring script
cat > /opt/tradebot/monitor.py << 'EOFMONITOR'
#!/usr/bin/env python3
import time
import requests
import subprocess
import logging
from google.cloud import monitoring_v3
from google.cloud import logging as cloud_logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_services():
    """Check if TradeBot services are running"""
    services = ['tradebot', 'tradebot-health', 'nginx']
    for service in services:
        try:
            result = subprocess.run(['systemctl', 'is-active', service], 
                                  capture_output=True, text=True)
            if result.stdout.strip() != 'active':
                logger.error(f"Service {service} is not active")
                # Restart service
                subprocess.run(['sudo', 'systemctl', 'restart', service])
        except Exception as e:
            logger.error(f"Error checking service {service}: {e}")

def check_health_endpoint():
    """Check health endpoint"""
    try:
        response = requests.get('http://localhost:8001/health', timeout=10)
        if response.status_code != 200:
            logger.error(f"Health check failed with status {response.status_code}")
    except Exception as e:
        logger.error(f"Health check error: {e}")

if __name__ == '__main__':
    while True:
        check_services()
        check_health_endpoint()
        time.sleep(60)  # Check every minute
EOFMONITOR

chmod +x /opt/tradebot/monitor.py

# Setup monitoring service
cat > /etc/systemd/system/tradebot-monitor.service << 'EOFMONITORSERVICE'
[Unit]
Description=TradeBot Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tradebot
Environment=PYTHONPATH=/opt/tradebot
Environment=PATH=/opt/tradebot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/tradebot/venv/bin/python /opt/tradebot/monitor.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOFMONITORSERVICE

systemctl daemon-reload
systemctl enable tradebot-monitor
systemctl start tradebot-monitor

# Log completion
echo "$(date): TradeBot Sentinel installation completed" >> /var/log/startup-script.log
EOF

    log_success "Startup script created"
}

create_instance() {
    log_info "Creating VM instance..."
    
    # Check if instance already exists
    if gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Instance '$INSTANCE_NAME' already exists"
        return 0
    fi
    
    # Create VM instance
    gcloud compute instances create "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --network-interface=network-tier=PREMIUM,subnet="$SUBNET_NAME" \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --service-account="$(gcloud iam service-accounts list --filter='displayName:Compute Engine default service account' --format='value(email)')" \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --tags=tradebot-server \
        --create-disk=auto-delete=yes,boot=yes,device-name="$INSTANCE_NAME",image=projects/"$IMAGE_PROJECT"/global/images/family/"$IMAGE_FAMILY",mode=rw,size="$BOOT_DISK_SIZE",type=projects/"$PROJECT_ID"/zones/"$ZONE"/diskTypes/pd-standard \
        --metadata-from-file startup-script=startup-script.sh \
        --labels=app=tradebot,environment=production
    
    log_success "VM instance created"
}

get_instance_info() {
    log_info "Getting instance information..."
    
    # Wait for instance to be running
    log_info "Waiting for instance to be running..."
    while true; do
        STATUS=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --format="value(status)")
        if [ "$STATUS" = "RUNNING" ]; then
            break
        fi
        sleep 10
    done
    
    # Get external IP
    EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$PROJECT_ID" \
        --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
    
    # Get internal IP
    INTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$PROJECT_ID" \
        --format="value(networkInterfaces[0].networkIP)")
    
    log_success "Instance is running"
    log_info "External IP: $EXTERNAL_IP"
    log_info "Internal IP: $INTERNAL_IP"
    
    # Save instance information
    cat > deployment-info.json << EOF
{
    "project_id": "$PROJECT_ID",
    "instance_name": "$INSTANCE_NAME",
    "zone": "$ZONE",
    "region": "$REGION",
    "machine_type": "$MACHINE_TYPE",
    "external_ip": "$EXTERNAL_IP",
    "internal_ip": "$INTERNAL_IP",
    "network": "$NETWORK_NAME",
    "subnet": "$SUBNET_NAME",
    "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log_info "Deployment information saved to deployment-info.json"
}

upload_files() {
    log_info "Uploading application files..."
    
    # Wait for instance to be ready
    sleep 60
    
    # Create tar archive of application files
    tar -czf tradebot-app.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='screenshots/*.png' \
        *.py *.yml *.yaml *.txt *.md *.env.template Dockerfile* docker-compose* requirements.txt 2>/dev/null || true
    
    # Upload files using gcloud scp
    gcloud compute scp tradebot-app.tar.gz "$INSTANCE_NAME":/tmp/ \
        --zone="$ZONE" \
        --project="$PROJECT_ID"
    
    # Extract and setup files on server
    gcloud compute ssh "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$PROJECT_ID" \
        --command="
            sudo mkdir -p /opt/tradebot
            cd /opt/tradebot
            sudo tar -xzf /tmp/tradebot-app.tar.gz
            sudo chown -R ubuntu:ubuntu /opt/tradebot
            sudo chmod +x *.py
            
            # Create environment file from template
            if [ -f '.env.template' ] && [ ! -f '.env' ]; then
                cp .env.template .env
                echo 'Environment template copied to .env - please configure it'
            fi
            
            # Start services
            sudo systemctl start tradebot
            sudo systemctl start tradebot-health
        "
    
    # Cleanup
    rm -f tradebot-app.tar.gz
    
    log_success "Application files uploaded and services started"
}

setup_ssl() {
    if [ -z "$DOMAIN_NAME" ] || [ -z "$SSL_EMAIL" ]; then
        log_warning "Domain name or SSL email not provided, skipping SSL setup"
        return 0
    fi
    
    log_info "Setting up SSL certificate for $DOMAIN_NAME..."
    
    # Wait for services to be ready
    sleep 120
    
    # Setup SSL certificate
    gcloud compute ssh "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --project="$PROJECT_ID" \
        --command="
            sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email $SSL_EMAIL
            sudo systemctl reload nginx
        "
    
    log_success "SSL certificate configured for $DOMAIN_NAME"
}

setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Create alerting policy for instance health
    cat > alerting-policy.json << EOF
{
  "displayName": "TradeBot Instance Health",
  "conditions": [
    {
      "displayName": "VM Instance down",
      "conditionThreshold": {
        "filter": "resource.type=\"gce_instance\" AND resource.labels.instance_id=\"$INSTANCE_NAME\"",
        "comparison": "COMPARISON_EQUAL",
        "thresholdValue": 0,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_MEAN",
            "crossSeriesReducer": "REDUCE_MEAN"
          }
        ]
      }
    }
  ],
  "combiner": "OR",
  "enabled": true
}
EOF
    
    log_success "Monitoring setup completed"
}

show_deployment_summary() {
    log_success "\n=== TradeBot Sentinel GCP Deployment Complete ==="
    echo ""
    echo "Project ID: $PROJECT_ID"
    echo "Instance Name: $INSTANCE_NAME"
    echo "Zone: $ZONE"
    echo "External IP: $EXTERNAL_IP"
    echo "SSH Command: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
    echo ""
    echo "Application URLs:"
    echo "  Main App: http://$EXTERNAL_IP:8000"
    echo "  Health Check: http://$EXTERNAL_IP/health"
    
    if [ -n "$DOMAIN_NAME" ]; then
        echo "  Domain: https://$DOMAIN_NAME"
    fi
    
    echo ""
    echo "Google Cloud Console:"
    echo "  VM Instances: https://console.cloud.google.com/compute/instances?project=$PROJECT_ID"
    echo "  Logs: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
    echo "  Monitoring: https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
    echo ""
    echo "Next Steps:"
    echo "1. SSH to the server and configure .env file with your credentials"
    echo "2. Restart the TradeBot service: sudo systemctl restart tradebot"
    echo "3. Monitor logs: sudo journalctl -u tradebot -f"
    echo "4. Check health: curl http://$EXTERNAL_IP/health"
    echo "5. View startup logs: sudo tail -f /var/log/startup-script.log"
    echo ""
    echo "Important Files:"
    echo "  - Deployment Info: deployment-info.json"
    echo "  - Startup Script: startup-script.sh"
    echo ""
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    
    # Delete instance if it was created
    if gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" &> /dev/null; then
        log_info "Deleting instance $INSTANCE_NAME..."
        gcloud compute instances delete "$INSTANCE_NAME" --zone="$ZONE" --project="$PROJECT_ID" --quiet || true
    fi
    
    # Remove temporary files
    rm -f startup-script.sh tradebot-app.tar.gz alerting-policy.json
    
    exit 1
}

# Main deployment function
main() {
    log_info "Starting TradeBot Sentinel GCP deployment..."
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Load configuration
    load_config "$@"
    
    # Check dependencies
    check_dependencies
    
    # Setup GCP project
    setup_project
    
    # Create network infrastructure
    create_network
    create_firewall_rules
    
    # Create startup script
    create_startup_script
    
    # Create VM instance
    create_instance
    
    # Get instance information
    get_instance_info
    
    # Upload application files
    upload_files
    
    # Setup SSL if domain provided
    setup_ssl
    
    # Setup monitoring
    setup_monitoring
    
    # Show deployment summary
    show_deployment_summary
    
    # Cleanup temporary files
    rm -f startup-script.sh alerting-policy.json
    
    log_success "TradeBot Sentinel deployed successfully on GCP!"
}

# Run main function with all arguments
main "$@"