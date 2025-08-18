# TradeBot Sentinel - Comprehensive Deployment Guide

This document provides complete instructions for deploying the TradeBot Sentinel across multiple environments, from local development to production cloud deployment with full automation, monitoring, and security hardening.

## Deployment Options

The TradeBot Sentinel supports multiple deployment strategies:

1. **Local Development** - Development environment setup
2. **Docker Deployment** - Containerized deployment with Docker Compose
3. **Kubernetes Deployment** - Scalable cloud-native deployment
4. **Cloud VPS Deployment** - Traditional VPS deployment (Contabo, DigitalOcean, AWS, etc.)
5. **GitHub Actions CI/CD** - Automated deployment pipeline
6. **Manual VPS Setup** - Direct setup on VPS using systemd

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 20GB+ available space
- **Network**: Stable internet connection with low latency

### Software Dependencies

- **Python**: 3.10+ (3.11 recommended)
- **Node.js**: 18+ (for frontend)
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+
- **Git**: Latest version
- **kubectl**: Latest (for Kubernetes deployment)

### Cloud Providers Supported

- **Contabo VPS** (Primary recommendation)
- **DigitalOcean Droplets**
- **AWS EC2**
- **Google Cloud Compute Engine**
- **Azure Virtual Machines**
- **Linode**
- **Vultr**

## Quick Start

### Environment Setup

```bash
# Clone repository
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Choose your deployment method:
# 1. Docker (Recommended for quick start)
docker-compose up -d --build

# 2. Kubernetes (For production)
./deployment/deploy-k8s.sh deploy

# 3. Cloud VPS (For traditional deployment)
./deployment/deploy-automation.sh deploy
```

### Cloud Control Panel

The cloud control panel provides a web interface for managing your trading system:

- **Dashboard**: Real-time trading statistics and account balances
- **Trade Management**: Execute manual trades and view trade history
- **System Control**: Start/stop services, toggle simulation mode
- **Monitoring**: View logs, system metrics, and performance data
- **Security**: Manage API keys, user access, and security settings

## Docker Deployment (Recommended)

### Quick Start

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f tradebot-app
```

### Production Docker Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale the application
docker-compose up -d --scale tradebot-app=3
```

### Docker Services

- **tradebot-app**: Main application container
- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **nginx**: Reverse proxy and load balancer
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboard
- **loki**: Log aggregation

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Deploy to Kubernetes

```bash
# Make deployment script executable
chmod +x deployment/deploy-k8s.sh

# Deploy to Kubernetes
./deployment/deploy-k8s.sh deploy

# Check deployment status
kubectl get pods -n tradebot
kubectl get services -n tradebot
```

### Kubernetes Management

```bash
# Scale deployment
./deployment/deploy-k8s.sh scale 5

# View logs
./deployment/deploy-k8s.sh logs

# Check metrics
./deployment/deploy-k8s.sh metrics

# Restart deployment
./deployment/deploy-k8s.sh restart

# Cleanup
./deployment/deploy-k8s.sh cleanup
```

## Cloud VPS Deployment

### Contabo VPS Setup (Recommended)

#### 1. Server Provisioning

- **Plan**: VPS M (4 vCPU, 16GB RAM, 400GB SSD)
- **OS**: Ubuntu 22.04 LTS
- **Location**: Choose closest to your trading region

#### 2. Initial Server Setup

```bash
# Connect to server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git htop unzip software-properties-common

# Create deployment user
useradd -m -s /bin/bash tradebot
usermod -aG sudo tradebot

# Setup SSH keys
mkdir -p /home/tradebot/.ssh
cp ~/.ssh/authorized_keys /home/tradebot/.ssh/
chown -R tradebot:tradebot /home/tradebot/.ssh
chmod 700 /home/tradebot/.ssh
chmod 600 /home/tradebot/.ssh/authorized_keys
```

#### 3. Security Hardening

