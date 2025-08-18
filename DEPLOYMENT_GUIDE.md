# TradeBot Sentinel Pro Advanced - Production Deployment Guide

🚀 **Complete Cloud Deployment on Contabo VPS**

This guide provides step-by-step instructions for deploying the Bulenox Trading Bot - Playwright Edition v2.0.0 to a production environment on Contabo VPS with full security, monitoring, and automation.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)

## 🎯 Overview

This guide covers multiple deployment scenarios for TradeBot Sentinel Pro Advanced:

- **Development**: Local development with hot-reload and debugging
- **Staging**: Pre-production testing environment
- **Production**: High-availability production deployment
- **Docker**: Containerized deployment for consistency
- **Cloud**: AWS, GCP, Azure deployment options

## 📋 Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB free space
- **Network**: Stable internet connection
- **OS**: Windows 10+, Ubuntu 18.04+, macOS 10.15+

#### Recommended Requirements
- **CPU**: 4+ cores, 3.0 GHz
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **Network**: High-speed internet (100+ Mbps)
- **OS**: Latest stable versions

### Software Prerequisites

```bash
# Required
Python 3.8+
Node.js 16+ (for web dashboard)
Git
Chrome/Chromium browser

# Optional but recommended
Docker & Docker Compose
Nginx (for production)
Redis (for caching)
PostgreSQL (for production database)
```

## 🏠 Local Development Setup

### Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd ai-trading-sentinel
   
   # Run automated setup
   python setup_advanced.py --dev
   ```

2. **Configure Environment**:
   ```bash
   # Copy environment template
   cp .env.template .env
   
   # Edit with your credentials
   nano .env  # or use your preferred editor
   ```

3. **Start Development Server**:
   ```bash
   # Start in development mode
   python tradebot_sentinel_pro_advanced.py --mode automation --debug
   
   # Or start individual components
   python tradebot_sentinel_pro_advanced.py --mode capture
   python tradebot_sentinel_pro_advanced.py --mode dashboard
   ```

### Development Environment Configuration

```bash
# .env for development
DEBUG_MODE=true
DRY_RUN_MODE=true
HEADLESS_MODE=false
SCREENSHOT_ON_ERROR=true
LOG_LEVEL=DEBUG

# Database (SQLite for development)
DATABASE_URL=sqlite:///data/trades_dev.db

# Dashboard
DASHBOARD_HOST=localhost
DASHBOARD_PORT=5000
DASHBOARD_AUTO_RELOAD=true
```

### Hot Reload Setup

```bash
# Install development dependencies
pip install watchdog flask-cors

# Start with auto-reload
python -m flask --app automation.monitoring_dashboard run --debug --reload
```

## 🏭 Production Deployment

### Server Setup (Ubuntu 20.04 LTS)

1. **System Preparation**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install system dependencies
   sudo apt install -y python3 python3-pip python3-venv git nginx redis-server postgresql postgresql-contrib
   
   # Install Chrome
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install -y google-chrome-stable
   ```

2. **User Setup**:
   ```bash
   # Create service user
   sudo useradd -m -s /bin/bash tradebot
   sudo usermod -aG sudo tradebot
   
   # Switch to service user
   sudo su - tradebot
   ```

3. **Application Setup**:
   ```bash
   # Clone repository
   git clone <repository-url> tradebot-sentinel
   cd tradebot-sentinel
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install application
   python setup_advanced.py --full
   ```

4. **Database Setup (PostgreSQL)**:
   ```bash
   # Create database and user
   sudo -u postgres psql
   
   CREATE DATABASE tradebot_prod;
   CREATE USER tradebot_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE tradebot_prod TO tradebot_user;
   \q
   ```

5. **Environment Configuration**:
   ```bash
   # Production .env
   cat > .env << EOF
   # Production Configuration
   DEBUG_MODE=false
   DRY_RUN_MODE=false
   HEADLESS_MODE=true
   LOG_LEVEL=INFO
   
   # Database
   DATABASE_URL=postgresql://tradebot_user:secure_password@localhost/tradebot_prod
   
   # Security
   SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   
   # Trading credentials
   BULENOX_USERNAME=your_username
   BULENOX_PASSWORD=your_password
   
   # Monitoring
   DASHBOARD_HOST=0.0.0.0
   DASHBOARD_PORT=5000
   
   # Notifications
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   EOF
   ```

### Systemd Service Setup

1. **Create Service File**:
   ```bash
   sudo tee /etc/systemd/system/tradebot-sentinel.service << EOF
   [Unit]
   Description=TradeBot Sentinel Pro Advanced
   After=network.target postgresql.service redis.service
   Wants=postgresql.service redis.service
   
   [Service]
   Type=simple
   User=tradebot
   Group=tradebot
   WorkingDirectory=/home/tradebot/tradebot-sentinel
   Environment=PATH=/home/tradebot/tradebot-sentinel/venv/bin
   ExecStart=/home/tradebot/tradebot-sentinel/venv/bin/python tradebot_sentinel_pro_advanced.py --mode automation
   ExecReload=/bin/kill -HUP \$MAINPID
   Restart=always
   RestartSec=10
   StandardOutput=journal
   StandardError=journal
   SyslogIdentifier=tradebot-sentinel
   
   # Security settings
   NoNewPrivileges=yes
   PrivateTmp=yes
   ProtectSystem=strict
   ProtectHome=yes
   ReadWritePaths=/home/tradebot/tradebot-sentinel/data
   ReadWritePaths=/home/tradebot/tradebot-sentinel/logs
   ReadWritePaths=/home/tradebot/tradebot-sentinel/screenshots
   
   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tradebot-sentinel
   sudo systemctl start tradebot-sentinel
   sudo systemctl status tradebot-sentinel
   ```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p data logs screenshots reports backups

