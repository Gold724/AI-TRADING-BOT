#!/usr/bin/env python3
"""
AI Trading Sentinel - Deployment Test Suite
Comprehensive testing for production deployment validation
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class DeploymentTester:
    """Comprehensive deployment testing suite"""
    
    def __init__(self, config_file: str = None):
        self.config = self.load_config(config_file)
        self.results = []
        self.start_time = datetime.now()
        
    def load_config(self, config_file: str) -> Dict:
        """Load test configuration"""
        default_config = {
            "api_base_url": "http://localhost:5000",
            "frontend_url": "http://localhost:3000",
            "timeout": 30,
            "retry_attempts": 3,
            "health_check_interval": 5
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def log_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results.append(result)
        
        # Color coding for console output
        color = "\033[92m" if status == "PASS" else "\033[91m" if status == "FAIL" else "\033[93m"
        reset = "\033[0m"
        print(f"{color}[{status}]{reset} {test_name}: {message}")
    
    def test_system_requirements(self) -> bool:
        """Test system requirements and dependencies"""
        print("\n=== Testing System Requirements ===")
        
        # Test Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.log_result("Python Version", "PASS", f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.log_result("Python Version", "FAIL", f"Python {python_version.major}.{python_version.minor} < 3.8")
            return False
        
        # Test required packages
        required_packages = [
            "flask", "requests", "selenium", "pandas", "numpy", "redis"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.log_result(f"Package: {package}", "PASS", "Installed")
            except ImportError:
                self.log_result(f"Package: {package}", "FAIL", "Not installed")
                return False
        
        # Test environment variables
        required_env_vars = [
            "FLASK_SECRET_KEY", "JWT_SECRET_KEY", "BULENOX_USERNAME", "BULENOX_PASSWORD"
        ]
        
        for env_var in required_env_vars:
            if os.getenv(env_var):
                self.log_result(f"Env Var: {env_var}", "PASS", "Set")
            else:
                self.log_result(f"Env Var: {env_var}", "WARN", "Not set")
        
        return True
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        print("\n=== Testing API Endpoints ===")
        
        base_url = self.config["api_base_url"]
        timeout = self.config["timeout"]
        
        endpoints = [
            ("/health", "GET", "Health check endpoint"),
            ("/api/status", "GET", "Status endpoint"),
            ("/api/config", "GET", "Configuration endpoint"),
            ("/api/trades", "GET", "Trades endpoint"),
            ("/api/logs", "GET", "Logs endpoint")
        ]
        
        all_passed = True
        
        for endpoint, method, description in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.request(method, url, timeout=timeout)
                
                if response.status_code == 200:
                    self.log_result(f"API: {endpoint}", "PASS", f"{description} - Status: {response.status_code}")
                elif response.status_code == 404:
                    self.log_result(f"API: {endpoint}", "WARN", f"{description} - Not implemented (404)")
                else:
                    self.log_result(f"API: {endpoint}", "FAIL", f"{description} - Status: {response.status_code}")
                    all_passed = False
                    
            except requests.exceptions.ConnectionError:
                self.log_result(f"API: {endpoint}", "FAIL", f"{description} - Connection refused")
                all_passed = False
            except requests.exceptions.Timeout:
                self.log_result(f"API: {endpoint}", "FAIL", f"{description} - Timeout")
                all_passed = False
            except Exception as e:
                self.log_result(f"API: {endpoint}", "FAIL", f"{description} - Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_database_connection(self) -> bool:
        """Test database connectivity"""
        print("\n=== Testing Database Connection ===")
        
        try:
            # Test Redis connection
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()
            self.log_result("Redis Connection", "PASS", "Connected successfully")
            
            # Test basic operations
            test_key = "deployment_test"
            test_value = "test_value"
            r.set(test_key, test_value)
            retrieved_value = r.get(test_key).decode('utf-8')
            
            if retrieved_value == test_value:
                self.log_result("Redis Operations", "PASS", "Read/Write operations successful")
                r.delete(test_key)  # Cleanup
                return True
            else:
                self.log_result("Redis Operations", "FAIL", "Read/Write operations failed")
                return False
                
        except Exception as e:
            self.log_result("Redis Connection", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_trading_bot_components(self) -> bool:
        """Test trading bot components"""
        print("\n=== Testing Trading Bot Components ===")
        
        try:
            # Test Selenium WebDriver
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://www.google.com")
            
            if "Google" in driver.title:
                self.log_result("Selenium WebDriver", "PASS", "Chrome WebDriver working")
                driver.quit()
            else:
                self.log_result("Selenium WebDriver", "FAIL", "Chrome WebDriver not working")
                driver.quit()
                return False
                
        except Exception as e:
            self.log_result("Selenium WebDriver", "FAIL", f"Error: {str(e)}")
            return False
        
        # Test trading logic imports
        try:
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            
            # Test if main trading modules can be imported
            test_imports = [
                "main",
                "backend_main",
                "bulenox_trader"
            ]
            
            for module in test_imports:
                try:
                    __import__(module)
                    self.log_result(f"Import: {module}", "PASS", "Module imported successfully")
                except ImportError as e:
                    self.log_result(f"Import: {module}", "WARN", f"Module not found: {str(e)}")
                except Exception as e:
                    self.log_result(f"Import: {module}", "FAIL", f"Import error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Trading Components", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_security_configuration(self) -> bool:
        """Test security configuration"""
        print("\n=== Testing Security Configuration ===")
        
        # Test SSL/HTTPS (if configured)
        if "https://" in self.config.get("api_base_url", ""):
            try:
                response = requests.get(self.config["api_base_url"] + "/health", verify=True)
                self.log_result("SSL Certificate", "PASS", "Valid SSL certificate")
            except requests.exceptions.SSLError:
                self.log_result("SSL Certificate", "FAIL", "Invalid SSL certificate")
                return False
        else:
            self.log_result("SSL Certificate", "WARN", "HTTPS not configured")
        
        # Test environment variable security
        sensitive_vars = ["FLASK_SECRET_KEY", "JWT_SECRET_KEY", "BULENOX_PASSWORD"]
        for var in sensitive_vars:
            value = os.getenv(var, "")
            if len(value) >= 16:
                self.log_result(f"Security: {var}", "PASS", "Secure value length")
            elif len(value) > 0:
                self.log_result(f"Security: {var}", "WARN", "Short security value")
            else:
                self.log_result(f"Security: {var}", "FAIL", "Missing security value")
        
        return True
    
    def test_performance_metrics(self) -> bool:
        """Test performance metrics"""
        print("\n=== Testing Performance Metrics ===")
        
        # Test API response times
        base_url = self.config["api_base_url"]
        
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/health", timeout=self.config["timeout"])
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response_time < 1000:  # Less than 1 second
                self.log_result("API Response Time", "PASS", f"{response_time:.2f}ms")
            elif response_time < 5000:  # Less than 5 seconds
                self.log_result("API Response Time", "WARN", f"{response_time:.2f}ms (slow)")
            else:
                self.log_result("API Response Time", "FAIL", f"{response_time:.2f}ms (too slow)")
                return False
                
        except Exception as e:
            self.log_result("API Response Time", "FAIL", f"Error: {str(e)}")
            return False
        
        # Test system resources
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent < 80:
                self.log_result("CPU Usage", "PASS", f"{cpu_percent}%")
            else:
                self.log_result("CPU Usage", "WARN", f"{cpu_percent}% (high)")
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent < 80:
                self.log_result("Memory Usage", "PASS", f"{memory_percent}%")
            else:
                self.log_result("Memory Usage", "WARN", f"{memory_percent}% (high)")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent < 80:
                self.log_result("Disk Usage", "PASS", f"{disk_percent:.1f}%")
            else:
                self.log_result("Disk Usage", "WARN", f"{disk_percent:.1f}% (high)")
                
        except ImportError:
            self.log_result("System Resources", "WARN", "psutil not installed")
        except Exception as e:
            self.log_result("System Resources", "FAIL", f"Error: {str(e)}")
        
        return True
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Count results
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        total = len(self.results)
        
        report = {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "success_rate": (passed / total * 100) if total > 0 else 0,
                "duration_seconds": duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "results": self.results,
            "deployment_ready": failed == 0
        }
        
        return report
    
    def run_all_tests(self) -> bool:
        """Run all deployment tests"""
        print("🚀 AI Trading Sentinel - Deployment Test Suite")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run test suites
        test_suites = [
            ("System Requirements", self.test_system_requirements),
            ("API Endpoints", self.test_api_endpoints),
            ("Database Connection", self.test_database_connection),
            ("Trading Bot Components", self.test_trading_bot_components),
            ("Security Configuration", self.test_security_configuration),
            ("Performance Metrics", self.test_performance_metrics)
        ]
        
        overall_success = True
        
        for suite_name, test_function in test_suites:
            try:
                success = test_function()
                if not success:
                    overall_success = False
            except Exception as e:
                self.log_result(f"Test Suite: {suite_name}", "FAIL", f"Exception: {str(e)}")
                overall_success = False
        
        # Generate and display report
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT TEST REPORT")
        print("=" * 60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"✅ Passed: {report['summary']['passed']}")
        print(f"❌ Failed: {report['summary']['failed']}")
        print(f"⚠️  Warnings: {report['summary']['warnings']}")
        print(f"📈 Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"⏱️  Duration: {report['summary']['duration_seconds']:.2f}s")
        print(f"🚀 Deployment Ready: {'YES' if report['deployment_ready'] else 'NO'}")
        
        # Save report to file
        report_file = f"deployment_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {report_file}")
        
        return overall_success and report['deployment_ready']

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Deployment Tester")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--api-url", help="API base URL", default="http://localhost:5000")
    parser.add_argument("--frontend-url", help="Frontend URL", default="http://localhost:3000")
    parser.add_argument("--timeout", type=int, help="Request timeout", default=30)
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = DeploymentTester(args.config)
    
    # Override config with command line arguments
    if args.api_url:
        tester.config["api_base_url"] = args.api_url
    if args.frontend_url:
        tester.config["frontend_url"] = args.frontend_url
    if args.timeout:
        tester.config["timeout"] = args.timeout
    
    # Run tests
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()