```bash
# Run security hardening script
wget https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/deployment/security-hardening.sh
chmod +x security-hardening.sh
./security-hardening.sh
```

#### 4. Application Deployment

```bash
# Switch to deployment user
su - tradebot

# Clone repository
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run deployment
chmod +x deployment/deploy-automation.sh
./deployment/deploy-automation.sh deploy
```

## Security Hardening

### Automated Security Setup

```bash
# Run comprehensive security hardening
./deployment/security-hardening.sh
```

### Security Features Implemented

#### Server Security
- Custom SSH port configuration
- SSH key-based authentication only
- UFW firewall with strict rules
- Fail2Ban intrusion prevention
- Automatic security updates
- System auditing with auditd
- Intrusion detection (AIDE, rkhunter)
- Antivirus scanning (ClamAV)

#### Network Security
- OpenVPN server setup
- Private network configuration
- Rate limiting and DDoS protection
- Network traffic monitoring
- Secure API endpoints with JWT

#### Application Security
- Environment variable encryption
- Database connection security
- API rate limiting
- Input validation and sanitization
- Secure session management

### VPN Setup

```bash
# Create VPN client
sudo ./deployment/tradebot-security vpn-create client1

# Download client configuration
scp root@your-server:/root/client1.ovpn ./

# Connect using OpenVPN client
sudo openvpn --config client1.ovpn
```

## Monitoring & Logging

### Start Monitoring Stack

```bash
# Start all monitoring services
chmod +x deployment/start-monitoring.sh
./deployment/start-monitoring.sh start

# Check status
./deployment/start-monitoring.sh status

# View logs
./deployment/start-monitoring.sh logs
```

### Access Monitoring Dashboards

- **Grafana**: https://your-domain.com/grafana (admin/admin)
- **Prometheus**: https://your-domain.com/prometheus
- **Alertmanager**: https://your-domain.com/alertmanager
- **Loki**: https://your-domain.com/loki

### Key Metrics Monitored

- **Application Health**: Uptime, response time, error rate
- **Trading Performance**: Trades per minute, success rate, P&L
- **System Resources**: CPU, memory, disk usage, network I/O
- **Browser Automation**: Page load time, element detection success
- **Database Performance**: Query time, connection pool usage

### Alert Configuration

- **Critical Alerts**: Application crashes, failed trades, login issues
- **Warning Alerts**: High resource usage, slow response times
- **Info Alerts**: Successful deployments, daily reports
- **Notification Channels**: Slack, email, SMS, webhook

## 1. Local Execution

Use the provided deployment scripts to deploy directly from your local machine.

### Windows (PowerShell)

```powershell
./trae_deploy.ps1 -VpsIp "your-vps-ip" -VpsUser "ubuntu" -SshKeyPath "path/to/private_key" -EnvFilePath ".env"
```

Optional parameters:
- `-NotifySlack` - Enable Slack notifications
- `-SlackWebhookUrl "your-webhook-url"` - Slack webhook URL for notifications

### Linux/macOS (Bash)

```bash
./trae_deploy.sh --vps-ip "your-vps-ip" --vps-user "ubuntu" --ssh-key "path/to/private_key" --env ".env"
```

Optional parameters:
- `--notify-slack` - Enable Slack notifications
- `--slack-webhook "your-webhook-url"` - Slack webhook URL for notifications

The deployment scripts will:
- Transfer project files to the VPS
- Set up Python virtual environment
- Install dependencies
- Configure systemd service
- Start the trading bot

## GitHub Actions CI/CD Pipeline

The repository includes a comprehensive CI/CD pipeline that automatically handles code quality checks, testing, security scanning, building, and deployment.

### Pipeline Features

- **Code Quality**: Formatting, linting, type checking
- **Security Scanning**: Vulnerability assessment, dependency audit
- **Testing**: Unit tests, integration tests, frontend tests
- **Building**: Docker image creation and registry push
- **Deployment**: Automated deployment to staging and production
- **Monitoring**: Health checks and rollback capabilities

### Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

#### Production Server
```
PRODUCTION_HOST=your-production-server-ip
PRODUCTION_USER=tradebot
PRODUCTION_SSH_KEY=your-private-ssh-key
PRODUCTION_SSH_PORT=22
```

#### Staging Server
```
STAGING_HOST=your-staging-server-ip
STAGING_USER=tradebot
STAGING_SSH_KEY=your-private-ssh-key
STAGING_SSH_PORT=22
```

#### Application Secrets
```
BULENOX_USERNAME=your-username
BULENOX_PASSWORD=your-password
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
```

#### Container Registry
```
DOCKER_REGISTRY=your-registry.com
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password
```

#### Notifications
```
SLACK_WEBHOOK_URL=your-slack-webhook
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Pipeline Triggers

- **Push to main**: Full pipeline with production deployment
- **Push to develop**: Full pipeline with staging deployment
- **Pull Request**: Code quality and testing only
- **Manual Trigger**: Configurable environment and deployment target

### Manual Deployment

```bash
# Trigger manual deployment via GitHub CLI
gh workflow run deploy.yml \
  -f environment=production \
  -f deploy_target=kubernetes

# Or via GitHub web interface
# Go to Actions → Deploy to Contabo VPS → Run workflow
```

## Manual VPS Setup

### SystemD Service Setup

For traditional systemd-based deployment:

```bash
# Copy service file to VPS
scp deployment/tradebot.service username@your-vps-ip:~/

# SSH into VPS and install service
ssh username@your-vps-ip
sudo mv ~/tradebot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tradebot
sudo systemctl start tradebot

# Check service status
sudo systemctl status tradebot
```

### Alternative Deployment Methods

#### Using Deploy Automation Script

```bash
# Local deployment to remote server
./deployment/deploy-automation.sh deploy --target=vps --host=your-server-ip

# Check deployment status
./deployment/deploy-automation.sh status --target=vps --host=your-server-ip

# Update deployment
./deployment/deploy-automation.sh update --target=vps --host=your-server-ip
```

#### Using Docker on VPS

```bash
# Deploy using Docker Compose on VPS
scp docker-compose.yml docker-compose.prod.yml username@your-vps-ip:~/
scp .env username@your-vps-ip:~/

ssh username@your-vps-ip
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check logs
docker-compose logs tradebot-app

# Check environment variables
docker-compose exec tradebot-app env | grep -E "(BULENOX|DATABASE|REDIS)"

# Restart services
docker-compose restart
```

#### Browser Automation Fails

```bash
# Check Chrome/Chromium installation
docker-compose exec tradebot-app which chromium-browser

# Test browser in headless mode
docker-compose exec tradebot-app python -c "from selenium import webdriver; driver = webdriver.Chrome(); print('Browser OK')"

# Check display settings
docker-compose exec tradebot-app echo $DISPLAY
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Test connection
docker-compose exec tradebot-app python -c "import psycopg2; psycopg2.connect('$DATABASE_URL'); print('DB OK')"

# Check database logs
docker-compose logs postgres
```

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Optimize Chrome options in docker-compose.yml:
# environment:
#   - CHROME_OPTIONS=--no-sandbox --disable-dev-shm-usage --disable-gpu
```

### Performance Optimization

#### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM trades WHERE timestamp > NOW() - INTERVAL '1 hour';
```

#### Application Optimization

```python
# Enable connection pooling
DATABASE_URL = "postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30"

# Use Redis for caching
CACHE_URL = "redis://localhost:6379/1"

# Optimize Selenium
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-images",
]
```

### Health Checks

```bash
# Application health
curl -f http://localhost:8000/health

# Database health
curl -f http://localhost:8000/health/db

# Redis health
curl -f http://localhost:8000/health/redis

