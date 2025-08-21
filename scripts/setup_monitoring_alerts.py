#!/usr/bin/env python3
"""
AI Trading Sentinel - Monitoring & Alerting Setup
Comprehensive monitoring infrastructure with Prometheus, Grafana, and alerting.
"""

import os
import sys
import json
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class MonitoringAlertsSetup:
    """Setup comprehensive monitoring and alerting infrastructure."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.monitoring_dir = self.project_root / "monitoring"
        self.config_dir = self.project_root / "config"
        self.scripts_dir = self.project_root / "scripts"
        
        # Create directories
        for directory in [self.monitoring_dir, self.config_dir]:
            directory.mkdir(exist_ok=True)
    
    def setup_prometheus_config(self) -> bool:
        """Setup Prometheus configuration with comprehensive scraping targets."""
        try:
            prometheus_config = {
                'global': {
                    'scrape_interval': '15s',
                    'evaluation_interval': '15s',
                    'external_labels': {
                        'monitor': 'ai-trading-sentinel',
                        'environment': 'production'
                    }
                },
                'rule_files': [
                    '/etc/prometheus/rules/*.yml'
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
                        'static_configs': [{
                            'targets': ['localhost:9090']
                        }]
                    },
                    {
                        'job_name': 'node-exporter',
                        'static_configs': [{
                            'targets': ['localhost:9100']
                        }]
                    },
                    {
                        'job_name': 'redis-exporter',
                        'static_configs': [{
                            'targets': ['localhost:9121']
                        }]
                    },
                    {
                        'job_name': 'nginx-exporter',
                        'static_configs': [{
                            'targets': ['localhost:9113']
                        }]
                    },
                    {
                        'job_name': 'trading-api',
                        'metrics_path': '/metrics',
                        'static_configs': [{
                            'targets': ['localhost:5000']
                        }]
                    },
                    {
                        'job_name': 'trading-bot',
                        'metrics_path': '/metrics',
                        'static_configs': [{
                            'targets': ['localhost:8080']
                        }]
                    },
                    {
                        'job_name': 'blackbox-http',
                        'metrics_path': '/probe',
                        'params': {
                            'module': ['http_2xx']
                        },
                        'static_configs': [{
                            'targets': [
                                'http://localhost:5000/health',
                                'http://localhost:3000',
                                'https://your-domain.com'
                            ]
                        }],
                        'relabel_configs': [{
                            'source_labels': ['__address__'],
                            'target_label': '__param_target'
                        }, {
                            'source_labels': ['__param_target'],
                            'target_label': 'instance'
                        }, {
                            'target_label': '__address__',
                            'replacement': 'localhost:9115'
                        }]
                    }
                ]
            }
            
            config_file = self.config_dir / "prometheus.yml"
            with open(config_file, 'w') as f:
                yaml.dump(prometheus_config, f, default_flow_style=False)
            
            print(f"✓ Prometheus configuration created: {config_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Prometheus config: {e}")
            return False
    
    def setup_alerting_rules(self) -> bool:
        """Setup Prometheus alerting rules for trading system monitoring."""
        try:
            rules_dir = self.monitoring_dir / "rules"
            rules_dir.mkdir(exist_ok=True)
            
            # Trading system alerts
            trading_rules = {
                'groups': [{
                    'name': 'trading_system',
                    'rules': [
                        {
                            'alert': 'TradingBotDown',
                            'expr': 'up{job="trading-bot"} == 0',
                            'for': '1m',
                            'labels': {
                                'severity': 'critical',
                                'service': 'trading-bot'
                            },
                            'annotations': {
                                'summary': 'Trading bot is down',
                                'description': 'Trading bot has been down for more than 1 minute'
                            }
                        },
                        {
                            'alert': 'TradingAPIDown',
                            'expr': 'up{job="trading-api"} == 0',
                            'for': '1m',
                            'labels': {
                                'severity': 'critical',
                                'service': 'trading-api'
                            },
                            'annotations': {
                                'summary': 'Trading API is down',
                                'description': 'Trading API has been down for more than 1 minute'
                            }
                        },
                        {
                            'alert': 'HighErrorRate',
                            'expr': 'rate(http_requests_total{status=~"5.."}[5m]) > 0.1',
                            'for': '2m',
                            'labels': {
                                'severity': 'warning',
                                'service': 'trading-api'
                            },
                            'annotations': {
                                'summary': 'High error rate detected',
                                'description': 'Error rate is above 10% for 2 minutes'
                            }
                        },
                        {
                            'alert': 'TradingLatencyHigh',
                            'expr': 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2',
                            'for': '3m',
                            'labels': {
                                'severity': 'warning',
                                'service': 'trading-api'
                            },
                            'annotations': {
                                'summary': 'High trading latency',
                                'description': '95th percentile latency is above 2 seconds'
                            }
                        },
                        {
                            'alert': 'RedisDown',
                            'expr': 'up{job="redis-exporter"} == 0',
                            'for': '1m',
                            'labels': {
                                'severity': 'critical',
                                'service': 'redis'
                            },
                            'annotations': {
                                'summary': 'Redis is down',
                                'description': 'Redis database is not responding'
                            }
                        },
                        {
                            'alert': 'RedisMemoryHigh',
                            'expr': 'redis_memory_used_bytes / redis_memory_max_bytes > 0.9',
                            'for': '5m',
                            'labels': {
                                'severity': 'warning',
                                'service': 'redis'
                            },
                            'annotations': {
                                'summary': 'Redis memory usage high',
                                'description': 'Redis memory usage is above 90%'
                            }
                        }
                    ]
                }]
            }
            
            # System resource alerts
            system_rules = {
                'groups': [{
                    'name': 'system_resources',
                    'rules': [
                        {
                            'alert': 'HighCPUUsage',
                            'expr': '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80',
                            'for': '5m',
                            'labels': {
                                'severity': 'warning',
                                'service': 'system'
                            },
                            'annotations': {
                                'summary': 'High CPU usage',
                                'description': 'CPU usage is above 80% for 5 minutes'
                            }
                        },
                        {
                            'alert': 'HighMemoryUsage',
                            'expr': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85',
                            'for': '5m',
                            'labels': {
                                'severity': 'warning',
                                'service': 'system'
                            },
                            'annotations': {
                                'summary': 'High memory usage',
                                'description': 'Memory usage is above 85% for 5 minutes'
                            }
                        },
                        {
                            'alert': 'DiskSpaceLow',
                            'expr': '(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100 > 85',
                            'for': '5m',
                            'labels': {
                                'severity': 'warning',
                                'service': 'system'
                            },
                            'annotations': {
                                'summary': 'Low disk space',
                                'description': 'Disk usage is above 85%'
                            }
                        },
                        {
                            'alert': 'HighNetworkTraffic',
                            'expr': 'rate(node_network_receive_bytes_total[5m]) > 100000000',
                            'for': '5m',
                            'labels': {
                                'severity': 'info',
                                'service': 'system'
                            },
                            'annotations': {
                                'summary': 'High network traffic',
                                'description': 'Network receive rate is above 100MB/s'
                            }
                        }
                    ]
                }]
            }
            
            # Write rule files
            with open(rules_dir / "trading_alerts.yml", 'w') as f:
                yaml.dump(trading_rules, f, default_flow_style=False)
            
            with open(rules_dir / "system_alerts.yml", 'w') as f:
                yaml.dump(system_rules, f, default_flow_style=False)
            
            print(f"✓ Alerting rules created in: {rules_dir}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating alerting rules: {e}")
            return False
    
    def setup_alertmanager_config(self) -> bool:
        """Setup Alertmanager configuration with Slack integration."""
        try:
            alertmanager_config = {
                'global': {
                    'smtp_smarthost': 'localhost:587',
                    'smtp_from': 'alerts@ai-trading-sentinel.com',
                    'slack_api_url': '${SLACK_WEBHOOK_URL}'
                },
                'templates': [
                    '/etc/alertmanager/templates/*.tmpl'
                ],
                'route': {
                    'group_by': ['alertname', 'cluster', 'service'],
                    'group_wait': '10s',
                    'group_interval': '10s',
                    'repeat_interval': '1h',
                    'receiver': 'default',
                    'routes': [
                        {
                            'match': {
                                'severity': 'critical'
                            },
                            'receiver': 'critical-alerts',
                            'group_wait': '5s',
                            'repeat_interval': '5m'
                        },
                        {
                            'match': {
                                'severity': 'warning'
                            },
                            'receiver': 'warning-alerts',
                            'repeat_interval': '30m'
                        },
                        {
                            'match': {
                                'service': 'trading-bot'
                            },
                            'receiver': 'trading-alerts',
                            'group_wait': '5s',
                            'repeat_interval': '10m'
                        }
                    ]
                },
                'receivers': [
                    {
                        'name': 'default',
                        'slack_configs': [{
                            'channel': '#trading-alerts',
                            'title': 'AI Trading Sentinel Alert',
                            'text': '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}{{ end }}',
                            'send_resolved': True
                        }]
                    },
                    {
                        'name': 'critical-alerts',
                        'slack_configs': [{
                            'channel': '#trading-critical',
                            'title': '🚨 CRITICAL: AI Trading Sentinel',
                            'text': '{{ range .Alerts }}**{{ .Labels.alertname }}**\n{{ .Annotations.description }}\nSeverity: {{ .Labels.severity }}{{ end }}',
                            'send_resolved': True,
                            'color': 'danger'
                        }]
                    },
                    {
                        'name': 'warning-alerts',
                        'slack_configs': [{
                            'channel': '#trading-warnings',
                            'title': '⚠️ WARNING: AI Trading Sentinel',
                            'text': '{{ range .Alerts }}**{{ .Labels.alertname }}**\n{{ .Annotations.description }}{{ end }}',
                            'send_resolved': True,
                            'color': 'warning'
                        }]
                    },
                    {
                        'name': 'trading-alerts',
                        'slack_configs': [{
                            'channel': '#trading-system',
                            'title': '📈 Trading System Alert',
                            'text': '{{ range .Alerts }}**{{ .Labels.alertname }}**\n{{ .Annotations.description }}\nService: {{ .Labels.service }}{{ end }}',
                            'send_resolved': True,
                            'color': 'good'
                        }]
                    }
                ],
                'inhibit_rules': [
                    {
                        'source_match': {
                            'severity': 'critical'
                        },
                        'target_match': {
                            'severity': 'warning'
                        },
                        'equal': ['alertname', 'cluster', 'service']
                    }
                ]
            }
            
            config_file = self.config_dir / "alertmanager.yml"
            with open(config_file, 'w') as f:
                yaml.dump(alertmanager_config, f, default_flow_style=False)
            
            print(f"✓ Alertmanager configuration created: {config_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Alertmanager config: {e}")
            return False
    
    def setup_grafana_dashboards(self) -> bool:
        """Setup Grafana dashboards for trading system monitoring."""
        try:
            dashboards_dir = self.monitoring_dir / "grafana" / "dashboards"
            dashboards_dir.mkdir(parents=True, exist_ok=True)
            
            # Trading System Overview Dashboard
            trading_dashboard = {
                "dashboard": {
                    "id": None,
                    "title": "AI Trading Sentinel - System Overview",
                    "tags": ["trading", "system", "overview"],
                    "timezone": "browser",
                    "panels": [
                        {
                            "id": 1,
                            "title": "System Status",
                            "type": "stat",
                            "targets": [{
                                "expr": "up{job=~'trading-.*'}",
                                "legendFormat": "{{job}}"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                        },
                        {
                            "id": 2,
                            "title": "API Response Time",
                            "type": "graph",
                            "targets": [{
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                        },
                        {
                            "id": 3,
                            "title": "Request Rate",
                            "type": "graph",
                            "targets": [{
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{status}}"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                        },
                        {
                            "id": 4,
                            "title": "Error Rate",
                            "type": "graph",
                            "targets": [{
                                "expr": "rate(http_requests_total{status=~'5..'}[5m]) / rate(http_requests_total[5m])",
                                "legendFormat": "Error Rate"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                        }
                    ],
                    "time": {"from": "now-1h", "to": "now"},
                    "refresh": "5s"
                }
            }
            
            # System Resources Dashboard
            resources_dashboard = {
                "dashboard": {
                    "id": None,
                    "title": "AI Trading Sentinel - System Resources",
                    "tags": ["system", "resources", "monitoring"],
                    "timezone": "browser",
                    "panels": [
                        {
                            "id": 1,
                            "title": "CPU Usage",
                            "type": "graph",
                            "targets": [{
                                "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
                                "legendFormat": "CPU Usage %"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                        },
                        {
                            "id": 2,
                            "title": "Memory Usage",
                            "type": "graph",
                            "targets": [{
                                "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                                "legendFormat": "Memory Usage %"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                        },
                        {
                            "id": 3,
                            "title": "Disk Usage",
                            "type": "graph",
                            "targets": [{
                                "expr": "(1 - (node_filesystem_avail_bytes{fstype!='tmpfs'} / node_filesystem_size_bytes{fstype!='tmpfs'})) * 100",
                                "legendFormat": "{{mountpoint}}"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                        },
                        {
                            "id": 4,
                            "title": "Network Traffic",
                            "type": "graph",
                            "targets": [{
                                "expr": "rate(node_network_receive_bytes_total[5m])",
                                "legendFormat": "RX {{device}}"
                            }, {
                                "expr": "rate(node_network_transmit_bytes_total[5m])",
                                "legendFormat": "TX {{device}}"
                            }],
                            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                        }
                    ],
                    "time": {"from": "now-1h", "to": "now"},
                    "refresh": "5s"
                }
            }
            
            # Write dashboard files
            with open(dashboards_dir / "trading_overview.json", 'w') as f:
                json.dump(trading_dashboard, f, indent=2)
            
            with open(dashboards_dir / "system_resources.json", 'w') as f:
                json.dump(resources_dashboard, f, indent=2)
            
            print(f"✓ Grafana dashboards created in: {dashboards_dir}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Grafana dashboards: {e}")
            return False
    
    def setup_grafana_provisioning(self) -> bool:
        """Setup Grafana provisioning configuration."""
        try:
            provisioning_dir = self.monitoring_dir / "grafana" / "provisioning"
            datasources_dir = provisioning_dir / "datasources"
            dashboards_dir = provisioning_dir / "dashboards"
            
            for directory in [datasources_dir, dashboards_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Datasource configuration
            datasource_config = {
                "apiVersion": 1,
                "datasources": [{
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://localhost:9090",
                    "isDefault": True,
                    "editable": True
                }]
            }
            
            with open(datasources_dir / "prometheus.yml", 'w') as f:
                yaml.dump(datasource_config, f, default_flow_style=False)
            
            # Dashboard provider configuration
            dashboard_config = {
                "apiVersion": 1,
                "providers": [{
                    "name": "AI Trading Sentinel",
                    "orgId": 1,
                    "folder": "",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": "/var/lib/grafana/dashboards"
                    }
                }]
            }
            
            with open(dashboards_dir / "dashboards.yml", 'w') as f:
                yaml.dump(dashboard_config, f, default_flow_style=False)
            
            print(f"✓ Grafana provisioning configuration created")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Grafana provisioning config: {e}")
            return False
    
    def create_docker_compose_monitoring(self) -> bool:
        """Create Docker Compose configuration for monitoring stack."""
        try:
            docker_compose = {
                'version': '3.8',
                'services': {
                    'prometheus': {
                        'image': 'prom/prometheus:latest',
                        'container_name': 'prometheus',
                        'ports': ['9090:9090'],
                        'volumes': [
                            './config/prometheus.yml:/etc/prometheus/prometheus.yml',
                            './monitoring/rules:/etc/prometheus/rules',
                            'prometheus_data:/prometheus'
                        ],
                        'command': [
                            '--config.file=/etc/prometheus/prometheus.yml',
                            '--storage.tsdb.path=/prometheus',
                            '--web.console.libraries=/etc/prometheus/console_libraries',
                            '--web.console.templates=/etc/prometheus/consoles',
                            '--storage.tsdb.retention.time=200h',
                            '--web.enable-lifecycle'
                        ],
                        'restart': 'unless-stopped'
                    },
                    'alertmanager': {
                        'image': 'prom/alertmanager:latest',
                        'container_name': 'alertmanager',
                        'ports': ['9093:9093'],
                        'volumes': [
                            './config/alertmanager.yml:/etc/alertmanager/alertmanager.yml'
                        ],
                        'restart': 'unless-stopped'
                    },
                    'grafana': {
                        'image': 'grafana/grafana:latest',
                        'container_name': 'grafana',
                        'ports': ['3001:3000'],
                        'volumes': [
                            'grafana_data:/var/lib/grafana',
                            './monitoring/grafana/provisioning:/etc/grafana/provisioning',
                            './monitoring/grafana/dashboards:/var/lib/grafana/dashboards'
                        ],
                        'environment': {
                            'GF_SECURITY_ADMIN_PASSWORD': '${GRAFANA_ADMIN_PASSWORD:-admin}',
                            'GF_USERS_ALLOW_SIGN_UP': 'false'
                        },
                        'restart': 'unless-stopped'
                    },
                    'node-exporter': {
                        'image': 'prom/node-exporter:latest',
                        'container_name': 'node-exporter',
                        'ports': ['9100:9100'],
                        'volumes': [
                            '/proc:/host/proc:ro',
                            '/sys:/host/sys:ro',
                            '/:/rootfs:ro'
                        ],
                        'command': [
                            '--path.procfs=/host/proc',
                            '--path.rootfs=/rootfs',
                            '--path.sysfs=/host/sys',
                            '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
                        ],
                        'restart': 'unless-stopped'
                    },
                    'redis-exporter': {
                        'image': 'oliver006/redis_exporter:latest',
                        'container_name': 'redis-exporter',
                        'ports': ['9121:9121'],
                        'environment': {
                            'REDIS_ADDR': 'redis://localhost:6379'
                        },
                        'restart': 'unless-stopped'
                    },
                    'blackbox-exporter': {
                        'image': 'prom/blackbox-exporter:latest',
                        'container_name': 'blackbox-exporter',
                        'ports': ['9115:9115'],
                        'volumes': [
                            './monitoring/blackbox.yml:/etc/blackbox_exporter/config.yml'
                        ],
                        'restart': 'unless-stopped'
                    }
                },
                'volumes': {
                    'prometheus_data': {},
                    'grafana_data': {}
                },
                'networks': {
                    'monitoring': {
                        'driver': 'bridge'
                    }
                }
            }
            
            compose_file = self.project_root / "docker-compose.monitoring.yml"
            with open(compose_file, 'w') as f:
                yaml.dump(docker_compose, f, default_flow_style=False)
            
            print(f"✓ Docker Compose monitoring configuration created: {compose_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Docker Compose config: {e}")
            return False
    
    def create_blackbox_config(self) -> bool:
        """Create Blackbox exporter configuration for HTTP monitoring."""
        try:
            blackbox_config = {
                'modules': {
                    'http_2xx': {
                        'prober': 'http',
                        'timeout': '5s',
                        'http': {
                            'valid_http_versions': ['HTTP/1.1', 'HTTP/2.0'],
                            'valid_status_codes': [],
                            'method': 'GET',
                            'headers': {
                                'Host': 'localhost',
                                'Accept-Language': 'en-US'
                            },
                            'no_follow_redirects': False,
                            'fail_if_ssl': False,
                            'fail_if_not_ssl': False,
                            'tls_config': {
                                'insecure_skip_verify': False
                            },
                            'preferred_ip_protocol': 'ip4'
                        }
                    },
                    'http_post_2xx': {
                        'prober': 'http',
                        'timeout': '5s',
                        'http': {
                            'method': 'POST',
                            'headers': {
                                'Content-Type': 'application/json'
                            },
                            'body': '{}'
                        }
                    },
                    'tcp_connect': {
                        'prober': 'tcp',
                        'timeout': '5s'
                    },
                    'icmp': {
                        'prober': 'icmp',
                        'timeout': '5s',
                        'icmp': {
                            'preferred_ip_protocol': 'ip4'
                        }
                    }
                }
            }
            
            config_file = self.monitoring_dir / "blackbox.yml"
            with open(config_file, 'w') as f:
                yaml.dump(blackbox_config, f, default_flow_style=False)
            
            print(f"✓ Blackbox exporter configuration created: {config_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Blackbox config: {e}")
            return False
    
    def create_systemd_services(self) -> bool:
        """Create systemd service files for monitoring components."""
        try:
            systemd_dir = self.project_root / "systemd"
            systemd_dir.mkdir(exist_ok=True)
            
            # Prometheus service
            prometheus_service = """
