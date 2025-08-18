# TradeBot Sentinel - Production Deployment Checklist

This checklist ensures a complete and secure deployment of TradeBot Sentinel to production infrastructure.

## Pre-Deployment Requirements

### 1. Infrastructure Setup
- [ ] **VPS/Cloud Server Provisioned**
  - [ ] Ubuntu 22.04/24.04 LTS installed
  - [ ] Minimum 4GB RAM, 2 CPU cores, 50GB storage
  - [ ] Static IP address assigned
  - [ ] SSH access configured

- [ ] **Domain & DNS Configuration**
  - [ ] Domain name registered (optional)
  - [ ] DNS A record pointing to server IP
  - [ ] SSL certificate obtained (Let's Encrypt recommended)

### 2. Local Development Environment
- [ ] **Repository Access**
  - [ ] GitHub repository cloned locally
  - [ ] All required files present
  - [ ] `.env.example` copied to `.env` and configured

- [ ] **GitHub Secrets Configured**
  - [ ] Run `./deployment/setup-github-secrets.sh`
  - [ ] Verify all secrets are set in GitHub repository settings

## Security Hardening

### 3. Server Security Setup
- [ ] **Run Security Hardening Script**
  ```bash
  sudo ./deployment/security-hardening.sh
  ```

- [ ] **Verify Security Configuration**
  - [ ] SSH key-based authentication enabled
  - [ ] Password authentication disabled
  - [ ] UFW firewall active with proper rules
  - [ ] Fail2Ban installed and configured
  - [ ] OpenVPN server configured (optional)
  - [ ] Security monitoring tools installed

- [ ] **Download VPN Configuration**
  - [ ] Download admin.ovpn from `/etc/openvpn/client-configs/`
  - [ ] Test VPN connection from local machine

### 4. User and Permissions
- [ ] **TradeBot User Created**
  - [ ] User `tradebot` exists with proper permissions
  - [ ] SSH key added to `~tradebot/.ssh/authorized_keys`
  - [ ] User can sudo without password for service management

## Application Deployment

### 5. Initial Deployment
- [ ] **Clone Repository on Server**
  ```bash
  sudo mkdir -p /opt/tradebot-sentinel
  sudo chown tradebot:tradebot /opt/tradebot-sentinel
  cd /opt/tradebot-sentinel
  git clone https://github.com/your-org/ai-trading-sentinel.git .
  ```

- [ ] **Install Dependencies**
  ```bash
  sudo apt update && sudo apt upgrade -y
  sudo apt install python3 python3-pip python3-venv nodejs npm postgresql redis-server nginx -y
  ```

- [ ] **Setup Python Environment**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  playwright install chromium
  ```

### 6. Database Setup
- [ ] **PostgreSQL Configuration**
  - [ ] Database created for TradeBot
  - [ ] Database user created with proper permissions
  - [ ] Connection string added to `.env`

- [ ] **Redis Configuration**
  - [ ] Redis server running
  - [ ] Redis connection string added to `.env`

### 7. Environment Configuration
- [ ] **Environment Variables**
  - [ ] Copy `.env.production` to `.env`
  - [ ] Configure all required environment variables:
    - [ ] `DATABASE_URL`
    - [ ] `REDIS_URL`
    - [ ] `FLASK_SECRET_KEY`
    - [ ] `ENVIRONMENT=production`
    - [ ] Trading platform credentials
    - [ ] Notification settings (Slack, Email)

### 8. Service Installation
- [ ] **Install SystemD Services**
  ```bash
  sudo cp deployment/systemd/*.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable tradebot-sentinel
  sudo systemctl enable tradebot-health-monitor
  ```

- [ ] **Start Services**
  ```bash
  sudo systemctl start tradebot-sentinel
  sudo systemctl start tradebot-health-monitor
  ```

### 9. Web Frontend Setup
- [ ] **Build Frontend**
  ```bash
  cd frontend
  npm install
  npm run build
  ```

- [ ] **Configure Nginx**
  ```bash
  sudo cp deployment/nginx/tradebot-sentinel.conf /etc/nginx/sites-available/
  sudo ln -s /etc/nginx/sites-available/tradebot-sentinel.conf /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl reload nginx
  ```

## Testing and Verification

### 10. Deployment Verification
- [ ] **Run Verification Script**
  ```bash
  ./deployment/verify-deployment.sh
  ```

- [ ] **Manual Verification**
  - [ ] TradeBot service is running: `sudo systemctl status tradebot-sentinel`
  - [ ] Health monitor is running: `sudo systemctl status tradebot-health-monitor`
  - [ ] API endpoints responding: `curl http://localhost:8000/health`
  - [ ] Frontend accessible via web browser
  - [ ] Database connectivity working
  - [ ] Redis connectivity working

### 11. Functional Testing
- [ ] **Browser Automation**
  - [ ] Test headless browser functionality
  - [ ] Verify trading platform login works
  - [ ] Test trade execution in paper trading mode

- [ ] **API Testing**
  - [ ] Test all API endpoints
  - [ ] Verify authentication works
  - [ ] Test WebSocket connections

- [ ] **Monitoring Testing**
  - [ ] Verify logs are being written
  - [ ] Test alert notifications (Slack/Email)
  - [ ] Check health monitoring dashboard

## CI/CD Pipeline

### 12. GitHub Actions Setup
- [ ] **Verify CI/CD Pipeline**
  - [ ] GitHub Actions workflow file exists
  - [ ] All GitHub secrets configured
  - [ ] SSH connection from GitHub Actions works
  - [ ] Test deployment by pushing to main branch

- [ ] **Pipeline Testing**
  - [ ] Create test branch and push changes
  - [ ] Verify tests run successfully
  - [ ] Verify deployment to staging (if configured)
  - [ ] Test production deployment

## Monitoring and Alerting

### 13. Monitoring Setup
- [ ] **Health Monitoring**
  - [ ] Health monitor service running
  - [ ] Test alert notifications
  - [ ] Verify log rotation working

- [ ] **Performance Monitoring** (Optional)
  - [ ] Prometheus installed and configured
  - [ ] Grafana dashboard setup
  - [ ] Alert manager configured

### 14. Backup Configuration
- [ ] **Automated Backups**
  - [ ] Database backup script configured
  - [ ] Application backup script configured
  - [ ] Backup retention policy set
  - [ ] Test backup restoration process

## Security Verification

### 15. Security Audit
- [ ] **Run Security Scans**
  ```bash
  sudo lynis audit system
  sudo rkhunter --check
  sudo clamscan -r /opt/tradebot-sentinel
  ```

- [ ] **Network Security**
  - [ ] Only required ports open (SSH, HTTP, HTTPS)
  - [ ] Fail2Ban actively monitoring
  - [ ] SSH brute force protection working
  - [ ] SSL/TLS certificates valid

### 16. Access Control
- [ ] **User Access**
  - [ ] Only necessary users have server access
  - [ ] SSH keys properly managed
  - [ ] VPN access configured (if used)
  - [ ] Application-level authentication working

## Production Readiness

### 17. Performance Optimization
- [ ] **System Tuning**
  - [ ] System resources adequate for load
  - [ ] Database performance optimized
  - [ ] Redis memory settings configured
  - [ ] Nginx performance tuned

### 18. Documentation
- [ ] **Operational Documentation**
  - [ ] Server access procedures documented
  - [ ] Emergency procedures documented
  - [ ] Monitoring and alerting procedures documented
  - [ ] Backup and recovery procedures documented

### 19. Final Checks
- [ ] **Pre-Go-Live**
  - [ ] All tests passing
  - [ ] All monitoring active
  - [ ] All alerts configured
  - [ ] Team trained on operations
  - [ ] Emergency contacts configured

## Go-Live

### 20. Production Launch
- [ ] **Switch to Live Trading**
  - [ ] Update environment to use live trading credentials
  - [ ] Start with minimal position sizes
  - [ ] Monitor closely for first 24 hours
  - [ ] Gradually increase position sizes as confidence builds

- [ ] **Post-Launch Monitoring**
  - [ ] Monitor system performance
  - [ ] Monitor trading performance
  - [ ] Monitor error rates and alerts
  - [ ] Review logs regularly

## Maintenance Schedule

### 21. Ongoing Maintenance
- [ ] **Daily Tasks**
  - [ ] Check system health dashboard
  - [ ] Review trading performance
  - [ ] Monitor error logs

- [ ] **Weekly Tasks**
  - [ ] Review system performance metrics
  - [ ] Check backup integrity
  - [ ] Update dependencies if needed

- [ ] **Monthly Tasks**
  - [ ] Security audit
  - [ ] Performance optimization review
  - [ ] Disaster recovery testing

## Emergency Procedures

### 22. Incident Response
- [ ] **Emergency Contacts**
  - [ ] Primary administrator contact
  - [ ] Secondary administrator contact
  - [ ] Escalation procedures defined

- [ ] **Emergency Procedures**
  - [ ] Service restart procedures
  - [ ] Rollback procedures
  - [ ] Emergency shutdown procedures
  - [ ] Data recovery procedures

---

## Quick Reference Commands

### Service Management
```bash
# Check service status
sudo systemctl status tradebot-sentinel
sudo systemctl status tradebot-health-monitor

# Restart services
sudo systemctl restart tradebot-sentinel
sudo systemctl restart tradebot-health-monitor

# View logs
sudo journalctl -u tradebot-sentinel -f
sudo journalctl -u tradebot-health-monitor -f
```

### Health Checks
```bash
# Run deployment verification
./deployment/verify-deployment.sh

# Run health checks
./deployment/health-monitor.sh check

# Test alerts
./deployment/health-monitor.sh test-alert
```

### Security Management
```bash
# Check firewall status
sudo ufw status

# Check Fail2Ban status
sudo fail2ban-client status

# Add allowed IP
sudo /usr/local/bin/tradebot-security add-ip <IP_ADDRESS>

# Run security scan
sudo /usr/local/bin/tradebot-security scan
```

### Backup and Recovery
```bash
# Manual backup
./deployment/backup.sh

# List backups
ls -la /opt/tradebot-backups/

# Restore from backup
./deployment/restore.sh <backup_file>
```

---

**Note**: This checklist should be customized based on your specific infrastructure and requirements. Always test procedures in a staging environment before applying to production.