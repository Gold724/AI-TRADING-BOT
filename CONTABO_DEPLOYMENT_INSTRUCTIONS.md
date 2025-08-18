# 🚀 Contabo VPS Deployment Guide - Bulenox Trading Bot

## Prerequisites

### 1. Contabo VPS Setup
- **VPS Plan**: VPS S (4 vCPU, 8GB RAM, 200GB SSD) or higher
- **OS**: Ubuntu 22.04 LTS
- **Root Access**: Enabled
- **SSH Key**: Generated and added to VPS

### 2. Required Accounts
- **Bulenox Trading Account**: Active account at https://bulenox.projectx.com
- **GitHub Repository**: Fork or clone this repository
- **Domain (Optional)**: For SSL and custom domain access

## 🔧 Quick Deployment Steps

### Step 1: Configure Deployment Settings

1. Copy the template configuration:
```bash
cp deployment_config_template.json deployment_config.json
```

2. Edit `deployment_config.json` with your actual details:
```json
{
  "vps_connection": {
    "host": "YOUR_CONTABO_VPS_IP",
    "username": "root",
    "key_file": "/path/to/your/ssh/key"
  },
  "github_repository": {
    "url": "https://github.com/yourusername/ai-trading-sentinel.git"
  },
  "environment_variables": {
    "BULENOX_USERNAME": "your_actual_username",
    "BULENOX_PASSWORD": "your_actual_password"
  }
}
```

### Step 2: Generate SSH Key (if needed)

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/contabo_key

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/contabo_key.pub root@YOUR_VPS_IP
```

### Step 3: Run Deployment

```bash
# Install dependencies
pip install paramiko

# Test connection (dry run)
python execute_deployment.py --config deployment_config.json --dry-run

# Execute actual deployment
python execute_deployment.py --config deployment_config.json
```

### Step 4: Verify Deployment

```bash
# Check deployment status
python validate_deployment.py --host YOUR_VPS_IP

# Monitor bot status
python remote_management.py --host YOUR_VPS_IP status
```

## 🔐 Security Configuration

### SSH Security
```bash
# Disable password authentication (recommended)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Environment Variables Security
- Store sensitive data in `/opt/trading-bot/.env`
- Set proper file permissions: `chmod 600 .env`
- Never commit `.env` to version control

## 📊 Monitoring & Management

### Remote Management Commands

```bash
# Check bot status
python remote_management.py --host YOUR_VPS_IP status

# View live logs
python remote_management.py --host YOUR_VPS_IP logs --follow

# Restart bot service
python remote_management.py --host YOUR_VPS_IP restart

# Emergency stop
python remote_management.py --host YOUR_VPS_IP emergency-stop

# Update bot code
python remote_management.py --host YOUR_VPS_IP update
```

### Health Monitoring

```bash
# Start monitoring daemon
python monitor_trading_bot.py --host YOUR_VPS_IP --daemon

# Check system resources
python monitor_trading_bot.py --host YOUR_VPS_IP --check-resources

# Generate status report
python monitor_trading_bot.py --host YOUR_VPS_IP --report
```

## 🔄 CI/CD Integration

### GitHub Actions Setup

1. Add secrets to your GitHub repository:
   - `CONTABO_HOST`: Your VPS IP address
   - `CONTABO_SSH_KEY`: Your private SSH key
   - `BULENOX_USERNAME`: Your Bulenox username
   - `BULENOX_PASSWORD`: Your Bulenox password

2. The workflow will automatically:
   - Run tests on code changes
   - Deploy to VPS on main branch pushes
   - Validate deployment success
   - Send notifications on failure

### Manual Deployment Trigger

```bash
# Trigger deployment from local machine
git push origin main

# Or deploy specific branch
git push origin feature-branch:main
```

## 🚨 Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Test SSH connection
ssh -i ~/.ssh/contabo_key root@YOUR_VPS_IP

# Check SSH key permissions
chmod 600 ~/.ssh/contabo_key
```

#### 2. Bot Service Not Starting
```bash
# Check service status
sudo systemctl status bulenox-trader

# View service logs
sudo journalctl -u bulenox-trader -f

# Restart service
sudo systemctl restart bulenox-trader
```

#### 3. Bulenox Login Issues
```bash
# Test login credentials
python validate_live_trading_contracts.py --test-login

# Check environment variables
cat /opt/trading-bot/.env | grep BULENOX
```

#### 4. High Resource Usage
```bash
# Check system resources
htop
df -h
free -h

# Restart bot if needed
sudo systemctl restart bulenox-trader
```

### Log Locations
- **Application Logs**: `/var/log/trading-bot/app.log`
- **System Logs**: `/var/log/syslog`
- **Nginx Logs**: `/var/log/nginx/`
- **Service Logs**: `journalctl -u bulenox-trader`

## 📈 Performance Optimization

### System Tuning
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize network settings
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf
sudo sysctl -p
```

### Bot Configuration
```bash
# Adjust contract sizes for your account
export MAX_CONTRACT_SIZE=5
export DEFAULT_CONTRACT_SIZE=1

# Set appropriate risk limits
export RISK_PERCENTAGE=1
export STOP_LOSS_PERCENTAGE=0.5
```

## 🔄 Backup & Recovery

### Automated Backups
```bash
# Backup configuration and logs
sudo crontab -e
# Add: 0 2 * * * /opt/trading-bot/scripts/backup.sh

# Manual backup
sudo /opt/trading-bot/scripts/backup.sh
```

### Recovery Process
```bash
# Restore from backup
sudo /opt/trading-bot/scripts/restore.sh /opt/backups/latest

# Restart services
sudo systemctl restart bulenox-trader
sudo systemctl restart nginx
```

## 📞 Support

- **Documentation**: Check this repository's Wiki
- **Issues**: Create GitHub issues for bugs
- **Emergency**: Use emergency stop commands
- **Updates**: Monitor GitHub releases

## ⚠️ Risk Disclaimer

- **Test First**: Always test in demo mode before live trading
- **Monitor Closely**: Keep an eye on bot performance
- **Risk Management**: Never risk more than you can afford to lose
- **Compliance**: Ensure compliance with local trading regulations

---

**Ready to deploy? Follow the steps above and your Bulenox trading bot will be running 24/7 on Contabo VPS!** 🚀