[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecReload=/bin/kill -HUP $MAINPID
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.external-url=

SyslogIdentifier=prometheus
Restart=always

[Install]
WantedBy=multi-user.target
"""
            
            # Alertmanager service
            alertmanager_service = """
[Unit]
Description=Alertmanager
Documentation=https://prometheus.io/docs/alerting/alertmanager/
After=network-online.target

[Service]
Type=simple
User=alertmanager
Group=alertmanager
ExecStart=/usr/local/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager/

Restart=always

[Install]
WantedBy=multi-user.target
"""
            
            # Node exporter service
            node_exporter_service = """
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=node_exporter
Group=node_exporter
ExecStart=/usr/local/bin/node_exporter

SyslogIdentifier=node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
"""
            
            # Write service files
            services = {
                'prometheus.service': prometheus_service,
                'alertmanager.service': alertmanager_service,
                'node_exporter.service': node_exporter_service
            }
            
            for filename, content in services.items():
                with open(systemd_dir / filename, 'w') as f:
                    f.write(content)
            
            print(f"✓ Systemd service files created in: {systemd_dir}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating systemd services: {e}")
            return False
    
    def create_monitoring_script(self) -> bool:
        """Create monitoring deployment and management script."""
        try:
            script_content = '''
#!/bin/bash

# AI Trading Sentinel - Monitoring Setup Script

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$PROJECT_ROOT/monitoring"
CONFIG_DIR="$PROJECT_ROOT/config"

echo "🚀 Setting up AI Trading Sentinel Monitoring Infrastructure..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Prometheus
install_prometheus() {
    echo "📊 Installing Prometheus..."
    
    if command_exists prometheus; then
        echo "✓ Prometheus already installed"
        return 0
    fi
    
    PROM_VERSION="2.45.0"
    cd /tmp
    wget https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz
    tar xvf prometheus-${PROM_VERSION}.linux-amd64.tar.gz
    
    sudo cp prometheus-${PROM_VERSION}.linux-amd64/prometheus /usr/local/bin/
    sudo cp prometheus-${PROM_VERSION}.linux-amd64/promtool /usr/local/bin/
    
    sudo useradd --no-create-home --shell /bin/false prometheus || true
    sudo mkdir -p /etc/prometheus /var/lib/prometheus
    sudo chown prometheus:prometheus /etc/prometheus /var/lib/prometheus
    
    echo "✓ Prometheus installed"
}

# Function to install Alertmanager
install_alertmanager() {
    echo "🚨 Installing Alertmanager..."
    
    if command_exists alertmanager; then
        echo "✓ Alertmanager already installed"
        return 0
    fi
    
    AM_VERSION="0.25.0"
    cd /tmp
    wget https://github.com/prometheus/alertmanager/releases/download/v${AM_VERSION}/alertmanager-${AM_VERSION}.linux-amd64.tar.gz
    tar xvf alertmanager-${AM_VERSION}.linux-amd64.tar.gz
    
    sudo cp alertmanager-${AM_VERSION}.linux-amd64/alertmanager /usr/local/bin/
    sudo cp alertmanager-${AM_VERSION}.linux-amd64/amtool /usr/local/bin/
    
    sudo useradd --no-create-home --shell /bin/false alertmanager || true
    sudo mkdir -p /etc/alertmanager /var/lib/alertmanager
    sudo chown alertmanager:alertmanager /etc/alertmanager /var/lib/alertmanager
    
    echo "✓ Alertmanager installed"
}

# Function to install Node Exporter
install_node_exporter() {
    echo "📈 Installing Node Exporter..."
    
    if command_exists node_exporter; then
        echo "✓ Node Exporter already installed"
        return 0
    fi
    
    NE_VERSION="1.6.0"
    cd /tmp
    wget https://github.com/prometheus/node_exporter/releases/download/v${NE_VERSION}/node_exporter-${NE_VERSION}.linux-amd64.tar.gz
    tar xvf node_exporter-${NE_VERSION}.linux-amd64.tar.gz
    
    sudo cp node_exporter-${NE_VERSION}.linux-amd64/node_exporter /usr/local/bin/
    
    sudo useradd --no-create-home --shell /bin/false node_exporter || true
    
    echo "✓ Node Exporter installed"
}

# Function to install Grafana
install_grafana() {
    echo "📊 Installing Grafana..."
    
    if command_exists grafana-server; then
        echo "✓ Grafana already installed"
        return 0
    fi
    
    # Add Grafana repository
    sudo apt-get install -y software-properties-common
    wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
    
    sudo apt-get update
    sudo apt-get install -y grafana
    
    echo "✓ Grafana installed"
}

# Function to setup configurations
setup_configurations() {
    echo "⚙️ Setting up configurations..."
    
    # Copy Prometheus config
    if [ -f "$CONFIG_DIR/prometheus.yml" ]; then
        sudo cp "$CONFIG_DIR/prometheus.yml" /etc/prometheus/
        sudo chown prometheus:prometheus /etc/prometheus/prometheus.yml
    fi
    
    # Copy Alertmanager config
    if [ -f "$CONFIG_DIR/alertmanager.yml" ]; then
        sudo cp "$CONFIG_DIR/alertmanager.yml" /etc/alertmanager/
        sudo chown alertmanager:alertmanager /etc/alertmanager/alertmanager.yml
    fi
    
    # Copy alert rules
    if [ -d "$MONITORING_DIR/rules" ]; then
        sudo cp -r "$MONITORING_DIR/rules" /etc/prometheus/
        sudo chown -R prometheus:prometheus /etc/prometheus/rules
    fi
    
    # Copy Grafana dashboards
    if [ -d "$MONITORING_DIR/grafana" ]; then
        sudo cp -r "$MONITORING_DIR/grafana/provisioning" /etc/grafana/
        sudo cp -r "$MONITORING_DIR/grafana/dashboards" /var/lib/grafana/
        sudo chown -R grafana:grafana /etc/grafana/provisioning /var/lib/grafana/dashboards
    fi
    
    echo "✓ Configurations setup complete"
}

# Function to setup systemd services
setup_services() {
    echo "🔧 Setting up systemd services..."
    
    # Copy service files
    if [ -d "$PROJECT_ROOT/systemd" ]; then
        sudo cp "$PROJECT_ROOT/systemd/"*.service /etc/systemd/system/
        sudo systemctl daemon-reload
    fi
    
    # Enable and start services
    for service in prometheus alertmanager node_exporter grafana-server; do
        sudo systemctl enable $service
        sudo systemctl start $service
        echo "✓ $service enabled and started"
    done
    
    echo "✓ All services setup complete"
}

# Function to verify installation
verify_installation() {
    echo "🔍 Verifying installation..."
    
    services=("prometheus" "alertmanager" "node_exporter" "grafana-server")
    ports=("9090" "9093" "9100" "3000")
    
    for i in "${!services[@]}"; do
        service="${services[$i]}"
        port="${ports[$i]}"
        
        if systemctl is-active --quiet $service; then
            echo "✓ $service is running"
            
            if nc -z localhost $port; then
                echo "✓ $service is accessible on port $port"
            else
                echo "⚠️ $service is running but port $port is not accessible"
            fi
        else
            echo "✗ $service is not running"
        fi
    done
    
    echo "\n📊 Access URLs:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Alertmanager: http://localhost:9093"
    echo "  Grafana: http://localhost:3000 (admin/admin)"
    echo "  Node Exporter: http://localhost:9100"
}

# Main installation flow
main() {
    echo "Starting monitoring infrastructure setup..."
    
    # Check if running as root for system installations
    if [[ $EUID -eq 0 ]]; then
        echo "⚠️ Running as root. This is required for system-wide installation."
    else
        echo "⚠️ Not running as root. Some operations may require sudo."
    fi
    
    # Install components
    install_prometheus
    install_alertmanager
    install_node_exporter
    install_grafana
    
    # Setup configurations
    setup_configurations
    
    # Setup services
    setup_services
    
    # Verify installation
    verify_installation
    
    echo "\n🎉 Monitoring infrastructure setup complete!"
    echo "\n📋 Next steps:"
    echo "  1. Configure Slack webhook URL in alertmanager.yml"
    echo "  2. Update Prometheus targets for your environment"
    echo "  3. Import additional Grafana dashboards as needed"
    echo "  4. Test alerting by triggering a test alert"
}

# Run main function
main "$@"
'''
            
            script_file = self.scripts_dir / "setup_monitoring.sh"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(script_file, 0o755)
            
            print(f"✓ Monitoring setup script created: {script_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating monitoring script: {e}")
            return False
    
    def setup_monitoring_alerts(self) -> bool:
        """Setup complete monitoring and alerting infrastructure."""
        print("🚀 Setting up AI Trading Sentinel Monitoring & Alerting...")
        
        success = True
        
        # Setup all components
        components = [
            ("Prometheus Configuration", self.setup_prometheus_config),
            ("Alerting Rules", self.setup_alerting_rules),
            ("Alertmanager Configuration", self.setup_alertmanager_config),
            ("Grafana Dashboards", self.setup_grafana_dashboards),
            ("Grafana Provisioning", self.setup_grafana_provisioning),
            ("Docker Compose Monitoring", self.create_docker_compose_monitoring),
            ("Blackbox Configuration", self.create_blackbox_config),
            ("Systemd Services", self.create_systemd_services),
            ("Monitoring Script", self.create_monitoring_script)
        ]
        
        for name, func in components:
            print(f"\n📋 Setting up {name}...")
            if not func():
                print(f"❌ Failed to setup {name}")
                success = False
            else:
                print(f"✅ {name} setup complete")
        
        if success:
            print("\n🎉 Monitoring & Alerting setup completed successfully!")
            print("\n📋 Next Steps:")
            print("  1. Run: chmod +x scripts/setup_monitoring.sh")
            print("  2. Run: sudo ./scripts/setup_monitoring.sh")
            print("  3. Configure Slack webhook in config/alertmanager.yml")
            print("  4. Update environment variables with monitoring URLs")
            print("  5. Test alerts: curl -X POST http://localhost:9093/api/v1/alerts")
            
            print("\n🔗 Access URLs (after deployment):")
            print("  📊 Prometheus: http://your-server:9090")
            print("  🚨 Alertmanager: http://your-server:9093")
            print("  📈 Grafana: http://your-server:3001 (admin/admin)")
            print("  📡 Node Exporter: http://your-server:9100")
        else:
            print("\n❌ Some components failed to setup. Check the logs above.")
        
        return success

def main():
    """Main function for monitoring alerts setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AI Trading Sentinel Monitoring & Alerting")
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--component', choices=[
        'prometheus', 'alertmanager', 'grafana', 'docker', 'systemd', 'all'
    ], default='all', help='Component to setup')
    
    args = parser.parse_args()
    
    setup = MonitoringAlertsSetup(args.project_root)
    
    if args.component == 'all':
        success = setup.setup_monitoring_alerts()
    elif args.component == 'prometheus':
        success = setup.setup_prometheus_config() and setup.setup_alerting_rules()
    elif args.component == 'alertmanager':
        success = setup.setup_alertmanager_config()
    elif args.component == 'grafana':
        success = setup.setup_grafana_dashboards() and setup.setup_grafana_provisioning()
    elif args.component == 'docker':
        success = setup.create_docker_compose_monitoring()
    elif args.component == 'systemd':
        success = setup.create_systemd_services()
    else:
        success = False
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())