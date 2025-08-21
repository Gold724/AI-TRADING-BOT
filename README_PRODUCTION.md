# AI Trading Sentinel - Production Deployment Guide

🚀 **TRAE-SentinelOps**: Complete 24/7 cloud deployment automation for profitable trading bot operations.

## 🎯 Quick Start

### Option 1: Automated Deployment (Recommended)
```bash
# Clone and setup
git clone <your-repo-url> ai-trading-sentinel
cd ai-trading-sentinel

# Run automated deployment
python deploy_orchestrator.py --mode docker --env production --ssl --github
```

### Option 2: Manual VPS Setup
```bash
# On your Contabo VPS (Ubuntu 22.04/24.04)
wget -O - https://raw.githubusercontent.com/<your-repo>/main/deploy_production.sh | bash
```

## 📋 Prerequisites

### System Requirements
- **VPS**: Contabo VPS (2+ CPU cores, 4GB+ RAM, 50GB+ SSD)
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS
- **Network**: Static IP, ports 80/443/22 accessible
- **Domain**: Optional but recommended for SSL

### Required Accounts
- **Broker Account**: Bulenox trading account with API access
- **GitHub**: Repository with deploy keys configured
- **Cloud Storage**: AWS S3 or compatible for backups (optional)
- **Monitoring**: Slack/Telegram for alerts (optional)

## 🔧 Deployment Options

### 1. Docker Deployment (Recommended)
**Best for**: Scalability, isolation, easy updates

```bash
# Quick Docker deployment
python deploy_orchestrator.py --mode docker --env production

# With SSL and monitoring
python deploy_orchestrator.py --mode docker --env production --domain yourdomain.com --ssl --github
```

**Services**:
- `backend`: Flask API (port 5000)
- `bot`: Trading automation with Playwright
- `frontend`: React dashboard (port 3000)
- `monitoring`: Health checks and alerts
- `nginx`: Reverse proxy with SSL
- `redis`: Session and cache storage

### 2. Systemd Deployment
**Best for**: Direct system integration, lower overhead

```bash
# Systemd deployment
python deploy_orchestrator.py --mode systemd --env production

# Manual systemd setup
sudo ./deploy_production.sh
```

**Services**:
- `aitrading-backend.service`
- `aitrading-bot.service`
- `aitrading-monitor.service`

### 3. Hybrid Deployment
**Best for**: Maximum reliability and flexibility

```bash
# Hybrid deployment (Docker + Systemd)
python deploy_orchestrator.py --mode hybrid --env production
```

## ⚙️ Configuration

### Environment Setup

1. **Copy environment template**:
```bash
cp .env.production.template .env.production
```

2. **Configure critical settings**:
```bash
# Broker Configuration
BROKER_USERNAME=your_bulenox_username
BROKER_PASSWORD=your_secure_password
BROKER_URL=https://bulenox.projectx.com/login

# Security
SECRET_KEY=your_super_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# Database
DATABASE_URL=sqlite:///data/trading.db

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### SSL Configuration

**Automatic (Let's Encrypt)**:
```bash
# During deployment
python deploy_orchestrator.py --domain yourdomain.com --ssl
```

**Manual**:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

## 🔒 Security Hardening

### Automated Security Setup
```bash
# Run security hardening
sudo ./security_hardening.sh
```

### Manual Security Steps

1. **SSH Hardening**:
```bash
# Disable password auth, enable key-only
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PubkeyAuthentication yes
sudo systemctl restart ssh
```

2. **Firewall Setup**:
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

3. **Fail2Ban**:
```bash
# Install and configure
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📊 Monitoring & Alerts

### Health Checks
```bash
# Check all services
curl http://localhost:5000/api/health
curl http://localhost:3000/health

# Check system resources
python monitoring_setup.py --status
```

### Log Monitoring
```bash
# Real-time logs
tail -f logs/backend.log
tail -f logs/bot.log
tail -f logs/monitoring.log

# System logs
sudo journalctl -u aitrading-backend -f
sudo journalctl -u aitrading-bot -f
```

### Alert Configuration

**Slack Integration**:
```bash
# Set in .env.production
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_CHANNELS=slack,email
```

