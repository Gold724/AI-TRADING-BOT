# AI Trading Sentinel - Production Deployment Guide

🚀 **Complete guide for deploying the AI Trading Sentinel to production on Contabo VPS with 24/7 reliability, monitoring, and automation.**

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [VPS Setup](#vps-setup)
3. [Initial Server Configuration](#initial-server-configuration)
4. [Repository Setup](#repository-setup)
5. [Environment Configuration](#environment-configuration)
6. [SSL Certificate Setup](#ssl-certificate-setup)
7. [Docker Deployment](#docker-deployment)
8. [Monitoring Stack](#monitoring-stack)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Security Hardening](#security-hardening)
11. [Backup Strategy](#backup-strategy)
12. [Health Monitoring](#health-monitoring)
13. [Troubleshooting](#troubleshooting)
14. [Maintenance](#maintenance)

## 🔧 Prerequisites

### VPS Requirements
- **Provider**: Contabo VPS (recommended: VPS M or higher)
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: Minimum 200GB SSD
- **CPU**: 4+ cores
- **Network**: 1Gbps connection

### Domain & DNS
- Domain name (e.g., `trading.yourdomain.com`)
- DNS A record pointing to your VPS IP
- Cloudflare (optional but recommended for DDoS protection)

### Required Accounts
- GitHub account with repository access
- Broker account credentials
- Slack workspace (for alerts)
- Email account (for notifications)

## 🖥️ VPS Setup

### 1. Initial VPS Configuration

```bash
# Connect to your VPS
ssh root@YOUR_VPS_IP

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Set timezone
timedatectl set-timezone UTC

# Configure hostname
hostnamectl set-hostname ai-trading-sentinel
echo "127.0.0.1 ai-trading-sentinel" >> /etc/hosts
```

### 2. Create Non-Root User (Optional but Recommended)

```bash
# Create deployment user
useradd -m -s /bin/bash deploy
usermod -aG sudo deploy

# Setup SSH key for deploy user
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

## 🔧 Initial Server Configuration

### 1. Run Automated Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
cd ai-trading-sentinel

# Make setup script executable
chmod +x deploy_vps_complete.py

# Run automated setup (as root)
python3 deploy_vps_complete.py --domain trading.yourdomain.com --email admin@yourdomain.com
```

### 2. Manual Setup (Alternative)

If you prefer manual setup or need to customize:

#### Install Docker

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add user to docker group
usermod -aG docker $USER
```

#### Install Docker Compose

```bash
# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## 📁 Repository Setup

### 1. Clone and Configure Repository

```bash
# Create application directory
mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git .

# Set up directory structure
mkdir -p {data/{postgres,redis,prometheus,grafana,alertmanager,loki},logs,ssl,nginx/conf.d,monitoring/{grafana/{dashboards,provisioning},prometheus,alertmanager},database/{init,backups},config}

# Set permissions
chown -R root:root /opt/ai-trading-sentinel
chmod -R 755 /opt/ai-trading-sentinel
```

### 2. Configure Git for Deployment

```bash
# Generate SSH key for GitHub
ssh-keygen -t ed25519 -C "deploy@ai-trading-sentinel" -f /root/.ssh/deploy_key -N ""

# Add deploy key to GitHub repository
cat /root/.ssh/deploy_key.pub
# Copy this key and add it to your GitHub repository's Deploy Keys

# Configure Git
git config --global user.name "AI Trading Sentinel Deploy"
git config --global user.email "deploy@yourdomain.com"
```

## ⚙️ Environment Configuration

### 1. Create Production Environment File

```bash
# Copy example environment file
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production
```

### 2. Essential Environment Variables

```bash
# Security Keys (Generate strong random values)
API_SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
SESSION_SECRET_KEY=$(openssl rand -hex 32)

# Database Passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Grafana Admin Password
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Update .env.production with these values
echo "API_SECRET_KEY=$API_SECRET_KEY" >> .env.production
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env.production
echo "SESSION_SECRET_KEY=$SESSION_SECRET_KEY" >> .env.production
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env.production
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> .env.production
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD" >> .env.production
```

### 3. Configure Broker Credentials

Update `.env.production` with your broker details:

```bash
BROKER_USERNAME=your-broker-username
BROKER_PASSWORD=your-broker-password
BROKER_URL=https://your-broker-platform.com
```

## 🔒 SSL Certificate Setup

### 1. Install Certbot

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Stop nginx if running
systemctl stop nginx 2>/dev/null || true
```

### 2. Obtain SSL Certificate

```bash
# Get SSL certificate
certbot certonly --standalone -d trading.yourdomain.com --email admin@yourdomain.com --agree-tos --non-interactive

# Copy certificates to nginx directory
cp /etc/letsencrypt/live/trading.yourdomain.com/fullchain.pem /opt/ai-trading-sentinel/ssl/
cp /etc/letsencrypt/live/trading.yourdomain.com/privkey.pem /opt/ai-trading-sentinel/ssl/

# Generate DH parameters
openssl dhparam -out /opt/ai-trading-sentinel/ssl/dhparam.pem 2048

# Set permissions
chmod 600 /opt/ai-trading-sentinel/ssl/*.pem
```

### 3. Setup Auto-Renewal

```bash
# Create renewal script
cat > /opt/ai-trading-sentinel/scripts/renew-ssl.sh << 'EOF'
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/trading.yourdomain.com/fullchain.pem /opt/ai-trading-sentinel/ssl/
cp /etc/letsencrypt/live/trading.yourdomain.com/privkey.pem /opt/ai-trading-sentinel/ssl/
docker-compose -f /opt/ai-trading-sentinel/docker-compose.prod.yml restart nginx
EOF

chmod +x /opt/ai-trading-sentinel/scripts/renew-ssl.sh

# Add to crontab
echo "0 3 * * * /opt/ai-trading-sentinel/scripts/renew-ssl.sh" | crontab -
```

## 🐳 Docker Deployment

### 1. Build and Deploy

```bash
cd /opt/ai-trading-sentinel

# Pull latest code
git pull origin main

# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 2. Verify Deployment

```bash
# Check all services are running
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoints
curl -f http://localhost/health
curl -f http://localhost:9090/-/healthy  # Prometheus
curl -f http://localhost:3000/api/health  # Grafana
```

## 📊 Monitoring Stack

### 1. Access Monitoring Services

- **Grafana**: https://trading.yourdomain.com/grafana/
  - Username: `admin`
  - Password: `${GRAFANA_ADMIN_PASSWORD}`

- **Prometheus**: https://trading.yourdomain.com/prometheus/
- **Alertmanager**: http://YOUR_VPS_IP:9093

### 2. Import Dashboards

Grafana dashboards are automatically provisioned from `monitoring/grafana/dashboards/`.

### 3. Configure Alerts

Alerts are configured in `monitoring/alert_rules.yml` and sent via:
- Slack webhooks
- Email notifications
- Custom webhooks

## 🔄 CI/CD Pipeline

### 1. GitHub Actions Setup

The CI/CD pipeline is configured in `.github/workflows/deploy.yml` and includes:

- **Security Scanning**: Trivy, TruffleHog
- **Testing**: Backend, Frontend, E2E tests
- **Building**: Docker images
- **Deployment**: Automated deployment to VPS
- **Performance Testing**: k6 load tests

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
VPS_HOST=your-vps-ip
VPS_USER=root
VPS_SSH_KEY=your-private-ssh-key
DOCKER_REGISTRY_TOKEN=your-github-token
SLACK_WEBHOOK_URL=your-slack-webhook
```

### 3. Deploy via GitHub Actions

```bash
# Push to main branch triggers deployment
git add .
git commit -m "Deploy to production"
git push origin main

# Or trigger manual deployment
# Go to GitHub Actions → AI Trading Sentinel - CI/CD Pipeline → Run workflow
```

## 🛡️ Security Hardening

### 1. Firewall Configuration

```bash
# Install and configure UFW
apt install -y ufw

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow monitoring (restrict to your IP)
# ufw allow from YOUR_IP to any port 9090
# ufw allow from YOUR_IP to any port 3000
# ufw allow from YOUR_IP to any port 9093

# Enable firewall
ufw --force enable
```

### 2. SSH Hardening

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Add/modify these settings:
# PermitRootLogin yes  # Keep for deployment, or change to 'no' if using deploy user
# PasswordAuthentication no
# PubkeyAuthentication yes
# Port 22  # Consider changing to non-standard port
# MaxAuthTries 3
# ClientAliveInterval 300
# ClientAliveCountMax 2

# Restart SSH
systemctl restart sshd
```

### 3. Fail2Ban Setup

```bash
# Install Fail2Ban
apt install -y fail2ban

# Configure Fail2Ban
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

# Start and enable Fail2Ban
systemctl start fail2ban
systemctl enable fail2ban
```

## 💾 Backup Strategy

### 1. Automated Backups

Backups are handled by the backup service in Docker Compose:

- **Database backups**: Daily PostgreSQL dumps
- **Redis backups**: RDB snapshots
- **Configuration backups**: Environment files, configs
- **Log backups**: Application and system logs

### 2. Manual Backup

```bash
# Create manual backup
cd /opt/ai-trading-sentinel
./scripts/backup.sh manual

# Restore from backup
./scripts/restore.sh /path/to/backup.tar.gz
```

### 3. S3 Backup (Optional)

Configure AWS S3 backup in `.env.production`:

```bash
S3_BACKUP_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## 🏥 Health Monitoring

### 1. System Health Checks

```bash
# Check system resources
df -h
free -h
top

# Check Docker containers
docker ps
docker stats

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### 2. Application Health

```bash
# API health check
curl -f https://trading.yourdomain.com/api/health

# Trading bot status
curl -f http://localhost:8001/health

# Database connectivity
docker exec ai-trading-postgres pg_isready -U trading_user

# Redis connectivity
docker exec ai-trading-redis redis-cli ping
```

### 3. Monitoring Alerts

Alerts are configured for:
- High CPU/Memory usage
- Disk space low
- Service downtime
- Trading errors
- Failed login attempts
- SSL certificate expiry

## 🔧 Troubleshooting

### Common Issues

#### 1. Services Not Starting

```bash
# Check Docker logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check system resources
df -h
free -h

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

#### 2. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /opt/ai-trading-sentinel/ssl/fullchain.pem -text -noout

# Renew certificate
certbot renew --force-renewal
/opt/ai-trading-sentinel/scripts/renew-ssl.sh
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL logs
docker logs ai-trading-postgres

# Connect to database
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db

# Check Redis
docker exec -it ai-trading-redis redis-cli
```

#### 4. High Memory Usage

```bash
# Check container memory usage
docker stats

# Restart memory-intensive services
docker-compose -f docker-compose.prod.yml restart trading-bot

# Clean up Docker
docker system prune -f
```

### Log Locations

- **Application logs**: `/opt/ai-trading-sentinel/logs/`
- **Nginx logs**: `/var/log/nginx/`
- **Docker logs**: `docker logs container-name`
- **System logs**: `/var/log/syslog`

## 🔄 Maintenance

### Daily Tasks

```bash
# Check system status
systemctl status docker
docker ps

# Check disk space
df -h

# Review logs for errors
tail -f /opt/ai-trading-sentinel/logs/app.log
```

### Weekly Tasks

```bash
# Update system packages
apt update && apt upgrade -y

# Clean up Docker
docker system prune -f

# Check backup integrity
ls -la /opt/ai-trading-sentinel/database/backups/

# Review monitoring alerts
# Check Grafana dashboards
```

### Monthly Tasks

```bash
# Rotate logs
logrotate -f /etc/logrotate.conf

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Security audit
apt list --upgradable
docker scan ai-trading-sentinel/backend:latest

# Performance review
# Analyze Grafana metrics
# Review trading performance
```

## 📞 Support & Monitoring

### Access URLs

- **Main Application**: https://trading.yourdomain.com
- **Grafana Dashboard**: https://trading.yourdomain.com/grafana/
- **Prometheus**: https://trading.yourdomain.com/prometheus/
- **API Documentation**: https://trading.yourdomain.com/api/docs

### Emergency Contacts

- **Slack Alerts**: #trading-alerts channel
- **Email Alerts**: admin@yourdomain.com
- **SMS Alerts**: Configure via Grafana

### Performance Metrics

- **Uptime Target**: 99.9%
- **Response Time**: < 200ms API calls
- **Trading Latency**: < 1 second
- **Error Rate**: < 0.1%

---

## 🎉 Deployment Complete!

Your AI Trading Sentinel is now deployed and running in production with:

✅ **24/7 Reliability**: Docker containers with auto-restart
✅ **SSL Security**: Let's Encrypt certificates with auto-renewal
✅ **Monitoring**: Prometheus + Grafana + Alertmanager
✅ **Automated Backups**: Daily database and configuration backups
✅ **CI/CD Pipeline**: GitHub Actions for automated deployments
✅ **Security Hardening**: Firewall, Fail2Ban, rate limiting
✅ **Performance Optimization**: Nginx reverse proxy, caching
✅ **Log Aggregation**: Centralized logging with Loki

**Next Steps:**
1. Configure your broker credentials
2. Set up Slack/email notifications
3. Import Grafana dashboards
4. Run initial trading tests
5. Monitor system performance

**Happy Trading! 🚀📈**