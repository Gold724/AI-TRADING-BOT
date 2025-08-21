#!/usr/bin/env python3
"""
AI Trading Sentinel - Monitoring Deployment Script

Automated deployment of comprehensive monitoring and alerting system.
Sets up Prometheus, Grafana, Alertmanager, and health monitoring on VPS.
"""

import os
import sys
import json
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime


class MonitoringDeployer:
    """Automated monitoring system deployment."""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "monitoring_config.yml"
        self.deployment_log = self.project_root / "logs" / "deployment.log"
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Deployment paths
        self.monitoring_dir = Path("/opt/ai-trading-sentinel/monitoring")
        self.systemd_dir = Path("/etc/systemd/system")
        self.nginx_dir = Path("/etc/nginx/sites-available")
        
        self.logger.info("Monitoring Deployer initialized")
    
    def setup_logging(self):
        """Setup deployment logging."""
        self.deployment_log.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.deployment_log),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('MonitoringDeployer')
    
    def load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                self.logger.warning(f"Config file not found: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration."""
        return {
            'prometheus': {
                'port': 9090,
                'retention': '30d',
                'scrape_interval': '15s'
            },
            'grafana': {
                'port': 3000,
                'admin_password': 'admin123'
            },
            'alertmanager': {
                'port': 9093
            },
            'node_exporter': {
                'port': 9100
            },
            'redis_exporter': {
                'port': 9121
            },
            'nginx_exporter': {
                'port': 9113
            }
        }
    
    def run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Execute shell command with logging."""
        self.logger.info(f"Executing: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                self.logger.info(f"Output: {result.stdout.strip()}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e}")
            if e.stdout:
                self.logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                self.logger.error(f"Stderr: {e.stderr}")
            raise
    
    def install_dependencies(self):
        """Install required system dependencies."""
        self.logger.info("Installing system dependencies...")
        
        # Update package list
        self.run_command("apt update")
        
        # Install required packages
        packages = [
            "wget", "curl", "tar", "systemd", "nginx",
            "python3", "python3-pip", "python3-venv",
            "docker.io", "docker-compose"
        ]
        
        self.run_command(f"apt install -y {' '.join(packages)}")
        
        # Install Python packages
        python_packages = [
            "pyyaml", "requests", "psutil", "jinja2",
            "prometheus-client", "redis"
        ]
        
        self.run_command(f"pip3 install {' '.join(python_packages)}")
        
        self.logger.info("Dependencies installed successfully")
    
    def create_monitoring_user(self):
        """Create dedicated monitoring user."""
        self.logger.info("Creating monitoring user...")
        
        # Create monitoring user
        self.run_command("useradd --system --shell /bin/false --home-dir /var/lib/prometheus prometheus", check=False)
        self.run_command("useradd --system --shell /bin/false --home-dir /var/lib/grafana grafana", check=False)
        self.run_command("useradd --system --shell /bin/false --home-dir /var/lib/alertmanager alertmanager", check=False)
        
        # Create directories
        directories = [
            "/var/lib/prometheus",
            "/var/lib/grafana",
            "/var/lib/alertmanager",
            "/etc/prometheus",
            "/etc/grafana",
            "/etc/alertmanager"
        ]
        
        for directory in directories:
            self.run_command(f"mkdir -p {directory}")
        
        # Set ownership
        self.run_command("chown -R prometheus:prometheus /var/lib/prometheus /etc/prometheus")
        self.run_command("chown -R grafana:grafana /var/lib/grafana /etc/grafana")
        self.run_command("chown -R alertmanager:alertmanager /var/lib/alertmanager /etc/alertmanager")
        
        self.logger.info("Monitoring users created successfully")
    
    def install_prometheus(self):
        """Install and configure Prometheus."""
        self.logger.info("Installing Prometheus...")
        
        # Download Prometheus
        prometheus_version = "2.45.0"
        prometheus_url = f"https://github.com/prometheus/prometheus/releases/download/v{prometheus_version}/prometheus-{prometheus_version}.linux-amd64.tar.gz"
        
        self.run_command(f"wget {prometheus_url} -O /tmp/prometheus.tar.gz")
        self.run_command("tar -xzf /tmp/prometheus.tar.gz -C /tmp")
        
        # Install binaries
        self.run_command(f"cp /tmp/prometheus-{prometheus_version}.linux-amd64/prometheus /usr/local/bin/")
        self.run_command(f"cp /tmp/prometheus-{prometheus_version}.linux-amd64/promtool /usr/local/bin/")
        self.run_command("chmod +x /usr/local/bin/prometheus /usr/local/bin/promtool")
        
        # Copy configuration
        prometheus_config = self.generate_prometheus_config()
        with open("/etc/prometheus/prometheus.yml", "w") as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        # Create systemd service
        prometheus_service = self.generate_prometheus_service()
        with open("/etc/systemd/system/prometheus.service", "w") as f:
            f.write(prometheus_service)
        
        # Set permissions
        self.run_command("chown prometheus:prometheus /etc/prometheus/prometheus.yml")
        
        self.logger.info("Prometheus installed successfully")
    
    def install_grafana(self):
        """Install and configure Grafana."""
        self.logger.info("Installing Grafana...")
        
        # Add Grafana repository
        self.run_command("wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -")
        self.run_command('echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list')
        
        # Install Grafana
        self.run_command("apt update")
        self.run_command("apt install -y grafana")
        
        # Configure Grafana
        grafana_config = self.generate_grafana_config()
        with open("/etc/grafana/grafana.ini", "w") as f:
            f.write(grafana_config)
        
        # Setup provisioning
        self.setup_grafana_provisioning()
        
        self.logger.info("Grafana installed successfully")
    
    def install_alertmanager(self):
        """Install and configure Alertmanager."""
        self.logger.info("Installing Alertmanager...")
        
        # Download Alertmanager
        alertmanager_version = "0.25.0"
        alertmanager_url = f"https://github.com/prometheus/alertmanager/releases/download/v{alertmanager_version}/alertmanager-{alertmanager_version}.linux-amd64.tar.gz"
        
        self.run_command(f"wget {alertmanager_url} -O /tmp/alertmanager.tar.gz")
        self.run_command("tar -xzf /tmp/alertmanager.tar.gz -C /tmp")
        
        # Install binaries
        self.run_command(f"cp /tmp/alertmanager-{alertmanager_version}.linux-amd64/alertmanager /usr/local/bin/")
        self.run_command(f"cp /tmp/alertmanager-{alertmanager_version}.linux-amd64/amtool /usr/local/bin/")
        self.run_command("chmod +x /usr/local/bin/alertmanager /usr/local/bin/amtool")
        
        # Copy configuration
        alertmanager_config = self.generate_alertmanager_config()
        with open("/etc/alertmanager/alertmanager.yml", "w") as f:
            yaml.dump(alertmanager_config, f, default_flow_style=False)
        
        # Create systemd service
        alertmanager_service = self.generate_alertmanager_service()
        with open("/etc/systemd/system/alertmanager.service", "w") as f:
            f.write(alertmanager_service)
        
        # Set permissions
        self.run_command("chown alertmanager:alertmanager /etc/alertmanager/alertmanager.yml")
        
        self.logger.info("Alertmanager installed successfully")
    
    def install_exporters(self):
        """Install monitoring exporters."""
        self.logger.info("Installing exporters...")
        
        # Node Exporter
        node_exporter_version = "1.6.0"
        node_exporter_url = f"https://github.com/prometheus/node_exporter/releases/download/v{node_exporter_version}/node_exporter-{node_exporter_version}.linux-amd64.tar.gz"
        
        self.run_command(f"wget {node_exporter_url} -O /tmp/node_exporter.tar.gz")
        self.run_command("tar -xzf /tmp/node_exporter.tar.gz -C /tmp")
        self.run_command(f"cp /tmp/node_exporter-{node_exporter_version}.linux-amd64/node_exporter /usr/local/bin/")
        self.run_command("chmod +x /usr/local/bin/node_exporter")
        
        # Create Node Exporter service
        node_exporter_service = self.generate_node_exporter_service()
        with open("/etc/systemd/system/node_exporter.service", "w") as f:
            f.write(node_exporter_service)
        
        # Redis Exporter (if Redis is used)
        if self.config.get('redis', {}).get('enabled', False):
            self.install_redis_exporter()
        
        self.logger.info("Exporters installed successfully")
    
    def install_redis_exporter(self):
        """Install Redis exporter."""
        self.logger.info("Installing Redis exporter...")
        
        redis_exporter_version = "1.51.0"
        redis_exporter_url = f"https://github.com/oliver006/redis_exporter/releases/download/v{redis_exporter_version}/redis_exporter-v{redis_exporter_version}.linux-amd64.tar.gz"
        
        self.run_command(f"wget {redis_exporter_url} -O /tmp/redis_exporter.tar.gz")
        self.run_command("tar -xzf /tmp/redis_exporter.tar.gz -C /tmp")
        self.run_command(f"cp /tmp/redis_exporter-v{redis_exporter_version}.linux-amd64/redis_exporter /usr/local/bin/")
        self.run_command("chmod +x /usr/local/bin/redis_exporter")
        
        # Create Redis Exporter service
        redis_exporter_service = self.generate_redis_exporter_service()
        with open("/etc/systemd/system/redis_exporter.service", "w") as f:
            f.write(redis_exporter_service)
    
    def setup_nginx_monitoring(self):
        """Setup Nginx monitoring configuration."""
        self.logger.info("Setting up Nginx monitoring...")
        
        # Create Nginx monitoring configuration
        nginx_monitoring_config = self.generate_nginx_monitoring_config()
        
        with open("/etc/nginx/sites-available/monitoring", "w") as f:
            f.write(nginx_monitoring_config)
        
        # Enable site
        self.run_command("ln -sf /etc/nginx/sites-available/monitoring /etc/nginx/sites-enabled/")
        
        # Test and reload Nginx
        self.run_command("nginx -t")
        self.run_command("systemctl reload nginx")
        
        self.logger.info("Nginx monitoring setup completed")
    
    def deploy_health_monitor(self):
        """Deploy health monitoring scripts."""
        self.logger.info("Deploying health monitor...")
        
        # Create monitoring directory
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy health monitor script
        health_monitor_src = self.project_root / "scripts" / "health_monitor.py"
        health_monitor_dst = self.monitoring_dir / "health_monitor.py"
        
        if health_monitor_src.exists():
            shutil.copy2(health_monitor_src, health_monitor_dst)
            self.run_command(f"chmod +x {health_monitor_dst}")
        
        # Copy alert manager
        alert_manager_src = self.project_root / "scripts" / "alert_manager.py"
        alert_manager_dst = self.monitoring_dir / "alert_manager.py"
        
        if alert_manager_src.exists():
            shutil.copy2(alert_manager_src, alert_manager_dst)
            self.run_command(f"chmod +x {alert_manager_dst}")
        
        # Copy configuration
        config_dst = self.monitoring_dir / "monitoring_config.yml"
        shutil.copy2(self.config_path, config_dst)
        
        # Create health monitor service
        health_monitor_service = self.generate_health_monitor_service()
        with open("/etc/systemd/system/health-monitor.service", "w") as f:
            f.write(health_monitor_service)
        
        self.logger.info("Health monitor deployed successfully")
    
    def start_services(self):
        """Start all monitoring services."""
        self.logger.info("Starting monitoring services...")
        
        # Reload systemd
        self.run_command("systemctl daemon-reload")
        
        # Enable and start services
        services = [
            "prometheus",
            "grafana-server",
            "alertmanager",
            "node_exporter",
            "health-monitor"
        ]
        
        if self.config.get('redis', {}).get('enabled', False):
            services.append("redis_exporter")
        
        for service in services:
            self.run_command(f"systemctl enable {service}")
            self.run_command(f"systemctl start {service}")
            
            # Check service status
            result = self.run_command(f"systemctl is-active {service}", check=False)
            if result.returncode == 0:
                self.logger.info(f"Service {service} started successfully")
            else:
                self.logger.error(f"Failed to start service {service}")
        
        self.logger.info("All services started")
    
    def verify_deployment(self):
        """Verify monitoring deployment."""
        self.logger.info("Verifying deployment...")
        
        # Check service endpoints
        endpoints = [
            ("Prometheus", f"http://localhost:{self.config['prometheus']['port']}"),
            ("Grafana", f"http://localhost:{self.config['grafana']['port']}"),
            ("Alertmanager", f"http://localhost:{self.config['alertmanager']['port']}"),
            ("Node Exporter", f"http://localhost:{self.config['node_exporter']['port']}/metrics")
        ]
        
        import requests
        
        for name, url in endpoints:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"✓ {name} is accessible at {url}")
                else:
                    self.logger.warning(f"⚠ {name} returned status {response.status_code}")
            except Exception as e:
                self.logger.error(f"✗ {name} is not accessible: {e}")
        
        # Check log files
        log_files = [
            "/var/log/prometheus/prometheus.log",
            "/var/log/grafana/grafana.log",
            "/var/log/alertmanager/alertmanager.log"
        ]
        
        for log_file in log_files:
            if Path(log_file).exists():
                self.logger.info(f"✓ Log file exists: {log_file}")
            else:
                self.logger.warning(f"⚠ Log file missing: {log_file}")
        
        self.logger.info("Deployment verification completed")
    
    def generate_prometheus_config(self) -> Dict[str, Any]:
        """Generate Prometheus configuration."""
        return {
            'global': {
                'scrape_interval': self.config['prometheus']['scrape_interval'],
                'evaluation_interval': '15s'
            },
            'alerting': {
                'alertmanagers': [{
                    'static_configs': [{
                        'targets': [f"localhost:{self.config['alertmanager']['port']}"]
                    }]
                }]
            },
            'rule_files': [
                '/etc/prometheus/alert_rules.yml'
            ],
            'scrape_configs': [
                {
                    'job_name': 'prometheus',
                    'static_configs': [{
                        'targets': [f"localhost:{self.config['prometheus']['port']}"]
                    }]
                },
                {
                    'job_name': 'node_exporter',
                    'static_configs': [{
                        'targets': [f"localhost:{self.config['node_exporter']['port']}"]
                    }]
                },
                {
                    'job_name': 'trading_api',
                    'static_configs': [{
                        'targets': ['localhost:8000']
                    }],
                    'metrics_path': '/metrics'
                }
            ]
        }
    
    def generate_prometheus_service(self) -> str:
        """Generate Prometheus systemd service."""
        return f"""[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:{self.config['prometheus']['port']} \
  --web.enable-lifecycle \
  --storage.tsdb.retention.time={self.config['prometheus']['retention']}

Restart=always
RestartSec=3
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""
    
    def generate_grafana_config(self) -> str:
        """Generate Grafana configuration."""
        return f"""[server]
http_port = {self.config['grafana']['port']}
domain = localhost
root_url = http://localhost:{self.config['grafana']['port']}/

[security]
admin_password = {self.config['grafana']['admin_password']}

[users]
allow_sign_up = false

[auth.anonymous]
enabled = false

[log]
mode = file
level = info

[paths]
data = /var/lib/grafana
logs = /var/log/grafana
plugins = /var/lib/grafana/plugins
provisioning = /etc/grafana/provisioning
"""
    
    def generate_alertmanager_config(self) -> Dict[str, Any]:
        """Generate Alertmanager configuration."""
        slack_config = self.config.get('notifications', {}).get('slack', {})
        
        return {
            'global': {
                'smtp_smarthost': 'localhost:587',
                'smtp_from': 'alerts@ai-trading-sentinel.com'
            },
            'route': {
                'group_by': ['alertname'],
                'group_wait': '10s',
                'group_interval': '10s',
                'repeat_interval': '1h',
                'receiver': 'web.hook'
            },
            'receivers': [
                {
                    'name': 'web.hook',
                    'slack_configs': [{
                        'api_url': slack_config.get('webhook_url', ''),
                        'channel': slack_config.get('channel', '#alerts'),
                        'username': 'AI Trading Sentinel',
                        'title': 'Alert: {{ .GroupLabels.alertname }}',
                        'text': '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
                    }] if slack_config.get('enabled') else []
                }
            ]
        }
    
    def generate_alertmanager_service(self) -> str:
        """Generate Alertmanager systemd service."""
        return f"""[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/usr/local/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager/ \
  --web.listen-address=0.0.0.0:{self.config['alertmanager']['port']}

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    def generate_node_exporter_service(self) -> str:
        """Generate Node Exporter systemd service."""
        return f"""[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
  --web.listen-address=0.0.0.0:{self.config['node_exporter']['port']}

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    def generate_redis_exporter_service(self) -> str:
        """Generate Redis Exporter systemd service."""
        return f"""[Unit]
Description=Redis Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=redis_exporter
Group=redis_exporter
Type=simple
ExecStart=/usr/local/bin/redis_exporter \
  --web.listen-address=0.0.0.0:{self.config['redis_exporter']['port']}

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    def generate_health_monitor_service(self) -> str:
        """Generate Health Monitor systemd service."""
        return f"""[Unit]
Description=AI Trading Sentinel Health Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.monitoring_dir}
ExecStart=/usr/bin/python3 {self.monitoring_dir}/health_monitor.py --config {self.monitoring_dir}/monitoring_config.yml --interval 60
Restart=always
RestartSec=10
Environment=PYTHONPATH={self.monitoring_dir}

[Install]
WantedBy=multi-user.target
"""
    
    def generate_nginx_monitoring_config(self) -> str:
        """Generate Nginx monitoring configuration."""
        return f"""server {{
    listen 80;
    server_name monitoring.ai-trading-sentinel.local;
    
    # Prometheus
    location /prometheus/ {{
        proxy_pass http://localhost:{self.config['prometheus']['port']}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Grafana
    location /grafana/ {{
        proxy_pass http://localhost:{self.config['grafana']['port']}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Alertmanager
    location /alertmanager/ {{
        proxy_pass http://localhost:{self.config['alertmanager']['port']}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Health status endpoint
    location /health {{
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
    
    def setup_grafana_provisioning(self):
        """Setup Grafana provisioning."""
        # Create provisioning directories
        provisioning_dirs = [
            "/etc/grafana/provisioning/datasources",
            "/etc/grafana/provisioning/dashboards"
        ]
        
        for directory in provisioning_dirs:
            self.run_command(f"mkdir -p {directory}")
        
        # Datasource provisioning
        datasource_config = {
            'apiVersion': 1,
            'datasources': [{
                'name': 'Prometheus',
                'type': 'prometheus',
                'access': 'proxy',
                'url': f"http://localhost:{self.config['prometheus']['port']}",
                'isDefault': True
            }]
        }
        
        with open("/etc/grafana/provisioning/datasources/prometheus.yml", "w") as f:
            yaml.dump(datasource_config, f)
        
        # Dashboard provisioning
        dashboard_config = {
            'apiVersion': 1,
            'providers': [{
                'name': 'default',
                'orgId': 1,
                'folder': '',
                'type': 'file',
                'disableDeletion': False,
                'updateIntervalSeconds': 10,
                'options': {
                    'path': '/etc/grafana/provisioning/dashboards'
                }
            }]
        }
        
        with open("/etc/grafana/provisioning/dashboards/dashboards.yml", "w") as f:
            yaml.dump(dashboard_config, f)
        
        # Set permissions
        self.run_command("chown -R grafana:grafana /etc/grafana/provisioning")
    
    def deploy(self):
        """Execute full monitoring deployment."""
        self.logger.info("Starting monitoring system deployment...")
        
        try:
            # Pre-deployment checks
            self.logger.info("Step 1/10: Installing dependencies...")
            self.install_dependencies()
            
            self.logger.info("Step 2/10: Creating monitoring users...")
            self.create_monitoring_user()
            
            self.logger.info("Step 3/10: Installing Prometheus...")
            self.install_prometheus()
            
            self.logger.info("Step 4/10: Installing Grafana...")
            self.install_grafana()
            
            self.logger.info("Step 5/10: Installing Alertmanager...")
            self.install_alertmanager()
            
            self.logger.info("Step 6/10: Installing exporters...")
            self.install_exporters()
            
            self.logger.info("Step 7/10: Setting up Nginx monitoring...")
            self.setup_nginx_monitoring()
            
            self.logger.info("Step 8/10: Deploying health monitor...")
            self.deploy_health_monitor()
            
            self.logger.info("Step 9/10: Starting services...")
            self.start_services()
            
            self.logger.info("Step 10/10: Verifying deployment...")
            self.verify_deployment()
            
            self.logger.info("🎉 Monitoring system deployment completed successfully!")
            
            # Print access information
            self.print_access_info()
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            raise
    
    def print_access_info(self):
        """Print access information for monitoring services."""
        print("\n" + "="*60)
        print("🚀 AI Trading Sentinel Monitoring System")
        print("="*60)
        print(f"📊 Grafana Dashboard: http://localhost:{self.config['grafana']['port']}")
        print(f"   Username: admin")
        print(f"   Password: {self.config['grafana']['admin_password']}")
        print()
        print(f"📈 Prometheus: http://localhost:{self.config['prometheus']['port']}")
        print(f"🚨 Alertmanager: http://localhost:{self.config['alertmanager']['port']}")
        print(f"💻 Node Exporter: http://localhost:{self.config['node_exporter']['port']}/metrics")
        print()
        print("📋 Service Management:")
        print("   systemctl status prometheus")
        print("   systemctl status grafana-server")
        print("   systemctl status alertmanager")
        print("   systemctl status health-monitor")
        print()
        print("📝 Logs:")
        print(f"   Deployment: {self.deployment_log}")
        print("   Health Monitor: /opt/ai-trading-sentinel/monitoring/logs/health_monitor.log")
        print("="*60)


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Monitoring Deployment")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing deployment')
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root (use sudo)")
        sys.exit(1)
    
    try:
        deployer = MonitoringDeployer(args.config)
        
        if args.verify_only:
            deployer.verify_deployment()
        elif args.dry_run:
            print("🔍 Dry run mode - showing deployment plan:")
            print("1. Install system dependencies")
            print("2. Create monitoring users")
            print("3. Install Prometheus")
            print("4. Install Grafana")
            print("5. Install Alertmanager")
            print("6. Install exporters")
            print("7. Setup Nginx monitoring")
            print("8. Deploy health monitor")
            print("9. Start services")
            print("10. Verify deployment")
        else:
            deployer.deploy()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())