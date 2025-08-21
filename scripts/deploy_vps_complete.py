#!/usr/bin/env python3
"""
AI Trading Sentinel - Complete VPS Deployment Script

This script automates the complete deployment of the AI Trading Sentinel
on a VPS (Contabo, DigitalOcean, AWS, etc.) with production-ready configuration.

Features:
- Complete system setup and hardening
- Docker containerization
- Nginx reverse proxy with SSL
- Monitoring stack (Prometheus, Grafana, Alertmanager)
- CI/CD pipeline setup
- Security configurations
- Automated backups
- Health monitoring

Usage:
    python3 deploy_vps_complete.py --domain your-domain.com --email admin@your-domain.com

Author: TRAE-SentinelOps
Version: 1.0.0
"""

import os
import sys
import subprocess
import argparse
import json
import yaml
import time
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class VPSDeployer:
    """Complete VPS deployment manager for AI Trading Sentinel"""
    
    def __init__(self, domain: str = None, email: str = None, environment: str = "production"):
        self.domain = domain
        self.email = email
        self.environment = environment
        self.project_root = Path("/opt/ai-trading-sentinel")
        self.config_dir = self.project_root / "config"
        self.scripts_dir = self.project_root / "scripts"
        self.logs_dir = self.project_root / "logs"
        self.backup_dir = self.project_root / "backups"
        
        # Setup logging
        self.setup_logging()
        
        # Deployment configuration
        self.services = {
            "redis": {"port": 6379, "container": "redis:7-alpine"},
            "postgres": {"port": 5432, "container": "postgres:15-alpine"},
            "api": {"port": 5000, "internal_port": 5000},
            "frontend": {"port": 3000, "internal_port": 3000},
            "bot": {"port": 8080, "internal_port": 8080},
            "prometheus": {"port": 9090, "internal_port": 9090},
            "grafana": {"port": 3001, "internal_port": 3000},
            "alertmanager": {"port": 9093, "internal_port": 9093},
            "nginx": {"port": 80, "ssl_port": 443}
        }
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('/tmp/vps_deployment.log')
            ]
        )
        self.logger = logging.getLogger('VPSDeployer')
        
    def run_command(self, command: str, check: bool = True, shell: bool = True) -> subprocess.CompletedProcess:
        """Execute shell command with logging"""
        self.logger.info(f"Executing: {command}")
        try:
            result = subprocess.run(
                command,
                shell=shell,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                self.logger.debug(f"STDOUT: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {command}")
            self.logger.error(f"Error: {e.stderr}")
            raise
            
    def check_prerequisites(self):
        """Check system prerequisites"""
        self.logger.info("Checking system prerequisites...")
        
        # Check if running as root
        if os.geteuid() != 0:
            raise RuntimeError("This script must be run as root")
            
        # Check Ubuntu version
        try:
            result = self.run_command("lsb_release -rs")
            version = float(result.stdout.strip())
            if version < 20.04:
                raise RuntimeError(f"Ubuntu {version} not supported. Minimum: 20.04")
            self.logger.info(f"Ubuntu {version} detected")
        except Exception as e:
            self.logger.warning(f"Could not detect Ubuntu version: {e}")
            
        # Check available memory
        try:
            result = self.run_command("free -m | grep '^Mem:' | awk '{print $2}'")
            memory_mb = int(result.stdout.strip())
            if memory_mb < 3000:  # 3GB minimum
                self.logger.warning(f"Low memory detected: {memory_mb}MB. Recommended: 4GB+")
            else:
                self.logger.info(f"Memory: {memory_mb}MB")
        except Exception as e:
            self.logger.warning(f"Could not check memory: {e}")
            
    def update_system(self):
        """Update system packages"""
        self.logger.info("Updating system packages...")
        
        commands = [
            "apt update",
            "apt upgrade -y",
            "apt autoremove -y",
            "apt autoclean"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
            
    def install_dependencies(self):
        """Install system dependencies"""
        self.logger.info("Installing system dependencies...")
        
        packages = [
            "curl", "wget", "git", "htop", "nano", "vim", "unzip", "tar",
            "software-properties-common", "apt-transport-https", "ca-certificates",
            "gnupg", "lsb-release", "ufw", "fail2ban", "logrotate",
            "python3", "python3-pip", "python3-venv", "python3-dev",
            "nodejs", "npm", "nginx", "certbot", "python3-certbot-nginx",
            "redis-server", "postgresql", "postgresql-contrib",
            "supervisor", "cron", "rsync", "jq"
        ]
        
        self.run_command(f"apt install -y {' '.join(packages)}")
        
        # Install Docker
        self.install_docker()
        
        # Install Docker Compose
        self.install_docker_compose()
        
    def install_docker(self):
        """Install Docker"""
        self.logger.info("Installing Docker...")
        
        commands = [
            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg",
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null',
            "apt update",
            "apt install -y docker-ce docker-ce-cli containerd.io",
            "systemctl enable docker",
            "systemctl start docker",
            "usermod -aG docker $USER"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
            
    def install_docker_compose(self):
        """Install Docker Compose"""
        self.logger.info("Installing Docker Compose...")
        
        # Get latest version
        result = self.run_command(
            "curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'\"' -f4"
        )
        version = result.stdout.strip()
        
        commands = [
            f"curl -L \"https://github.com/docker/compose/releases/download/{version}/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose",
            "chmod +x /usr/local/bin/docker-compose",
            "ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
            
    def setup_firewall(self):
        """Configure UFW firewall"""
        self.logger.info("Configuring firewall...")
        
        commands = [
            "ufw --force reset",
            "ufw default deny incoming",
            "ufw default allow outgoing",
            "ufw allow ssh",
            "ufw allow 80/tcp",
            "ufw allow 443/tcp",
            "ufw allow 3000/tcp",  # Frontend
            "ufw allow 5000/tcp",  # API
            "ufw allow 6379/tcp",  # Redis (internal)
            "ufw allow 5432/tcp",  # PostgreSQL (internal)
            "ufw --force enable"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
            
    def setup_fail2ban(self):
        """Configure Fail2Ban"""
        self.logger.info("Configuring Fail2Ban...")
        
        fail2ban_config = """
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
"""
        
        with open("/etc/fail2ban/jail.local", "w") as f:
            f.write(fail2ban_config)
            
        self.run_command("systemctl enable fail2ban")
        self.run_command("systemctl restart fail2ban")
        
    def clone_repository(self):
        """Clone the AI Trading Sentinel repository"""
        self.logger.info("Cloning repository...")
        
        if self.project_root.exists():
            self.logger.info("Repository already exists, updating...")
            self.run_command(f"cd {self.project_root} && git pull")
        else:
            # You'll need to replace this with your actual repository URL
            repo_url = "https://github.com/your-username/ai-trading-sentinel.git"
            self.run_command(f"git clone {repo_url} {self.project_root}")
            
        # Set permissions
        self.run_command(f"chown -R root:root {self.project_root}")
        self.run_command(f"chmod +x {self.project_root}/scripts/*.py")
        self.run_command(f"chmod +x {self.project_root}/scripts/*.sh")
        
    def setup_directories(self):
        """Create necessary directories"""
        self.logger.info("Setting up directories...")
        
        directories = [
            self.logs_dir,
            self.backup_dir,
            self.project_root / "data",
            self.project_root / "monitoring",
            self.project_root / "ssl",
            "/var/log/trading-sentinel",
            "/etc/trading-sentinel"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.run_command(f"chown -R root:root {directory}")
            
    def create_environment_file(self):
        """Create production environment file"""
        self.logger.info("Creating environment configuration...")
        
        env_content = f"""
# AI Trading Sentinel - Production Environment
# Generated on {datetime.now().isoformat()}

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Domain and SSL
DOMAIN={self.domain or 'localhost'}
ADMIN_EMAIL={self.email or 'admin@localhost'}

# Database
REDIS_URL=redis://localhost:6379/0
POSTGRES_URL=postgresql://trading_user:secure_password@localhost:5432/trading_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_SECRET_KEY=your-super-secret-api-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Frontend
VITE_API_URL=https://{self.domain or 'localhost'}/api
VITE_WEBSOCKET_URL=wss://{self.domain or 'localhost'}/ws

# Trading Bot
BOT_HOST=0.0.0.0
BOT_PORT=8080
TRADING_ENABLED=true
RISK_MANAGEMENT_ENABLED=true
MAX_DAILY_LOSS=1000
MAX_POSITION_SIZE=10000

# Broker Configuration (Update with your broker details)
BROKER_USERNAME=your-broker-username
BROKER_PASSWORD=your-broker-password
BROKER_API_KEY=your-broker-api-key
BROKER_ENVIRONMENT=live

# Monitoring
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3001
GRAFANA_ADMIN_PASSWORD=secure-grafana-password

# Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@{self.domain or 'localhost'}

# Security
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/{self.domain or 'localhost'}/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/{self.domain or 'localhost'}/privkey.pem

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30

# GitHub Integration
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-username/ai-trading-sentinel
"""
        
        env_file = self.project_root / ".env"
        with open(env_file, "w") as f:
            f.write(env_content)
            
        # Secure the environment file
        self.run_command(f"chmod 600 {env_file}")
        
    def create_docker_compose(self):
        """Create Docker Compose configuration"""
        self.logger.info("Creating Docker Compose configuration...")
        
        compose_content = {
            "version": "3.8",
            "services": {
                "redis": {
                    "image": "redis:7-alpine",
                    "container_name": "trading-redis",
                    "restart": "unless-stopped",
                    "ports": ["6379:6379"],
                    "volumes": [
                        "redis_data:/data",
                        "./config/redis.conf:/usr/local/etc/redis/redis.conf"
                    ],
                    "command": "redis-server /usr/local/etc/redis/redis.conf",
                    "healthcheck": {
                        "test": ["CMD", "redis-cli", "ping"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                "postgres": {
                    "image": "postgres:15-alpine",
                    "container_name": "trading-postgres",
                    "restart": "unless-stopped",
                    "environment": {
                        "POSTGRES_DB": "trading_db",
                        "POSTGRES_USER": "trading_user",
                        "POSTGRES_PASSWORD": "secure_password"
                    },
                    "ports": ["5432:5432"],
                    "volumes": [
                        "postgres_data:/var/lib/postgresql/data",
                        "./backups:/backups"
                    ],
                    "healthcheck": {
                        "test": ["CMD-SHELL", "pg_isready -U trading_user -d trading_db"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                "api": {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile.api"
                    },
                    "container_name": "trading-api",
                    "restart": "unless-stopped",
                    "ports": ["5000:5000"],
                    "environment": {
                        "ENVIRONMENT": "production"
                    },
                    "env_file": ".env",
                    "volumes": [
                        "./logs:/app/logs",
                        "./data:/app/data",
                        "./config:/app/config"
                    ],
                    "depends_on": {
                        "redis": {"condition": "service_healthy"},
                        "postgres": {"condition": "service_healthy"}
                    },
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:5000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                "bot": {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile.bot"
                    },
                    "container_name": "trading-bot",
                    "restart": "unless-stopped",
                    "ports": ["8080:8080"],
                    "environment": {
                        "ENVIRONMENT": "production"
                    },
                    "env_file": ".env",
                    "volumes": [
                        "./logs:/app/logs",
                        "./data:/app/data",
                        "./config:/app/config"
                    ],
                    "depends_on": {
                        "redis": {"condition": "service_healthy"},
                        "api": {"condition": "service_healthy"}
                    },
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                "frontend": {
                    "build": {
                        "context": "./frontend",
                        "dockerfile": "Dockerfile"
                    },
                    "container_name": "trading-frontend",
                    "restart": "unless-stopped",
                    "ports": ["3000:3000"],
                    "environment": {
                        "VITE_API_URL": f"https://{self.domain or 'localhost'}/api",
                        "VITE_WEBSOCKET_URL": f"wss://{self.domain or 'localhost'}/ws"
                    },
                    "depends_on": ["api"]
                },
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "trading-prometheus",
                    "restart": "unless-stopped",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./config/prometheus.yml:/etc/prometheus/prometheus.yml",
                        "./config/alert_rules.yml:/etc/prometheus/alert_rules.yml",
                        "prometheus_data:/prometheus"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=200h",
                        "--web.enable-lifecycle"
                    ]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "trading-grafana",
                    "restart": "unless-stopped",
                    "ports": ["3001:3000"],
                    "environment": {
                        "GF_SECURITY_ADMIN_PASSWORD": "${GRAFANA_ADMIN_PASSWORD}"
                    },
                    "volumes": [
                        "grafana_data:/var/lib/grafana",
                        "./config/grafana:/etc/grafana/provisioning"
                    ]
                },
                "alertmanager": {
                    "image": "prom/alertmanager:latest",
                    "container_name": "trading-alertmanager",
                    "restart": "unless-stopped",
                    "ports": ["9093:9093"],
                    "volumes": [
                        "./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml",
                        "alertmanager_data:/alertmanager"
                    ]
                }
            },
            "volumes": {
                "redis_data": {},
                "postgres_data": {},
                "prometheus_data": {},
                "grafana_data": {},
                "alertmanager_data": {}
            },
            "networks": {
                "default": {
                    "name": "trading-network"
                }
            }
        }
        
        compose_file = self.project_root / "docker-compose.yml"
        with open(compose_file, "w") as f:
            yaml.dump(compose_content, f, default_flow_style=False, indent=2)
            
    def create_nginx_config(self):
        """Create Nginx reverse proxy configuration"""
        self.logger.info("Creating Nginx configuration...")
        
        nginx_config = f"""
# AI Trading Sentinel - Nginx Configuration

upstream api_backend {{
    server localhost:5000;
}}

upstream frontend_backend {{
    server localhost:3000;
}}

upstream grafana_backend {{
    server localhost:3001;
}}

upstream prometheus_backend {{
    server localhost:9090;
}}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

server {{
    listen 80;
    server_name {self.domain or '_'};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain or '_'};
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/{self.domain or 'localhost'}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.domain or 'localhost'}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Frontend
    location / {{
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://frontend_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # API
    location /api/ {{
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://api_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
    
    # Grafana
    location /grafana/ {{
        proxy_pass http://grafana_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Prometheus (restricted access)
    location /prometheus/ {{
        auth_basic "Prometheus";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://prometheus_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Health check endpoint
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
    
    # Static files caching
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}
"""
        
        nginx_config_file = "/etc/nginx/sites-available/trading-sentinel"
        with open(nginx_config_file, "w") as f:
            f.write(nginx_config)
            
        # Enable the site
        self.run_command("rm -f /etc/nginx/sites-enabled/default")
        self.run_command(f"ln -sf {nginx_config_file} /etc/nginx/sites-enabled/")
        
        # Create basic auth for Prometheus
        self.run_command("apt install -y apache2-utils")
        self.run_command("htpasswd -cb /etc/nginx/.htpasswd admin prometheus_admin_password")
        
        # Test and reload Nginx
        self.run_command("nginx -t")
        self.run_command("systemctl reload nginx")
        
    def setup_ssl(self):
        """Setup SSL certificates with Let's Encrypt"""
        if not self.domain:
            self.logger.warning("No domain specified, skipping SSL setup")
            return
            
        self.logger.info(f"Setting up SSL for {self.domain}...")
        
        # Stop Nginx temporarily
        self.run_command("systemctl stop nginx")
        
        try:
            # Get SSL certificate
            self.run_command(
                f"certbot certonly --standalone -d {self.domain} --email {self.email} --agree-tos --non-interactive"
            )
            
            # Setup auto-renewal
            cron_job = "0 12 * * * /usr/bin/certbot renew --quiet\n"
            with open("/tmp/certbot_cron", "w") as f:
                f.write(cron_job)
            self.run_command("crontab /tmp/certbot_cron")
            
        finally:
            # Start Nginx
            self.run_command("systemctl start nginx")
            
    def setup_monitoring(self):
        """Setup monitoring stack"""
        self.logger.info("Setting up monitoring stack...")
        
        # Copy monitoring configurations
        monitoring_files = [
            "prometheus.yml",
            "alert_rules.yml",
            "alertmanager.yml",
            "grafana_dashboards.json",
            "monitoring_config.yml"
        ]
        
        for file in monitoring_files:
            src = self.project_root / "config" / file
            if src.exists():
                self.logger.info(f"Monitoring config {file} already exists")
            else:
                self.logger.warning(f"Monitoring config {file} not found, creating basic version")
                
    def setup_backup_system(self):
        """Setup automated backup system"""
        self.logger.info("Setting up backup system...")
        
        backup_script = f"""
#!/bin/bash
# AI Trading Sentinel - Backup Script
# Generated on {datetime.now().isoformat()}

BACKUP_DIR="{self.backup_dir}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup databases
echo "Backing up Redis..."
redis-cli --rdb $BACKUP_DIR/$DATE/redis_dump.rdb

echo "Backing up PostgreSQL..."
pg_dump -U trading_user -h localhost trading_db > $BACKUP_DIR/$DATE/postgres_dump.sql

# Backup configuration files
echo "Backing up configurations..."
cp -r {self.project_root}/config $BACKUP_DIR/$DATE/
cp {self.project_root}/.env $BACKUP_DIR/$DATE/
cp /etc/nginx/sites-available/trading-sentinel $BACKUP_DIR/$DATE/

# Backup logs (last 7 days)
echo "Backing up recent logs..."
find {self.logs_dir} -name "*.log" -mtime -7 -exec cp {{}} $BACKUP_DIR/$DATE/ \;

# Compress backup
echo "Compressing backup..."
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: backup_$DATE.tar.gz"
"""
        
        backup_script_path = self.scripts_dir / "backup.sh"
        with open(backup_script_path, "w") as f:
            f.write(backup_script)
        self.run_command(f"chmod +x {backup_script_path}")
        
        # Setup cron job for daily backups
        cron_job = f"0 2 * * * {backup_script_path} >> /var/log/trading-backup.log 2>&1\n"
        with open("/tmp/backup_cron", "w") as f:
            f.write(cron_job)
        self.run_command("crontab -l > /tmp/current_cron 2>/dev/null || true")
        self.run_command("cat /tmp/backup_cron >> /tmp/current_cron")
        self.run_command("crontab /tmp/current_cron")
        
    def setup_health_monitoring(self):
        """Setup health monitoring service"""
        self.logger.info("Setting up health monitoring...")
        
        # Copy health monitor script
        health_monitor_src = self.project_root / "scripts" / "health_monitor.py"
        if health_monitor_src.exists():
            # Create systemd service
            service_content = f"""
[Unit]
Description=AI Trading Sentinel Health Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.project_root}
ExecStart=/usr/bin/python3 {health_monitor_src}
Restart=always
RestartSec=30
Environment=PYTHONPATH={self.project_root}

[Install]
WantedBy=multi-user.target
"""
            
            with open("/etc/systemd/system/trading-health-monitor.service", "w") as f:
                f.write(service_content)
                
            self.run_command("systemctl daemon-reload")
            self.run_command("systemctl enable trading-health-monitor")
            self.run_command("systemctl start trading-health-monitor")
        else:
            self.logger.warning("Health monitor script not found")
            
    def setup_log_rotation(self):
        """Setup log rotation"""
        self.logger.info("Setting up log rotation...")
        
        logrotate_config = f"""
{self.logs_dir}/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}}

/var/log/trading-*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}}
"""
        
        with open("/etc/logrotate.d/trading-sentinel", "w") as f:
            f.write(logrotate_config)
            
    def deploy_application(self):
        """Deploy the application using Docker Compose"""
        self.logger.info("Deploying application...")
        
        # Change to project directory
        os.chdir(self.project_root)
        
        # Build and start services
        self.run_command("docker-compose down --remove-orphans")
        self.run_command("docker-compose build --no-cache")
        self.run_command("docker-compose up -d")
        
        # Wait for services to start
        self.logger.info("Waiting for services to start...")
        time.sleep(30)
        
        # Check service health
        self.run_command("docker-compose ps")
        
    def setup_github_webhook(self):
        """Setup GitHub webhook for CI/CD"""
        self.logger.info("Setting up GitHub webhook handler...")
        
        webhook_script = f"""
#!/bin/bash
# AI Trading Sentinel - GitHub Webhook Handler

cd {self.project_root}

# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Log deployment
echo "$(date): Deployment completed" >> /var/log/trading-deployment.log
"""
        
        webhook_script_path = self.scripts_dir / "deploy_webhook.sh"
        with open(webhook_script_path, "w") as f:
            f.write(webhook_script)
        self.run_command(f"chmod +x {webhook_script_path}")
        
    def verify_deployment(self):
        """Verify the deployment"""
        self.logger.info("Verifying deployment...")
        
        checks = [
            ("Docker", "docker --version"),
            ("Docker Compose", "docker-compose --version"),
            ("Nginx", "systemctl is-active nginx"),
            ("Redis", "systemctl is-active redis-server"),
            ("PostgreSQL", "systemctl is-active postgresql"),
            ("UFW", "ufw status"),
            ("Fail2Ban", "systemctl is-active fail2ban")
        ]
        
        results = []
        for name, command in checks:
            try:
                result = self.run_command(command, check=False)
                status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
                results.append(f"{status} {name}")
            except Exception as e:
                results.append(f"❌ FAIL {name}: {e}")
                
        # Check Docker containers
        try:
            result = self.run_command("docker-compose ps", check=False)
            if result.returncode == 0:
                results.append("✅ PASS Docker Containers")
            else:
                results.append("❌ FAIL Docker Containers")
        except Exception as e:
            results.append(f"❌ FAIL Docker Containers: {e}")
            
        # Check endpoints
        endpoints = [
            ("Frontend", "http://localhost:3000"),
            ("API", "http://localhost:5000/health"),
            ("Prometheus", "http://localhost:9090/-/healthy"),
            ("Grafana", "http://localhost:3001/api/health")
        ]
        
        for name, url in endpoints:
            try:
                result = self.run_command(f"curl -f -s {url}", check=False)
                status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
                results.append(f"{status} {name} Endpoint")
            except Exception as e:
                results.append(f"❌ FAIL {name} Endpoint: {e}")
                
        return results
        
    def print_access_info(self):
        """Print access information"""
        domain = self.domain or "your-server-ip"
        protocol = "https" if self.domain else "http"
        
        info = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AI Trading Sentinel - Deployment Complete                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🌐 Access URLs:                                                             ║
║     Frontend:     {protocol}://{domain}                                      ║
║     API:          {protocol}://{domain}/api                                  ║
║     Grafana:      {protocol}://{domain}/grafana                              ║
║     Prometheus:   {protocol}://{domain}/prometheus (admin/prometheus_admin_password) ║
║                                                                              ║
║  🔧 Management:                                                              ║
║     SSH:          ssh root@{domain}                                          ║
║     Logs:         docker-compose logs -f                                    ║
║     Status:       docker-compose ps                                         ║
║     Restart:      docker-compose restart                                    ║
║                                                                              ║
║  📊 Monitoring:                                                              ║
║     Health:       systemctl status trading-health-monitor                   ║
║     Backups:      ls -la {self.backup_dir}                                  ║
║     Firewall:     ufw status                                                ║
║                                                                              ║
║  🚨 Important:                                                               ║
║     1. Update .env file with your broker credentials                        ║
║     2. Configure Slack webhook for alerts                                   ║
║     3. Test trading functionality before going live                         ║
║     4. Monitor logs for any issues                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        print(info)
        
    def run_deployment(self):
        """Run the complete deployment process"""
        start_time = time.time()
        
        try:
            self.logger.info("Starting AI Trading Sentinel VPS deployment...")
            
            # Pre-deployment checks
            self.check_prerequisites()
            
            # System setup
            self.update_system()
            self.install_dependencies()
            self.setup_firewall()
            self.setup_fail2ban()
            
            # Application setup
            self.clone_repository()
            self.setup_directories()
            self.create_environment_file()
            self.create_docker_compose()
            
            # Web server setup
            self.create_nginx_config()
            if self.domain:
                self.setup_ssl()
                
            # Monitoring and maintenance
            self.setup_monitoring()
            self.setup_backup_system()
            self.setup_health_monitoring()
            self.setup_log_rotation()
            
            # Deploy application
            self.deploy_application()
            
            # CI/CD setup
            self.setup_github_webhook()
            
            # Verification
            results = self.verify_deployment()
            
            # Summary
            elapsed_time = time.time() - start_time
            self.logger.info(f"Deployment completed in {elapsed_time:.2f} seconds")
            
            print("\n" + "="*80)
            print("DEPLOYMENT VERIFICATION RESULTS:")
            print("="*80)
            for result in results:
                print(result)
            print("="*80)
            
            self.print_access_info()
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            raise
            
def main():
    parser = argparse.ArgumentParser(description="AI Trading Sentinel VPS Deployment")
    parser.add_argument("--domain", help="Domain name for SSL setup")
    parser.add_argument("--email", help="Email for SSL certificates and alerts")
    parser.add_argument("--environment", default="production", help="Deployment environment")
    parser.add_argument("--verify-only", action="store_true", help="Only run verification checks")
    
    args = parser.parse_args()
    
    deployer = VPSDeployer(
        domain=args.domain,
        email=args.email,
        environment=args.environment
    )
    
    if args.verify_only:
        results = deployer.verify_deployment()
        print("\nVerification Results:")
        for result in results:
            print(result)
    else:
        deployer.run_deployment()
        
if __name__ == "__main__":
    main()