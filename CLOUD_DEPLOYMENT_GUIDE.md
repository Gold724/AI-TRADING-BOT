# 🚀 AI Trading Sentinel - Complete Cloud Deployment Guide

## Architecture Overview

Your AI Trading Sentinel has **3 main components**:

1. **React Frontend** (`/frontend`) - Modern UI dashboard (Port 3000/5173)
2. **Flask Backend API** (`backend_main.py`) - Core trading API (Port 5000) 
3. **Bulenox Sentinel** (`bulenox_sentinel.py`) - Project X control panel (Port 8090)

## 🌐 Cloud Deployment Options

### Option 1: Single VPS Deployment (Recommended)

**Contabo VPS Setup:**
- **OS:** Ubuntu 22.04 LTS
- **RAM:** 8GB+ (for browser automation)
- **Storage:** 50GB SSD
- **CPU:** 4+ cores

### Option 2: Multi-Service Architecture

**Frontend:** Vercel/Netlify (Static hosting)
**Backend:** Contabo VPS (API + Trading bot)
**Database:** PostgreSQL/MongoDB Atlas

# 🚀 TradeBot Sentinel - Comprehensive Cloud Deployment Guide

## 📋 Overview
Deploy your TradeBot Sentinel to various cloud platforms for 24/7 headless operation, ensuring continuous automated trading with robust monitoring, scaling, and security features.

### 🎯 What This Guide Covers
- **Multi-cloud deployment** (AWS, GCP, Azure, VPS providers)
- **Docker containerization** with production-ready configurations
- **Security hardening** and credential management
- **Monitoring & alerting** with Prometheus, Grafana, and Loki
- **Auto-scaling** and high availability setup
- **Cost optimization** strategies
- **Troubleshooting** and maintenance procedures

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your Laptop   │    │   GitHub Repo    │    │  Contabo VPS    │
│                 │    │                  │    │                 │
│ • Development   │───▶│ • Code Storage   │───▶│ • 24/7 Trading  │
│ • Testing       │    │ • Version Control│    │ • Auto-restart  │
│ • Monitoring    │    │ • CI/CD Pipeline │    │ • Logging       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               ▲
         │              ┌──────────────────┐             │
         └─────────────▶│   Termius SSH    │─────────────┘
                        │                  │
                        │ • Remote Access  │
                        │ • File Transfer  │
                        │ • Monitoring     │
                        └──────────────────┘
```

## 🚀 Quick Start Options

### Option 1: Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/Gold724/AI-TRADING-BOT.git
cd AI-TRADING-BOT

# Build and run with Docker
docker build -t tradebot-sentinel .
docker run -d --name tradebot-sentinel --env-file .env -p 5000:5000 --restart unless-stopped tradebot-sentinel
```

### Option 2: Direct VPS Deployment

```bash
# Use existing deployment scripts
./trae_deploy.sh --vps-ip "your-server-ip" --vps-user "ubuntu" --ssh-key "~/.ssh/your-key.pem"
```

### Option 3: Environment Setup

```bash
# Interactive environment configuration
python setup_environment.py

# Cloud-specific setup
python setup_environment.py --cloud-provider aws

# Validate configuration
python setup_environment.py --validate-only
```

## 🔧 Prerequisites

### Required Software
- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Python** (v3.9+) with pip
- **Git** for version control
- **SSH client** for secure server access