# Set environment variables
ENV PYTHONPATH=/home/app
ENV PYTHONUNBUFFERED=1
ENV HEADLESS_MODE=true
ENV DISPLAY=:99

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start application
CMD ["python", "tradebot_sentinel_pro_advanced.py", "--mode", "automation"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  tradebot:
    build: .
    container_name: tradebot-sentinel
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://tradebot:password@postgres:5432/tradebot
      - REDIS_URL=redis://redis:6379/0
      - HEADLESS_MODE=true
      - LOG_LEVEL=INFO
    env_file:
      - .env
    volumes:
      - ./data:/home/app/data
      - ./logs:/home/app/logs
      - ./screenshots:/home/app/screenshots
      - ./reports:/home/app/reports
      - ./backups:/home/app/backups
    depends_on:
      - postgres
      - redis
    networks:
      - tradebot-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  postgres:
    image: postgres:15-alpine
    container_name: tradebot-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: tradebot
      POSTGRES_USER: tradebot
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - tradebot-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tradebot"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: tradebot-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - tradebot-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  postgres_data:
  redis_data:

networks:
  tradebot-network:
    driver: bridge
```

## ☁️ Cloud Deployment

### AWS Deployment

#### EC2 Instance Setup

```bash
# Launch EC2 instance (t3.medium recommended)
# Security Group: Allow ports 22, 80, 443, 5000

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy application
git clone <repository-url>
cd ai-trading-sentinel
cp .env.template .env
# Edit .env with your configuration
docker-compose up -d
```

## 📊 Monitoring & Maintenance

### System Monitoring

1. **Health Checks**:
   ```python
   # health_check.py
   import requests
   import sys
   
   def check_health():
       try:
           response = requests.get('http://localhost:5000/api/health', timeout=10)
           if response.status_code == 200:
               print(f"✅ System healthy: {response.json()}")
               return True
           else:
               print(f"❌ Health check failed: {response.status_code}")
               return False
       except Exception as e:
           print(f"❌ Health check error: {e}")
           return False
   
   if __name__ == '__main__':
       if not check_health():
           sys.exit(1)
   ```

2. **Log Management**:
   ```bash
   # /etc/logrotate.d/tradebot-sentinel
   /home/tradebot/tradebot-sentinel/logs/*.log {
       daily
       missingok
       rotate 30
       compress
       delaycompress
       notifempty
       create 644 tradebot tradebot
       postrotate
           systemctl reload tradebot-sentinel
       endscript
   }
   ```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/tradebot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h localhost -U tradebot_user tradebot_prod > "$BACKUP_DIR/db_backup_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

## 🔒 Security Considerations

### Security Checklist

- [ ] **Environment Variables**: All sensitive data in environment variables
- [ ] **SSL/TLS**: HTTPS enabled with valid certificates
- [ ] **Firewall**: Only necessary ports open
- [ ] **User Permissions**: Service runs with minimal privileges
- [ ] **Database Security**: Strong passwords, encrypted connections
- [ ] **API Security**: Rate limiting, authentication, input validation
- [ ] **Log Security**: No sensitive data in logs
- [ ] **Backup Security**: Encrypted backups, secure storage
- [ ] **Update Strategy**: Regular security updates
- [ ] **Monitoring**: Security event monitoring

### Security Hardening

```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Enable firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Browser Automation Failures

**Symptoms**: Playwright/Selenium errors, browser crashes

**Solutions**:
```bash
# Check browser installation
playwright install chromium

# Test browser launch
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop()"

# Check display (for headless issues)
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
```

#### 2. Database Connection Issues

**Symptoms**: Database connection errors, migration failures

**Solutions**:
```bash
# Check database status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U tradebot_user -d tradebot_prod

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Memory Issues

**Symptoms**: Out of memory errors, slow performance

**Solutions**:
```bash
# Monitor memory usage
free -h
top -p $(pgrep -f tradebot)

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Debug Mode

```bash
# Enable debug logging
export TRADEBOT_DEBUG=1
export TRADEBOT_LOG_LEVEL=DEBUG

# Run with debug
python tradebot_sentinel_pro_advanced.py --debug --mode capture

# Check logs
tail -f logs/tradebot_advanced_$(date +%Y%m%d).log
```

## ⚡ Performance Optimization

### System Optimization

1. **Database Optimization**:
   ```sql
   -- Create indexes
   CREATE INDEX idx_trades_timestamp ON trades(timestamp);
   CREATE INDEX idx_trades_symbol ON trades(symbol);
   CREATE INDEX idx_trades_status ON trades(status);
   
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM trades WHERE timestamp > NOW() - INTERVAL '1 day';
   ```

2. **Memory Optimization**:
   ```python
   # Optimize memory usage
   import gc
   
   # Force garbage collection
   gc.collect()
   
   # Limit concurrent operations
   MAX_CONCURRENT_TRADES = 3
   
   # Use connection pooling
   from sqlalchemy.pool import QueuePool
   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=20
   )
   ```

3. **Caching Strategy**:
   ```python
   # Redis caching
   import redis
   from functools import wraps
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   def cache_result(expiration=300):
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
               cached = redis_client.get(cache_key)
               if cached:
                   return json.loads(cached)
               
               result = func(*args, **kwargs)
               redis_client.setex(cache_key, expiration, json.dumps(result))
               return result
           return wrapper
       return decorator
   ```

---

## 📞 Support

For deployment support:
- **Documentation**: [README_ADVANCED.md](README_ADVANCED.md)
- **Issues**: Create GitHub issues for bugs and feature requests
- **Testing**: Run `python test_tradebot_pro_advanced_features.py` before deployment

**⚠️ Security Notice**: Always follow security best practices and keep your system updated. Never expose sensitive credentials in logs or configuration files.

**🚀 Ready to deploy? Choose your deployment method and follow the guide above!**

## Linux Deployment

### Prerequisites

- Linux server with systemd (Ubuntu, Debian, CentOS, etc.)
- Root or sudo access
- Python 3.8+ installed
- Git (to clone the repository if needed)

### Automatic Deployment

The easiest way to deploy the TRAE AI Trading Bot on Linux is to use the provided deployment script:

```bash
# Make the script executable
chmod +x deploy_adaptive_intelligence.sh

# Run as root
sudo ./deploy_adaptive_intelligence.sh
```

This script will automatically:
1. Copy the trae-bot.service file to /etc/systemd/system/
2. Reload the systemd daemon
3. Enable the trae-bot service
4. Start the trae-bot service
5. Set up the cron jobs for Adaptive Intelligence

### Manual Deployment

If you prefer to deploy manually, follow these steps:

1. Copy the service file to systemd:
   ```bash
   sudo cp trae-bot.service /etc/systemd/system/
   ```

2. Reload the systemd daemon:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start on boot:
   ```bash
   sudo systemctl enable trae-bot
   ```

4. Start the service:
   ```bash
   sudo systemctl start trae-bot
   ```

5. Set up the cron jobs:
   ```bash
   chmod +x setup_adaptive_intelligence_cron.sh
   ./setup_adaptive_intelligence_cron.sh
   ```

### Verifying Deployment

To verify that the deployment was successful:

1. Check the service status:
   ```bash
   sudo systemctl status trae-bot
   ```

2. Check the logs:
   ```bash
   tail -f /root/AI-TRADING-BOT/trae_output.log
   ```

3. Verify cron jobs:
   ```bash
   crontab -l | grep activate_adaptive_intelligence
   ```

## Windows Deployment

### Prerequisites

- Windows 10/11 or Windows Server 2016+
- Administrator access
- Python 3.8+ installed and added to PATH
- PowerShell 5.0+ (included in Windows 10+)

### Automatic Deployment

The easiest way to deploy on Windows is to use the provided batch file:

1. Right-click on `deploy_adaptive_intelligence.bat`
2. Select "Run as administrator"

Alternatively, you can run the PowerShell script directly:

1. Open PowerShell as Administrator
2. Navigate to the project directory
3. Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\deploy_adaptive_intelligence.ps1
   ```

The deployment script will:
1. Check for Python installation
2. Activate the virtual environment if present
3. Set up scheduled tasks for Adaptive Intelligence
4. Test the Adaptive Intelligence activation
5. Verify the deployment

### Manual Deployment

If you prefer to deploy manually:

1. Set up scheduled tasks:
   ```powershell
   # Run as Administrator
   .\setup_adaptive_intelligence_tasks.ps1
   ```

2. Test the Adaptive Intelligence system:
   ```powershell
   .\activate_adaptive_intelligence.ps1 -mode initialize
   ```

### Verifying Deployment

To verify that the deployment was successful:

1. Check scheduled tasks:
   ```powershell
   Get-ScheduledTask | Where-Object {$_.TaskName -like "*TRAE*"} | Format-Table TaskName,State
   ```

2. Check the logs directory for log files

## Troubleshooting

### Linux

- **Service fails to start**: Check the logs with `journalctl -u trae-bot`
- **Cron jobs not running**: Verify cron service is running with `systemctl status cron`
- **Permission issues**: Ensure all scripts have execute permission with `chmod +x *.sh`

### Windows

- **PowerShell execution policy**: If scripts won't run, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- **Scheduled tasks not running**: Check Task Scheduler for error details
- **Python not found**: Ensure Python is in your PATH environment variable

## Additional Resources

For more information about the Adaptive Intelligence System, refer to the [ADAPTIVE_INTELLIGENCE_SYSTEM.md](ADAPTIVE_INTELLIGENCE_SYSTEM.md) documentation.