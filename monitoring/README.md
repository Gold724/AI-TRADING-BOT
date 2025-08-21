# Trae AI Trading Sentinel - Production Monitoring Stack

## Overview

This monitoring stack provides comprehensive 24/7 observability for the Trae AI Trading Sentinel system, ensuring reliable operation and early detection of issues in production environments.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trading Bot   │───▶│   Prometheus    │───▶│    Grafana      │
│   (main.py)     │    │  (Metrics DB)   │    │  (Dashboard)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Health Checks  │    │  Alertmanager   │    │   Notifications │
│  (SystemD)      │    │  (Alert Rules)  │    │ (Slack/Email)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Prometheus (Port 9090)
- **Purpose**: Metrics collection and storage
- **Retention**: 30 days
- **Scrape Interval**: 15 seconds
- **Storage**: 10GB limit with automatic cleanup

### 2. Grafana (Port 3000)
- **Purpose**: Visualization and dashboards
- **Default Login**: admin/admin (change on first login)
- **Features**: 
  - Real-time trading metrics
  - System resource monitoring
  - Alert visualization
  - Custom dashboards

### 3. Alertmanager (Port 9093)
- **Purpose**: Alert routing and notifications
- **Features**:
  - Multi-channel notifications (Slack, Email)
  - Alert grouping and deduplication
  - Escalation policies
  - Silence management

### 4. Node Exporter (Port 9100)
- **Purpose**: System metrics collection
- **Metrics**: CPU, Memory, Disk, Network, Load

### 5. cAdvisor (Port 8080)
- **Purpose**: Container metrics (if using Docker)
- **Metrics**: Container resource usage, performance

## Quick Start

### 1. Deploy Monitoring Stack

```bash
# On your Contabo VPS
sudo ./deploy/setup-monitoring.sh
```

### 2. Start Services

```bash
# Start monitoring stack
cd /opt/trae-sentinel/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps
```

### 3. Access Dashboards

- **Grafana**: http://your-vps-ip:3000
- **Prometheus**: http://your-vps-ip:9090
- **Alertmanager**: http://your-vps-ip:9093

## Configuration

### Prometheus Configuration

Edit `prometheus.yml` to customize:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'trae-bot'
    static_configs:
      - targets: ['localhost:5000']
    scrape_interval: 5s
    params:
      format: ['prometheus']
