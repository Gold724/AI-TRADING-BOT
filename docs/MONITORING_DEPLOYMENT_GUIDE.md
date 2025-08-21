# AI Trading Sentinel - Complete Monitoring Deployment Guide

This guide provides comprehensive instructions for deploying the complete monitoring infrastructure for the AI Trading Sentinel on a Contabo VPS or similar cloud server.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS
- **RAM**: Minimum 4GB (8GB recommended)
- **CPU**: 2+ cores
- **Storage**: 50GB+ SSD
- **Network**: Stable internet connection

### Required Access
- Root/sudo access to the VPS
- SSH access configured
- Domain name (optional but recommended)
- Slack workspace for alerts (recommended)

## 🚀 Quick Start

### 1. Initial Server Setup

```bash
# Connect to your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y git curl wget htop nano ufw

# Configure firewall
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 3000  # Frontend
ufw allow 3001  # Grafana
ufw allow 5000  # API
ufw allow 9090  # Prometheus
ufw allow 9093  # Alertmanager
ufw --force enable
```

### 2. Clone Repository

```bash
# Clone the project
cd /opt
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel

# Set permissions
chown -R root:root /opt/ai-trading-sentinel
chmod +x scripts/*.py
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```bash
# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email Alerts
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@your-domain.com
ADMIN_EMAIL=admin@your-domain.com
DEV_EMAIL=dev@your-domain.com

# Grafana
GRAFANA_ADMIN_PASSWORD=your-secure-password

# Security
JWT_SECRET_KEY=your-jwt-secret
API_SECRET_KEY=your-api-secret

# Trading Configuration
BROKER_USERNAME=your-broker-username
BROKER_PASSWORD=your-broker-password
BROKER_API_KEY=your-broker-api-key
```

### 4. Run Complete Monitoring Setup

```bash
# Make setup script executable
chmod +x scripts/setup_monitoring_complete.py

# Install Python dependencies
apt install -y python3-pip python3-venv
pip3 install pyyaml requests psutil

# Run the complete monitoring setup
python3 scripts/setup_monitoring_complete.py
```

## 📊 Manual Setup (Alternative)

If you prefer manual setup or need to customize the installation:

### Step 1: Install Prometheus

```bash
# Create prometheus user
useradd --no-create-home --shell /bin/false prometheus

# Create directories
mkdir -p /opt/trading/monitoring/prometheus/{data,rules,consoles,console_libraries}
chown -R prometheus:prometheus /opt/trading/monitoring/prometheus

# Download and install Prometheus
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar -xzf prometheus-2.45.0.linux-amd64.tar.gz
cp prometheus-2.45.0.linux-amd64/prometheus /usr/local/bin/
cp prometheus-2.45.0.linux-amd64/promtool /usr/local/bin/
cp -r prometheus-2.45.0.linux-amd64/consoles /opt/trading/monitoring/prometheus/
cp -r prometheus-2.45.0.linux-amd64/console_libraries /opt/trading/monitoring/prometheus/
chown -R prometheus:prometheus /opt/trading/monitoring/prometheus
chmod +x /usr/local/bin/prometheus /usr/local/bin/promtool
```

### Step 2: Install Grafana

```bash
# Add Grafana repository
wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list

# Install Grafana
apt update
apt install -y grafana

# Configure Grafana
systemctl enable grafana-server
systemctl start grafana-server
```

### Step 3: Install Alertmanager

```bash
# Download and install Alertmanager
cd /tmp
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
tar -xzf alertmanager-0.25.0.linux-amd64.tar.gz
cp alertmanager-0.25.0.linux-amd64/alertmanager /usr/local/bin/
cp alertmanager-0.25.0.linux-amd64/amtool /usr/local/bin/
chmod +x /usr/local/bin/alertmanager /usr/local/bin/amtool

# Create directories
mkdir -p /opt/trading/monitoring/alertmanager/data
chown -R prometheus:prometheus /opt/trading/monitoring/alertmanager
```

### Step 4: Install Exporters

```bash
# Node Exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
tar -xzf node_exporter-1.6.0.linux-amd64.tar.gz
cp node_exporter-1.6.0.linux-amd64/node_exporter /usr/local/bin/
chmod +x /usr/local/bin/node_exporter

# Redis Exporter
wget https://github.com/oliver006/redis_exporter/releases/download/v1.51.0/redis_exporter-v1.51.0.linux-amd64.tar.gz
tar -xzf redis_exporter-v1.51.0.linux-amd64.tar.gz
cp redis_exporter-v1.51.0.linux-amd64/redis_exporter /usr/local/bin/
chmod +x /usr/local/bin/redis_exporter

# Nginx Exporter
wget https://github.com/nginxinc/nginx-prometheus-exporter/releases/download/v0.11.0/nginx-prometheus-exporter_0.11.0_linux_amd64.tar.gz
tar -xzf nginx-prometheus-exporter_0.11.0_linux_amd64.tar.gz
cp nginx-prometheus-exporter /usr/local/bin/
chmod +x /usr/local/bin/nginx-prometheus-exporter
```

## ⚙️ Configuration Files

### Prometheus Configuration

Create `/opt/trading/monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/opt/trading/monitoring/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'trading-api'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'trading-bot'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Alertmanager Configuration

