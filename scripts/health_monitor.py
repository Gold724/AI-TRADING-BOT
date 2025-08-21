#!/usr/bin/env python3
"""
AI Trading Sentinel - Health Monitor
Continuous health monitoring and alerting system for production deployment.
"""

import os
import sys
import time
import json
import yaml
import psutil
import redis
import requests
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class HealthStatus:
    """Health status data structure."""
    service: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = None
    response_time: float = None

@dataclass
class SystemMetrics:
    """System metrics data structure."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    load_average: Tuple[float, float, float]
    uptime: float
    timestamp: datetime

class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "monitoring_config.yml"
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components
        self.redis_client = None
        self.health_history = []
        self.alert_cooldowns = {}
        
        # Service endpoints
        self.endpoints = {
            'trading-api': 'http://localhost:5000/health',
            'frontend': 'http://localhost:3000',
            'prometheus': 'http://localhost:9090/-/healthy',
            'grafana': 'http://localhost:3001/api/health',
            'alertmanager': 'http://localhost:9093/-/healthy'
        }
        
        # System thresholds
        self.thresholds = self.config.get('performance', {}).get('thresholds', {
            'cpu_warning': 80,
            'cpu_critical': 95,
            'memory_warning': 85,
            'memory_critical': 95,
            'disk_warning': 85,
            'disk_critical': 95,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0
        })
        
        self.logger.info("Health Monitor initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / "health_monitor.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('HealthMonitor')
    
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
        """Get default configuration."""
        return {
            'health_checks': {
                'enabled': True,
                'interval': 30,
                'timeout': 10
            },
            'notifications': {
                'slack': {
                    'enabled': True,
                    'webhook_url': os.getenv('SLACK_WEBHOOK_URL')
                }
            },
            'performance': {
                'thresholds': {
                    'cpu_warning': 80,
                    'cpu_critical': 95,
                    'memory_warning': 85,
                    'memory_critical': 95,
                    'disk_warning': 85,
                    'disk_critical': 95
                }
            }
        }
    
    def connect_redis(self) -> bool:
        """Connect to Redis database."""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            return False
    
    def check_service_health(self, service: str, url: str, timeout: int = 10) -> HealthStatus:
        """Check health of a specific service."""
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = 'healthy'
                message = f"Service responding normally (HTTP {response.status_code})"
                
                # Check response time thresholds
                if response_time > self.thresholds['response_time_critical']:
                    status = 'critical'
                    message = f"Service responding but very slow ({response_time:.2f}s)"
                elif response_time > self.thresholds['response_time_warning']:
                    status = 'warning'
                    message = f"Service responding but slow ({response_time:.2f}s)"
            else:
                status = 'warning'
                message = f"Service returned HTTP {response.status_code}"
                response_time = time.time() - start_time
            
            return HealthStatus(
                service=service,
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time=response_time
            )
            
        except requests.exceptions.Timeout:
            return HealthStatus(
                service=service,
                status='critical',
                message=f"Service timeout after {timeout}s",
                timestamp=datetime.now(),
                response_time=timeout
            )
        except requests.exceptions.ConnectionError:
            return HealthStatus(
                service=service,
                status='critical',
                message="Service not reachable",
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthStatus(
                service=service,
                status='unknown',
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_redis_health(self) -> HealthStatus:
        """Check Redis database health."""
        try:
            if not self.redis_client:
                if not self.connect_redis():
                    return HealthStatus(
                        service='redis',
                        status='critical',
                        message='Cannot connect to Redis',
                        timestamp=datetime.now()
                    )
            
            start_time = time.time()
            info = self.redis_client.info()
            response_time = time.time() - start_time
            
            # Check Redis metrics
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            connected_clients = info.get('connected_clients', 0)
            
            metrics = {
                'memory_usage': memory_usage,
                'max_memory': max_memory,
                'connected_clients': connected_clients,
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
            
            # Determine status
            status = 'healthy'
            message = 'Redis is healthy'
            
            if max_memory > 0 and (memory_usage / max_memory) > 0.9:
                status = 'warning'
                message = f'Redis memory usage high: {(memory_usage/max_memory)*100:.1f}%'
            
            if connected_clients > 100:
                status = 'warning'
                message = f'High number of Redis connections: {connected_clients}'
            
            return HealthStatus(
                service='redis',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics=metrics,
                response_time=response_time
            )
            
        except Exception as e:
            return HealthStatus(
                service='redis',
                status='critical',
                message=f'Redis error: {str(e)}',
                timestamp=datetime.now()
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage (root partition)
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Load average
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            # System uptime
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                load_average=load_avg,
                uptime=uptime,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                network_io={},
                load_average=(0, 0, 0),
                uptime=0,
                timestamp=datetime.now()
            )
    
    def check_system_health(self) -> List[HealthStatus]:
        """Check system resource health."""
        metrics = self.get_system_metrics()
        health_checks = []
        
        # CPU check
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            status = 'critical'
            message = f'Critical CPU usage: {metrics.cpu_percent:.1f}%'
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            status = 'warning'
            message = f'High CPU usage: {metrics.cpu_percent:.1f}%'
        else:
            status = 'healthy'
            message = f'CPU usage normal: {metrics.cpu_percent:.1f}%'
        
        health_checks.append(HealthStatus(
            service='system-cpu',
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={'cpu_percent': metrics.cpu_percent}
        ))
        
        # Memory check
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            status = 'critical'
            message = f'Critical memory usage: {metrics.memory_percent:.1f}%'
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            status = 'warning'
            message = f'High memory usage: {metrics.memory_percent:.1f}%'
        else:
            status = 'healthy'
            message = f'Memory usage normal: {metrics.memory_percent:.1f}%'
        
        health_checks.append(HealthStatus(
            service='system-memory',
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={'memory_percent': metrics.memory_percent}
        ))
        
        # Disk check
        if metrics.disk_percent >= self.thresholds['disk_critical']:
            status = 'critical'
            message = f'Critical disk usage: {metrics.disk_percent:.1f}%'
        elif metrics.disk_percent >= self.thresholds['disk_warning']:
            status = 'warning'
            message = f'High disk usage: {metrics.disk_percent:.1f}%'
        else:
            status = 'healthy'
            message = f'Disk usage normal: {metrics.disk_percent:.1f}%'
        
        health_checks.append(HealthStatus(
            service='system-disk',
            status=status,
            message=message,
            timestamp=datetime.now(),
            metrics={'disk_percent': metrics.disk_percent}
        ))
        
        return health_checks
    
    def check_process_health(self) -> List[HealthStatus]:
        """Check health of critical processes."""
        critical_processes = [
            'python',  # Trading bot/API processes
            'redis-server',
            'nginx',
            'prometheus',
            'grafana-server'
        ]
        
        health_checks = []
        
        for process_name in critical_processes:
            try:
                processes = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']) 
                           if process_name in p.info['name']]
                
                if processes:
                    total_cpu = sum(p.info['cpu_percent'] or 0 for p in processes)
                    total_memory = sum(p.info['memory_percent'] or 0 for p in processes)
                    
                    status = 'healthy'
                    message = f'{process_name} running ({len(processes)} processes)'
                    
                    if total_cpu > 80:
                        status = 'warning'
                        message = f'{process_name} high CPU usage: {total_cpu:.1f}%'
                    
                    if total_memory > 80:
                        status = 'warning'
                        message = f'{process_name} high memory usage: {total_memory:.1f}%'
                    
                    health_checks.append(HealthStatus(
                        service=f'process-{process_name}',
                        status=status,
                        message=message,
                        timestamp=datetime.now(),
                        metrics={
                            'process_count': len(processes),
                            'cpu_percent': total_cpu,
                            'memory_percent': total_memory
                        }
                    ))
                else:
                    health_checks.append(HealthStatus(
                        service=f'process-{process_name}',
                        status='critical',
                        message=f'{process_name} not running',
                        timestamp=datetime.now()
                    ))
                    
            except Exception as e:
                health_checks.append(HealthStatus(
                    service=f'process-{process_name}',
                    status='unknown',
                    message=f'Error checking {process_name}: {str(e)}',
                    timestamp=datetime.now()
                ))
        
        return health_checks
    
    def check_log_errors(self) -> List[HealthStatus]:
        """Check for recent errors in log files."""
        log_files = {
            'api': self.logs_dir / 'api.log',
            'bot': self.logs_dir / 'bot.log',
            'monitor': self.logs_dir / 'health_monitor.log'
        }
        
        health_checks = []
        error_patterns = ['ERROR', 'CRITICAL', 'FATAL', 'EXCEPTION']
        
        for log_name, log_file in log_files.items():
            try:
                if not log_file.exists():
                    continue
                
                # Check last 100 lines for errors in the last 5 minutes
                cutoff_time = datetime.now() - timedelta(minutes=5)
                error_count = 0
                
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    
                    for line in lines:
                        # Simple timestamp parsing (adjust based on your log format)
                        if any(pattern in line.upper() for pattern in error_patterns):
                            error_count += 1
                
                if error_count > 10:
                    status = 'critical'
                    message = f'High error rate in {log_name} logs: {error_count} errors'
                elif error_count > 5:
                    status = 'warning'
                    message = f'Elevated error rate in {log_name} logs: {error_count} errors'
                else:
                    status = 'healthy'
                    message = f'{log_name} logs normal: {error_count} errors'
                
                health_checks.append(HealthStatus(
                    service=f'logs-{log_name}',
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    metrics={'error_count': error_count}
                ))
                
            except Exception as e:
                health_checks.append(HealthStatus(
                    service=f'logs-{log_name}',
                    status='unknown',
                    message=f'Error checking logs: {str(e)}',
                    timestamp=datetime.now()
                ))
        
        return health_checks
    
    def run_comprehensive_health_check(self) -> List[HealthStatus]:
        """Run comprehensive health check of all components."""
        all_health_checks = []
        
        self.logger.info("Starting comprehensive health check...")
        
        # Check services in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Service health checks
            service_futures = {
                executor.submit(self.check_service_health, service, url): service 
                for service, url in self.endpoints.items()
            }
            
            # Redis health check
            redis_future = executor.submit(self.check_redis_health)
            
            # System health checks
            system_future = executor.submit(self.check_system_health)
            
            # Process health checks
            process_future = executor.submit(self.check_process_health)
            
            # Log error checks
            log_future = executor.submit(self.check_log_errors)
            
            # Collect service results
            for future in as_completed(service_futures):
                try:
                    result = future.result(timeout=30)
                    all_health_checks.append(result)
                except Exception as e:
                    service = service_futures[future]
                    self.logger.error(f"Error checking {service}: {e}")
                    all_health_checks.append(HealthStatus(
                        service=service,
                        status='unknown',
                        message=f'Health check failed: {str(e)}',
                        timestamp=datetime.now()
                    ))
            
            # Collect other results
            try:
                all_health_checks.append(redis_future.result(timeout=30))
            except Exception as e:
                self.logger.error(f"Redis health check failed: {e}")
            
            try:
                all_health_checks.extend(system_future.result(timeout=30))
            except Exception as e:
                self.logger.error(f"System health check failed: {e}")
            
            try:
                all_health_checks.extend(process_future.result(timeout=30))
            except Exception as e:
                self.logger.error(f"Process health check failed: {e}")
            
            try:
                all_health_checks.extend(log_future.result(timeout=30))
            except Exception as e:
                self.logger.error(f"Log health check failed: {e}")
        
        self.logger.info(f"Health check completed. {len(all_health_checks)} checks performed.")
        return all_health_checks
    
    def send_slack_notification(self, health_status: HealthStatus) -> bool:
        """Send Slack notification for health status."""
        try:
            slack_config = self.config.get('notifications', {}).get('slack', {})
            webhook_url = slack_config.get('webhook_url')
            
            if not webhook_url:
                self.logger.warning("Slack webhook URL not configured")
                return False
            
            # Determine color and emoji based on status
            color_map = {
                'healthy': 'good',
                'warning': 'warning',
                'critical': 'danger',
                'unknown': '#808080'
            }
            
            emoji_map = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '🚨',
                'unknown': '❓'
            }
            
            color = color_map.get(health_status.status, '#808080')
            emoji = emoji_map.get(health_status.status, '❓')
            
            # Build message
            message = {
                'username': 'AI Trading Sentinel Monitor',
                'icon_emoji': ':robot_face:',
                'attachments': [{
                    'color': color,
                    'title': f'{emoji} {health_status.service.upper()} - {health_status.status.upper()}',
                    'text': health_status.message,
                    'fields': [
                        {
                            'title': 'Service',
                            'value': health_status.service,
                            'short': True
                        },
                        {
                            'title': 'Status',
                            'value': health_status.status,
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': health_status.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            'short': True
                        }
                    ],
                    'footer': 'AI Trading Sentinel Health Monitor',
                    'ts': int(health_status.timestamp.timestamp())
                }]
            }
            
            # Add metrics if available
            if health_status.metrics:
                metrics_text = '\n'.join([f'{k}: {v}' for k, v in health_status.metrics.items()])
                message['attachments'][0]['fields'].append({
                    'title': 'Metrics',
                    'value': f'```{metrics_text}```',
                    'short': False
                })
            
            # Add response time if available
            if health_status.response_time:
                message['attachments'][0]['fields'].append({
                    'title': 'Response Time',
                    'value': f'{health_status.response_time:.2f}s',
                    'short': True
                })
            
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack notification sent for {health_status.service}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def should_send_alert(self, health_status: HealthStatus) -> bool:
        """Determine if an alert should be sent based on cooldown and severity."""
        service = health_status.service
        status = health_status.status
        
        # Only send alerts for warning, critical, or unknown status
        if status == 'healthy':
            # Clear cooldown for healthy services
            if service in self.alert_cooldowns:
                del self.alert_cooldowns[service]
            return False
        
        # Check cooldown
        now = datetime.now()
        if service in self.alert_cooldowns:
            last_alert_time, last_status = self.alert_cooldowns[service]
            
            # Different cooldown periods based on severity
            cooldown_minutes = {
                'critical': 5,   # 5 minutes for critical
                'warning': 15,   # 15 minutes for warning
                'unknown': 10    # 10 minutes for unknown
            }
            
            cooldown_period = timedelta(minutes=cooldown_minutes.get(status, 15))
            
            # Send alert if status changed or cooldown expired
            if last_status != status or (now - last_alert_time) > cooldown_period:
                self.alert_cooldowns[service] = (now, status)
                return True
            else:
                return False
        else:
            # First alert for this service
            self.alert_cooldowns[service] = (now, status)
            return True
    
    def process_health_results(self, health_results: List[HealthStatus]):
        """Process health check results and send alerts if needed."""
        # Store results in history
        self.health_history.extend(health_results)
        
        # Keep only last 1000 results
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]
        
        # Count status types
        status_counts = {'healthy': 0, 'warning': 0, 'critical': 0, 'unknown': 0}
        for result in health_results:
            status_counts[result.status] += 1
        
        self.logger.info(
            f"Health check summary: "
            f"Healthy: {status_counts['healthy']}, "
            f"Warning: {status_counts['warning']}, "
            f"Critical: {status_counts['critical']}, "
            f"Unknown: {status_counts['unknown']}"
        )
        
        # Send alerts for non-healthy services
        for result in health_results:
            if self.should_send_alert(result):
                self.logger.info(f"Sending alert for {result.service}: {result.status}")
                self.send_slack_notification(result)
        
        # Save results to file
        self.save_health_results(health_results)
    
    def save_health_results(self, health_results: List[HealthStatus]):
        """Save health results to JSON file."""
        try:
            results_file = self.logs_dir / "health_results.json"
            
            # Convert to serializable format
            serializable_results = []
            for result in health_results:
                result_dict = asdict(result)
                result_dict['timestamp'] = result.timestamp.isoformat()
                serializable_results.append(result_dict)
            
            # Load existing results
            existing_results = []
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        existing_results = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load existing results: {e}")
            
            # Append new results
            all_results = existing_results + serializable_results
            
            # Keep only last 10000 results
            if len(all_results) > 10000:
                all_results = all_results[-10000:]
            
            # Save results
            with open(results_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            self.logger.debug(f"Health results saved to {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving health results: {e}")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        if not self.health_history:
            return {'error': 'No health data available'}
        
        # Get recent results (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_results = [r for r in self.health_history if r.timestamp > cutoff_time]
        
        if not recent_results:
            return {'error': 'No recent health data available'}
        
        # Group by service
        services = {}
        for result in recent_results:
            if result.service not in services:
                services[result.service] = []
            services[result.service].append(result)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_services': len(services),
                'healthy_services': 0,
                'warning_services': 0,
                'critical_services': 0,
                'unknown_services': 0
            },
            'services': {}
        }
        
        for service, results in services.items():
            latest_result = max(results, key=lambda x: x.timestamp)
            
            # Count status in summary
            report['summary'][f'{latest_result.status}_services'] += 1
            
            # Service details
            report['services'][service] = {
                'status': latest_result.status,
                'message': latest_result.message,
                'last_check': latest_result.timestamp.isoformat(),
                'response_time': latest_result.response_time,
                'metrics': latest_result.metrics,
                'check_count': len(results)
            }
        
        return report
    
    def run_monitoring_loop(self, interval: int = 30):
        """Run continuous monitoring loop."""
        self.logger.info(f"Starting health monitoring loop (interval: {interval}s)")
        
        try:
            while True:
                start_time = time.time()
                
                # Run health checks
                health_results = self.run_comprehensive_health_check()
                
                # Process results
                self.process_health_results(health_results)
                
                # Calculate sleep time
                elapsed_time = time.time() - start_time
                sleep_time = max(0, interval - elapsed_time)
                
                self.logger.debug(f"Health check completed in {elapsed_time:.2f}s, sleeping for {sleep_time:.2f}s")
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            self.logger.info("Health monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Health monitoring loop error: {e}")
            raise

def main():
    """Main function for health monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Health Monitor")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--interval', type=int, default=30, help='Monitoring interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run health check once and exit')
    parser.add_argument('--report', action='store_true', help='Generate health report and exit')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = HealthMonitor(args.config)
    
    if args.report:
        # Generate and print report
        report = monitor.generate_health_report()
        print(json.dumps(report, indent=2))
        return 0
    
    if args.once:
        # Run single health check
        health_results = monitor.run_comprehensive_health_check()
        monitor.process_health_results(health_results)
        
        # Print summary
        status_counts = {'healthy': 0, 'warning': 0, 'critical': 0, 'unknown': 0}
        for result in health_results:
            status_counts[result.status] += 1
        
        print(f"\nHealth Check Summary:")
        print(f"  Healthy: {status_counts['healthy']}")
        print(f"  Warning: {status_counts['warning']}")
        print(f"  Critical: {status_counts['critical']}")
        print(f"  Unknown: {status_counts['unknown']}")
        
        return 0 if status_counts['critical'] == 0 else 1
    
    # Run continuous monitoring
    monitor.run_monitoring_loop(args.interval)
    return 0

if __name__ == '__main__':
    sys.exit(main())