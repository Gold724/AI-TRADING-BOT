# 🚀 TradeBot Sentinel Implementation Guide

## Phase 1: Configure GitHub Repository Secrets

### Required Secrets Setup

Navigate to your GitHub repository → Settings → Secrets and variables → Actions

#### Production Server Secrets
```bash
# Server Access
PRODUCTION_HOST=your-production-server-ip
PRODUCTION_USER=tradebot
PRODUCTION_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
PRODUCTION_SSH_PORT=22

# Staging Server (Optional)
STAGING_HOST=your-staging-server-ip
STAGING_USER=tradebot
STAGING_SSH_KEY=your-staging-private-key
STAGING_SSH_PORT=22
```

#### Application Secrets
```bash
# Trading Credentials
BULENOX_USERNAME=your-trading-username
BULENOX_PASSWORD=your-trading-password

# Security Keys
SECRET_KEY=your-flask-secret-key-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-32-chars

# Database & Cache
DATABASE_URL=postgresql://tradebot:password@localhost:5432/tradebot
REDIS_URL=redis://localhost:6379/0
```

#### Container Registry (Optional)
```bash
DOCKER_REGISTRY=ghcr.io
DOCKER_USERNAME=your-github-username
DOCKER_PASSWORD=your-github-token
```

#### Notification Secrets
```bash
# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Generate SSH Keys for VPS Access

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "tradebot-deployment" -f ~/.ssh/tradebot_deploy

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/tradebot_deploy.pub root@your-vps-ip

# Add private key content to GitHub secret PRODUCTION_SSH_KEY
cat ~/.ssh/tradebot_deploy
```

---

## Phase 2: Deploy Security Hardening

### Step 1: Prepare VPS Environment

```bash
# Connect to your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Git if not present
apt install -y git curl wget
```

### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel

# Make scripts executable
chmod +x deployment/*.sh
```

### Step 3: Run Security Hardening

```bash
# Execute security hardening script
sudo ./deployment/security-hardening.sh

# Follow the interactive prompts:
# 1. Choose SSH port (default: 2222)
# 2. Set up OpenVPN (y/n)
# 3. Configure monitoring email
# 4. Set admin IP whitelist
```

### Step 4: Verify Security Setup

```bash
# Check firewall status
sudo ufw status verbose

# Verify Fail2Ban
sudo fail2ban-client status

# Test SSH on new port
ssh -p 2222 tradebot@your-vps-ip

# Check security monitoring
sudo systemctl status tradebot-security-monitor
```

---

## Phase 3: Launch TradeBot Sentinel

### Option A: Docker Deployment (Recommended)

```bash
# Create environment file
cp .env.example .env
vim .env  # Configure your settings

# Deploy with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose ps
docker-compose logs -f tradebot-app
```

### Option B: Kubernetes Deployment

```bash
# Install kubectl and helm (if not present)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n tradebot
kubectl logs -f deployment/tradebot-app -n tradebot
```

### Option C: SystemD Service

```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd service
sudo cp deployment/tradebot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tradebot
sudo systemctl start tradebot

# Check service status
sudo systemctl status tradebot
```

### Option D: Automated Deployment Script

```bash
# Use deployment automation
./deployment/deploy-automation.sh deploy --target=vps --host=your-vps-ip

# Check deployment status
./deployment/deploy-automation.sh status
```

---

## Phase 4: Setup Monitoring & Dashboards

### Step 1: Deploy Monitoring Stack

```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps
```

### Step 2: Access Dashboards

#### Grafana Dashboard
```bash
# URL: http://your-vps-ip:3000
# Default credentials: admin/admin
# Import dashboards from grafana/dashboards/
```

#### Prometheus Metrics
```bash
# URL: http://your-vps-ip:9090
# Check targets: Status → Targets
```

#### Alertmanager
```bash
# URL: http://your-vps-ip:9093
# Configure alerts in prometheus.yml
```

### Step 3: Configure Alerts

```yaml
# Add to prometheus.yml
rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Step 4: Key Metrics to Monitor

- **Trading Performance**: Win rate, profit/loss, drawdown
- **System Health**: CPU, memory, disk usage
- **Application**: Response time, error rate, active sessions
- **Security**: Failed logins, suspicious activity
- **Browser**: Selenium session health, page load times

---

## Verification Checklist

### ✅ Security Verification

```bash
# Test firewall
nmap -p 1-65535 your-vps-ip

# Check SSH hardening
ssh -p 22 root@your-vps-ip  # Should fail
ssh -p 2222 tradebot@your-vps-ip  # Should work

# Verify Fail2Ban
sudo fail2ban-client status sshd

# Test VPN (if configured)
openvpn --config client.ovpn
```

### ✅ Application Health

```bash
# Health endpoints
curl -f http://your-vps-ip:8000/health
curl -f http://your-vps-ip:8000/health/db
curl -f http://your-vps-ip:8000/health/redis

# Trading system
curl -f http://your-vps-ip:8000/api/status
```

### ✅ Monitoring Verification

```bash
# Check Grafana
curl -f http://your-vps-ip:3000/api/health

# Verify Prometheus targets
curl -f http://your-vps-ip:9090/api/v1/targets

# Test alerts
curl -f http://your-vps-ip:9093/api/v1/alerts
```

---

## Troubleshooting Common Issues

### Issue: SSH Connection Refused
```bash
# Check if SSH service is running
sudo systemctl status ssh

# Verify firewall rules
sudo ufw status numbered

# Check SSH configuration
sudo sshd -T | grep port
```

### Issue: Docker Containers Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Verify Docker Compose file
docker-compose config

# Check container logs
docker-compose logs container-name
```

### Issue: Browser Automation Fails
```bash
# Install Chrome dependencies
sudo apt install -y chromium-browser chromium-chromedriver

# Test headless mode
chromium-browser --headless --no-sandbox --dump-dom https://google.com

# Check display settings
echo $DISPLAY
export DISPLAY=:99
```

### Issue: Database Connection Failed
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U tradebot -d tradebot

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## Next Steps

1. **Test Trading Logic**: Run in simulation mode first
2. **Configure Risk Management**: Set position sizes and stop losses
3. **Setup Backup Strategy**: Automated database and config backups
4. **Performance Optimization**: Monitor and tune system resources
5. **Scale Deployment**: Add load balancing and multiple instances

---

## Support Resources

- **Documentation**: Check DEPLOYMENT.md for detailed guides
- **Logs**: Always check application and system logs first
- **Monitoring**: Use Grafana dashboards for real-time insights
- **Security**: Review security-hardening.sh output for any issues

**🎯 Your TradeBot Sentinel is now ready for 24/7 automated trading!**