Create `/opt/trading/monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@ai-trading-sentinel.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#trading-alerts'
    title: 'AI Trading Sentinel Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## 🔧 Systemd Services

### Create Service Files

**Prometheus Service** (`/etc/systemd/system/prometheus.service`):
```ini
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /opt/trading/monitoring/prometheus/prometheus.yml \
    --storage.tsdb.path /opt/trading/monitoring/prometheus/data \
    --web.console.templates=/opt/trading/monitoring/prometheus/consoles \
    --web.console.libraries=/opt/trading/monitoring/prometheus/console_libraries \
    --web.listen-address=0.0.0.0:9090 \
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
```

**Alertmanager Service** (`/etc/systemd/system/alertmanager.service`):
```ini
[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file=/opt/trading/monitoring/alertmanager/alertmanager.yml \
    --storage.path=/opt/trading/monitoring/alertmanager/data

[Install]
WantedBy=multi-user.target
```

**Node Exporter Service** (`/etc/systemd/system/node-exporter.service`):
```ini
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/node_exporter --web.listen-address=0.0.0.0:9100

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable prometheus alertmanager grafana-server node-exporter redis-exporter

# Start services
systemctl start prometheus alertmanager grafana-server node-exporter redis-exporter

# Check status
systemctl status prometheus alertmanager grafana-server
```

## 🔍 Health Monitoring Setup

### Deploy Health Monitor

```bash
# Copy health monitor script
cp scripts/health_monitor.py /opt/trading/scripts/
chmod +x /opt/trading/scripts/health_monitor.py

# Create systemd service
cp scripts/health-monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable health-monitor
systemctl start health-monitor
```

### Deploy Alert Manager

```bash
# Install Python dependencies
pip3 install jinja2 smtplib

# Test alert system
python3 scripts/alert_manager.py --test
```

## 📈 Grafana Dashboard Setup

### 1. Access Grafana

- URL: `http://your-vps-ip:3001`
- Default login: `admin/admin`
- Change password on first login

### 2. Configure Data Source

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL: `http://localhost:9090`
5. Click **Save & Test**

### 3. Import Dashboards

```bash
# Copy dashboard configurations
cp config/grafana_dashboards.json /var/lib/grafana/dashboards/
chown grafana:grafana /var/lib/grafana/dashboards/grafana_dashboards.json

# Restart Grafana
systemctl restart grafana-server
```

## 🚨 Alert Configuration

### 1. Copy Alert Rules

```bash
# Copy alert rules
cp config/alert_rules.yml /opt/trading/monitoring/prometheus/rules/
chown prometheus:prometheus /opt/trading/monitoring/prometheus/rules/alert_rules.yml

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

### 2. Test Alerts

```bash
# Test Slack integration
python3 scripts/alert_manager.py --create --service "test" --severity "warning" --title "Test Alert" --message "This is a test alert"

# Check Alertmanager
curl http://localhost:9093/api/v1/alerts
```

## 🔐 Security Configuration

### 1. SSL/TLS Setup (Optional)

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 2. Nginx Reverse Proxy

Create `/etc/nginx/sites-available/trading-monitoring`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /grafana/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /alertmanager/ {
        proxy_pass http://localhost:9093/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/trading-monitoring /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## ✅ Verification

### 1. Check Service Status

```bash
# Check all services
systemctl status prometheus alertmanager grafana-server node-exporter redis-exporter

# Check logs
journalctl -u prometheus -f
journalctl -u alertmanager -f
journalctl -u grafana-server -f
```

### 2. Test Endpoints

```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Alertmanager
curl http://localhost:9093/-/healthy

# Grafana
curl http://localhost:3001/api/health

# Exporters
curl http://localhost:9100/metrics
curl http://localhost:9121/metrics
```

### 3. Run Verification Script

```bash
python3 scripts/setup_monitoring_complete.py --verify-only
```

## 🔧 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   journalctl -u service-name -n 50
   
   # Check configuration
   promtool check config /opt/trading/monitoring/prometheus/prometheus.yml
   ```

2. **Permission errors**
   ```bash
   # Fix ownership
   chown -R prometheus:prometheus /opt/trading/monitoring/
   ```

3. **Port conflicts**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :9090
   ```

4. **Firewall issues**
   ```bash
   # Check UFW status
   ufw status
   
   # Allow specific ports
   ufw allow 9090
   ```

### Log Locations

- Prometheus: `journalctl -u prometheus`
- Grafana: `/var/log/grafana/grafana.log`
- Alertmanager: `journalctl -u alertmanager`
- Health Monitor: `/opt/trading/logs/health_monitor.log`

## 📱 Access Information

After successful deployment:

| Service | URL | Default Credentials |
|---------|-----|--------------------|
| Prometheus | `http://your-vps-ip:9090` | None |
| Grafana | `http://your-vps-ip:3001` | admin/admin |
| Alertmanager | `http://your-vps-ip:9093` | None |
| Trading API | `http://your-vps-ip:5000` | API Key required |
| Frontend | `http://your-vps-ip:3000` | None |

## 🔄 Maintenance

### Regular Tasks

1. **Update monitoring stack**
   ```bash
   # Update Prometheus
   systemctl stop prometheus
   # Download new version and replace binary
   systemctl start prometheus
   ```

2. **Backup configurations**
   ```bash
   # Create backup
   tar -czf monitoring-backup-$(date +%Y%m%d).tar.gz /opt/trading/monitoring/
   ```

3. **Clean old data**
   ```bash
   # Prometheus data retention is configured in prometheus.yml
   # Grafana dashboard versions are limited in configuration
   ```

### Monitoring the Monitors

- Set up external monitoring (e.g., UptimeRobot) for critical endpoints
- Configure log rotation for monitoring logs
- Regular backup of Grafana dashboards and Prometheus data

## 🆘 Support

For issues and support:

1. Check the troubleshooting section above
2. Review service logs using `journalctl`
3. Verify configuration files
4. Check network connectivity and firewall rules
5. Consult official documentation:
   - [Prometheus Documentation](https://prometheus.io/docs/)
   - [Grafana Documentation](https://grafana.com/docs/)
   - [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

---

**Next Steps**: After completing the monitoring setup, proceed to deploy the trading application and configure the CI/CD pipeline for automated deployments.