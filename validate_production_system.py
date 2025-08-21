#!/usr/bin/env python3
"""
AI Trading Sentinel - Production System Validation
TRAE-SentinelOps: Comprehensive health check and validation suite

This script performs end-to-end validation of the production system:
- System health checks
- Service availability
- Database connectivity
- API endpoint testing
- Security validation
- Performance benchmarks
- Integration testing
"""

import os
import sys
import time
import json
import asyncio
import logging
import subprocess
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Third-party imports
try:
    import psutil
    import aiohttp
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install: pip install psutil aiohttp playwright")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/trae-sentinel/validation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Represents the result of a validation check"""
    name: str
    status: str  # 'PASS', 'FAIL', 'WARNING', 'SKIP'
    message: str
    details: Dict[str, Any] = None
    duration: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.details is None:
            self.details = {}

class ProductionValidator:
    """Main validation class for production system checks"""
    
    def __init__(self, config_path: str = "/etc/trae-sentinel/.env"):
        self.config_path = config_path
        self.config = self._load_config()
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
        # Service endpoints
        self.backend_url = f"http://localhost:{self.config.get('BACKEND_PORT', 5000)}"
        self.frontend_url = f"http://localhost:{self.config.get('FRONTEND_PORT', 3000)}"
        self.bulenox_url = self.config.get('BULENOX_API_URL', 'https://bulenox.projectx.com/login')
        
        # Thresholds
        self.cpu_threshold = float(self.config.get('CPU_THRESHOLD', 85))
        self.memory_threshold = float(self.config.get('MEMORY_THRESHOLD', 90))
        self.disk_threshold = float(self.config.get('DISK_THRESHOLD', 95))
        
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment file"""
        config = {}
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            
            # Load from environment variables as fallback
            for key in ['BACKEND_PORT', 'FRONTEND_PORT', 'BULENOX_API_URL', 
                       'CPU_THRESHOLD', 'MEMORY_THRESHOLD', 'DISK_THRESHOLD']:
                if key in os.environ:
                    config[key] = os.environ[key]
                    
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            
        return config
    
    def _add_result(self, name: str, status: str, message: str, 
                   details: Dict[str, Any] = None, duration: float = 0.0):
        """Add a validation result"""
        result = ValidationResult(
            name=name,
            status=status,
            message=message,
            details=details or {},
            duration=duration
        )
        self.results.append(result)
        
        # Log result
        level = logging.INFO if status == 'PASS' else logging.WARNING if status == 'WARNING' else logging.ERROR
        logger.log(level, f"{name}: {status} - {message}")
    
    def validate_system_resources(self) -> None:
        """Validate system resource usage"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = 'PASS' if cpu_percent < self.cpu_threshold else 'FAIL'
            self._add_result(
                "System CPU Usage",
                cpu_status,
                f"CPU usage: {cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)",
                {"cpu_percent": cpu_percent, "threshold": self.cpu_threshold}
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_status = 'PASS' if memory.percent < self.memory_threshold else 'FAIL'
            self._add_result(
                "System Memory Usage",
                memory_status,
                f"Memory usage: {memory.percent:.1f}% (threshold: {self.memory_threshold}%)",
                {
                    "memory_percent": memory.percent,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "threshold": self.memory_threshold
                }
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = 'PASS' if disk_percent < self.disk_threshold else 'FAIL'
            self._add_result(
                "System Disk Usage",
                disk_status,
                f"Disk usage: {disk_percent:.1f}% (threshold: {self.disk_threshold}%)",
                {
                    "disk_percent": disk_percent,
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "threshold": self.disk_threshold
                }
            )
            
            # Load average
            load_avg = os.getloadavg()
            load_status = 'PASS' if load_avg[0] < 5.0 else 'WARNING'
            self._add_result(
                "System Load Average",
                load_status,
                f"Load average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}",
                {"load_1m": load_avg[0], "load_5m": load_avg[1], "load_15m": load_avg[2]}
            )
            
        except Exception as e:
            self._add_result(
                "System Resources",
                "FAIL",
                f"Failed to check system resources: {e}"
            )
        
        duration = time.time() - start_time
        self._add_result(
            "System Resource Check",
            "PASS",
            "System resource validation completed",
            duration=duration
        )
    
    def validate_services(self) -> None:
        """Validate systemd services"""
        services = [
            'trae-enhanced-monitor.service',
            'trae-backend.service',
            'trae-trading-bot.service',
            'nginx.service',
            'redis-server.service'
        ]
        
        for service in services:
            start_time = time.time()
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                status = 'PASS' if result.returncode == 0 else 'FAIL'
                state = result.stdout.strip()
                
                # Get additional service info
                info_result = subprocess.run(
                    ['systemctl', 'show', service, '--property=ActiveState,SubState,LoadState'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                service_info = {}
                for line in info_result.stdout.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        service_info[key] = value
                
                self._add_result(
                    f"Service: {service}",
                    status,
                    f"Service state: {state}",
                    service_info,
                    time.time() - start_time
                )
                
            except subprocess.TimeoutExpired:
                self._add_result(
                    f"Service: {service}",
                    "FAIL",
                    "Service check timed out",
                    duration=time.time() - start_time
                )
            except Exception as e:
                self._add_result(
                    f"Service: {service}",
                    "FAIL",
                    f"Failed to check service: {e}",
                    duration=time.time() - start_time
                )
    
    async def validate_api_endpoints(self) -> None:
        """Validate API endpoints"""
        endpoints = [
            (f"{self.backend_url}/api/health", "Backend Health"),
            (f"{self.backend_url}/api/status", "Backend Status"),
            (f"{self.backend_url}/api/metrics", "Backend Metrics"),
            (f"{self.frontend_url}", "Frontend"),
        ]
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for url, name in endpoints:
                start_time = time.time()
                try:
                    async with session.get(url) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                self._add_result(
                                    f"API Endpoint: {name}",
                                    "PASS",
                                    f"Endpoint responding (HTTP {response.status})",
                                    {
                                        "url": url,
                                        "status_code": response.status,
                                        "response_time_ms": round(duration * 1000, 2),
                                        "content_type": response.headers.get('content-type', ''),
                                        "response_size": len(str(data))
                                    },
                                    duration
                                )
                            except:
                                # Not JSON response, but still successful
                                self._add_result(
                                    f"API Endpoint: {name}",
                                    "PASS",
                                    f"Endpoint responding (HTTP {response.status})",
                                    {
                                        "url": url,
                                        "status_code": response.status,
                                        "response_time_ms": round(duration * 1000, 2),
                                        "content_type": response.headers.get('content-type', '')
                                    },
                                    duration
                                )
                        else:
                            self._add_result(
                                f"API Endpoint: {name}",
                                "FAIL",
                                f"Endpoint returned HTTP {response.status}",
                                {
                                    "url": url,
                                    "status_code": response.status,
                                    "response_time_ms": round(duration * 1000, 2)
                                },
                                duration
                            )
                            
                except asyncio.TimeoutError:
                    self._add_result(
                        f"API Endpoint: {name}",
                        "FAIL",
                        "Endpoint request timed out",
                        {"url": url, "timeout": True},
                        time.time() - start_time
                    )
                except Exception as e:
                    self._add_result(
                        f"API Endpoint: {name}",
                        "FAIL",
                        f"Endpoint request failed: {e}",
                        {"url": url, "error": str(e)},
                        time.time() - start_time
                    )
    
    def validate_database_connectivity(self) -> None:
        """Validate database connectivity"""
        start_time = time.time()
        
        database_url = self.config.get('DATABASE_URL', '')
        
        if not database_url:
            self._add_result(
                "Database Connectivity",
                "SKIP",
                "No database URL configured"
            )
            return
        
        try:
            if database_url.startswith('sqlite'):
                # SQLite validation
                db_path = database_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    self._add_result(
                        "Database Connectivity",
                        "PASS",
                        f"SQLite database accessible with {len(tables)} tables",
                        {
                            "database_type": "sqlite",
                            "database_path": db_path,
                            "table_count": len(tables),
                            "tables": [table[0] for table in tables]
                        },
                        time.time() - start_time
                    )
                else:
                    self._add_result(
                        "Database Connectivity",
                        "FAIL",
                        f"SQLite database file not found: {db_path}",
                        {"database_type": "sqlite", "database_path": db_path}
                    )
                    
            elif database_url.startswith('postgresql'):
                # PostgreSQL validation
                try:
                    import psycopg2
                    conn = psycopg2.connect(database_url)
                    cursor = conn.cursor()
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
                    table_count = cursor.fetchone()[0]
                    conn.close()
                    
                    self._add_result(
                        "Database Connectivity",
                        "PASS",
                        f"PostgreSQL database accessible",
                        {
                            "database_type": "postgresql",
                            "version": version,
                            "table_count": table_count
                        },
                        time.time() - start_time
                    )
                except ImportError:
                    self._add_result(
                        "Database Connectivity",
                        "FAIL",
                        "psycopg2 not installed for PostgreSQL connectivity"
                    )
                    
        except Exception as e:
            self._add_result(
                "Database Connectivity",
                "FAIL",
                f"Database connection failed: {e}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    def validate_redis_connectivity(self) -> None:
        """Validate Redis connectivity"""
        start_time = time.time()
        
        redis_url = self.config.get('REDIS_URL', '')
        
        if not redis_url:
            self._add_result(
                "Redis Connectivity",
                "SKIP",
                "No Redis URL configured"
            )
            return
        
        try:
            import redis
            r = redis.from_url(redis_url)
            
            # Test basic operations
            test_key = f"trae_health_check_{int(time.time())}"
            r.set(test_key, "test_value", ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            # Get Redis info
            info = r.info()
            
            self._add_result(
                "Redis Connectivity",
                "PASS",
                "Redis connection and operations successful",
                {
                    "redis_version": info.get('redis_version'),
                    "connected_clients": info.get('connected_clients'),
                    "used_memory_human": info.get('used_memory_human'),
                    "uptime_in_seconds": info.get('uptime_in_seconds')
                },
                time.time() - start_time
            )
            
        except ImportError:
            self._add_result(
                "Redis Connectivity",
                "FAIL",
                "redis-py not installed"
            )
        except Exception as e:
            self._add_result(
                "Redis Connectivity",
                "FAIL",
                f"Redis connection failed: {e}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    async def validate_browser_automation(self) -> None:
        """Validate browser automation capabilities"""
        start_time = time.time()
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                
                # Test basic navigation
                await page.goto('https://httpbin.org/get')
                title = await page.title()
                
                # Test JavaScript execution
                result = await page.evaluate('() => ({ userAgent: navigator.userAgent, timestamp: Date.now() })')
                
                await browser.close()
                
                self._add_result(
                    "Browser Automation",
                    "PASS",
                    "Browser automation working correctly",
                    {
                        "browser": "chromium",
                        "page_title": title,
                        "user_agent": result.get('userAgent', ''),
                        "javascript_enabled": True
                    },
                    time.time() - start_time
                )
                
        except Exception as e:
            self._add_result(
                "Browser Automation",
                "FAIL",
                f"Browser automation failed: {e}",
                {"error": str(e)},
                time.time() - start_time
            )
    
    def validate_file_permissions(self) -> None:
        """Validate file and directory permissions"""
        start_time = time.time()
        
        critical_paths = [
            ('/opt/trae-sentinel', 'trae-sentinel', 'trae-sentinel', 0o755),
            ('/etc/trae-sentinel/.env', 'root', 'trae-sentinel', 0o640),
            ('/etc/trae-sentinel/secrets', 'root', 'root', 0o700),
            ('/var/log/trae-sentinel', 'trae-sentinel', 'trae-sentinel', 0o750),
            ('/var/lib/trae-sentinel', 'trae-sentinel', 'trae-sentinel', 0o750)
        ]
        
        permission_issues = []
        
        for path, expected_user, expected_group, expected_mode in critical_paths:
            try:
                if not os.path.exists(path):
                    permission_issues.append(f"{path}: Path does not exist")
                    continue
                
                stat_info = os.stat(path)
                actual_mode = stat_info.st_mode & 0o777
                
                # Get user and group names
                import pwd
                import grp
                actual_user = pwd.getpwuid(stat_info.st_uid).pw_name
                actual_group = grp.getgrgid(stat_info.st_gid).gr_name
                
                if actual_user != expected_user:
                    permission_issues.append(f"{path}: Owner is {actual_user}, expected {expected_user}")
                
                if actual_group != expected_group:
                    permission_issues.append(f"{path}: Group is {actual_group}, expected {expected_group}")
                
                if actual_mode != expected_mode:
                    permission_issues.append(
                        f"{path}: Mode is {oct(actual_mode)}, expected {oct(expected_mode)}"
                    )
                    
            except Exception as e:
                permission_issues.append(f"{path}: Error checking permissions: {e}")
        
        if permission_issues:
            self._add_result(
                "File Permissions",
                "FAIL",
                f"Found {len(permission_issues)} permission issues",
                {"issues": permission_issues},
                time.time() - start_time
            )
        else:
            self._add_result(
                "File Permissions",
                "PASS",
                "All file permissions are correct",
                {"checked_paths": len(critical_paths)},
                time.time() - start_time
            )
    
    def validate_network_connectivity(self) -> None:
        """Validate network connectivity"""
        start_time = time.time()
        
        test_urls = [
            ('https://google.com', 'Internet connectivity'),
            ('https://bulenox.projectx.com', 'Bulenox platform'),
            ('https://api.github.com', 'GitHub API')
        ]
        
        connectivity_results = []
        
        for url, description in test_urls:
            try:
                response = requests.get(url, timeout=10)
                connectivity_results.append({
                    "url": url,
                    "description": description,
                    "status_code": response.status_code,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "success": response.status_code < 400
                })
            except Exception as e:
                connectivity_results.append({
                    "url": url,
                    "description": description,
                    "error": str(e),
                    "success": False
                })
        
        failed_connections = [r for r in connectivity_results if not r['success']]
        
        if failed_connections:
            self._add_result(
                "Network Connectivity",
                "WARNING" if len(failed_connections) < len(connectivity_results) else "FAIL",
                f"{len(failed_connections)} of {len(connectivity_results)} connections failed",
                {"results": connectivity_results},
                time.time() - start_time
            )
        else:
            self._add_result(
                "Network Connectivity",
                "PASS",
                "All network connections successful",
                {"results": connectivity_results},
                time.time() - start_time
            )
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("Starting production system validation...")
        
        # System-level validations
        self.validate_system_resources()
        self.validate_services()
        self.validate_file_permissions()
        self.validate_network_connectivity()
        
        # Database and cache validations
        self.validate_database_connectivity()
        self.validate_redis_connectivity()
        
        # Application-level validations
        await self.validate_api_endpoints()
        await self.validate_browser_automation()
        
        # Generate summary
        total_duration = time.time() - self.start_time
        
        summary = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "total_duration_seconds": round(total_duration, 2),
            "total_checks": len(self.results),
            "passed": len([r for r in self.results if r.status == 'PASS']),
            "failed": len([r for r in self.results if r.status == 'FAIL']),
            "warnings": len([r for r in self.results if r.status == 'WARNING']),
            "skipped": len([r for r in self.results if r.status == 'SKIP']),
            "overall_status": self._get_overall_status(),
            "results": [asdict(r) for r in self.results]
        }
        
        logger.info(f"Validation completed in {total_duration:.2f}s")
        logger.info(f"Results: {summary['passed']} passed, {summary['failed']} failed, {summary['warnings']} warnings")
        
        return summary
    
    def _get_overall_status(self) -> str:
        """Determine overall validation status"""
        if any(r.status == 'FAIL' for r in self.results):
            return 'FAIL'
        elif any(r.status == 'WARNING' for r in self.results):
            return 'WARNING'
        else:
            return 'PASS'
    
    def save_report(self, summary: Dict[str, Any], output_path: str = None) -> str:
        """Save validation report to file"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"/var/log/trae-sentinel/validation_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Validation report saved to: {output_path}")
        return output_path

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Production Validation')
    parser.add_argument('--config', '-c', default='/etc/trae-sentinel/.env',
                       help='Path to configuration file')
    parser.add_argument('--output', '-o', help='Output file for validation report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run validation
    validator = ProductionValidator(args.config)
    summary = await validator.run_all_validations()
    
    # Save report
    report_path = validator.save_report(summary, args.output)
    
    # Output results
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        # Human-readable output
        print("\n" + "="*80)
        print("AI Trading Sentinel - Production Validation Report")
        print("="*80)
        print(f"Validation Time: {summary['validation_timestamp']}")
        print(f"Total Duration: {summary['total_duration_seconds']}s")
        print(f"Overall Status: {summary['overall_status']}")
        print()
        print(f"Results Summary:")
        print(f"  ✅ Passed: {summary['passed']}")
        print(f"  ❌ Failed: {summary['failed']}")
        print(f"  ⚠️  Warnings: {summary['warnings']}")
        print(f"  ⏭️  Skipped: {summary['skipped']}")
        print()
        
        # Show failed checks
        failed_results = [r for r in validator.results if r.status == 'FAIL']
        if failed_results:
            print("Failed Checks:")
            for result in failed_results:
                print(f"  ❌ {result.name}: {result.message}")
            print()
        
        # Show warnings
        warning_results = [r for r in validator.results if r.status == 'WARNING']
        if warning_results:
            print("Warnings:")
            for result in warning_results:
                print(f"  ⚠️  {result.name}: {result.message}")
            print()
        
        print(f"Full report saved to: {report_path}")
        print("="*80)
    
    # Exit with appropriate code
    if summary['overall_status'] == 'FAIL':
        sys.exit(1)
    elif summary['overall_status'] == 'WARNING':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())