```

### Alert Rules

Customize alerts in `alert_rules.yml`:

```yaml
groups:
  - name: trading_alerts
    rules:
      - alert: TradingBotDown
        expr: up{job="trae-bot"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Trading bot is down"
```

### Grafana Dashboards

The system includes pre-configured dashboards:

1. **System Overview**: CPU, Memory, Disk usage
2. **Trading Performance**: Trades, P&L, Success rate
3. **System Health**: Error rates, Response times
4. **Alert Status**: Active alerts and notifications

## Alert Configuration

### Slack Integration

1. Create a Slack webhook URL
2. Update `alertmanager.yml`:

```yaml
receivers:
  - name: 'slack-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#trae-alerts'
        title: 'Trae Sentinel Alert'
```

### Email Notifications

1. Configure SMTP settings in `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
```

## Health Monitoring

### SystemD Health Checks

The system includes automated health monitoring:

```bash
# Manual health check
/opt/trae-sentinel/scripts/health-check.sh

# View health check logs
journalctl -u trae-sentinel-monitor.service -f
```

### System Monitoring

```bash
# Manual system check
/opt/trae-sentinel/scripts/system-monitor.sh --report

# View system metrics
tail -f /var/log/trae-sentinel/system-metrics.log
```

## Key Metrics

### System Metrics
- **CPU Usage**: Target < 80%, Alert > 95%
- **Memory Usage**: Target < 85%, Alert > 95%
- **Disk Usage**: Target < 80%, Alert > 90%
- **Load Average**: Monitor 1min, 5min, 15min

### Trading Metrics
- **Trade Execution Rate**: Trades per hour
- **Success Rate**: Successful trades percentage
- **API Response Time**: Target < 1s, Alert > 5s
- **Error Rate**: Target < 0.1%, Alert > 1%
- **P&L Tracking**: Real-time profit/loss
- **Position Size**: Current exposure
- **Drawdown**: Maximum loss from peak

### Application Metrics
- **Process Status**: Main bot process health
- **Memory Leaks**: Process memory growth
- **Connection Status**: Broker connectivity
- **Login Success**: Authentication status

## Troubleshooting

### Common Issues

1. **Grafana not accessible**
   ```bash
   # Check container status
   docker ps | grep grafana
   
   # Check logs
   docker logs tradebot-grafana
   
   # Restart if needed
   docker-compose restart grafana
   ```

2. **Prometheus not scraping**
   ```bash
   # Check targets in Prometheus UI
   # Go to: http://your-ip:9090/targets
   
   # Verify bot is exposing metrics
   curl http://localhost:5000/metrics
   ```

3. **Alerts not firing**
   ```bash
   # Check alert rules
   # Go to: http://your-ip:9090/alerts
   
   # Verify alertmanager config
   docker logs tradebot-alertmanager
   ```

### Log Locations

- **Application Logs**: `/var/log/trae-sentinel/`
- **SystemD Logs**: `journalctl -u trae.service`
- **Docker Logs**: `docker logs <container-name>`
- **System Metrics**: `/var/log/trae-sentinel/system-metrics.log`
- **Health Checks**: `/var/log/trae-sentinel/health-check.log`

## Maintenance

### Regular Tasks

1. **Weekly**:
   - Review alert history
   - Check disk usage trends
   - Verify backup integrity

2. **Monthly**:
   - Update monitoring stack
   - Review and tune alert thresholds
   - Analyze performance trends

3. **Quarterly**:
   - Security updates
   - Capacity planning review
   - Disaster recovery testing

### Updates

```bash
# Update monitoring stack
cd /opt/trae-sentinel/monitoring
docker-compose -f docker-compose.monitoring.yml pull
docker-compose -f docker-compose.monitoring.yml up -d
```

### Backup

```bash
# Backup monitoring data
docker run --rm -v monitoring_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data
docker run --rm -v monitoring_grafana_data:/data -v $(pwd):/backup alpine tar czf /backup/grafana-backup.tar.gz /data
```

## Security

### Network Security
- Monitoring ports restricted to local network
- Firewall rules configured automatically
- No external access to sensitive metrics

### Authentication
- Grafana: Change default admin password
- Prometheus: Admin API disabled in production
- Alertmanager: Configure webhook authentication

### Data Protection
- Metrics retention limited to 30 days
- No sensitive data in metric labels
- Secure credential storage

## Performance Tuning

### Prometheus Optimization
```yaml
# In prometheus.yml
global:
  scrape_interval: 15s  # Increase for lower resource usage
  evaluation_interval: 15s

# Reduce retention for lower disk usage
command:
  - '--storage.tsdb.retention.time=15d'
```

### Grafana Optimization
```yaml
# In grafana configuration
environment:
  - GF_RENDERING_SERVER_URL=http://renderer:8081/render
  - GF_RENDERING_CALLBACK_URL=http://grafana:3000/
  - GF_LOG_FILTERS=rendering:debug
```

## Support

For issues and questions:

1. **Check logs**: Start with application and system logs
2. **Review metrics**: Use Grafana dashboards for insights
3. **Health checks**: Run manual health and system checks
4. **Documentation**: Refer to component-specific docs

## Advanced Configuration

### Custom Metrics

Add custom metrics to your trading bot:

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
trades_total = Counter('trae_trades_total', 'Total number of trades')
trade_duration = Histogram('trae_trade_duration_seconds', 'Trade execution time')
current_position = Gauge('trae_current_position', 'Current position size')

# Use in your code
trades_total.inc()
with trade_duration.time():
    execute_trade()
current_position.set(position_size)
```

### Custom Dashboards

Create custom Grafana dashboards:

1. Access Grafana UI
2. Create new dashboard
3. Add panels with PromQL queries
4. Export JSON for version control

### Integration with CI/CD

```yaml
# In GitHub Actions
- name: Deploy Monitoring
  run: |
    ssh user@vps 'cd /opt/trae-sentinel && docker-compose -f monitoring/docker-compose.monitoring.yml up -d'
```

This monitoring stack ensures your Trae AI Trading Sentinel operates reliably in production with comprehensive observability and alerting.