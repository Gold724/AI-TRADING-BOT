#!/usr/bin/env python3
"""
AI Trading Sentinel - Complete Monitoring Setup
Sets up comprehensive monitoring infrastructure with Prometheus, Grafana, Alertmanager
"""

import os
import sys
import json
import yaml
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MonitoringSetup:
    """Complete monitoring infrastructure setup"""
    
    def __init__(self, config_path: str = "config/monitoring_config.yml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.base_dir = Path("/opt/trading")
        self.monitoring_dir = self.base_dir / "monitoring"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Service directories
        self.prometheus_dir = self.monitoring_dir / "prometheus"
        self.grafana_dir = self.monitoring_dir / "grafana"
        self.alertmanager_dir = self.monitoring_dir / "alertmanager"
        self.exporters_dir = self.monitoring_dir / "exporters"
        
    def load_config(self) -> Dict:
        """Load monitoring configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default monitoring configuration"""
        return {
            'prometheus': {'enabled': True, 'port': 9090},
            'grafana': {'enabled': True, 'port': 3001},
            'alertmanager': {'enabled': True, 'port': 9093},
            'exporters': {
                'node': {'enabled': True, 'port': 9100},
                'redis': {'enabled': True, 'port': 9121},
                'nginx': {'enabled': True, 'port': 9113}
            }
        }
    
    def setup_directories(self):
        """Create necessary directories"""
        logger.info("Setting up monitoring directories...")
        
        directories = [
            self.base_dir,
            self.monitoring_dir,
            self.data_dir,
            self.logs_dir,
            self.prometheus_dir,
            self.grafana_dir,
            self.alertmanager_dir,
            self.exporters_dir,
            self.prometheus_dir / "data",
            self.grafana_dir / "data",
            self.grafana_dir / "dashboards",
            self.grafana_dir / "provisioning" / "datasources",
            self.grafana_dir / "provisioning" / "dashboards",
            self.alertmanager_dir / "data"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def install_dependencies(self):
        """Install required system packages"""
        logger.info("Installing system dependencies...")
        
        packages = [
            "wget", "curl", "tar", "systemd", "nginx",
            "python3-pip", "python3-venv", "redis-server"
        ]
        
        try:
            # Update package list
            subprocess.run(["apt", "update"], check=True)
            
            # Install packages
            subprocess.run(["apt", "install", "-y"] + packages, check=True)
            
            logger.info("System dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            raise
    
    def download_and_install_prometheus(self):
        """Download and install Prometheus"""
        logger.info("Installing Prometheus...")
        
        version = "2.45.0"
        arch = "linux-amd64"
        filename = f"prometheus-{version}.{arch}.tar.gz"
        url = f"https://github.com/prometheus/prometheus/releases/download/v{version}/{filename}"
        
        try:
            # Download
            subprocess.run(["wget", "-O", f"/tmp/{filename}", url], check=True)
            
            # Extract
            subprocess.run(["tar", "-xzf", f"/tmp/{filename}", "-C", "/tmp"], check=True)
            
            # Install binaries
            src_dir = f"/tmp/prometheus-{version}.{arch}"
            subprocess.run(["cp", f"{src_dir}/prometheus", "/usr/local/bin/"], check=True)
            subprocess.run(["cp", f"{src_dir}/promtool", "/usr/local/bin/"], check=True)
            
            # Set permissions
            subprocess.run(["chmod", "+x", "/usr/local/bin/prometheus"], check=True)
            subprocess.run(["chmod", "+x", "/usr/local/bin/promtool"], check=True)
            
            # Copy console files
            shutil.copytree(f"{src_dir}/consoles", self.prometheus_dir / "consoles", dirs_exist_ok=True)
            shutil.copytree(f"{src_dir}/console_libraries", self.prometheus_dir / "console_libraries", dirs_exist_ok=True)
            
            logger.info("Prometheus installed successfully")
        except Exception as e:
            logger.error(f"Failed to install Prometheus: {e}")
            raise
    
    def download_and_install_grafana(self):
        """Download and install Grafana"""
        logger.info("Installing Grafana...")
        
        try:
            # Add Grafana repository
            subprocess.run([
                "wget", "-q", "-O", "-", 
                "https://packages.grafana.com/gpg.key"
            ], stdout=subprocess.PIPE, check=True)
            
            # Install Grafana
            subprocess.run([
                "apt-get", "install", "-y", "software-properties-common"
            ], check=True)
            
            subprocess.run([
                "add-apt-repository", 
                "deb https://packages.grafana.com/oss/deb stable main"
            ], check=True)
            
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "grafana"], check=True)
            
            logger.info("Grafana installed successfully")
        except Exception as e:
            logger.error(f"Failed to install Grafana: {e}")
            raise
    
    def download_and_install_alertmanager(self):
        """Download and install Alertmanager"""
        logger.info("Installing Alertmanager...")
        
        version = "0.25.0"
        arch = "linux-amd64"
        filename = f"alertmanager-{version}.{arch}.tar.gz"
        url = f"https://github.com/prometheus/alertmanager/releases/download/v{version}/{filename}"
        
        try:
            # Download
            subprocess.run(["wget", "-O", f"/tmp/{filename}", url], check=True)
            
            # Extract
            subprocess.run(["tar", "-xzf", f"/tmp/{filename}", "-C", "/tmp"], check=True)
            
            # Install binaries
            src_dir = f"/tmp/alertmanager-{version}.{arch}"
            subprocess.run(["cp", f"{src_dir}/alertmanager", "/usr/local/bin/"], check=True)
            subprocess.run(["cp", f"{src_dir}/amtool", "/usr/local/bin/"], check=True)
            
            # Set permissions
            subprocess.run(["chmod", "+x", "/usr/local/bin/alertmanager"], check=True)
            subprocess.run(["chmod", "+x", "/usr/local/bin/amtool"], check=True)
            
            logger.info("Alertmanager installed successfully")
        except Exception as e:
            logger.error(f"Failed to install Alertmanager: {e}")
            raise
    
    def install_exporters(self):
        """Install Prometheus exporters"""
        logger.info("Installing Prometheus exporters...")
        
        exporters = {
            "node_exporter": {
                "version": "1.6.0",
                "binary": "node_exporter"
            },
            "redis_exporter": {
                "version": "1.51.0",
                "binary": "redis_exporter"
            },
            "nginx_exporter": {
                "version": "0.11.0",
                "binary": "nginx-prometheus-exporter"
            }
        }
        
        for exporter, info in exporters.items():
            try:
                version = info["version"]
                binary = info["binary"]
                arch = "linux-amd64"
                
                if exporter == "nginx_exporter":
                    filename = f"nginx-prometheus-exporter_{version}_{arch}.tar.gz"
                    url = f"https://github.com/nginxinc/nginx-prometheus-exporter/releases/download/v{version}/{filename}"
                else:
                    filename = f"{exporter}-{version}.{arch}.tar.gz"
                    url = f"https://github.com/prometheus/{exporter}/releases/download/v{version}/{filename}"
                
                # Download
                subprocess.run(["wget", "-O", f"/tmp/{filename}", url], check=True)
                
                # Extract
                subprocess.run(["tar", "-xzf", f"/tmp/{filename}", "-C", "/tmp"], check=True)
                
                # Find and install binary
                if exporter == "nginx_exporter":
                    src_binary = f"/tmp/{binary}"
                else:
                    src_dir = f"/tmp/{exporter}-{version}.{arch}"
                    src_binary = f"{src_dir}/{binary}"
                
                subprocess.run(["cp", src_binary, "/usr/local/bin/"], check=True)
                subprocess.run(["chmod", "+x", f"/usr/local/bin/{binary}"], check=True)
                
                logger.info(f"{exporter} installed successfully")
                
            except Exception as e:
                logger.error(f"Failed to install {exporter}: {e}")
                continue
    
    def create_prometheus_config(self):
        """Create Prometheus configuration"""
        logger.info("Creating Prometheus configuration...")
        
        config = {
            'global': {
                'scrape_interval': '15s',
                'evaluation_interval': '15s'
            },
            'rule_files': [
                '/opt/trading/monitoring/prometheus/rules/*.yml'
            ],
            'alerting': {
                'alertmanagers': [{
                    'static_configs': [{
                        'targets': ['localhost:9093']
                    }]
                }]
            },
            'scrape_configs': [
                {
                    'job_name': 'prometheus',
                    'static_configs': [{'targets': ['localhost:9090']}]
                },
                {
                    'job_name': 'node-exporter',
                    'static_configs': [{'targets': ['localhost:9100']}]
                },
                {
                    'job_name': 'redis-exporter',
                    'static_configs': [{'targets': ['localhost:9121']}]
                },
                {
                    'job_name': 'nginx-exporter',
                    'static_configs': [{'targets': ['localhost:9113']}]
                },
                {
                    'job_name': 'trading-api',
                    'static_configs': [{'targets': ['localhost:5000']}],
                    'metrics_path': '/metrics',
                    'scrape_interval': '5s'
                },
                {
                    'job_name': 'trading-bot',
                    'static_configs': [{'targets': ['localhost:8080']}],
                    'metrics_path': '/metrics',
                    'scrape_interval': '5s'
                }
            ]
        }
        
        config_file = self.prometheus_dir / "prometheus.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Prometheus config created: {config_file}")
    
    def create_alertmanager_config(self):
        """Create Alertmanager configuration"""
        logger.info("Creating Alertmanager configuration...")
        
        config = {
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
            'receivers': [{
                'name': 'web.hook',
                'slack_configs': [{
                    'api_url': '${SLACK_WEBHOOK_URL}',
                    'channel': '#trading-alerts',
                    'title': 'AI Trading Sentinel Alert',
                    'text': '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
                }]
            }]
        }
        
        config_file = self.alertmanager_dir / "alertmanager.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Alertmanager config created: {config_file}")
    
    def create_grafana_config(self):
        """Create Grafana configuration"""
        logger.info("Creating Grafana configuration...")
        
        # Datasource configuration
        datasource_config = {
            'apiVersion': 1,
            'datasources': [{
                'name': 'Prometheus',
                'type': 'prometheus',
                'access': 'proxy',
                'url': 'http://localhost:9090',
                'isDefault': True
            }]
        }
        
        datasource_file = self.grafana_dir / "provisioning" / "datasources" / "prometheus.yml"
        with open(datasource_file, 'w') as f:
            yaml.dump(datasource_config, f, default_flow_style=False)
        
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
                    'path': str(self.grafana_dir / "dashboards")
                }
            }]
        }
        
        dashboard_file = self.grafana_dir / "provisioning" / "dashboards" / "default.yml"
        with open(dashboard_file, 'w') as f:
            yaml.dump(dashboard_config, f, default_flow_style=False)
        
        logger.info("Grafana configuration created")
    
    def copy_dashboards(self):
        """Copy Grafana dashboards"""
        logger.info("Copying Grafana dashboards...")
        
        dashboard_source = Path("config/grafana_dashboards.json")
        if dashboard_source.exists():
            with open(dashboard_source, 'r') as f:
                dashboards_data = json.load(f)
            
            for i, dashboard_config in enumerate(dashboards_data.get('dashboards', [])):
                dashboard_file = self.grafana_dir / "dashboards" / f"dashboard_{i+1}.json"
                with open(dashboard_file, 'w') as f:
                    json.dump(dashboard_config['dashboard'], f, indent=2)
                
                logger.info(f"Dashboard copied: {dashboard_file}")
        else:
            logger.warning("No dashboard configuration found")
    
    def copy_alert_rules(self):
        """Copy Prometheus alert rules"""
        logger.info("Copying Prometheus alert rules...")
        
        rules_dir = self.prometheus_dir / "rules"
        rules_dir.mkdir(exist_ok=True)
        
        alert_rules_source = Path("config/alert_rules.yml")
        if alert_rules_source.exists():
            shutil.copy2(alert_rules_source, rules_dir / "trading_alerts.yml")
            logger.info("Alert rules copied successfully")
        else:
            logger.warning("No alert rules found")
    
    def create_systemd_services(self):
        """Create systemd service files"""
        logger.info("Creating systemd services...")
        
        services = {
            'prometheus': {
                'binary': '/usr/local/bin/prometheus',
                'args': [
                    f'--config.file={self.prometheus_dir}/prometheus.yml',
                    f'--storage.tsdb.path={self.prometheus_dir}/data',
                    '--web.console.templates=/opt/trading/monitoring/prometheus/consoles',
                    '--web.console.libraries=/opt/trading/monitoring/prometheus/console_libraries',
                    '--web.listen-address=0.0.0.0:9090',
                    '--web.enable-lifecycle'
                ]
            },
            'alertmanager': {
                'binary': '/usr/local/bin/alertmanager',
                'args': [
                    f'--config.file={self.alertmanager_dir}/alertmanager.yml',
                    f'--storage.path={self.alertmanager_dir}/data',
                    '--web.listen-address=0.0.0.0:9093'
                ]
            },
            'node-exporter': {
                'binary': '/usr/local/bin/node_exporter',
                'args': ['--web.listen-address=0.0.0.0:9100']
            },
            'redis-exporter': {
                'binary': '/usr/local/bin/redis_exporter',
                'args': ['--web.listen-address=0.0.0.0:9121']
            },
            'nginx-exporter': {
                'binary': '/usr/local/bin/nginx-prometheus-exporter',
                'args': ['-nginx.scrape-uri=http://localhost/nginx_status']
            }
        }
        
        for service_name, service_config in services.items():
            service_content = f"""[Unit]
Description={service_name.title()} Service
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart={service_config['binary']} {' '.join(service_config['args'])}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
            
            service_file = f"/etc/systemd/system/{service_name}.service"
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            logger.info(f"Created systemd service: {service_file}")
    
    def create_users_and_permissions(self):
        """Create system users and set permissions"""
        logger.info("Setting up users and permissions...")
        
        try:
            # Create prometheus user
            subprocess.run([
                "useradd", "--no-create-home", "--shell", "/bin/false", "prometheus"
            ], check=False)  # Don't fail if user exists
            
            # Set ownership
            subprocess.run(["chown", "-R", "prometheus:prometheus", str(self.monitoring_dir)], check=True)
            subprocess.run(["chown", "-R", "prometheus:prometheus", str(self.data_dir)], check=True)
            
            # Set permissions
            subprocess.run(["chmod", "-R", "755", str(self.monitoring_dir)], check=True)
            
            logger.info("Users and permissions configured")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set permissions: {e}")
            raise
    
    def start_services(self):
        """Start all monitoring services"""
        logger.info("Starting monitoring services...")
        
        services = [
            'prometheus', 'alertmanager', 'grafana-server',
            'node-exporter', 'redis-exporter', 'nginx-exporter'
        ]
        
        try:
            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            # Enable and start services
            for service in services:
                subprocess.run(["systemctl", "enable", service], check=True)
                subprocess.run(["systemctl", "start", service], check=True)
                logger.info(f"Started service: {service}")
            
            logger.info("All monitoring services started successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start services: {e}")
            raise
    
    def verify_installation(self):
        """Verify monitoring installation"""
        logger.info("Verifying monitoring installation...")
        
        endpoints = {
            'Prometheus': 'http://localhost:9090/-/healthy',
            'Grafana': 'http://localhost:3001/api/health',
            'Alertmanager': 'http://localhost:9093/-/healthy',
            'Node Exporter': 'http://localhost:9100/metrics',
            'Redis Exporter': 'http://localhost:9121/metrics'
        }
        
        import requests
        
        for service, url in endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✓ {service} is healthy")
                else:
                    logger.warning(f"⚠ {service} returned status {response.status_code}")
            except Exception as e:
                logger.error(f"✗ {service} is not accessible: {e}")
    
    def setup_complete_monitoring(self):
        """Run complete monitoring setup"""
        logger.info("Starting complete monitoring setup...")
        
        try:
            self.setup_directories()
            self.install_dependencies()
            self.download_and_install_prometheus()
            self.download_and_install_grafana()
            self.download_and_install_alertmanager()
            self.install_exporters()
            
            self.create_prometheus_config()
            self.create_alertmanager_config()
            self.create_grafana_config()
            self.copy_dashboards()
            self.copy_alert_rules()
            
            self.create_users_and_permissions()
            self.create_systemd_services()
            self.start_services()
            
            # Wait a moment for services to start
            import time
            time.sleep(10)
            
            self.verify_installation()
            
            logger.info("Monitoring setup completed successfully!")
            self.print_access_info()
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
            raise
    
    def print_access_info(self):
        """Print access information"""
        print("\n" + "="*60)
        print("AI Trading Sentinel - Monitoring Setup Complete")
        print("="*60)
        print("\nAccess URLs:")
        print(f"  Prometheus: http://localhost:9090")
        print(f"  Grafana:    http://localhost:3001 (admin/admin)")
        print(f"  Alertmanager: http://localhost:9093")
        print("\nExporter Metrics:")
        print(f"  Node Exporter: http://localhost:9100/metrics")
        print(f"  Redis Exporter: http://localhost:9121/metrics")
        print(f"  Nginx Exporter: http://localhost:9113/metrics")
        print("\nNext Steps:")
        print("  1. Configure Slack webhook URL in environment")
        print("  2. Set Grafana admin password")
        print("  3. Import custom dashboards")
        print("  4. Test alert notifications")
        print("\n" + "="*60)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AI Trading Sentinel Monitoring")
    parser.add_argument("--config", default="config/monitoring_config.yml",
                       help="Path to monitoring configuration file")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify existing installation")
    
    args = parser.parse_args()
    
    # Ensure running as root
    if os.geteuid() != 0:
        print("This script must be run as root (use sudo)")
        sys.exit(1)
    
    setup = MonitoringSetup(args.config)
    
    if args.verify_only:
        setup.verify_installation()
    else:
        setup.setup_complete_monitoring()

if __name__ == "__main__":
    main()