### Required Accounts
- **Bulenox trading platform** account with API access
- **Cloud provider** account (AWS, GCP, Azure, or VPS provider)
- **Domain name** (recommended for production)
- **SSL certificate** (Let's Encrypt recommended)

### Required Knowledge
- Basic Docker and containerization concepts
- Cloud provider fundamentals
- Linux command line basics
- Environment variable management

## ☁️ Cloud Provider Options

### 🌩️ Amazon Web Services (AWS)

**Recommended Services:**
- **EC2**: t3.medium or t3.large instances
- **ECS**: For container orchestration
- **RDS**: PostgreSQL for data storage
- **ElastiCache**: Redis for caching
- **S3**: File storage and backups
- **CloudWatch**: Monitoring and logging
- **Route 53**: DNS management
- **Certificate Manager**: SSL certificates

**Deployment Steps:**

1. **Create EC2 Instance**
```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx
```

2. **Setup Security Groups**
```bash
# Create security group
aws ec2 create-security-group \
  --group-name tradebot-sg \
  --description "TradeBot Sentinel Security Group"

# Allow SSH (port 22)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Allow HTTP/HTTPS (ports 80, 443)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

### ☁️ Google Cloud Platform (GCP)

**Recommended Services:**
- **Compute Engine**: e2-standard-2 instances
- **Cloud Run**: Serverless container deployment
- **Cloud SQL**: PostgreSQL database
- **Memorystore**: Redis caching
- **Cloud Storage**: File storage
- **Cloud Monitoring**: Observability

**Deployment Steps:**

1. **Create VM Instance**
```bash
# Create instance
gcloud compute instances create tradebot-sentinel \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=http-server,https-server
```

2. **Deploy with Cloud Run**
```bash
# Build and push image
docker build -f Dockerfile.tradebot -t gcr.io/PROJECT-ID/tradebot-sentinel .
docker push gcr.io/PROJECT-ID/tradebot-sentinel

# Deploy to Cloud Run
gcloud run deploy tradebot-sentinel \
  --image gcr.io/PROJECT-ID/tradebot-sentinel \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1
```

### 🔷 Microsoft Azure

**Recommended Services:**
- **Virtual Machines**: Standard_B2s or Standard_D2s_v3
- **Container Instances**: For simple deployments
- **App Service**: Web app hosting
- **Database for PostgreSQL**: Managed database
- **Cache for Redis**: Caching layer

**Deployment Steps:**

1. **Create Resource Group**
```bash
az group create --name tradebot-rg --location eastus
```

2. **Create Virtual Machine**
```bash
az vm create \
  --resource-group tradebot-rg \
  --name tradebot-vm \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys
```

### 🖥️ VPS Providers (DigitalOcean, Linode, Vultr, Contabo)

**Recommended Specifications:**
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB recommended)
- **Storage**: 50GB+ SSD
- **Bandwidth**: Unlimited or 4TB+
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS

**DigitalOcean Deployment:**

1. **Create Droplet**
```bash
# Using doctl CLI
doctl compute droplet create tradebot-sentinel \
  --size s-2vcpu-4gb \
  --image ubuntu-20-04-x64 \
  --region nyc1 \
  --ssh-keys your-ssh-key-id
```

2. **Setup Server**
```bash
# SSH to droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

## 🐳 Docker Deployment

### Single Container Deployment

```bash
# Build the image
docker build -f Dockerfile.tradebot -t tradebot-sentinel .

# Run with environment file
docker run -d \
  --name tradebot \
  --restart unless-stopped \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/screenshots:/app/screenshots \
  tradebot-sentinel
```

### Docker Compose Deployment

```bash
# Deploy full stack
docker-compose -f docker-compose.tradebot.yml up -d

# View logs
docker-compose -f docker-compose.tradebot.yml logs -f tradebot

# Scale services
docker-compose -f docker-compose.tradebot.yml up -d --scale tradebot=2
```

## 🔒 Security Best Practices

### Server Security

1. **Update System**
```bash
# Regular updates
apt update && apt upgrade -y

# Enable automatic security updates
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

2. **Configure Firewall**
```bash
# Enable UFW
ufw enable

# Allow SSH
ufw allow ssh

# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Deny all other incoming
ufw default deny incoming
ufw default allow outgoing
```

3. **SSH Hardening**
```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Recommended settings:
# Port 2222  # Change default port
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# MaxAuthTries 3

# Restart SSH
systemctl restart sshd
```

### Application Security

1. **Use Strong Secrets**
```bash
# Generate strong passwords
openssl rand -base64 32

# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

2. **Enable HTTPS**
```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring & Logging

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'tradebot'
    static_configs:
      - targets: ['tradebot:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboards

1. **Import TradeBot Dashboard**
   - Dashboard ID: Create custom dashboard
   - Metrics: Trading performance, system health, error rates

2. **Key Metrics to Monitor**
   - Trade execution success rate
   - Response times
   - Memory and CPU usage
   - Error rates and types
   - Network connectivity

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: tradebot
    rules:
      - alert: TradeBotDown
        expr: up{job="tradebot"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "TradeBot is down"
          description: "TradeBot has been down for more than 1 minute"
      
      - alert: HighErrorRate
        expr: rate(tradebot_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
```

## 🔧 Troubleshooting

### Common Issues

1. **Browser Issues**
```bash
# Check Chrome installation
which google-chrome
google-chrome --version

# Install missing dependencies
apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0

# Test headless mode
xvfb-run -a google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://google.com
```

2. **Memory Issues**
```bash
# Check memory usage
free -h
docker stats

# Increase swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

3. **Network Issues**
```bash
# Test connectivity
curl -I https://bulenox.projectx.com
ping 8.8.8.8

# Check DNS
nslookup bulenox.com

# Test from container
docker exec tradebot curl -I https://bulenox.projectx.com
```

## 💰 Cost Optimization

### Cloud Provider Costs

**AWS Cost Optimization:**
- Use **Spot Instances** for non-critical workloads
- Enable **Auto Scaling** to handle variable loads
- Use **Reserved Instances** for predictable workloads
- Monitor with **AWS Cost Explorer**

**GCP Cost Optimization:**
- Use **Preemptible VMs** for cost savings
- Enable **Sustained Use Discounts**
- Use **Committed Use Contracts**
- Monitor with **Cloud Billing**

**Azure Cost Optimization:**
- Use **Spot VMs** for development/testing
- Enable **Auto-shutdown** for VMs
- Use **Reserved VM Instances**
- Monitor with **Cost Management**

### Resource Optimization

1. **Right-sizing**
```bash
# Monitor resource usage
docker stats --no-stream
htop
iotop
```

2. **Efficient Scheduling**
```python
# Run during off-peak hours
SCHEDULE_HOURS = [9, 10, 11, 14, 15, 16]  # Market hours only
TIMEZONE = 'US/Eastern'
```

---

**⚠️ Disclaimer:** Trading involves risk. This bot is for educational purposes. Always test thoroughly before using with real money.

**🔐 Security Notice:** Never commit credentials to version control. Always use secure environment variable management.

---

*Last updated: 2024-01-16*
*Version: 2.0.0*./deploy_aws.sh

# Google Cloud
./deploy_gcp.sh

# DigitalOcean
./deploy_digitalocean.sh
```

## 🌍 Cloud Platform Options

### 1. AWS EC2 (Enterprise Grade)

**Recommended Instance Types:**
- `t3.medium` (2 vCPU, 4GB RAM) - $30/month
- `t3.large` (2 vCPU, 8GB RAM) - $60/month
- `c5.large` (2 vCPU, 4GB RAM) - $70/month (CPU optimized)

**Setup Commands:**
```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx

# Deploy
./trae_deploy.sh --vps-ip "your-ec2-ip" --vps-user "ubuntu" --ssh-key "~/.ssh/your-key.pem"
```

### 2. Google Cloud Platform (AI/ML Optimized)

**Recommended Machine Types:**
- `e2-medium` (1 vCPU, 4GB RAM) - $25/month
- `e2-standard-2` (2 vCPU, 8GB RAM) - $50/month
- `n1-standard-2` (2 vCPU, 7.5GB RAM) - $55/month

**Setup Commands:**
```bash
# Create VM instance
gcloud compute instances create tradebot-sentinel \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud

# Deploy
EXTERNAL_IP=$(gcloud compute instances describe tradebot-sentinel --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
./trae_deploy.sh --vps-ip "$EXTERNAL_IP" --vps-user "ubuntu"
```

### 3. DigitalOcean (Developer Friendly)

**Recommended Droplet Sizes:**
- Basic: $12/month (2GB RAM, 1 vCPU)
- Standard: $24/month (4GB RAM, 2 vCPU)
- Premium: $48/month (8GB RAM, 4 vCPU)

**Setup Commands:**
```bash
# Create droplet
doctl compute droplet create tradebot-sentinel \
  --size s-2vcpu-4gb \
  --image ubuntu-22-04-x64 \
  --region nyc1

# Deploy
./trae_deploy.sh --vps-ip "your-droplet-ip" --vps-user "root"
```

### 4. Contabo VPS (Most Cost-Effective)

**Recommended Plans:**
- VPS S: €4.99/month (4GB RAM, 4 vCPU, 200GB SSD)
- VPS M: €8.99/month (8GB RAM, 6 vCPU, 400GB SSD)
- VPS L: €14.99/month (16GB RAM, 8 vCPU, 800GB SSD)

**Setup:**
```bash
# Use existing Contabo deployment script
./contabo_deploy.sh
```

### 5. Vast.ai (GPU Cloud for AI Trading)

**For AI-Enhanced Trading:**
- GPU instances starting at $0.20/hour
- Perfect for machine learning models
- Preemptible instances for cost savings

```bash
# Deploy to Vast.ai
python3 deploy_to_vast.py
```

## 🐳 Docker Deployment (Production Ready)

### Optimized Multi-Stage Dockerfile

Our production `Dockerfile` includes:
- Ubuntu 22.04 base with security updates
- Headless Chrome/Chromium with GPU acceleration disabled
- Virtual display (Xvfb) for browser automation
- Supervisor for process management
- Non-root user for enhanced security
- Health checks and monitoring

### Docker Compose for Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  tradebot-sentinel:
    build: .
    container_name: tradebot-sentinel
    restart: unless-stopped
    environment:
      - HEADLESS=true
      - ENVIRONMENT=production
      - DISPLAY=:99
    env_file: .env
    ports:
      - "5000:5000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./screenshots:/app/screenshots
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    container_name: tradebot-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    container_name: tradebot-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - tradebot-sentinel

volumes:
  redis_data:
```

### Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f tradebot-sentinel

# Scale horizontally
docker-compose up -d --scale tradebot-sentinel=3

# Update deployment
docker-compose pull && docker-compose up -d
```

### 2. GitHub Repository Setup

**Create Deploy Keys:**
```bash
# Generate SSH key for GitHub access
ssh-keygen -t ed25519 -C "trading-bot@contabo-vps" -f ~/.ssh/github_deploy

# Add to GitHub repository settings > Deploy keys
cat ~/.ssh/github_deploy.pub
```

**Clone Repository:**
```bash
# Clone your trading bot repository
git clone git@github.com:yourusername/ai-trading-sentinel.git
cd ai-trading-sentinel

# Set up SSH config for GitHub
echo "Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_deploy" >> ~/.ssh/config
```

### 3. Environment Setup

**Install Python Dependencies:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browsers
playwright install
playwright install-deps
```

**Set Environment Variables:**
```bash
# Create environment file
cat > .env << EOF
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=XujhMzFf6K
ENVIRONMENT=production
HEADLESS=true
LOG_LEVEL=INFO
EOF

# Make it secure
chmod 600 .env
```

### 4. Systemd Service Configuration

**Create Service File:**
```bash
sudo tee /etc/systemd/system/trading-sentinel.service << EOF
[Unit]
Description=AI Trading Sentinel
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/ai-trading-sentinel
Environment=PATH=/home/$USER/ai-trading-sentinel/venv/bin
EnvironmentFile=/home/$USER/ai-trading-sentinel/.env
ExecStart=/home/$USER/ai-trading-sentinel/venv/bin/python tradebot_sentinel_advanced_pro.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-sentinel

[Install]
WantedBy=multi-user.target
EOF
```

**Enable and Start Service:**
```bash
# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable trading-sentinel.service
sudo systemctl start trading-sentinel.service

# Check status
sudo systemctl status trading-sentinel.service
```

### 5. Auto-Update System

**Create Update Script:**
```bash
cat > update_bot.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Updating AI Trading Sentinel..."

# Navigate to project directory
cd /home/$USER/ai-trading-sentinel

# Pull latest changes
git fetch origin
LATEST_COMMIT=$(git rev-parse origin/main)
CURRENT_COMMIT=$(git rev-parse HEAD)

if [ "$LATEST_COMMIT" != "$CURRENT_COMMIT" ]; then
    echo "📥 New updates found, pulling changes..."
    
    # Stop the service
    sudo systemctl stop trading-sentinel.service
    
    # Pull updates
    git pull origin main
    
    # Update dependencies if requirements changed
    if git diff --name-only HEAD~1 HEAD | grep -q requirements.txt; then
        echo "📦 Updating dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Restart the service
    sudo systemctl start trading-sentinel.service
    
    echo "✅ Update completed successfully!"
else
    echo "✅ Already up to date!"
fi
EOF

chmod +x update_bot.sh
```

**Setup Cron Job for Auto-Updates:**
```bash
# Add to crontab (check for updates every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/$USER/ai-trading-sentinel/update_bot.sh >> /home/$USER/update.log 2>&1") | crontab -
```

### 6. Monitoring and Logging

**Create Monitoring Script:**
```bash
cat > monitor.sh << 'EOF'
#!/bin/bash

# Check service status
echo "=== Service Status ==="
sudo systemctl status trading-sentinel.service --no-pager

echo -e "\n=== Recent Logs ==="
sudo journalctl -u trading-sentinel.service -n 20 --no-pager

echo -e "\n=== System Resources ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.2f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo -e "\n=== Network Status ==="
ping -c 1 bulenox.projectx.com > /dev/null && echo "✅ Trading platform reachable" || echo "❌ Trading platform unreachable"
EOF

chmod +x monitor.sh
```

**Log Rotation:**
```bash
sudo tee /etc/logrotate.d/trading-sentinel << EOF
/home/$USER/ai-trading-sentinel/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
```

### 7. Termius Configuration

**SSH Key Setup:**
1. Generate SSH key pair in Termius
2. Add public key to VPS: `~/.ssh/authorized_keys`
3. Configure connection in Termius:
   - **Host**: Your Contabo VPS IP
   - **Username**: Your VPS username
   - **Port**: 22 (or custom if changed)
   - **Authentication**: SSH Key

**Useful Termius Snippets:**
```bash
# Quick status check
sudo systemctl status trading-sentinel.service

# View live logs
sudo journalctl -u trading-sentinel.service -f

# Restart service
sudo systemctl restart trading-sentinel.service

# Check system resources
htop

# Update bot
./update_bot.sh

# Monitor script
./monitor.sh
```

## 🔒 Security Best Practices

### 1. Firewall Configuration
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (change port if using custom)
sudo ufw allow 22/tcp

# Allow outbound HTTPS (for trading platform)
sudo ufw allow out 443/tcp

# Deny all other incoming connections
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### 2. SSH Hardening
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Recommended settings:
# Port 2222  # Change default port
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# MaxAuthTries 3

# Restart SSH service
sudo systemctl restart sshd
```

### 3. Fail2Ban Protection
```bash
# Install and configure Fail2Ban
sudo apt install fail2ban -y

sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📊 Monitoring Dashboard

**Create Simple Web Dashboard:**
```python
# dashboard.py
from flask import Flask, render_template_string
import subprocess
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Get service status
    status = subprocess.run(['systemctl', 'is-active', 'trading-sentinel.service'], 
                          capture_output=True, text=True).stdout.strip()
    
    # Get recent logs
    logs = subprocess.run(['journalctl', '-u', 'trading-sentinel.service', '-n', '10', '--no-pager'], 
                         capture_output=True, text=True).stdout
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Trading Sentinel - Status</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .active { background: #2d5a2d; }
            .inactive { background: #5a2d2d; }
            .logs { background: #2a2a2a; padding: 15px; border-radius: 5px; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>🤖 AI Trading Sentinel Status</h1>
        <div class="status {{ 'active' if status == 'active' else 'inactive' }}">
            <h2>Service Status: {{ status.upper() }}</h2>
            <p>Last Updated: {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
        </div>
        <h2>Recent Logs:</h2>
        <div class="logs">
            <pre>{{ logs }}</pre>
        </div>
    </body>
    </html>
    ''', status=status, logs=logs, datetime=datetime)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## 🚨 Emergency Procedures

### 1. Emergency Stop
```bash
# Stop trading immediately
sudo systemctl stop trading-sentinel.service

# Disable auto-restart
sudo systemctl disable trading-sentinel.service
```

### 2. Emergency Recovery
```bash
# Reset to last known good state
git reset --hard HEAD~1

# Restart service
sudo systemctl start trading-sentinel.service
```

### 3. Backup and Restore
```bash
# Create backup
tar -czf trading-bot-backup-$(date +%Y%m%d).tar.gz ai-trading-sentinel/

# Restore from backup
tar -xzf trading-bot-backup-YYYYMMDD.tar.gz
```

## 📱 Mobile Monitoring

**Termius Mobile App:**
- Install Termius on your phone
- Sync your VPS connection
- Set up quick commands for monitoring
- Enable push notifications for connection issues

**Telegram Bot (Optional):**
```python
# telegram_notifier.py
import requests

def send_telegram_message(message):
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    requests.post(url, json=payload)

# Usage in your trading bot
send_telegram_message("🚀 Trading bot started successfully!")
send_telegram_message("⚠️ Trading bot encountered an error!")
```

## 🎯 Benefits of Cloud Deployment

✅ **24/7 Operation**: Runs continuously regardless of laptop status
✅ **High Uptime**: Professional VPS with 99.9% uptime guarantee
✅ **Auto-Recovery**: Automatic restart on failures
✅ **Remote Access**: Monitor and control from anywhere
✅ **Scalability**: Easy to upgrade resources as needed
✅ **Security**: Isolated environment with proper security measures
✅ **Backup**: Automated backups and version control
✅ **Cost-Effective**: Much cheaper than keeping laptop running 24/7

## 💰 Cost Analysis

**Contabo VPS M (Monthly):**
- VPS Cost: €8.99/month (~$9.50)
- Electricity Savings: ~$30-50/month (vs running laptop 24/7)
- **Net Savings**: $20-40/month

**ROI**: Cloud deployment pays for itself while providing better reliability!

---

**Ready to deploy? Follow the steps above and your AI Trading Sentinel will be running 24/7 in the cloud! 🚀**