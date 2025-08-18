#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Testing Script
Comprehensive end-to-end testing for production deployment

Usage:
    python production_test.py --domain your-domain.com --api-key your-api-key
    python production_test.py --config test_config.json
"""

import asyncio
import json
import logging
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import requests
import websocket
import ssl
import subprocess
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ai-trading-sentinel/production_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Test configuration parameters"""
    domain: str
    api_key: Optional[str] = None
    timeout: int = 30
    ssl_verify: bool = True
    test_trading: bool = False
    test_websocket: bool = True
    test_monitoring: bool = True
    test_security: bool = True
    test_performance: bool = True

class ProductionTester:
    """Comprehensive production testing suite"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.base_url = f"https://{config.domain}"
        self.api_url = f"{self.base_url}/api"
        self.ws_url = f"wss://{config.domain}/ws"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'domain': config.domain,
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        # Configure requests session
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.ssl_verify
        
        if config.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json'
            })
    
    def log_test_result(self, test_name: str, passed: bool, message: str, 
                       details: Optional[Dict] = None, warning: bool = False):
        """Log test result"""
        status = 'WARNING' if warning else ('PASS' if passed else 'FAIL')
        logger.info(f"[{status}] {test_name}: {message}")
        
        self.results['tests'][test_name] = {
            'status': status,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total'] += 1
        if warning:
            self.results['summary']['warnings'] += 1
        elif passed:
            self.results['summary']['passed'] += 1
        else:
            self.results['summary']['failed'] += 1
    
    def test_ssl_certificate(self) -> bool:
        """Test SSL certificate validity and configuration"""
        try:
            # Test HTTPS connection
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            # Check SSL certificate details
            import ssl
            import socket
            
            context = ssl.create_default_context()
            with socket.create_connection((self.config.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.config.domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate expiry
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days
                    
                    details = {
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'subject': dict(x[0] for x in cert['subject']),
                        'expires': cert['notAfter'],
                        'days_until_expiry': days_until_expiry,
                        'san': cert.get('subjectAltName', [])
                    }
                    
                    if days_until_expiry < 30:
                        self.log_test_result(
                            'ssl_certificate', True, 
                            f"SSL certificate expires in {days_until_expiry} days",
                            details, warning=True
                        )
                    else:
                        self.log_test_result(
                            'ssl_certificate', True, 
                            f"SSL certificate valid, expires in {days_until_expiry} days",
                            details
                        )
                    
                    return True
                    
        except Exception as e:
            self.log_test_result(
                'ssl_certificate', False, 
                f"SSL certificate test failed: {str(e)}"
            )
            return False
    
    def test_http_security_headers(self) -> bool:
        """Test HTTP security headers"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            required_headers = {
                'Strict-Transport-Security': 'HSTS header',
                'X-Content-Type-Options': 'Content type options',
                'X-Frame-Options': 'Frame options',
                'X-XSS-Protection': 'XSS protection',
                'Referrer-Policy': 'Referrer policy'
            }
            
            missing_headers = []
            present_headers = {}
            
            for header, description in required_headers.items():
                if header in headers:
                    present_headers[header] = headers[header]
                else:
                    missing_headers.append(f"{header} ({description})")
            
            details = {
                'present_headers': present_headers,
                'missing_headers': missing_headers,
                'response_code': response.status_code
            }
            
            if missing_headers:
                self.log_test_result(
                    'security_headers', False,
                    f"Missing security headers: {', '.join(missing_headers)}",
                    details
                )
                return False
            else:
                self.log_test_result(
                    'security_headers', True,
                    "All required security headers present",
                    details
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                'security_headers', False,
                f"Security headers test failed: {str(e)}"
            )
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoint availability and responses"""
        endpoints = [
            ('/health', 'GET', 200, 'Health check'),
            ('/api/status', 'GET', 200, 'Bot status'),
            ('/api/config', 'GET', [200, 401], 'Configuration'),
            ('/api/trades', 'GET', [200, 401], 'Trade history'),
            ('/api/metrics', 'GET', [200, 401], 'System metrics')
        ]
        
        all_passed = True
        endpoint_results = {}
        
        for endpoint, method, expected_codes, description in endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.request(method, url)
                
                expected_codes = expected_codes if isinstance(expected_codes, list) else [expected_codes]
                
                if response.status_code in expected_codes:
                    endpoint_results[endpoint] = {
                        'status': 'PASS',
                        'code': response.status_code,
                        'response_time': response.elapsed.total_seconds()
                    }
                else:
                    endpoint_results[endpoint] = {
                        'status': 'FAIL',
                        'code': response.status_code,
                        'expected': expected_codes,
                        'response_time': response.elapsed.total_seconds()
                    }
                    all_passed = False
                    
            except Exception as e:
                endpoint_results[endpoint] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                all_passed = False
        
        self.log_test_result(
            'api_endpoints', all_passed,
            f"API endpoints test {'passed' if all_passed else 'failed'}",
            {'endpoints': endpoint_results}
        )
        
        return all_passed
    
    def test_websocket_connection(self) -> bool:
        """Test WebSocket connection and real-time updates"""
        if not self.config.test_websocket:
            return True
            
        try:
            import websocket
            
            messages_received = []
            connection_established = False
            
            def on_message(ws, message):
                messages_received.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': message
                })
            
            def on_open(ws):
                nonlocal connection_established
                connection_established = True
                # Send test message
                ws.send(json.dumps({'type': 'ping', 'timestamp': time.time()}))
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=on_message,
                on_open=on_open,
                on_error=on_error
            )
            
            # Run WebSocket in a separate thread for 5 seconds
            import threading
            ws_thread = threading.Thread(target=ws.run_forever, kwargs={'sslopt': {"cert_reqs": ssl.CERT_NONE}})
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection and messages
            time.sleep(5)
            ws.close()
            
            details = {
                'connection_established': connection_established,
                'messages_received': len(messages_received),
                'sample_messages': messages_received[:3]
            }
            
            if connection_established:
                self.log_test_result(
                    'websocket_connection', True,
                    f"WebSocket connection successful, received {len(messages_received)} messages",
                    details
                )
                return True
            else:
                self.log_test_result(
                    'websocket_connection', False,
                    "WebSocket connection failed",
                    details
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                'websocket_connection', False,
                f"WebSocket test failed: {str(e)}"
            )
            return False
    
    def test_system_performance(self) -> bool:
        """Test system performance and response times"""
        if not self.config.test_performance:
            return True
            
        try:
            # Test response times for key endpoints
            performance_tests = [
                ('/health', 1.0),  # Health check should be < 1s
                ('/api/status', 2.0),  # Status should be < 2s
                ('/', 3.0)  # Frontend should load < 3s
            ]
            
            performance_results = {}
            all_passed = True
            
            for endpoint, max_time in performance_tests:
                url = urljoin(self.base_url, endpoint)
                start_time = time.time()
                
                try:
                    response = self.session.get(url)
                    response_time = time.time() - start_time
                    
                    performance_results[endpoint] = {
                        'response_time': response_time,
                        'max_allowed': max_time,
                        'status_code': response.status_code,
                        'passed': response_time <= max_time
                    }
                    
                    if response_time > max_time:
                        all_passed = False
                        
                except Exception as e:
                    performance_results[endpoint] = {
                        'error': str(e),
                        'passed': False
                    }
                    all_passed = False
            
            # Test concurrent requests
            concurrent_start = time.time()
            concurrent_requests = 10
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [executor.submit(self.session.get, f"{self.base_url}/health") 
                          for _ in range(concurrent_requests)]
                concurrent.futures.wait(futures)
            
            concurrent_time = time.time() - concurrent_start
            
            performance_results['concurrent_test'] = {
                'requests': concurrent_requests,
                'total_time': concurrent_time,
                'avg_time_per_request': concurrent_time / concurrent_requests,
                'passed': concurrent_time < 10.0  # Should handle 10 requests in < 10s
            }
            
            if concurrent_time >= 10.0:
                all_passed = False
            
            self.log_test_result(
                'system_performance', all_passed,
                f"Performance test {'passed' if all_passed else 'failed'}",
                performance_results
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                'system_performance', False,
                f"Performance test failed: {str(e)}"
            )
            return False
    
    def test_trading_bot_status(self) -> bool:
        """Test trading bot status and functionality"""
        try:
            # Check bot status via API
            response = self.session.get(f"{self.api_url}/status")
            
            if response.status_code == 200:
                status_data = response.json()
                
                bot_running = status_data.get('bot_running', False)
                last_heartbeat = status_data.get('last_heartbeat')
                
                details = {
                    'bot_running': bot_running,
                    'last_heartbeat': last_heartbeat,
                    'status_data': status_data
                }
                
                if bot_running:
                    # Check if heartbeat is recent (within last 5 minutes)
                    if last_heartbeat:
                        heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                        time_diff = datetime.now() - heartbeat_time.replace(tzinfo=None)
                        
                        if time_diff < timedelta(minutes=5):
                            self.log_test_result(
                                'trading_bot_status', True,
                                "Trading bot is running and responsive",
                                details
                            )
                            return True
                        else:
                            self.log_test_result(
                                'trading_bot_status', False,
                                f"Trading bot heartbeat is stale ({time_diff})",
                                details
                            )
                            return False
                    else:
                        self.log_test_result(
                            'trading_bot_status', True,
                            "Trading bot is running (no heartbeat data)",
                            details,
                            warning=True
                        )
                        return True
                else:
                    self.log_test_result(
                        'trading_bot_status', False,
                        "Trading bot is not running",
                        details
                    )
                    return False
            else:
                self.log_test_result(
                    'trading_bot_status', False,
                    f"Failed to get bot status: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                'trading_bot_status', False,
                f"Trading bot status test failed: {str(e)}"
            )
            return False
    
    def test_monitoring_endpoints(self) -> bool:
        """Test monitoring and metrics endpoints"""
        if not self.config.test_monitoring:
            return True
            
        try:
            monitoring_endpoints = [
                (f"https://{self.config.domain}:9090/metrics", "Prometheus metrics"),
                (f"https://{self.config.domain}:3001/api/health", "Grafana health"),
                (f"{self.api_url}/metrics", "Application metrics")
            ]
            
            monitoring_results = {}
            all_passed = True
            
            for url, description in monitoring_endpoints:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    monitoring_results[description] = {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'content_length': len(response.content),
                        'passed': response.status_code in [200, 401]  # 401 is OK for protected endpoints
                    }
                    
                    if response.status_code not in [200, 401]:
                        all_passed = False
                        
                except Exception as e:
                    monitoring_results[description] = {
                        'error': str(e),
                        'passed': False
                    }
                    all_passed = False
            
            self.log_test_result(
                'monitoring_endpoints', all_passed,
                f"Monitoring endpoints test {'passed' if all_passed else 'failed'}",
                monitoring_results
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                'monitoring_endpoints', False,
                f"Monitoring endpoints test failed: {str(e)}"
            )
            return False
    
    def test_security_configuration(self) -> bool:
        """Test security configuration and hardening"""
        if not self.config.test_security:
            return True
            
        try:
            security_results = {}
            all_passed = True
            
            # Test for common security vulnerabilities
            security_tests = [
                # Test for directory traversal
                ('/../../../etc/passwd', 'Directory traversal protection'),
                # Test for SQL injection patterns
                ('/api/status?id=1\'OR\'1\'=\'1', 'SQL injection protection'),
                # Test for XSS patterns
                ('/search?q=<script>alert(1)</script>', 'XSS protection')
            ]
            
            for test_path, test_name in security_tests:
                try:
                    url = urljoin(self.base_url, test_path)
                    response = self.session.get(url)
                    
                    # Security tests should return 400, 403, 404, or redirect
                    secure_codes = [400, 403, 404, 301, 302]
                    
                    security_results[test_name] = {
                        'status_code': response.status_code,
                        'passed': response.status_code in secure_codes,
                        'test_path': test_path
                    }
                    
                    if response.status_code not in secure_codes:
                        all_passed = False
                        
                except Exception as e:
                    security_results[test_name] = {
                        'error': str(e),
                        'passed': True  # Exception is OK for security tests
                    }
            
            # Test rate limiting
            try:
                rate_limit_start = time.time()
                rate_limit_responses = []
                
                for i in range(20):  # Send 20 rapid requests
                    response = self.session.get(f"{self.base_url}/health")
                    rate_limit_responses.append(response.status_code)
                
                rate_limit_time = time.time() - rate_limit_start
                
                # Check if any requests were rate limited (429 status)
                rate_limited = 429 in rate_limit_responses
                
                security_results['rate_limiting'] = {
                    'total_requests': 20,
                    'time_taken': rate_limit_time,
                    'rate_limited': rate_limited,
                    'status_codes': list(set(rate_limit_responses)),
                    'passed': True  # Rate limiting is optional but good
                }
                
            except Exception as e:
                security_results['rate_limiting'] = {
                    'error': str(e),
                    'passed': True
                }
            
            self.log_test_result(
                'security_configuration', all_passed,
                f"Security configuration test {'passed' if all_passed else 'failed'}",
                security_results
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                'security_configuration', False,
                f"Security configuration test failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all production tests"""
        logger.info(f"Starting production tests for {self.config.domain}")
        
        # Core functionality tests
        self.test_ssl_certificate()
        self.test_http_security_headers()
        self.test_api_endpoints()
        self.test_trading_bot_status()
        
        # Optional tests based on configuration
        if self.config.test_websocket:
            self.test_websocket_connection()
        
        if self.config.test_monitoring:
            self.test_monitoring_endpoints()
        
        if self.config.test_security:
            self.test_security_configuration()
        
        if self.config.test_performance:
            self.test_system_performance()
        
        # Calculate final results
        summary = self.results['summary']
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        
        self.results['summary']['success_rate'] = success_rate
        self.results['summary']['overall_status'] = 'PASS' if summary['failed'] == 0 else 'FAIL'
        
        logger.info(f"Production tests completed: {summary['passed']}/{summary['total']} passed ({success_rate:.1f}%)")
        
        return self.results
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate detailed test report"""
        report_data = {
            'test_results': self.results,
            'generated_at': datetime.now().isoformat(),
            'config': {
                'domain': self.config.domain,
                'timeout': self.config.timeout,
                'ssl_verify': self.config.ssl_verify
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Test report saved to {output_file}")
        
        return json.dumps(report_data, indent=2)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Production Testing')
    parser.add_argument('--domain', required=True, help='Domain name to test')
    parser.add_argument('--api-key', help='API key for authenticated endpoints')
    parser.add_argument('--config', help='JSON configuration file')
    parser.add_argument('--output', help='Output file for test results')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL verification')
    parser.add_argument('--skip-websocket', action='store_true', help='Skip WebSocket tests')
    parser.add_argument('--skip-monitoring', action='store_true', help='Skip monitoring tests')
    parser.add_argument('--skip-security', action='store_true', help='Skip security tests')
    parser.add_argument('--skip-performance', action='store_true', help='Skip performance tests')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        config = TestConfig(**config_data)
    else:
        config = TestConfig(
            domain=args.domain,
            api_key=args.api_key,
            timeout=args.timeout,
            ssl_verify=not args.no_ssl_verify,
            test_websocket=not args.skip_websocket,
            test_monitoring=not args.skip_monitoring,
            test_security=not args.skip_security,
            test_performance=not args.skip_performance
        )
    
    # Run tests
    tester = ProductionTester(config)
    results = tester.run_all_tests()
    
    # Generate report
    output_file = args.output or f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    tester.generate_report(output_file)
    
    # Print summary
    summary = results['summary']
    print(f"\n{'='*60}")
    print(f"PRODUCTION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Domain: {config.domain}")
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Report: {output_file}")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if summary['failed'] == 0 else 1)

if __name__ == '__main__':
    main()