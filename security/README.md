# AI Trading Sentinel - Security Infrastructure

Comprehensive security framework for 24/7 trading bot operations with advanced threat detection, intrusion prevention, and automated monitoring.

## 🛡️ Security Components Overview

### Core Security Features
- **Multi-layered Defense**: Firewall, WAF, IDS/IPS, and behavioral monitoring
- **Real-time Threat Detection**: Continuous monitoring with instant alerts
- **Automated Response**: Fail2Ban integration with custom actions
- **File Integrity Monitoring**: AIDE-based change detection
- **Comprehensive Logging**: Centralized security event logging
- **Compliance Ready**: Audit trails and security reporting

## 📁 File Structure

```
security/
├── deploy-security.sh          # Main deployment script
├── security-scanner.sh         # Comprehensive security scanner
├── security-monitor.sh         # Real-time monitoring daemon
├── security-monitor.service    # Systemd service configuration
├── monitor.conf               # Monitoring configuration
├── nginx-security.conf        # Nginx WAF and security rules
├── fail2ban/
│   ├── jail.local            # Fail2Ban jail configuration
│   └── filter.d/             # Custom Fail2Ban filters
│       ├── nginx-exploits.conf
│       ├── nginx-api-abuse.conf
│       ├── nginx-login-bruteforce.conf
│       ├── nginx-sqli.conf
│       ├── nginx-xss.conf
│       └── nginx-badbots.conf
└── README.md                  # This documentation
```

## 🚀 Quick Deployment

### Prerequisites
- Ubuntu 22.04/24.04 LTS
- Root access
- Internet connection
- At least 2GB RAM and 10GB disk space

### One-Command Deployment
```bash
# Make deployment script executable and run
sudo chmod +x security/deploy-security.sh
sudo ./security/deploy-security.sh
```

### Manual Step-by-Step Deployment
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install security packages
sudo apt install -y fail2ban ufw nginx clamav aide auditd

