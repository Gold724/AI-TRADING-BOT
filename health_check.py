#!/usr/bin/env python3
"""
Health Check Script for TradeBot Sentinel
Comprehensive monitoring for cloud deployment
"""

import os
import sys
import json
import time
import psutil
import logging
import asyncio
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import our modules
try:
    from browser_config import CloudBrowserConfig
    from tradebot_sentinel import TradeBotSentinel
except ImportError as e:
    logging.warning(f"Could not import modules: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthCheckError(Exception):
    """Custom exception for health check errors"""
    pass

class TradeBotHealthChecker:
    """
    Comprehensive health checker for TradeBot Sentinel
    Monitors system resources, browser health, and trading platform connectivity
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or '.env'
        self.start_time = datetime.now()
        self.health_data = {}
        
        # Load environment variables
        self._load_environment()
        
        # Health check configuration
        self.checks = {
            'system': self._check_system_resources,
            'browser': self._check_browser_health,
            'network': self._check_network_connectivity,
            'trading_platform': self._check_trading_platform,
            'dependencies': self._check_dependencies,
            'storage': self._check_storage,
            'processes': self._check_processes,
            'environment': self._check_environment
        }
        
        logger.info("Health checker initialized")
    
    def _load_environment(self):
        """
        Load environment variables from .env file
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip().strip('"\'')
                logger.info(f"Environment loaded from {self.config_path}")
            except Exception as e:
                logger.warning(f"Could not load environment file: {e}")
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """
        Check system resource usage
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Load average (Unix-like systems)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                pass
            
            # Boot time and uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            system_health = {
                'status': 'healthy',
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': load_avg
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_percent': memory.percent,
                    'swap_used_percent': swap.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'used_percent': round((disk.used / disk.total) * 100, 2)
                },
                'uptime': {
                    'boot_time': boot_time.isoformat(),
                    'uptime_hours': round(uptime.total_seconds() / 3600, 2)
                }
            }
            
            # Determine health status
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 85:
                warnings.append(f"High memory usage: {memory.percent}%")
            if disk.used / disk.total > 0.9:
                warnings.append(f"Low disk space: {system_health['disk']['used_percent']}% used")
            
            if warnings:
                system_health['status'] = 'warning'
                system_health['warnings'] = warnings
            
            return system_health
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_browser_health(self) -> Dict[str, Any]:
        """
        Check browser and Playwright health
        """
        try:
            # Create browser config
            browser_config = CloudBrowserConfig(headless=True)
            health = browser_config.health_check()
            
            # Test Playwright installation
            playwright_health = self._test_playwright()
            health.update(playwright_health)
            
            # Determine overall status
            if health.get('chrome_available') and health.get('playwright_installed'):
                health['status'] = 'healthy'
            else:
                health['status'] = 'error'
                health['issues'] = []
                if not health.get('chrome_available'):
                    health['issues'].append('Chrome/Chromium not found')
                if not health.get('playwright_installed'):
                    health['issues'].append('Playwright not properly installed')
            
            return health
            
        except Exception as e:
            logger.error(f"Browser health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _test_playwright(self) -> Dict[str, Any]:
        """
        Test Playwright installation and browser availability
        """
        try:
            # Check if playwright is installed
            import playwright
            playwright_version = playwright.__version__
            
            # Test browser installation
            result = subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', '--dry-run', 'chromium'],
                capture_output=True, text=True, timeout=10
            )
            
            return {
                'playwright_installed': True,
                'playwright_version': playwright_version,
                'browser_install_status': 'ok' if result.returncode == 0 else 'needs_install'
            }
            
        except ImportError:
            return {
                'playwright_installed': False,
                'error': 'Playwright not installed'
            }
        except Exception as e:
            return {
                'playwright_installed': False,
                'error': str(e)
            }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """
        Check network connectivity to essential services
        """
        test_urls = [
            ('google.com', 'https://www.google.com'),
            ('bulenox.com', 'https://bulenox.com'),
            ('github.com', 'https://github.com'),
            ('docker.com', 'https://hub.docker.com')
        ]
        
        connectivity_results = {}
        total_tests = len(test_urls)
        successful_tests = 0
        
        for name, url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10, allow_redirects=True)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                connectivity_results[name] = {
                    'status': 'ok',
                    'status_code': response.status_code,
                    'response_time_ms': response_time
                }
                
                if response.status_code == 200:
                    successful_tests += 1
                    
            except requests.exceptions.RequestException as e:
                connectivity_results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
            except Exception as e:
                connectivity_results[name] = {
                    'status': 'error',
                    'error': f"Unexpected error: {e}"
                }
        
        # Overall network health
        success_rate = successful_tests / total_tests
        network_health = {
            'status': 'healthy' if success_rate >= 0.75 else 'warning' if success_rate >= 0.5 else 'error',
            'success_rate': round(success_rate * 100, 2),
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'results': connectivity_results
        }
        
        return network_health
    
    def _check_trading_platform(self) -> Dict[str, Any]:
        """
        Check trading platform connectivity and authentication
        """
        try:
            # Check if credentials are available
            username = os.getenv('BULENOX_USERNAME')
            password = os.getenv('BULENOX_PASSWORD')
            
            if not username or not password:
                return {
                    'status': 'warning',
                    'message': 'Trading credentials not configured',
                    'credentials_available': False
                }
            
            # Test platform connectivity
            platform_url = 'https://bulenox.com'
            try:
                response = requests.get(platform_url, timeout=15)
                platform_accessible = response.status_code == 200
            except Exception as e:
                platform_accessible = False
                platform_error = str(e)
            
            trading_health = {
                'status': 'healthy' if platform_accessible else 'error',
                'credentials_available': True,
                'platform_accessible': platform_accessible,
                'platform_url': platform_url
            }
            
            if not platform_accessible:
                trading_health['platform_error'] = platform_error
            
            return trading_health
            
        except Exception as e:
            logger.error(f"Trading platform check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """
        Check required Python dependencies
        """
        required_packages = [
            'playwright',
            'requests',
            'psutil',
            'schedule',
            'python-telegram-bot',
            'curlconverter'
        ]
        
        dependency_status = {}
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                dependency_status[package] = 'installed'
            except ImportError:
                dependency_status[package] = 'missing'
                missing_packages.append(package)
        
        dependencies_health = {
            'status': 'healthy' if not missing_packages else 'error',
            'packages': dependency_status,
            'missing_count': len(missing_packages)
        }
        
        if missing_packages:
            dependencies_health['missing_packages'] = missing_packages
        
        return dependencies_health
    
    def _check_storage(self) -> Dict[str, Any]:
        """
        Check storage and file system health
        """
        try:
            current_dir = Path.cwd()
            
            # Check required directories
            required_dirs = ['logs', 'screenshots', 'data']
            dir_status = {}
            
            for dir_name in required_dirs:
                dir_path = current_dir / dir_name
                dir_status[dir_name] = {
                    'exists': dir_path.exists(),
                    'writable': dir_path.exists() and os.access(dir_path, os.W_OK)
                }
            
            # Check log files
            log_files = list(current_dir.glob('*.log'))
            log_status = {
                'count': len(log_files),
                'total_size_mb': sum(f.stat().st_size for f in log_files) / (1024*1024)
            }
            
            # Check screenshot files
            screenshot_files = list(current_dir.glob('screenshots/*.png'))
            screenshot_status = {
                'count': len(screenshot_files),
                'total_size_mb': sum(f.stat().st_size for f in screenshot_files) / (1024*1024)
            }
            
            storage_health = {
                'status': 'healthy',
                'directories': dir_status,
                'logs': log_status,
                'screenshots': screenshot_status,
                'current_directory': str(current_dir)
            }
            
            # Check for issues
            issues = []
            for dir_name, status in dir_status.items():
                if not status['exists']:
                    issues.append(f"Directory '{dir_name}' does not exist")
                elif not status['writable']:
                    issues.append(f"Directory '{dir_name}' is not writable")
            
            if issues:
                storage_health['status'] = 'warning'
                storage_health['issues'] = issues
            
            return storage_health
            
        except Exception as e:
            logger.error(f"Storage check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_processes(self) -> Dict[str, Any]:
        """
        Check running processes related to TradeBot
        """
        try:
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            
            # Find related processes
            related_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(keyword in cmdline.lower() for keyword in ['tradebot', 'playwright', 'chrome', 'chromium']):
                        related_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': round(proc.info['memory_percent'], 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            process_health = {
                'status': 'healthy',
                'current_process': {
                    'pid': current_pid,
                    'name': current_process.name(),
                    'cpu_percent': current_process.cpu_percent(),
                    'memory_percent': round(current_process.memory_percent(), 2),
                    'create_time': datetime.fromtimestamp(current_process.create_time()).isoformat()
                },
                'related_processes': related_processes,
                'total_related': len(related_processes)
            }
            
            return process_health
            
        except Exception as e:
            logger.error(f"Process check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_environment(self) -> Dict[str, Any]:
        """
        Check environment configuration
        """
        try:
            # Check critical environment variables
            critical_vars = [
                'BULENOX_USERNAME',
                'BULENOX_PASSWORD',
                'TRADING_MODE',
                'HEADLESS_BROWSER'
            ]
            
            env_status = {}
            missing_vars = []
            
            for var in critical_vars:
                value = os.getenv(var)
                if value:
                    env_status[var] = 'set' if var not in ['BULENOX_USERNAME', 'BULENOX_PASSWORD'] else 'set (hidden)'
                else:
                    env_status[var] = 'missing'
                    missing_vars.append(var)
            
            # Check Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # Check platform info
            platform_info = {
                'system': os.name,
                'platform': sys.platform,
                'python_version': python_version,
                'executable': sys.executable
            }
            
            environment_health = {
                'status': 'healthy' if not missing_vars else 'warning',
                'environment_variables': env_status,
                'platform': platform_info,
                'missing_variables': missing_vars
            }
            
            return environment_health
            
        except Exception as e:
            logger.error(f"Environment check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_health_check(self, checks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run comprehensive health check
        """
        logger.info("Starting comprehensive health check...")
        
        # Determine which checks to run
        checks_to_run = checks or list(self.checks.keys())
        
        # Run health checks
        results = {}
        overall_status = 'healthy'
        
        for check_name in checks_to_run:
            if check_name in self.checks:
                logger.info(f"Running {check_name} check...")
                try:
                    start_time = time.time()
                    result = self.checks[check_name]()
                    duration = round((time.time() - start_time) * 1000, 2)
                    
                    result['check_duration_ms'] = duration
                    results[check_name] = result
                    
                    # Update overall status
                    if result.get('status') == 'error':
                        overall_status = 'error'
                    elif result.get('status') == 'warning' and overall_status != 'error':
                        overall_status = 'warning'
                        
                except Exception as e:
                    logger.error(f"Health check '{check_name}' failed: {e}")
                    results[check_name] = {
                        'status': 'error',
                        'error': f"Check failed: {e}"
                    }
                    overall_status = 'error'
        
        # Compile final health report
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'uptime_seconds': round((datetime.now() - self.start_time).total_seconds(), 2),
            'checks_run': len(results),
            'results': results
        }
        
        # Add summary
        status_counts = {}
        for result in results.values():
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        health_report['summary'] = status_counts
        
        logger.info(f"Health check completed - Overall status: {overall_status}")
        return health_report
    
    def save_health_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """
        Save health report to file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'health_report_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Health report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save health report: {e}")

def main():
    """
    Main function for command-line usage
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='TradeBot Sentinel Health Checker')
    parser.add_argument('--config', '-c', help='Path to configuration file', default='.env')
    parser.add_argument('--checks', '-k', nargs='+', help='Specific checks to run')
    parser.add_argument('--output', '-o', help='Output file for health report')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create health checker
    checker = TradeBotHealthChecker(config_path=args.config)
    
    # Run health check
    report = checker.run_health_check(checks=args.checks)
    
    # Output results
    if args.format == 'json':
        output = json.dumps(report, indent=2, default=str)
    else:
        # Text format
        output = f"TradeBot Sentinel Health Report\n"
        output += f"Timestamp: {report['timestamp']}\n"
        output += f"Overall Status: {report['overall_status'].upper()}\n"
        output += f"Uptime: {report['uptime_seconds']} seconds\n\n"
        
        for check_name, result in report['results'].items():
            status = result.get('status', 'unknown').upper()
            output += f"{check_name.title()}: {status}\n"
            if 'error' in result:
                output += f"  Error: {result['error']}\n"
            if 'warnings' in result:
                for warning in result['warnings']:
                    output += f"  Warning: {warning}\n"
            output += "\n"
    
    # Save or print output
    if args.output:
        checker.save_health_report(report, args.output)
    else:
        print(output)
    
    # Exit with appropriate code
    exit_code = 0 if report['overall_status'] == 'healthy' else 1
    sys.exit(exit_code)

if __name__ == '__main__':
    main()