**Telegram Integration**:
```bash
# Set in .env.production
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🔄 CI/CD Pipeline

### GitHub Actions Setup

1. **Configure secrets** in GitHub repository:
```
VPS_HOST=your.vps.ip.address
VPS_USER=aitrading
VPS_SSH_KEY=your_private_ssh_key
BROKER_USERNAME=your_username
BROKER_PASSWORD=your_password
```

2. **Auto-deployment** on push:
```yaml
# .github/workflows/deploy.yml is already configured
# Push to main branch triggers deployment
git push origin main
```

### Manual Deployment
```bash
# On VPS
cd /home/aitrading/ai-trading-sentinel
git pull origin main

# Docker mode
docker-compose down && docker-compose up -d --build

# Systemd mode
sudo systemctl restart aitrading-backend aitrading-bot aitrading-monitor
```

## 💾 Backup & Recovery

### Automated Backups
```bash
# Setup daily backups
./backup_recovery.sh setup

# Manual backup
./backup_recovery.sh backup

# List backups
./backup_recovery.sh list
```

### Recovery Process
```bash
# Restore from backup
./backup_recovery.sh restore backup_20240101_120000.tar.gz

# Emergency recovery
./backup_recovery.sh emergency-restore
```

## 🚨 Troubleshooting

### Common Issues

**Bot Login Failures**:
```bash
# Check browser automation
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Check credentials
grep BROKER_ .env.production

# Test login manually
python test_login.py
```

**Service Startup Issues**:
```bash
# Check service status
sudo systemctl status aitrading-backend
sudo systemctl status aitrading-bot

# Check logs
sudo journalctl -u aitrading-backend --since "1 hour ago"
```

**Performance Issues**:
```bash
# Check system resources
htop
df -h
free -h

# Check Docker resources
docker stats
docker system df
```

### Emergency Procedures

**Stop All Services**:
```bash
# Docker mode
docker-compose down

# Systemd mode
sudo systemctl stop aitrading-*
```

**Emergency Restart**:
```bash
# Full system restart
sudo reboot

# Service restart only
./deploy_orchestrator.py --mode docker --env production
```

## 📈 Scaling & Optimization

### Multi-Account Setup
```bash
# Copy configuration for additional accounts
cp .env.production .env.account2

# Modify ports and credentials
sed -i 's/5000/5001/g' .env.account2
sed -i 's/3000/3001/g' .env.account2

# Deploy additional instance
FLASK_PORT=5001 FRONTEND_PORT=3001 python deploy_orchestrator.py
```

### Performance Tuning
```bash
# Optimize Python
export PYTHONOPTIMIZE=1

# Increase worker processes
export GUNICORN_WORKERS=4

# Enable caching
export REDIS_CACHE_ENABLED=true
```

## 🔧 Maintenance

### Regular Maintenance Tasks

**Daily**:
- Check service health
- Review trading logs
- Monitor system resources

**Weekly**:
- Update system packages
- Rotate logs
- Test backup restoration

**Monthly**:
- Security audit
- Performance optimization
- Dependency updates

### Update Procedures

**System Updates**:
```bash
# Update OS packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip install -r requirements.txt --upgrade

# Update Docker images
docker-compose pull && docker-compose up -d
```

**Application Updates**:
```bash
# Pull latest code
git pull origin main

# Restart services
./deploy_orchestrator.py --mode docker --env production
```

## 📞 Support & Resources

### Documentation
- [API Documentation](./docs/api.md)
- [Configuration Reference](./docs/configuration.md)
- [Troubleshooting Guide](./docs/troubleshooting.md)

### Monitoring Dashboards
- **Health**: http://your-domain.com/api/health
- **Metrics**: http://your-domain.com/metrics
- **Logs**: http://your-domain.com/logs

### Emergency Contacts
- **System Admin**: Configure in monitoring alerts
- **Trading Desk**: Configure in risk management
- **Technical Support**: GitHub Issues

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] ✅ Backend API responding at `/api/health`
- [ ] ✅ Frontend accessible and loading
- [ ] ✅ Bot successfully logging into broker
- [ ] ✅ Trading automation executing
- [ ] ✅ Monitoring alerts configured
- [ ] ✅ Backups running automatically
- [ ] ✅ SSL certificates valid
- [ ] ✅ CI/CD pipeline working
- [ ] ✅ Log rotation configured
- [ ] ✅ Security hardening applied

**🚀 Your AI Trading Sentinel is now running 24/7 in production!**

---

*TRAE-SentinelOps: Ensuring continuous, secure, and profitable trading operations.*