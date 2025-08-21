#!/usr/bin/env python3
"""
AI Trading Sentinel - Monitoring Setup Script
Comprehensive 24/7 monitoring infrastructure deployment
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import requests
from datetime import datetime

class MonitoringSetup:
    """Setup and configure comprehensive monitoring infrastructure"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.monitoring_dir = self.project_root / "monitoring"
        self.config_dir = self.monitoring_dir / "config"
        self.data_dir = self.monitoring_dir / "data"
        self.logs_dir = self.monitoring_dir / "logs"
        
        # Service ports
        self.ports = {
            "prometheus": 9090,
            "grafana": 3001,
            "alertmanager": 9093,
            "node_exporter": 9100,
            "redis_exporter": 9121,
            "nginx_exporter": 9113,
            "blackbox_exporter": 9115
        }
        
        # Create directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.monitoring_dir,
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.data_dir / "prometheus",
            self.data_dir / "grafana",
            self.data_dir / "alertmanager"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
    
    def setup_prometheus(self) -> bool:
        """Setup Prometheus monitoring"""
        print("\n🔧 Setting up Prometheus...")
        
        try:
            # Copy Prometheus configuration
            prometheus_config = self.monitoring_dir / "prometheus_config.yml"
            if prometheus_config.exists():
                shutil.copy2(prometheus_config, self.config_dir / "prometheus.yml")
                print("✅ Prometheus configuration copied")
            else:
                self._create_default_prometheus_config()
            
            # Create Prometheus systemd service
            self._create_prometheus_service()
            
            # Download and install Prometheus (if not exists)
            if not self._check_prometheus_installed():
                self._install_prometheus()
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Prometheus: {e}")
            return False
    
    def setup_grafana(self) -> bool:
        """Setup Grafana dashboard"""
        print("\n📊 Setting up Grafana...")
        
        try:
            # Create Grafana configuration
            self._create_grafana_config()
            
            # Create Grafana systemd service
            self._create_grafana_service()
            
            # Download and install Grafana (if not exists)
            if not self._check_grafana_installed():
                self._install_grafana()
            
            # Import dashboard
            self._setup_grafana_dashboard()
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Grafana: {e}")
            return False
    
    def setup_alertmanager(self) -> bool:
        """Setup Alertmanager for notifications"""
        print("\n🚨 Setting up Alertmanager...")
        
        try:
            # Create Alertmanager configuration
            self._create_alertmanager_config()
            
            # Create Alertmanager systemd service
            self._create_alertmanager_service()
            
            # Download and install Alertmanager (if not exists)
            if not self._check_alertmanager_installed():
                self._install_alertmanager()
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Alertmanager: {e}")
            return False
    
    def setup_exporters(self) -> bool:
        """Setup various exporters for metrics collection"""
        print("\n📈 Setting up exporters...")
        
        try:
            # Node Exporter for system metrics
            self._setup_node_exporter()
            
            # Redis Exporter for database metrics
            self._setup_redis_exporter()
            
            # Nginx Exporter for web server metrics
            self._setup_nginx_exporter()
            
            # Blackbox Exporter for URL monitoring
            self._setup_blackbox_exporter()
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up exporters: {e}")
            return False
    
    def setup_slack_integration(self) -> bool:
        """Setup Slack alerting integration"""
        print("\n💬 Setting up Slack integration...")
        
        try:
            # Copy Slack alerting script
            slack_script = self.monitoring_dir / "slack_alerting.py"
            if slack_script.exists():
                # Make it executable
                os.chmod(slack_script, 0o755)
                print("✅ Slack alerting script configured")
            
            # Create Slack webhook service
            self._create_slack_webhook_service()
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Slack integration: {e}")
            return False
    
    def _create_default_prometheus_config(self):
        """Create default Prometheus configuration"""
        config = {
            'global': {
                'scrape_interval': '15s',
                'evaluation_interval': '15s'
            },
            'alerting': {
                'alertmanagers': [
                    {'static_configs': [{'targets': ['localhost:9093']}]}
                ]
            },
            'rule_files': [
                'alert_rules.yml'
            ],
            'scrape_configs': [
                {
                    'job_name': 'prometheus',
                    'static_configs': [{'targets': ['localhost:9090']}]
                },
                {
                    'job_name': 'trading-sentinel-api',
                    'static_configs': [{'targets': ['localhost:5000']}],
                    'metrics_path': '/metrics'
                },
                {
                    'job_name': 'node-exporter',
                    'static_configs': [{'targets': ['localhost:9100']}]
                }
            ]
        }
        
        with open(self.config_dir / "prometheus.yml", 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print("✅ Default Prometheus configuration created")
    
    def _create_prometheus_service(self):
        """Create Prometheus systemd service"""
        service_content = f"""[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecReload=/bin/kill -HUP $MAINPID
ExecStart=/usr/local/bin/prometheus \
  --config.file={self.config_dir}/prometheus.yml \
  --storage.tsdb.path={self.data_dir}/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:{self.ports['prometheus']} \
  --web.external-url=

SyslogIdentifier=prometheus
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/prometheus.service")
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            print("✅ Prometheus systemd service created")
        except PermissionError:
            print("⚠️  Need sudo privileges to create systemd service")
            # Save to local directory for manual installation
            with open(self.config_dir / "prometheus.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Service file saved to {self.config_dir}/prometheus.service")
    
    def _create_grafana_config(self):
        """Create Grafana configuration"""
        config_content = f"""[server]
http_port = {self.ports['grafana']}
domain = localhost
root_url = http://localhost:{self.ports['grafana']}/

[database]
type = sqlite3
path = {self.data_dir}/grafana/grafana.db

[security]
admin_user = admin
admin_password = admin123
secret_key = SW2YcwTIb9zpOOhoPsMm

[users]
allow_sign_up = false
allow_org_create = false

[auth.anonymous]
enabled = false

[log]
mode = file
level = info
format = text

[log.file]
path = {self.logs_dir}/grafana.log
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 7

[alerting]
enabled = true
execute_alerts = true

[metrics]
enabled = true
basic_auth_username = 
basic_auth_password = 
"""
        
        with open(self.config_dir / "grafana.ini", 'w') as f:
            f.write(config_content)
        
        print("✅ Grafana configuration created")
    
    def _create_grafana_service(self):
        """Create Grafana systemd service"""
        service_content = f"""[Unit]
Description=Grafana instance
Documentation=http://docs.grafana.org
Wants=network-online.target
After=network-online.target
After=postgresql.service mariadb.service mysql.service

[Service]
EnvironmentFile=/etc/default/grafana-server
User=grafana
Group=grafana
Type=simple
Restart=on-failure
WorkingDirectory=/usr/share/grafana
RuntimeDirectory=grafana
RuntimeDirectoryMode=0750
ExecStart=/usr/sbin/grafana-server \
  --config={self.config_dir}/grafana.ini \
  --pidfile=/var/run/grafana/grafana-server.pid \
  --packaging=deb \
  cfg:default.paths.logs={self.logs_dir} \
  cfg:default.paths.data={self.data_dir}/grafana \
  cfg:default.paths.plugins=/var/lib/grafana/plugins

LimitNOFILE=10000
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/grafana-server.service")
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            print("✅ Grafana systemd service created")
        except PermissionError:
            with open(self.config_dir / "grafana-server.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Service file saved to {self.config_dir}/grafana-server.service")
    
    def _create_alertmanager_config(self):
        """Create Alertmanager configuration"""
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK')
        
        config = {
            'global': {
                'smtp_smarthost': 'localhost:587',
                'smtp_from': 'alerts@ai-trading-sentinel.com',
                'slack_api_url': slack_webhook
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
                    'slack_configs': [
                        {
                            'api_url': slack_webhook,
                            'channel': '#trading-alerts',
                            'title': 'AI Trading Sentinel Alert',
                            'text': '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}',
                            'send_resolved': True
                        }
                    ]
                }
            ],
            'inhibit_rules': [
                {
                    'source_match': {'severity': 'critical'},
                    'target_match': {'severity': 'warning'},
                    'equal': ['alertname', 'dev', 'instance']
                }
            ]
        }
        
        with open(self.config_dir / "alertmanager.yml", 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print("✅ Alertmanager configuration created")
    
    def _create_alertmanager_service(self):
        """Create Alertmanager systemd service"""
        service_content = f"""[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/usr/local/bin/alertmanager \
  --config.file={self.config_dir}/alertmanager.yml \
  --storage.path={self.data_dir}/alertmanager/ \
  --web.listen-address=0.0.0.0:{self.ports['alertmanager']}

Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/alertmanager.service")
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            print("✅ Alertmanager systemd service created")
        except PermissionError:
            with open(self.config_dir / "alertmanager.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Service file saved to {self.config_dir}/alertmanager.service")
    
    def _setup_node_exporter(self):
        """Setup Node Exporter for system metrics"""
        service_content = f"""[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
  --web.listen-address=0.0.0.0:{self.ports['node_exporter']}

Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open("/etc/systemd/system/node_exporter.service", 'w') as f:
                f.write(service_content)
            print("✅ Node Exporter service created")
        except PermissionError:
            with open(self.config_dir / "node_exporter.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Node Exporter service file saved")
    
    def _setup_redis_exporter(self):
        """Setup Redis Exporter"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        service_content = f"""[Unit]
Description=Redis Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=redis_exporter
Group=redis_exporter
Type=simple
Environment=REDIS_ADDR={redis_url}
ExecStart=/usr/local/bin/redis_exporter \
  -web.listen-address=0.0.0.0:{self.ports['redis_exporter']}

Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open("/etc/systemd/system/redis_exporter.service", 'w') as f:
                f.write(service_content)
            print("✅ Redis Exporter service created")
        except PermissionError:
            with open(self.config_dir / "redis_exporter.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Redis Exporter service file saved")
    
    def _setup_nginx_exporter(self):
        """Setup Nginx Exporter"""
        service_content = f"""[Unit]
Description=Nginx Prometheus Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=nginx_exporter
Group=nginx_exporter
Type=simple
ExecStart=/usr/local/bin/nginx-prometheus-exporter \
  -web.listen-address=0.0.0.0:{self.ports['nginx_exporter']} \
  -nginx.scrape-uri=http://localhost/nginx_status

Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open("/etc/systemd/system/nginx_exporter.service", 'w') as f:
                f.write(service_content)
            print("✅ Nginx Exporter service created")
        except PermissionError:
            with open(self.config_dir / "nginx_exporter.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Nginx Exporter service file saved")
    
    def _setup_blackbox_exporter(self):
        """Setup Blackbox Exporter for URL monitoring"""
        # Create blackbox exporter config
        blackbox_config = {
            'modules': {
                'http_2xx': {
                    'prober': 'http',
                    'timeout': '5s',
                    'http': {
                        'valid_http_versions': ['HTTP/1.1', 'HTTP/2.0'],
                        'valid_status_codes': [],
                        'method': 'GET'
                    }
                },
                'tcp_connect': {
                    'prober': 'tcp',
                    'timeout': '5s'
                }
            }
        }
        
        with open(self.config_dir / "blackbox.yml", 'w') as f:
            yaml.dump(blackbox_config, f, default_flow_style=False)
        
        service_content = f"""[Unit]
Description=Blackbox Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=blackbox_exporter
Group=blackbox_exporter
Type=simple
ExecStart=/usr/local/bin/blackbox_exporter \
  --config.file={self.config_dir}/blackbox.yml \
  --web.listen-address=0.0.0.0:{self.ports['blackbox_exporter']}

Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open("/etc/systemd/system/blackbox_exporter.service", 'w') as f:
                f.write(service_content)
            print("✅ Blackbox Exporter service created")
        except PermissionError:
            with open(self.config_dir / "blackbox_exporter.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Blackbox Exporter service file saved")
    
    def _create_slack_webhook_service(self):
        """Create Slack webhook service for alerts"""
        service_content = f"""[Unit]
Description=AI Trading Sentinel Slack Alerting
Wants=network-online.target
After=network-online.target

[Service]
User=trading
Group=trading
Type=simple
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
ExecStart=/usr/bin/python3 {self.monitoring_dir}/slack_alerting.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open("/etc/systemd/system/trading-slack-alerts.service", 'w') as f:
                f.write(service_content)
            print("✅ Slack alerting service created")
        except PermissionError:
            with open(self.config_dir / "trading-slack-alerts.service", 'w') as f:
                f.write(service_content)
            print(f"📄 Slack alerting service file saved")
    
    def _check_prometheus_installed(self) -> bool:
        """Check if Prometheus is installed"""
        return shutil.which('prometheus') is not None
    
    def _check_grafana_installed(self) -> bool:
        """Check if Grafana is installed"""
        return shutil.which('grafana-server') is not None
    
    def _check_alertmanager_installed(self) -> bool:
        """Check if Alertmanager is installed"""
        return shutil.which('alertmanager') is not None
    
    def _install_prometheus(self):
        """Install Prometheus (placeholder - requires manual installation)"""
        print("⚠️  Prometheus not found. Please install manually:")
        print("   wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz")
        print("   tar xvfz prometheus-*.tar.gz")
        print("   sudo cp prometheus-*/prometheus /usr/local/bin/")
        print("   sudo cp prometheus-*/promtool /usr/local/bin/")
    
    def _install_grafana(self):
        """Install Grafana (placeholder - requires manual installation)"""
        print("⚠️  Grafana not found. Please install manually:")
        print("   wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -")
        print("   echo 'deb https://packages.grafana.com/oss/deb stable main' | sudo tee -a /etc/apt/sources.list.d/grafana.list")
        print("   sudo apt update && sudo apt install grafana")
    
    def _install_alertmanager(self):
        """Install Alertmanager (placeholder - requires manual installation)"""
        print("⚠️  Alertmanager not found. Please install manually:")
        print("   wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz")
        print("   tar xvfz alertmanager-*.tar.gz")
        print("   sudo cp alertmanager-*/alertmanager /usr/local/bin/")
    
    def _setup_grafana_dashboard(self):
        """Setup Grafana dashboard"""
        dashboard_file = self.monitoring_dir / "grafana_dashboard.json"
        if dashboard_file.exists():
            print("✅ Grafana dashboard configuration found")
            print(f"📄 Import dashboard from: {dashboard_file}")
        else:
            print("⚠️  Grafana dashboard configuration not found")
    
    def create_monitoring_users(self):
        """Create system users for monitoring services"""
        print("\n👥 Creating monitoring users...")
        
        users = ['prometheus', 'grafana', 'alertmanager', 'node_exporter', 'redis_exporter', 'nginx_exporter', 'blackbox_exporter']
        
        for user in users:
            try:
                subprocess.run(['sudo', 'useradd', '--no-create-home', '--shell', '/bin/false', user], 
                             check=False, capture_output=True)
                print(f"✅ User {user} created (or already exists)")
            except Exception as e:
                print(f"⚠️  Could not create user {user}: {e}")
    
    def set_permissions(self):
        """Set proper permissions for monitoring directories"""
        print("\n🔒 Setting permissions...")
        
        try:
            # Set ownership for data directories
            subprocess.run(['sudo', 'chown', '-R', 'prometheus:prometheus', str(self.data_dir / "prometheus")], 
                         check=False)
            subprocess.run(['sudo', 'chown', '-R', 'grafana:grafana', str(self.data_dir / "grafana")], 
                         check=False)
            subprocess.run(['sudo', 'chown', '-R', 'alertmanager:alertmanager', str(self.data_dir / "alertmanager")], 
                         check=False)
            
            # Set permissions
            subprocess.run(['sudo', 'chmod', '-R', '755', str(self.monitoring_dir)], check=False)
            
            print("✅ Permissions set")
            
        except Exception as e:
            print(f"⚠️  Could not set permissions: {e}")
    
    def start_services(self):
        """Start monitoring services"""
        print("\n🚀 Starting monitoring services...")
        
        services = [
            'prometheus',
            'grafana-server',
            'alertmanager',
            'node_exporter',
            'redis_exporter',
            'nginx_exporter',
            'blackbox_exporter',
            'trading-slack-alerts'
        ]
        
        for service in services:
            try:
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
                subprocess.run(['sudo', 'systemctl', 'enable', service], check=False)
                subprocess.run(['sudo', 'systemctl', 'start', service], check=False)
                
                # Check status
                result = subprocess.run(['sudo', 'systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip() == 'active':
                    print(f"✅ {service} started successfully")
                else:
                    print(f"⚠️  {service} may not be running properly")
                    
            except Exception as e:
                print(f"❌ Error starting {service}: {e}")
    
    def verify_setup(self) -> Dict[str, bool]:
        """Verify monitoring setup"""
        print("\n🔍 Verifying monitoring setup...")
        
        results = {}
        
        # Check service endpoints
        endpoints = {
            'Prometheus': f'http://localhost:{self.ports["prometheus"]}/api/v1/status/config',
            'Grafana': f'http://localhost:{self.ports["grafana"]}/api/health',
            'Alertmanager': f'http://localhost:{self.ports["alertmanager"]}/-/healthy'
        }
        
        for service, url in endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service} is responding")
                    results[service] = True
                else:
                    print(f"⚠️  {service} returned status {response.status_code}")
                    results[service] = False
            except Exception as e:
                print(f"❌ {service} is not accessible: {e}")
                results[service] = False
        
        return results
    
    def generate_summary(self):
        """Generate setup summary"""
        print("\n" + "="*60)
        print("🎯 AI TRADING SENTINEL MONITORING SETUP COMPLETE")
        print("="*60)
        print(f"📁 Monitoring Directory: {self.monitoring_dir}")
        print(f"⚙️  Configuration Directory: {self.config_dir}")
        print(f"💾 Data Directory: {self.data_dir}")
        print(f"📋 Logs Directory: {self.logs_dir}")
        print("\n🌐 Service URLs:")
        print(f"   Prometheus: http://localhost:{self.ports['prometheus']}")
        print(f"   Grafana: http://localhost:{self.ports['grafana']} (admin/admin123)")
        print(f"   Alertmanager: http://localhost:{self.ports['alertmanager']}")
        print("\n📊 Next Steps:")
        print("   1. Import Grafana dashboard from grafana_dashboard.json")
        print("   2. Configure Slack webhook URL in environment variables")
        print("   3. Test alert notifications")
        print("   4. Set up SSL certificates for production")
        print("   5. Configure firewall rules for monitoring ports")
        print("\n🔧 Management Commands:")
        print("   sudo systemctl status prometheus")
        print("   sudo systemctl restart grafana-server")
        print("   sudo journalctl -u alertmanager -f")
        print("="*60)

def main():
    """Main setup function"""
    print("🚀 AI Trading Sentinel - Monitoring Setup")
    print("Setting up comprehensive 24/7 monitoring infrastructure...\n")
    
    # Initialize setup
    setup = MonitoringSetup()
    
    # Create users
    setup.create_monitoring_users()
    
    # Setup components
    success = True
    success &= setup.setup_prometheus()
    success &= setup.setup_grafana()
    success &= setup.setup_alertmanager()
    success &= setup.setup_exporters()
    success &= setup.setup_slack_integration()
    
    # Set permissions
    setup.set_permissions()
    
    # Start services
    setup.start_services()
    
    # Wait for services to start
    print("\n⏳ Waiting for services to start...")
    time.sleep(10)
    
    # Verify setup
    results = setup.verify_setup()
    
    # Generate summary
    setup.generate_summary()
    
    # Exit with appropriate code
    if all(results.values()):
        print("\n🎉 Monitoring setup completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some services may need manual configuration")
        sys.exit(1)

if __name__ == "__main__":
    main()