# 3. Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 4. Deploy security configurations
sudo cp security/nginx-security.conf /etc/nginx/conf.d/
sudo cp security/fail2ban/jail.local /etc/fail2ban/
sudo cp security/fail2ban/filter.d/*.conf /etc/fail2ban/filter.d/

# 5. Start security services
sudo systemctl restart nginx fail2ban
sudo systemctl enable nginx fail2ban

# 6. Install monitoring daemon
sudo cp security/security-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable security-monitor
sudo systemctl start security-monitor
```

## 🔧 Configuration

### Environment Variables
Create `/etc/environment` or add to your shell profile:
```bash
# Slack notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Email notifications
export SECURITY_EMAIL="security@yourcompany.com"

# SMS notifications (optional)
export SMS_API_URL="https://api.sms-provider.com/send"
export SMS_API_KEY="your-sms-api-key"
export SMS_PHONE_NUMBERS="+1234567890,+0987654321"
```

### Monitoring Configuration
Edit `security/monitor.conf` to customize:
```bash
# Alert thresholds
ALERT_THRESHOLD_CRITICAL=1
ALERT_THRESHOLD_HIGH=5

# System resource thresholds
CPU_THRESHOLD_CRITICAL=95
MEMORY_THRESHOLD_CRITICAL=95
DISK_THRESHOLD_CRITICAL=95

# Monitoring intervals
MONITOR_INTERVAL=300  # 5 minutes
DEEP_SCAN_INTERVAL=3600  # 1 hour
```

### Fail2Ban Customization
Edit `security/fail2ban/jail.local`:
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1 YOUR_TRUSTED_IP

# Enable/disable specific jails
[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-rate-limit]
enabled = true
```

## 📊 Monitoring and Alerts

### Real-time Monitoring
```bash
# Check security monitor status
sudo systemctl status security-monitor

# View live security logs
sudo tail -f /var/log/security-monitor/monitor.log

# Check active alerts
sudo ls -la /opt/ai-trading-sentinel/security/alerts/

# View latest security report
sudo find /opt/ai-trading-sentinel/security/reports -name "*.json" -newest
```

### Manual Security Scans
```bash
# Run comprehensive security scan
sudo ./security/security-scanner.sh

# Quick system check
sudo ./security/security-scanner.sh --quick

# Generate security report
sudo ./security/security-scanner.sh --report-only
```

### Fail2Ban Management
```bash
# Check Fail2Ban status
sudo fail2ban-client status

# Check specific jail
sudo fail2ban-client status nginx-rate-limit

# Unban IP address
sudo fail2ban-client set nginx-rate-limit unbanip 192.168.1.100

# View banned IPs
sudo fail2ban-client banned
```

## 🚨 Alert Types and Responses

### Critical Alerts (Immediate Action Required)
- **File Integrity Violations**: Critical system files modified
- **Root Access Attempts**: Unauthorized root login attempts
- **Service Failures**: Security services stopped or crashed
- **Resource Exhaustion**: System resources critically low

### High Priority Alerts
- **Multiple Failed Logins**: Brute force attack detected
- **Suspicious Network Activity**: Unusual connection patterns
- **Malware Detection**: Virus or malware found
- **Configuration Changes**: Security configuration modified

### Medium Priority Alerts
- **High Resource Usage**: System performance degraded
- **Security Updates Available**: Patches need installation
- **Log Anomalies**: Unusual log patterns detected
- **Network Scanning**: Port scanning activity

### Low Priority Alerts
- **Information Gathering**: Reconnaissance attempts
- **Minor Policy Violations**: Non-critical security events
- **Maintenance Reminders**: Scheduled maintenance due

## 🔍 Security Scanning

### Automated Scans
- **System Security Audit**: Lynis-based comprehensive scan
- **Rootkit Detection**: RKHunter and chkrootkit
- **Malware Scanning**: ClamAV full system scan
- **Network Security**: Nmap port scanning
- **Web Vulnerability**: Nikto web server scan
- **Code Security**: Bandit Python security analysis

### Manual Security Tests
```bash
# Network security scan
sudo nmap -sS -O localhost

# Web application scan
sudo nikto -h http://localhost

# System audit
sudo lynis audit system

# Rootkit check
sudo rkhunter --check
sudo chkrootkit

# File integrity check
sudo aide --check

# Malware scan
sudo clamscan -r /home /opt /var/www
```

## 🛠️ Maintenance and Updates

### Daily Maintenance
```bash
# Update virus definitions
sudo freshclam

# Update security signatures
sudo rkhunter --update

# Check system logs
sudo journalctl -p err -since "1 day ago"
```

### Weekly Maintenance
```bash
# Run automated maintenance
sudo /usr/local/bin/security-maintenance

# Update AIDE database
sudo aide --update
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Security audit
sudo lynis audit system --quick
```

### Monthly Maintenance
```bash
# Full security scan
sudo ./security/security-scanner.sh --full

# Review security logs
sudo logrotate -f /etc/logrotate.d/security

# Update security tools
sudo apt update && sudo apt upgrade
sudo pip3 install --upgrade bandit safety semgrep
```

## 📈 Performance Optimization

### Resource Management
```bash
# Monitor security service resource usage
sudo systemctl status security-monitor
sudo ps aux | grep -E '(fail2ban|clamav|aide)'

# Optimize ClamAV scanning
sudo sed -i 's/#OnAccessMaxFileSize 5M/OnAccessMaxFileSize 10M/' /etc/clamav/clamd.conf

# Tune Fail2Ban performance
sudo sed -i 's/backend = auto/backend = systemd/' /etc/fail2ban/jail.local
```

### Log Management
```bash
# Configure log rotation
sudo logrotate -d /etc/logrotate.d/security

# Clean old logs
sudo find /var/log -name "*.log.*.gz" -mtime +90 -delete

# Monitor log sizes
sudo du -sh /var/log/*
```

## 🔐 Security Best Practices

### SSH Hardening
- Disable root login
- Use key-based authentication only
- Change default SSH port (optional)
- Implement connection rate limiting
- Enable SSH banner warnings

### Web Security
- Enable HTTPS with strong SSL/TLS
- Implement Content Security Policy (CSP)
- Use security headers (HSTS, X-Frame-Options)
- Rate limit API endpoints
- Hide server version information

### System Hardening
- Regular security updates
- Minimal service exposure
- Strong password policies
- File permission auditing
- Network segmentation

### Application Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF token implementation
- Secure session management

## 🚨 Incident Response

### Security Incident Workflow
1. **Detection**: Automated monitoring alerts
2. **Assessment**: Determine severity and impact
3. **Containment**: Isolate affected systems
4. **Investigation**: Analyze logs and evidence
5. **Remediation**: Fix vulnerabilities and restore services
6. **Recovery**: Return to normal operations
7. **Lessons Learned**: Update security measures

### Emergency Procedures
```bash
# Emergency system lockdown
sudo ufw deny incoming
sudo systemctl stop nginx
sudo fail2ban-client stop

# Isolate compromised system
sudo iptables -A INPUT -j DROP
sudo iptables -A OUTPUT -j DROP

# Preserve evidence
sudo dd if=/dev/sda of=/mnt/evidence/disk_image.dd
sudo tar -czf /mnt/evidence/logs_$(date +%Y%m%d).tar.gz /var/log

# Emergency contact
echo "Security incident detected on $(hostname) at $(date)" | \
  mail -s "URGENT: Security Incident" security@company.com
```

## 📞 Support and Troubleshooting

### Common Issues

#### Security Monitor Not Starting
```bash
# Check service status
sudo systemctl status security-monitor

# Check logs
sudo journalctl -u security-monitor -f

# Restart service
sudo systemctl restart security-monitor
```

#### Fail2Ban Not Blocking IPs
```bash
# Check jail status
sudo fail2ban-client status

# Test filter patterns
sudo fail2ban-regex /var/log/nginx/access.log /etc/fail2ban/filter.d/nginx-rate-limit.conf

# Restart Fail2Ban
sudo systemctl restart fail2ban
```

#### High False Positive Alerts
```bash
# Adjust thresholds in monitor.conf
sudo nano /opt/ai-trading-sentinel/security/monitor.conf

# Whitelist trusted IPs
sudo nano /etc/fail2ban/jail.local
# Add to ignoreip = 127.0.0.1/8 ::1 YOUR_TRUSTED_IP

# Restart services
sudo systemctl restart fail2ban security-monitor
```

### Log Locations
- **Security Monitor**: `/var/log/security-monitor/`
- **Fail2Ban**: `/var/log/fail2ban.log`
- **Nginx**: `/var/log/nginx/`
- **System Auth**: `/var/log/auth.log`
- **Security Alerts**: `/var/log/security-alerts.log`
- **Audit**: `/var/log/audit/`

### Performance Tuning
```bash
# Reduce monitoring frequency for better performance
sudo sed -i 's/MONITOR_INTERVAL=300/MONITOR_INTERVAL=600/' /opt/ai-trading-sentinel/security/monitor.conf

# Optimize ClamAV for lower resource usage
sudo sed -i 's/#MaxThreads 12/MaxThreads 2/' /etc/clamav/clamd.conf

# Reduce Fail2Ban log processing
sudo sed -i 's/maxlines = 10/maxlines = 5/' /etc/fail2ban/jail.local
```

## 📚 Additional Resources

### Documentation
- [Fail2Ban Documentation](https://fail2ban.readthedocs.io/)
- [Nginx Security Guide](https://nginx.org/en/docs/http/ngx_http_security_module.html)
- [Ubuntu Security Guide](https://ubuntu.com/security)
- [OWASP Security Guidelines](https://owasp.org/)

### Security Tools
- [Lynis Security Auditing](https://cisofy.com/lynis/)
- [AIDE File Integrity](https://aide.github.io/)
- [ClamAV Antivirus](https://www.clamav.net/)
- [RKHunter Rootkit Detection](http://rkhunter.sourceforge.net/)

### Compliance Frameworks
- **PCI DSS**: Payment Card Industry Data Security Standard
- **SOC 2**: Service Organization Control 2
- **ISO 27001**: Information Security Management
- **GDPR**: General Data Protection Regulation

## 🏆 Security Metrics and KPIs

### Key Performance Indicators
- **Mean Time to Detection (MTTD)**: < 5 minutes
- **Mean Time to Response (MTTR)**: < 15 minutes
- **False Positive Rate**: < 5%
- **Security Incident Count**: Track monthly
- **Vulnerability Remediation Time**: < 24 hours for critical
- **System Uptime**: > 99.9%

### Monitoring Dashboard
```bash
# Generate security metrics report
sudo ./security/security-scanner.sh --metrics

# View real-time security status
watch -n 30 'sudo fail2ban-client status && echo && sudo systemctl status security-monitor'

# Security health check
sudo ./security/security-monitor.sh status
```

---

## 🎯 Conclusion

This comprehensive security framework provides enterprise-grade protection for the AI Trading Sentinel platform. The multi-layered approach ensures robust defense against various threat vectors while maintaining system performance and operational efficiency.

**Key Benefits:**
- ✅ **24/7 Automated Monitoring**: Continuous threat detection and response
- ✅ **Real-time Alerts**: Instant notifications via Slack, email, and SMS
- ✅ **Comprehensive Coverage**: Network, system, application, and data security
- ✅ **Compliance Ready**: Audit trails and security reporting
- ✅ **Scalable Architecture**: Supports multi-account and multi-environment deployments
- ✅ **Easy Management**: Automated deployment and maintenance scripts

For additional support or custom security requirements, please refer to the troubleshooting section or contact the security team.

**Remember**: Security is an ongoing process, not a one-time setup. Regular updates, monitoring, and incident response planning are essential for maintaining a strong security posture.