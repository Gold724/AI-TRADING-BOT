# AI Trading Sentinel - Production Deployment Checklist

**TRAE-SentinelOps: Complete Production Deployment Guide**

This checklist ensures a secure, reliable, and monitored deployment of the AI Trading Sentinel on Contabo VPS.

## 🚀 Pre-Deployment Requirements

### Server Specifications (Minimum)
- [ ] **VPS**: Contabo VPS M (4 vCPU, 8GB RAM, 200GB SSD)
- [ ] **OS**: Ubuntu 22.04 LTS or 24.04 LTS
- [ ] **Network**: Static IP with reverse DNS configured
- [ ] **Bandwidth**: Unlimited (for API calls and data streaming)

### Access & Security
- [ ] **SSH Access**: Key-based authentication configured
- [ ] **Firewall**: UFW configured with necessary ports
- [ ] **SSL Certificate**: Let's Encrypt or commercial SSL
- [ ] **Backup Strategy**: Automated daily backups configured

## 📋 Deployment Steps

### Phase 1: Server Preparation

#### 1.1 Initial Server Setup
```bash
# Connect to server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git unzip htop nano ufw fail2ban
```

#### 1.2 Security Configuration
```bash
# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

#### 1.3 Create Deployment User
```bash
# Create system user
useradd -r -m -s /bin/bash trae-sentinel
usermod -aG sudo trae-sentinel

# Create directory structure
mkdir -p /opt/trae-sentinel
mkdir -p /etc/trae-sentinel
mkdir -p /var/log/trae-sentinel
mkdir -p /var/lib/trae-sentinel

# Set permissions
chown -R trae-sentinel:trae-sentinel /opt/trae-sentinel
chown -R root:trae-sentinel /etc/trae-sentinel
chown -R trae-sentinel:trae-sentinel /var/log/trae-sentinel
chown -R trae-sentinel:trae-sentinel /var/lib/trae-sentinel

chmod 755 /opt/trae-sentinel
chmod 750 /etc/trae-sentinel
chmod 750 /var/log/trae-sentinel
chmod 750 /var/lib/trae-sentinel
```

### Phase 2: Dependencies Installation

#### 2.1 Python Environment
```bash
# Install Python 3.10+
apt install -y python3 python3-pip python3-venv python3-dev

# Verify Python version
python3 --version  # Should be 3.10 or higher
```

#### 2.2 Node.js Environment
```bash
# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Verify versions
node --version  # Should be v18+
npm --version
```

#### 2.3 Database & Cache
```bash
# Install Redis
apt install -y redis-server
systemctl enable redis-server
systemctl start redis-server

# Install SQLite (usually pre-installed)
apt install -y sqlite3
```

#### 2.4 Web Server
```bash
# Install Nginx
apt install -y nginx
systemctl enable nginx
systemctl start nginx
```

#### 2.5 Browser Dependencies
```bash
# Install Playwright dependencies
apt install -y libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgtk-3-0 libatspi2.0-0 libxss1 libasound2 xvfb
```

### Phase 3: Application Deployment

#### 3.1 Clone Repository
```bash
# Switch to deployment user
su - trae-sentinel

# Clone repository
cd /opt/trae-sentinel
git clone https://github.com/your-username/ai-trading-sentinel.git .

# Set up Git for future updates
git config --global user.name "TRAE-SentinelOps"
git config --global user.email "ops@trae-sentinel.com"
```

#### 3.2 Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps
```

#### 3.3 Frontend Setup
```bash
# Install frontend dependencies
cd frontend
npm install

# Build production frontend
npm run build

# Return to root directory
cd ..
```

### Phase 4: Configuration

#### 4.1 Environment Configuration
```bash
# Run production environment setup
sudo ./setup_production_env.sh

# Follow interactive prompts to configure:
# - Trading credentials
# - API endpoints
# - Database settings
# - Notification settings
# - Security settings
```

#### 4.2 SSL Certificate Setup
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

#### 4.3 Nginx Configuration
```bash
# Deploy Nginx configuration
sudo cp config/nginx/trae-sentinel.conf /etc/nginx/sites-available/trae-sentinel
sudo ln -sf /etc/nginx/sites-available/trae-sentinel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Phase 5: Service Configuration

#### 5.1 Deploy Systemd Services
```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable trae-enhanced-monitor.service
sudo systemctl enable trae-enhanced-monitor.timer
sudo systemctl enable trae-backend.service
sudo systemctl enable trae-trading-bot.service
```

#### 5.2 Start Services
```bash
# Start monitoring first
sudo systemctl start trae-enhanced-monitor.service
sudo systemctl start trae-enhanced-monitor.timer

# Start backend services
sudo systemctl start trae-backend.service

# Start trading bot (after testing)
sudo systemctl start trae-trading-bot.service
```

### Phase 6: Validation & Testing

#### 6.1 Run System Validation
```bash
# Run comprehensive validation
sudo python3 validate_production_system.py --verbose

# Run deployment verification
sudo ./verify_deployment.sh
```

#### 6.2 Test API Endpoints
```bash
# Test backend health
curl -f http://localhost:5000/api/health

# Test frontend
curl -f http://localhost/

# Test SSL (if configured)
curl -f https://your-domain.com/api/health
```

#### 6.3 Test Trading Bot (Simulation Mode)
```bash
# Enable simulation mode
echo "SIMULATION_MODE=true" >> /etc/trae-sentinel/.env

# Test login functionality
sudo -u trae-sentinel /opt/trae-sentinel/venv/bin/python test_login.py

# Monitor logs
tail -f /var/log/trae-sentinel/trading_bot.log
```

### Phase 7: Monitoring & Alerts

#### 7.1 Configure Notifications
```bash
# Test Slack notifications
sudo -u trae-sentinel /opt/trae-sentinel/venv/bin/python -c "
from scripts.slack_notifications import send_slack_prophetic
send_slack_prophetic('🚀 AI Trading Sentinel deployed successfully!', 'system')
"

