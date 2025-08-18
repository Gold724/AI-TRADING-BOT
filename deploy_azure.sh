#!/bin/bash

# TradeBot Sentinel - Azure Deployment Script
# Automated deployment to Azure Virtual Machines

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="tradebot-sentinel"
RESOURCE_GROUP="tradebot-rg"
LOCATION="eastus"
VM_NAME="tradebot-vm"
VM_SIZE="Standard_B2s"
VM_IMAGE="Ubuntu2204"
ADMIN_USERNAME="azureuser"
SSH_KEY_PATH="~/.ssh/id_rsa.pub"
DOMAIN_NAME=""
SSL_EMAIL=""
INSTALL_MONITORING="true"
SETUP_FIREWALL="true"
ENABLE_AUTO_UPDATES="true"
ENABLE_BACKUP="true"
TAGS="Environment=Production Project=TradeBotSentinel"

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
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Please install Azure CLI."
        log_info "Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install jq for JSON processing."
        exit 1
    fi
    
    # Check SSH key
    if [ ! -f "$SSH_KEY_PATH" ]; then
        log_error "SSH public key not found at $SSH_KEY_PATH"
        log_info "Generate SSH key: ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa"
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
            --resource-group)
                RESOURCE_GROUP="$2"
                shift 2
                ;;
            --location)
                LOCATION="$2"
                shift 2
                ;;
            --vm-name)
                VM_NAME="$2"
                shift 2
                ;;
            --vm-size)
                VM_SIZE="$2"
                shift 2
                ;;
            --admin-user)
                ADMIN_USERNAME="$2"
                shift 2
                ;;
            --ssh-key)
                SSH_KEY_PATH="$2"
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
            --no-monitoring)
                INSTALL_MONITORING="false"
                shift
                ;;
            --no-firewall)
                SETUP_FIREWALL="false"
                shift
                ;;
            --no-auto-updates)
                ENABLE_AUTO_UPDATES="false"
                shift
                ;;
            --no-backup)
                ENABLE_BACKUP="false"
                shift
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
    
    log_info "Resource Group: $RESOURCE_GROUP"
    log_info "Location: $LOCATION"
    log_info "VM Name: $VM_NAME"
    log_info "VM Size: $VM_SIZE"
}

show_help() {
    echo "TradeBot Sentinel Azure Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --resource-group NAME    Azure resource group name (default: tradebot-rg)"
    echo "  --location LOCATION      Azure region (default: eastus)"
    echo "  --vm-name NAME           Virtual machine name (default: tradebot-vm)"
    echo "  --vm-size SIZE           VM size (default: Standard_B2s)"
    echo "  --admin-user USER        Admin username (default: azureuser)"
    echo "  --ssh-key PATH           Path to SSH public key (default: ~/.ssh/id_rsa.pub)"
    echo "  --domain DOMAIN          Domain name for SSL certificate"
    echo "  --ssl-email EMAIL        Email for Let's Encrypt SSL certificate"
    echo "  --no-monitoring          Skip monitoring setup"
    echo "  --no-firewall            Skip firewall configuration"
    echo "  --no-auto-updates        Skip automatic updates setup"
    echo "  --no-backup              Skip backup configuration"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --resource-group my-rg --location westus2"
    echo "  $0 --vm-size Standard_B4ms --domain tradebot.example.com"
}

check_azure_login() {
    log_info "Checking Azure login status..."
    
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    
    log_info "Logged in to Azure subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
}

create_resource_group() {
    log_info "Creating resource group..."
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_warning "Resource group $RESOURCE_GROUP already exists"
    else
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --tags $TAGS
        
        log_success "Resource group $RESOURCE_GROUP created"
    fi
}

