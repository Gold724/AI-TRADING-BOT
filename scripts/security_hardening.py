#!/usr/bin/env python3
"""
AI Trading Sentinel - Security Hardening Script
Advanced security implementation for production deployment
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import yaml
from cryptography.fernet import Fernet
import secrets
import string

class SecurityHardening:
    """Advanced security hardening for AI Trading Sentinel"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.security_dir = self.project_root / "security"
        self.config_dir = self.security_dir / "config"
        self.certs_dir = self.security_dir / "certs"
        self.keys_dir = self.security_dir / "keys"
        
        # Create security directories
        self._create_directories()
        
        print(f"🔒 Security Hardening initialized")
        print(f"📁 Security directory: {self.security_dir}")
    
    def _create_directories(self):
        """Create security directories"""
        directories = [
            self.security_dir,
            self.config_dir,
            self.certs_dir,
            self.keys_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions
            os.chmod(directory, 0o700)
        
        print(f"✅ Security directories created with restrictive permissions")
    
    def generate_encryption_keys(self) -> Dict[str, str]:
        """Generate encryption keys for sensitive data"""
        print("\n🔑 Generating encryption keys...")
        
        keys = {}
        
        # Generate Fernet key for symmetric encryption
        fernet_key = Fernet.generate_key()
        keys['fernet_key'] = fernet_key.decode('utf-8')
        
        # Generate JWT secret key
        jwt_secret = secrets.token_urlsafe(64)
        keys['jwt_secret'] = jwt_secret
        
        # Generate Flask secret key
        flask_secret = secrets.token_urlsafe(32)
        keys['flask_secret'] = flask_secret
        
        # Generate API keys
        api_key = secrets.token_urlsafe(32)
        keys['api_key'] = api_key
        
        # Generate webhook secret
        webhook_secret = secrets.token_urlsafe(32)
        keys['webhook_secret'] = webhook_secret
        
        # Save keys to secure file
        keys_file = self.keys_dir / "encryption_keys.json"
        with open(keys_file, 'w') as f:
            json.dump(keys, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(keys_file, 0o600)
        
        print(f"✅ Encryption keys generated and saved to {keys_file}")
        return keys
    
    def setup_ssl_certificates(self) -> bool:
        """Setup SSL certificates for HTTPS"""
        print("\n🔐 Setting up SSL certificates...")
        
        try:
            # Generate self-signed certificate for development/testing
            cert_file = self.certs_dir / "server.crt"
            key_file = self.certs_dir / "server.key"
            
            # Generate private key
            subprocess.run([
                'openssl', 'genrsa', '-out', str(key_file), '2048'
            ], check=True, capture_output=True)
            
            # Generate certificate signing request
            csr_file = self.certs_dir / "server.csr"
            subprocess.run([
                'openssl', 'req', '-new', '-key', str(key_file),
                '-out', str(csr_file), '-subj',
                '/C=US/ST=State/L=City/O=AI-Trading-Sentinel/CN=localhost'
            ], check=True, capture_output=True)
            
            # Generate self-signed certificate
            subprocess.run([
                'openssl', 'x509', '-req', '-days', '365',
                '-in', str(csr_file), '-signkey', str(key_file),
                '-out', str(cert_file)
            ], check=True, capture_output=True)
            
            # Set permissions
            os.chmod(key_file, 0o600)
            os.chmod(cert_file, 0o644)
            
            # Create certificate chain file
            chain_file = self.certs_dir / "fullchain.pem"
            with open(chain_file, 'w') as chain, open(cert_file, 'r') as cert:
                chain.write(cert.read())
            
            print(f"✅ SSL certificates generated")
            print(f"📄 Certificate: {cert_file}")
            print(f"🔑 Private key: {key_file}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ SSL certificate generation failed: {e}")
            return False
        except Exception as e:
            print(f"❌ SSL setup error: {e}")
            return False
    
    def create_nginx_security_config(self) -> bool:
        """Create Nginx security configuration"""
        print("\n🛡️  Creating Nginx security configuration...")
        
        nginx_config = f"""
# AI Trading Sentinel - Nginx Security Configuration

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;

# Security headers map
map $sent_http_content_type $content_type_csp {{
    ~^text/html "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' wss: https:; frame-ancestors 'none';";
    default "default-src 'none';";
}}

server {{
    listen 80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate {self.certs_dir}/server.crt;
    ssl_certificate_key {self.certs_dir}/server.key;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy $content_type_csp always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # Hide server information
    server_tokens off;
    
    # Connection limits
    limit_conn conn_limit_per_ip 20;
    
    # Request size limits
    client_max_body_size 10M;
    client_body_buffer_size 128k;
    
    # Timeout settings
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Buffer overflow protection
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    # API endpoints with rate limiting
    location /api/ {{
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security headers for API
        add_header X-API-Version "1.0" always;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }}
    
    # Login endpoint with strict rate limiting
    location /api/auth/login {{
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # WebSocket connections
    location /ws {{
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Static files
    location /static/ {{
        alias /opt/ai-trading-sentinel/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Security for static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # Frontend application
    location / {{
        root /opt/ai-trading-sentinel/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # Block access to sensitive files
    location ~ /\. {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    location ~ /(config|logs|backups|keys|certs)/ {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    # Block common attack patterns
    location ~* /(wp-admin|wp-login|phpmyadmin|admin|administrator) {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # Logging
    access_log /var/log/nginx/ai-trading-sentinel.access.log;
    error_log /var/log/nginx/ai-trading-sentinel.error.log warn;
}}
"""
        
        config_file = self.config_dir / "nginx_security.conf"
        with open(config_file, 'w') as f:
            f.write(nginx_config)
        
        print(f"✅ Nginx security configuration created: {config_file}")
        return True
    
    def create_fail2ban_config(self) -> bool:
        """Create Fail2ban configuration for intrusion prevention"""
        print("\n🚫 Creating Fail2ban configuration...")
        
        # Fail2ban jail configuration
        jail_config = """
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = auto

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/ai-trading-sentinel.error.log
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/ai-trading-sentinel.error.log
maxretry = 10
findtime = 600
bantime = 3600

[trading-api-auth]
enabled = true
filter = trading-api-auth
logpath = /var/log/ai-trading-sentinel/api.log
maxretry = 5
findtime = 300
bantime = 1800

[trading-bot-suspicious]
enabled = true
filter = trading-bot-suspicious
logpath = /var/log/ai-trading-sentinel/bot.log
maxretry = 3
findtime = 600
bantime = 7200
"""
        
        jail_file = self.config_dir / "jail.local"
        with open(jail_file, 'w') as f:
            f.write(jail_config)
        
        # Custom filters
        filters = {
            "nginx-http-auth": """
[Definition]
failregex = ^ \[error\] \d+#\d+: \*\d+ user \"\S+\":
            ^ \[error\] \d+#\d+: \*\d+ no user/password was provided for basic authentication
ignoreregex =
""",
            "nginx-limit-req": """
[Definition]
failregex = limiting requests, excess: [\d\.]+ by zone \".*\", client: <HOST>
ignoreregex =
""",
            "trading-api-auth": """
[Definition]
failregex = Authentication failed for IP: <HOST>
            Invalid API key from IP: <HOST>
            Suspicious login attempt from IP: <HOST>
ignoreregex =
""",
            "trading-bot-suspicious": """
[Definition]
failregex = Suspicious trading activity detected from IP: <HOST>
            Unauthorized bot access attempt from IP: <HOST>
            Bot manipulation detected from IP: <HOST>
ignoreregex =
"""
        }
        
        for filter_name, filter_config in filters.items():
            filter_file = self.config_dir / f"{filter_name}.conf"
            with open(filter_file, 'w') as f:
                f.write(filter_config)
        
        print(f"✅ Fail2ban configuration created")
        return True
    
    def create_firewall_rules(self) -> bool:
        """Create UFW firewall rules"""
        print("\n🔥 Creating firewall rules...")
        
        firewall_script = f"""
#!/bin/bash
# AI Trading Sentinel - Firewall Configuration

set -e

echo "🔥 Configuring UFW firewall..."

# Reset UFW to defaults
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (change port if using non-standard)
ufw allow 22/tcp comment 'SSH'

# Allow HTTP and HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Allow monitoring ports (restrict to specific IPs in production)
ufw allow from 127.0.0.1 to any port 9090 comment 'Prometheus'
ufw allow from 127.0.0.1 to any port 3001 comment 'Grafana'
ufw allow from 127.0.0.1 to any port 9093 comment 'Alertmanager'

# Allow Redis (local only)
ufw allow from 127.0.0.1 to any port 6379 comment 'Redis'

# Allow API ports (local only)
ufw allow from 127.0.0.1 to any port 5000 comment 'Trading API'
ufw allow from 127.0.0.1 to any port 5001 comment 'Trading Bot'
ufw allow from 127.0.0.1 to any port 5002 comment 'Trading Monitor'

# Rate limiting for SSH
ufw limit ssh comment 'SSH rate limiting'

# Enable UFW
ufw --force enable

# Show status
ufw status verbose

echo "✅ Firewall configured successfully"
"""
        
        firewall_file = self.config_dir / "setup_firewall.sh"
        with open(firewall_file, 'w') as f:
            f.write(firewall_script)
        
        os.chmod(firewall_file, 0o755)
        
        print(f"✅ Firewall configuration script created: {firewall_file}")
        return True
    
    def create_security_monitoring(self) -> bool:
        """Create security monitoring configuration"""
        print("\n👁️  Creating security monitoring...")
        
        # Security monitoring script
        monitoring_script = f"""
#!/usr/bin/env python3
"""
AI Trading Sentinel - Security Monitoring
Real-time security event monitoring and alerting
"""

import os
import re
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import subprocess

class SecurityMonitor:
    def __init__(self):
        self.log_files = {{
            'nginx_access': '/var/log/nginx/ai-trading-sentinel.access.log',
            'nginx_error': '/var/log/nginx/ai-trading-sentinel.error.log',
            'auth_log': '/var/log/auth.log',
            'api_log': '/var/log/ai-trading-sentinel/api.log',
            'bot_log': '/var/log/ai-trading-sentinel/bot.log'
        }}
        
        self.alert_patterns = {{
            'brute_force': r'Failed password for .* from ([0-9.]+)',
            'sql_injection': r'(union|select|insert|delete|drop|create|alter).*from',
            'xss_attempt': r'<script|javascript:|onload=|onerror=',
            'path_traversal': r'\.\.[\\/]',
            'suspicious_user_agent': r'(sqlmap|nikto|nmap|masscan|zap)',
            'rate_limit_exceeded': r'limiting requests.*client: ([0-9.]+)',
            'authentication_failure': r'Authentication failed.*IP: ([0-9.]+)'
        }}
        
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    def monitor_logs(self):
        """Monitor log files for security events"""
        print("🔍 Starting security monitoring...")
        
        while True:
            try:
                for log_name, log_path in self.log_files.items():
                    if os.path.exists(log_path):
                        self.check_log_file(log_name, log_path)
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                print("\n🛑 Security monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {{e}}")
                time.sleep(30)
    
    def check_log_file(self, log_name: str, log_path: str):
        """Check log file for security patterns"""
        try:
            # Get last 100 lines
            result = subprocess.run(
                ['tail', '-n', '100', log_path],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    self.analyze_log_line(log_name, line)
                    
        except Exception as e:
            print(f"⚠️  Error checking {{log_path}}: {{e}}")
    
    def analyze_log_line(self, log_name: str, line: str):
        """Analyze log line for security threats"""
        for pattern_name, pattern in self.alert_patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                self.send_security_alert({{
                    'type': pattern_name,
                    'log_source': log_name,
                    'line': line.strip(),
                    'ip_address': match.group(1) if match.groups() else 'unknown',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }})
    
    def send_security_alert(self, alert: Dict):
        """Send security alert notification"""
        if not self.webhook_url:
            return
        
        severity_colors = {{
            'brute_force': 'danger',
            'sql_injection': 'danger',
            'xss_attempt': 'warning',
            'path_traversal': 'warning',
            'suspicious_user_agent': 'warning',
            'rate_limit_exceeded': 'good',
            'authentication_failure': 'warning'
        }}
        
        color = severity_colors.get(alert['type'], 'warning')
        
        payload = {{
            "attachments": [{{
                "color": color,
                "title": f"🚨 Security Alert: {{alert['type'].replace('_', ' ').title()}}",
                "text": f"Security event detected on AI Trading Sentinel",
                "fields": [
                    {{"title": "Type", "value": alert['type'], "short": True}},
                    {{"title": "Source", "value": alert['log_source'], "short": True}},
                    {{"title": "IP Address", "value": alert['ip_address'], "short": True}},
                    {{"title": "Timestamp", "value": alert['timestamp'], "short": True}},
                    {{"title": "Details", "value": f"```{{alert['line'][:200]}}```", "short": False}}
                ]
            }}]
        }}
        
        try:
            requests.post(self.webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"❌ Failed to send alert: {{e}}")

if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.monitor_logs()
"""
        
        monitoring_file = self.config_dir / "security_monitor.py"
        with open(monitoring_file, 'w') as f:
            f.write(monitoring_script)
        
        os.chmod(monitoring_file, 0o755)
        
        # Create systemd service for security monitoring
        service_config = f"""
[Unit]
Description=AI Trading Sentinel Security Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.config_dir}
ExecStart=/usr/bin/python3 {monitoring_file}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.config_dir / "security-monitor.service"
        with open(service_file, 'w') as f:
            f.write(service_config)
        
        print(f"✅ Security monitoring created")
        return True
    
    def create_backup_encryption(self) -> bool:
        """Create encrypted backup system"""
        print("\n💾 Creating encrypted backup system...")
        
        backup_script = f"""
#!/bin/bash
# AI Trading Sentinel - Encrypted Backup Script

set -e

BACKUP_DIR="/opt/backups/encrypted"
SOURCE_DIR="/opt/ai-trading-sentinel"
ENCRYPTION_KEY_FILE="{self.keys_dir}/backup_key.txt"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="ai-trading-sentinel_$TIMESTAMP"

echo "💾 Starting encrypted backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate encryption key if it doesn't exist
if [ ! -f "$ENCRYPTION_KEY_FILE" ]; then
    openssl rand -base64 32 > "$ENCRYPTION_KEY_FILE"
    chmod 600 "$ENCRYPTION_KEY_FILE"
    echo "🔑 Generated new encryption key"
fi

# Create compressed archive
echo "📦 Creating archive..."
tar -czf "/tmp/$BACKUP_NAME.tar.gz" -C "$(dirname $SOURCE_DIR)" "$(basename $SOURCE_DIR)"

# Encrypt the archive
echo "🔐 Encrypting backup..."
openssl enc -aes-256-cbc -salt -in "/tmp/$BACKUP_NAME.tar.gz" -out "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" -pass file:"$ENCRYPTION_KEY_FILE"

# Cleanup unencrypted archive
rm "/tmp/$BACKUP_NAME.tar.gz"

# Create checksum
sha256sum "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" > "$BACKUP_DIR/$BACKUP_NAME.sha256"

# Remove old backups (keep last 7 days)
find "$BACKUP_DIR" -name "ai-trading-sentinel_*.tar.gz.enc" -mtime +7 -delete
find "$BACKUP_DIR" -name "ai-trading-sentinel_*.sha256" -mtime +7 -delete

echo "✅ Encrypted backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz.enc"
echo "📊 Backup size: $(du -h $BACKUP_DIR/$BACKUP_NAME.tar.gz.enc | cut -f1)"
"""
        
        backup_file = self.config_dir / "encrypted_backup.sh"
        with open(backup_file, 'w') as f:
            f.write(backup_script)
        
        os.chmod(backup_file, 0o755)
        
        # Create cron job for automated backups
        cron_config = f"""
# AI Trading Sentinel Automated Encrypted Backups
# Run daily at 2 AM
0 2 * * * root {backup_file} >> /var/log/ai-trading-sentinel/backup.log 2>&1

# Run weekly full system backup on Sundays at 3 AM
0 3 * * 0 root {backup_file} && rsync -av /opt/backups/encrypted/ backup-server:/remote/backups/ >> /var/log/ai-trading-sentinel/backup.log 2>&1
"""
        
        cron_file = self.config_dir / "backup_cron"
        with open(cron_file, 'w') as f:
            f.write(cron_config)
        
        print(f"✅ Encrypted backup system created")
        return True
    
    def generate_security_report(self) -> Dict:
        """Generate comprehensive security report"""
        print("\n📋 Generating security report...")
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "security_measures": {
                "encryption_keys": "Generated",
                "ssl_certificates": "Self-signed (replace with CA-signed for production)",
                "nginx_security": "Configured with security headers and rate limiting",
                "fail2ban": "Configured for intrusion prevention",
                "firewall": "UFW configured with restrictive rules",
                "security_monitoring": "Real-time log monitoring enabled",
                "encrypted_backups": "Automated encrypted backups configured"
            },
            "recommendations": [
                "Replace self-signed certificates with CA-signed certificates",
                "Configure external backup storage",
                "Set up centralized logging (ELK stack)",
                "Implement Web Application Firewall (WAF)",
                "Configure DDoS protection (Cloudflare)",
                "Set up vulnerability scanning (OpenVAS)",
                "Implement network segmentation",
                "Configure audit logging",
                "Set up honeypots for threat detection",
                "Implement multi-factor authentication"
            ],
            "next_steps": [
                "Deploy configurations to production server",
                "Test all security measures",
                "Configure monitoring alerts",
                "Perform security audit",
                "Create incident response plan",
                "Train team on security procedures"
            ]
        }
        
        report_file = self.security_dir / "security_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Security report generated: {report_file}")
        return report
    
    def deploy_security_configurations(self) -> bool:
        """Deploy security configurations to system"""
        print("\n🚀 Deploying security configurations...")
        
        try:
            # Copy Nginx configuration
            nginx_config = self.config_dir / "nginx_security.conf"
            if nginx_config.exists():
                print(f"📄 Nginx config ready for deployment: {nginx_config}")
            
            # Copy Fail2ban configuration
            jail_config = self.config_dir / "jail.local"
            if jail_config.exists():
                print(f"📄 Fail2ban config ready for deployment: {jail_config}")
            
            # Make scripts executable
            firewall_script = self.config_dir / "setup_firewall.sh"
            if firewall_script.exists():
                os.chmod(firewall_script, 0o755)
                print(f"📄 Firewall script ready: {firewall_script}")
            
            backup_script = self.config_dir / "encrypted_backup.sh"
            if backup_script.exists():
                os.chmod(backup_script, 0o755)
                print(f"📄 Backup script ready: {backup_script}")
            
            print(f"✅ Security configurations ready for deployment")
            print(f"\n📋 Manual deployment steps:")
            print(f"   1. sudo cp {nginx_config} /etc/nginx/sites-available/ai-trading-sentinel")
            print(f"   2. sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/")
            print(f"   3. sudo cp {jail_config} /etc/fail2ban/")
            print(f"   4. sudo systemctl restart nginx fail2ban")
            print(f"   5. sudo {firewall_script}")
            print(f"   6. sudo crontab {self.config_dir}/backup_cron")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment preparation failed: {e}")
            return False
    
    def run_security_hardening(self) -> bool:
        """Run complete security hardening process"""
        print("\n" + "="*60)
        print("🔒 AI TRADING SENTINEL - SECURITY HARDENING")
        print("="*60)
        
        success = True
        
        try:
            # Generate encryption keys
            self.generate_encryption_keys()
            
            # Setup SSL certificates
            success &= self.setup_ssl_certificates()
            
            # Create security configurations
            success &= self.create_nginx_security_config()
            success &= self.create_fail2ban_config()
            success &= self.create_firewall_rules()
            success &= self.create_security_monitoring()
            success &= self.create_backup_encryption()
            
            # Generate security report
            report = self.generate_security_report()
            
            # Prepare for deployment
            success &= self.deploy_security_configurations()
            
            if success:
                print("\n🎉 SECURITY HARDENING COMPLETED SUCCESSFULLY!")
                print(f"📁 Security files location: {self.security_dir}")
                print(f"📋 Security report: {self.security_dir}/security_report.json")
            else:
                print("\n⚠️  Security hardening completed with some issues")
            
            return success
            
        except Exception as e:
            print(f"\n❌ SECURITY HARDENING FAILED: {e}")
            return False

def main():
    """Main security hardening function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Security Hardening')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--keys-only', action='store_true', help='Generate encryption keys only')
    parser.add_argument('--ssl-only', action='store_true', help='Setup SSL certificates only')
    
    args = parser.parse_args()
    
    # Initialize security hardening
    security = SecurityHardening(args.project_root)
    
    if args.keys_only:
        security.generate_encryption_keys()
        sys.exit(0)
    
    if args.ssl_only:
        success = security.setup_ssl_certificates()
        sys.exit(0 if success else 1)
    
    # Run complete security hardening
    success = security.run_security_hardening()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()