# Test email notifications (if configured)
sudo -u trae-sentinel /opt/trae-sentinel/venv/bin/python -c "
from scripts.alert_manager import AlertManager
alert_manager = AlertManager()
alert_manager.send_email_alert('Deployment Complete', 'AI Trading Sentinel is now live!')
"
```

#### 7.2 Setup Log Rotation
```bash
# Configure logrotate
sudo tee /etc/logrotate.d/trae-sentinel << EOF
/var/log/trae-sentinel/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 trae-sentinel trae-sentinel
    postrotate
        systemctl reload trae-enhanced-monitor || true
    endscript
}
EOF
```

### Phase 8: Backup & Recovery

#### 8.1 Setup Automated Backups
```bash
# Create backup script
sudo tee /opt/trae-sentinel/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/trae-sentinel"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /etc/trae-sentinel/

# Backup database
cp /var/lib/trae-sentinel/trading_bot.db "$BACKUP_DIR/database_$DATE.db"

# Backup logs (last 7 days)
find /var/log/trae-sentinel -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/trae-sentinel/scripts/backup.sh

# Setup cron job
echo "0 2 * * * /opt/trae-sentinel/scripts/backup.sh >> /var/log/trae-sentinel/backup.log 2>&1" | sudo crontab -u trae-sentinel -
```

### Phase 9: CI/CD Pipeline

#### 9.1 Setup GitHub Actions
```bash
# Generate deploy key
ssh-keygen -t ed25519 -f /home/trae-sentinel/.ssh/deploy_key -N ""

# Add public key to GitHub repository (Deploy Keys)
cat /home/trae-sentinel/.ssh/deploy_key.pub

# Configure SSH for GitHub
sudo -u trae-sentinel tee /home/trae-sentinel/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile /home/trae-sentinel/.ssh/deploy_key
    StrictHostKeyChecking no
EOF
```

#### 9.2 Setup Webhook Endpoint (Optional)
```bash
# Configure webhook receiver for auto-deployment
# This allows GitHub to trigger deployments on push
sudo systemctl enable trae-webhook-receiver.service
sudo systemctl start trae-webhook-receiver.service
```

### Phase 10: Go Live

#### 10.1 Final Pre-Live Checks
- [ ] All services running and healthy
- [ ] SSL certificate valid and auto-renewal configured
- [ ] Monitoring and alerts working
- [ ] Backup system operational
- [ ] Trading credentials verified in simulation mode
- [ ] Risk management parameters configured
- [ ] Emergency stop procedures documented

#### 10.2 Enable Live Trading
```bash
# Disable simulation mode
sudo sed -i 's/SIMULATION_MODE=true/SIMULATION_MODE=false/' /etc/trae-sentinel/.env

# Restart trading bot
sudo systemctl restart trae-trading-bot.service

# Monitor initial trades
tail -f /var/log/trae-sentinel/trading_bot.log
```

## 🔧 Post-Deployment Maintenance

### Daily Tasks
- [ ] Check service status: `systemctl status trae-*`
- [ ] Review trading logs: `tail -100 /var/log/trae-sentinel/trading_bot.log`
- [ ] Monitor system resources: `htop`, `df -h`
- [ ] Check for security updates: `apt list --upgradable`

### Weekly Tasks
- [ ] Review trading performance reports
- [ ] Update dependencies: `pip list --outdated`
- [ ] Check backup integrity
- [ ] Review and rotate logs

### Monthly Tasks
- [ ] Security audit and updates
- [ ] Performance optimization review
- [ ] Backup strategy review
- [ ] Disaster recovery testing

## 🚨 Emergency Procedures

### Stop All Trading
```bash
# Emergency stop
sudo systemctl stop trae-trading-bot.service

# Verify no active trades
curl http://localhost:5000/api/status
```

### System Recovery
```bash
# Restore from backup
sudo systemctl stop trae-*
sudo tar -xzf /var/backups/trae-sentinel/config_YYYYMMDD_HHMMSS.tar.gz -C /
sudo cp /var/backups/trae-sentinel/database_YYYYMMDD_HHMMSS.db /var/lib/trae-sentinel/trading_bot.db
sudo systemctl start trae-*
```

### Contact Information
- **Primary**: ops@trae-sentinel.com
- **Emergency**: +1-XXX-XXX-XXXX
- **Slack**: #trae-sentinel-alerts

## 📊 Monitoring Dashboard

Access the monitoring dashboard at:
- **Local**: http://localhost/dashboard
- **Public**: https://your-domain.com/dashboard

### Key Metrics to Monitor
- System CPU, Memory, Disk usage
- Trading bot uptime and performance
- API response times
- Trade success/failure rates
- Account balance and P&L
- Network connectivity to Bulenox

## 🔐 Security Considerations

### Regular Security Tasks
- [ ] Update system packages monthly
- [ ] Rotate SSH keys quarterly
- [ ] Review firewall rules
- [ ] Monitor failed login attempts
- [ ] Audit user access and permissions
- [ ] Review and update SSL certificates

### Security Incident Response
1. **Isolate**: Stop trading and isolate system
2. **Assess**: Determine scope and impact
3. **Contain**: Prevent further damage
4. **Recover**: Restore from clean backups
5. **Learn**: Update security measures

---

**✅ Deployment Complete!**

Your AI Trading Sentinel is now running in production with:
- 24/7 monitoring and health checks
- Automated alerts and notifications
- Secure configuration and access controls
- Automated backups and recovery procedures
- CI/CD pipeline for seamless updates

For support and updates, visit: https://github.com/your-username/ai-trading-sentinel