# Trading system health
curl -f http://localhost:8000/health/trading
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U tradebot tradebot > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T postgres psql -U tradebot tradebot < backup_20240101_120000.sql
```

### Application Data Backup

```bash
# Backup configuration and logs
tar -czf tradebot_backup_$(date +%Y%m%d).tar.gz \
  .env \
  logs/ \
  data/ \
  deployment/
```

### Automated Backups

```bash
# Add to crontab for daily backups
0 2 * * * /opt/tradebot-sentinel/scripts/backup.sh
```

## Updating the System

### Automated Updates via CI/CD

```bash
# Push to main branch triggers automatic deployment
git push origin main

# Or trigger manual deployment
gh workflow run deploy.yml -f environment=production
```

### Manual Updates

```bash
# Update using deployment automation
./deployment/deploy-automation.sh update

# Or update Docker containers
docker-compose pull
docker-compose up -d

# Or update systemd service
cd ~/ai-trading-sentinel
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart tradebot
```

## Notification Setup

### Slack Integration

```bash
# Create Slack app and get webhook URL
# Add SLACK_WEBHOOK_URL to your environment variables

# Test Slack notifications
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"TradeBot Sentinel deployment test"}' \
  $SLACK_WEBHOOK_URL
```

### Email Notifications

```bash
# Configure SMTP settings in .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com
SMTP_TO=admin@yourcompany.com
```

### Webhook Notifications

```bash
# Configure webhook endpoints for external integrations
WEBHOOK_URL=https://your-webhook-endpoint.com/notify
WEBHOOK_SECRET=your-webhook-secret
```

## Alternative Cloud Providers

### DigitalOcean Deployment

```bash
# Create droplet using doctl
doctl compute droplet create tradebot-sentinel \
  --size s-2vcpu-4gb \
  --image ubuntu-22-04-x64 \
  --region nyc1 \
  --ssh-keys your-ssh-key-id

# Deploy using automation script
./deployment/deploy-automation.sh deploy --target=digitalocean --droplet-ip=your-droplet-ip
```

### AWS EC2 Deployment

```bash
# Launch instance using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx

# Deploy using automation script
./deployment/deploy-automation.sh deploy --target=aws --instance-ip=your-instance-ip
```

### Google Cloud Platform

```bash
# Create VM instance
gcloud compute instances create tradebot-sentinel \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud

# Deploy using automation script
./deployment/deploy-automation.sh deploy --target=gcp --instance-ip=your-instance-ip
```

## Production Checklist

### Pre-Deployment

- [ ] Environment variables configured and secured
- [ ] SSH keys generated and deployed
- [ ] Firewall rules configured
- [ ] SSL certificates obtained (if using HTTPS)
- [ ] Database backups scheduled
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Security audit performed

### Post-Deployment

- [ ] Health checks passing
- [ ] Monitoring dashboards accessible
- [ ] Log aggregation working
- [ ] Backup and recovery tested
- [ ] Performance metrics baseline established
- [ ] Security monitoring active
- [ ] Documentation updated
- [ ] Team access configured

### Maintenance Schedule

- **Daily**: Check application logs, monitor trading performance
- **Weekly**: Review system metrics, update dependencies
- **Monthly**: Security audit, performance optimization
- **Quarterly**: Full system backup, disaster recovery test

## Support and Resources

### Documentation

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Contabo VPS Documentation](https://contabo.com/en/product-docs/)
- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)

### Getting Help

- **Documentation**: Check this guide and inline code comments
- **Logs**: Always check application and system logs first
- **Community**: Join our Discord/Slack for community support
- **Issues**: Report bugs on GitHub Issues

### Version Management

```bash
# Check current version
./deployment/deploy-automation.sh version

# Update to latest version
./deployment/deploy-automation.sh update

# Rollback to previous version
./deployment/deploy-automation.sh rollback

# List available versions
./deployment/deploy-automation.sh list-versions
```

---

**Note**: This deployment guide is continuously updated. Always refer to the latest version in the repository for the most current information.

**Security Warning**: Never commit sensitive credentials to version control. Always use environment variables or secure secret management systems.