create_network_security_group() {
    log_info "Creating network security group..."
    
    NSG_NAME="${VM_NAME}-nsg"
    
    # Create NSG
    az network nsg create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$NSG_NAME" \
        --location "$LOCATION" \
        --tags $TAGS
    
    # Allow SSH
    az network nsg rule create \
        --resource-group "$RESOURCE_GROUP" \
        --nsg-name "$NSG_NAME" \
        --name "AllowSSH" \
        --protocol tcp \
        --priority 1000 \
        --destination-port-range 22 \
        --access allow
    
    # Allow HTTP
    az network nsg rule create \
        --resource-group "$RESOURCE_GROUP" \
        --nsg-name "$NSG_NAME" \
        --name "AllowHTTP" \
        --protocol tcp \
        --priority 1001 \
        --destination-port-range 80 \
        --access allow
    
    # Allow HTTPS
    az network nsg rule create \
        --resource-group "$RESOURCE_GROUP" \
        --nsg-name "$NSG_NAME" \
        --name "AllowHTTPS" \
        --protocol tcp \
        --priority 1002 \
        --destination-port-range 443 \
        --access allow
    
    # Allow application port
    az network nsg rule create \
        --resource-group "$RESOURCE_GROUP" \
        --nsg-name "$NSG_NAME" \
        --name "AllowApp" \
        --protocol tcp \
        --priority 1003 \
        --destination-port-range 8000 \
        --access allow
    
    # Allow health check port
    az network nsg rule create \
        --resource-group "$RESOURCE_GROUP" \
        --nsg-name "$NSG_NAME" \
        --name "AllowHealth" \
        --protocol tcp \
        --priority 1004 \
        --destination-port-range 8001 \
        --access allow
    
    log_success "Network security group $NSG_NAME created with rules"
}

create_virtual_network() {
    log_info "Creating virtual network..."
    
    VNET_NAME="${VM_NAME}-vnet"
    SUBNET_NAME="${VM_NAME}-subnet"
    
    # Create VNet
    az network vnet create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$VNET_NAME" \
        --address-prefix 10.0.0.0/16 \
        --subnet-name "$SUBNET_NAME" \
        --subnet-prefix 10.0.1.0/24 \
        --location "$LOCATION" \
        --tags $TAGS
    
    log_success "Virtual network $VNET_NAME created"
}

create_public_ip() {
    log_info "Creating public IP..."
    
    PUBLIC_IP_NAME="${VM_NAME}-ip"
    
    az network public-ip create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$PUBLIC_IP_NAME" \
        --allocation-method Static \
        --sku Standard \
        --location "$LOCATION" \
        --tags $TAGS
    
    PUBLIC_IP=$(az network public-ip show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$PUBLIC_IP_NAME" \
        --query ipAddress -o tsv)
    
    log_success "Public IP $PUBLIC_IP_NAME created: $PUBLIC_IP"
}

create_network_interface() {
    log_info "Creating network interface..."
    
    NIC_NAME="${VM_NAME}-nic"
    VNET_NAME="${VM_NAME}-vnet"
    SUBNET_NAME="${VM_NAME}-subnet"
    NSG_NAME="${VM_NAME}-nsg"
    PUBLIC_IP_NAME="${VM_NAME}-ip"
    
    az network nic create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$NIC_NAME" \
        --vnet-name "$VNET_NAME" \
        --subnet "$SUBNET_NAME" \
        --public-ip-address "$PUBLIC_IP_NAME" \
        --network-security-group "$NSG_NAME" \
        --location "$LOCATION" \
        --tags $TAGS
    
    log_success "Network interface $NIC_NAME created"
}

create_startup_script() {
    log_info "Creating startup script..."
    
    cat > azure_startup.sh << 'EOF'
#!/bin/bash

# TradeBot Sentinel Azure VM Startup Script

set -e

# Configuration from environment
INSTALL_MONITORING=${INSTALL_MONITORING:-true}
SETUP_FIREWALL=${SETUP_FIREWALL:-true}
ENABLE_AUTO_UPDATES=${ENABLE_AUTO_UPDATES:-true}
DOMAIN_NAME=${DOMAIN_NAME:-""}
SSL_EMAIL=${SSL_EMAIL:-""}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a /var/log/tradebot-setup.log
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a /var/log/tradebot-setup.log
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a /var/log/tradebot-setup.log
}

# Update system
log_info "Updating system packages..."
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git htop unzip jq software-properties-common apt-transport-https ca-certificates gnupg lsb-release python3 python3-pip python3-venv python3-dev nginx

# Install Docker
log_info "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker $ADMIN_USERNAME

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker
systemctl enable docker
systemctl start docker

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Create application directory
mkdir -p /opt/tradebot/{logs,screenshots,data,config,backups}

# Create application user
if ! id "tradebot" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/tradebot tradebot
fi

# Setup Python environment
python3 -m venv /opt/tradebot/venv
source /opt/tradebot/venv/bin/activate
pip install --upgrade pip
pip install playwright requests psutil schedule python-telegram-bot curlconverter flask gunicorn azure-identity azure-storage-blob azure-monitor-opentelemetry

# Install Playwright browsers
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

# Set permissions
chown -R tradebot:tradebot /opt/tradebot
chmod -R 755 /opt/tradebot

# Create systemd services
cat > /etc/systemd/system/tradebot.service << 'EOFSERVICE'
[Unit]
Description=TradeBot Sentinel
After=network.target

[Service]
Type=simple
User=tradebot
Group=tradebot
WorkingDirectory=/opt/tradebot
Environment=PYTHONPATH=/opt/tradebot
Environment=PATH=/opt/tradebot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/tradebot/venv/bin/python /opt/tradebot/tradebot_sentinel.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOFSERVICE

cat > /etc/systemd/system/tradebot-health.service << 'EOFHEALTHSERVICE'
[Unit]
Description=TradeBot Health Check Endpoint
After=network.target

[Service]
Type=simple
User=tradebot
Group=tradebot
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

# Configure Nginx
cat > /etc/nginx/sites-available/tradebot << 'EOFNGINX'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=health:10m rate=30r/s;
    
    # Main application
    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        proxy_buffering off;
    }
    
    # Health check endpoint
    location /health {
        limit_req zone=health burst=10 nodelay;
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        access_log off;
    }
    
    # Azure health probe
    location /azure-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOFNGINX

# Enable Nginx site
ln -sf /etc/nginx/sites-available/tradebot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Setup firewall
if [ "$SETUP_FIREWALL" = "true" ]; then
    log_info "Setting up firewall..."
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    ufw allow 8001/tcp
    ufw --force enable
fi

# Setup monitoring with Azure Monitor
if [ "$INSTALL_MONITORING" = "true" ]; then
    log_info "Setting up Azure monitoring..."
    
    # Install Azure Monitor Agent
    wget https://aka.ms/azcmagent -O ~/install_linux_azcmagent.sh
    bash ~/install_linux_azcmagent.sh
    
    # Create monitoring script
    cat > /opt/tradebot/azure_monitor.py << 'EOFMONITOR'
#!/usr/bin/env python3
import time
import requests
import subprocess
import logging
import psutil
import json
from datetime import datetime
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.identity import DefaultAzureCredential

# Configure Azure Monitor
try:
    configure_azure_monitor()
except Exception as e:
    print(f"Azure Monitor configuration failed: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/tradebot/logs/azure_monitor.log'),
        logging.StreamHandler()
    ]
)
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
                logger.info(f"Restarted service {service}")
        except Exception as e:
            logger.error(f"Error checking service {service}: {e}")

def send_azure_metrics():
    """Send custom metrics to Azure Monitor"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics
        health_status = 0
        try:
            response = requests.get('http://localhost:8001/health', timeout=5)
            health_status = 1 if response.status_code == 200 else 0
        except:
            pass
        
        # Log metrics (Azure Monitor will collect these)
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'health_status': health_status
        }
        
        logger.info(f"Azure metrics: {json.dumps(metrics)}")
        
    except Exception as e:
        logger.error(f"Azure metrics error: {e}")

if __name__ == '__main__':
    logger.info("Starting TradeBot Azure monitoring")
    while True:
        try:
            check_services()
            send_azure_metrics()
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        
        time.sleep(60)  # Check every minute
EOFMONITOR
    
    chmod +x /opt/tradebot/azure_monitor.py
    
    # Create monitoring service
    cat > /etc/systemd/system/tradebot-azure-monitor.service << 'EOFMONITORSERVICE'
[Unit]
Description=TradeBot Azure Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tradebot
Environment=PYTHONPATH=/opt/tradebot
Environment=PATH=/opt/tradebot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/tradebot/venv/bin/python /opt/tradebot/azure_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOFMONITORSERVICE
    
    systemctl daemon-reload
    systemctl enable tradebot-azure-monitor
fi

# Setup automatic updates
if [ "$ENABLE_AUTO_UPDATES" = "true" ]; then
    log_info "Setting up automatic updates..."
    apt-get install -y unattended-upgrades
    
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOFUPDATES'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
EOFUPDATES
    
    echo 'APT::Periodic::Update-Package-Lists "1";' > /etc/apt/apt.conf.d/20auto-upgrades
    echo 'APT::Periodic::Unattended-Upgrade "1";' >> /etc/apt/apt.conf.d/20auto-upgrades
fi

# Setup SSL certificate
if [ -n "$DOMAIN_NAME" ] && [ -n "$SSL_EMAIL" ]; then
    log_info "Setting up SSL certificate for $DOMAIN_NAME..."
    apt-get install -y certbot python3-certbot-nginx
    certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "$SSL_EMAIL"
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
fi

# Setup log rotation
cat > /etc/logrotate.d/tradebot << 'EOFLOGROTATE'
/opt/tradebot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 tradebot tradebot
    postrotate
        systemctl reload tradebot
        systemctl reload tradebot-health
    endscript
}
EOFLOGROTATE

# Enable services
systemctl daemon-reload
systemctl enable tradebot
systemctl enable tradebot-health
systemctl enable nginx

# Start services
systemctl start nginx

log_success "TradeBot Sentinel Azure VM setup completed!"

# Create status file
echo "Setup completed at $(date)" > /opt/tradebot/setup_complete.txt
EOF

    log_success "Startup script created"
}

create_virtual_machine() {
    log_info "Creating virtual machine..."
    
    NIC_NAME="${VM_NAME}-nic"
    
    # Encode startup script
    CUSTOM_DATA=$(base64 -w 0 azure_startup.sh)
    
    az vm create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$VM_NAME" \
        --image "$VM_IMAGE" \
        --size "$VM_SIZE" \
        --admin-username "$ADMIN_USERNAME" \
        --ssh-key-values "$SSH_KEY_PATH" \
        --nics "$NIC_NAME" \
        --custom-data azure_startup.sh \
        --location "$LOCATION" \
        --tags $TAGS \
        --no-wait
    
    log_info "VM creation initiated. Waiting for completion..."
    
    # Wait for VM to be created
    az vm wait \
        --resource-group "$RESOURCE_GROUP" \
        --name "$VM_NAME" \
        --created \
        --timeout 600
    
    log_success "Virtual machine $VM_NAME created"
}

setup_backup() {
    if [ "$ENABLE_BACKUP" != "true" ]; then
        log_info "Skipping backup setup"
        return 0
    fi
    
    log_info "Setting up Azure Backup..."
    
    VAULT_NAME="${VM_NAME}-vault"
    
    # Create Recovery Services vault
    az backup vault create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$VAULT_NAME" \
        --location "$LOCATION" \
        --tags $TAGS
    
    # Enable backup for VM
    az backup protection enable-for-vm \
        --resource-group "$RESOURCE_GROUP" \
        --vault-name "$VAULT_NAME" \
        --vm "$VM_NAME" \
        --policy-name "DefaultPolicy"
    
    log_success "Azure Backup configured for $VM_NAME"
}

upload_application_files() {
    log_info "Uploading application files..."
    
    # Wait for VM to be fully ready
    log_info "Waiting for VM to be ready..."
    sleep 60
    
    # Get VM IP
    PUBLIC_IP_NAME="${VM_NAME}-ip"
    VM_IP=$(az network public-ip show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$PUBLIC_IP_NAME" \
        --query ipAddress -o tsv)
    
    # Test SSH connection
    SSH_OPTS="-o ConnectTimeout=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    log_info "Testing SSH connection to $VM_IP..."
    
    # Wait for SSH to be available
    for i in {1..30}; do
        if ssh $SSH_OPTS "$ADMIN_USERNAME@$VM_IP" "echo 'SSH ready'" &> /dev/null; then
            log_success "SSH connection established"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "SSH connection failed after 30 attempts"
            exit 1
        fi
        
        log_info "Waiting for SSH... (attempt $i/30)"
        sleep 10
    done
    
    # Create tar archive of application files
    tar -czf tradebot-app.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='screenshots/*.png' \
        --exclude='venv' \
        --exclude='node_modules' \
        *.py *.yml *.yaml *.txt *.md *.env.template Dockerfile* docker-compose* requirements.txt 2>/dev/null || true
    
    # Upload files
    scp $SSH_OPTS tradebot-app.tar.gz "$ADMIN_USERNAME@$VM_IP":/tmp/
    
    # Extract and setup files on server
    ssh $SSH_OPTS "$ADMIN_USERNAME@$VM_IP" "
        sudo mkdir -p /opt/tradebot
        cd /opt/tradebot
        sudo tar -xzf /tmp/tradebot-app.tar.gz
        sudo chown -R tradebot:tradebot /opt/tradebot
        sudo chmod +x *.py
        
        # Create environment file from template
        if [ -f '.env.template' ] && [ ! -f '.env' ]; then
            sudo cp .env.template .env
            echo 'Environment template copied to .env - please configure it'
        fi
        
        # Wait for setup to complete
        while [ ! -f '/opt/tradebot/setup_complete.txt' ]; do
            echo 'Waiting for VM setup to complete...'
            sleep 10
        done
        
        # Start services
        sudo systemctl start tradebot
        sudo systemctl start tradebot-health
        
        if [ '$INSTALL_MONITORING' = 'true' ]; then
            sudo systemctl start tradebot-azure-monitor
        fi
    "
    
    # Cleanup
    rm -f tradebot-app.tar.gz azure_startup.sh
    
    log_success "Application files uploaded and services started"
}

show_deployment_summary() {
    log_success "\n=== TradeBot Sentinel Azure Deployment Complete ==="
    
    PUBLIC_IP_NAME="${VM_NAME}-ip"
    VM_IP=$(az network public-ip show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$PUBLIC_IP_NAME" \
        --query ipAddress -o tsv)
    
    echo ""
    echo "Azure Resources:"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  VM Name: $VM_NAME"
    echo "  VM Size: $VM_SIZE"
    echo "  Location: $LOCATION"
    echo "  Public IP: $VM_IP"
    echo ""
    echo "SSH Access:"
    echo "  ssh $ADMIN_USERNAME@$VM_IP"
    echo ""
    echo "Application URLs:"
    echo "  Main App: http://$VM_IP"
    echo "  Health Check: http://$VM_IP/health"
    echo "  Azure Health: http://$VM_IP/azure-health"
    
    if [ -n "$DOMAIN_NAME" ]; then
        echo "  Domain: https://$DOMAIN_NAME"
    fi
    
    echo ""
    echo "Azure Services:"
    echo "  Virtual Machine: $VM_NAME"
    echo "  Network Security Group: ${VM_NAME}-nsg"
    echo "  Virtual Network: ${VM_NAME}-vnet"
    echo "  Public IP: ${VM_NAME}-ip"
    
    if [ "$ENABLE_BACKUP" = "true" ]; then
        echo "  Recovery Vault: ${VM_NAME}-vault"
    fi
    
    echo ""
    echo "Installed Services:"
    echo "  - TradeBot Sentinel (systemctl status tradebot)"
    echo "  - Health Check Endpoint (systemctl status tradebot-health)"
    echo "  - Nginx (systemctl status nginx)"
    
    if [ "$INSTALL_MONITORING" = "true" ]; then
        echo "  - Azure Monitor (systemctl status tradebot-azure-monitor)"
    fi
    
    echo ""
    echo "Next Steps:"
    echo "1. SSH to the server: ssh $ADMIN_USERNAME@$VM_IP"
    echo "2. Configure .env file: sudo nano /opt/tradebot/.env"
    echo "3. Restart services: sudo systemctl restart tradebot tradebot-health"
    echo "4. Monitor logs: sudo journalctl -u tradebot -f"
    echo "5. Check health: curl http://$VM_IP/health"
    echo "6. View Azure metrics in Azure Monitor"
    echo ""
    echo "Azure Management:"
    echo "  View resources: az resource list --resource-group $RESOURCE_GROUP --output table"
    echo "  VM status: az vm show --resource-group $RESOURCE_GROUP --name $VM_NAME --show-details"
    echo "  Stop VM: az vm stop --resource-group $RESOURCE_GROUP --name $VM_NAME"
    echo "  Start VM: az vm start --resource-group $RESOURCE_GROUP --name $VM_NAME"
    echo "  Delete resources: az group delete --name $RESOURCE_GROUP --yes --no-wait"
    echo ""
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    
    # Remove temporary files
    rm -f azure_startup.sh tradebot-app.tar.gz
    
    # Optionally clean up Azure resources
    read -p "Do you want to delete the resource group $RESOURCE_GROUP? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting resource group $RESOURCE_GROUP..."
        az group delete --name "$RESOURCE_GROUP" --yes --no-wait
        log_info "Resource group deletion initiated"
    fi
    
    exit 1
}

# Main deployment function
main() {
    log_info "Starting TradeBot Sentinel Azure deployment..."
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Load configuration
    load_config "$@"
    
    # Check dependencies
    check_dependencies
    
    # Check Azure login
    check_azure_login
    
    # Create Azure resources
    create_resource_group
    create_network_security_group
    create_virtual_network
    create_public_ip
    create_network_interface
    
    # Create startup script and VM
    create_startup_script
    create_virtual_machine
    
    # Setup backup
    setup_backup
    
    # Upload application files
    upload_application_files
    
    # Show deployment summary
    show_deployment_summary
    
    log_success "TradeBot Sentinel deployed successfully to Azure!"
}

# Run main function with all arguments
main "$@"