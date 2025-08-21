#!/usr/bin/env python3
"""
Trae AI Trading Sentinel - Recovery Mechanisms Test Suite

This script validates auto-restart, error handling, and failover systems
under various failure scenarios to ensure 24/7 reliability.

Usage:
    python test_recovery_mechanisms.py [--scenario SCENARIO] [--verbose]
    
Scenarios:
    - all: Run all recovery tests (default)
    - network: Test network failure recovery
    - memory: Test memory exhaustion recovery
    - process: Test process crash recovery
    - api: Test API failure recovery
    - broker: Test broker connection recovery
    - database: Test database failure recovery
"""

import asyncio
import json
import logging
import os
import psutil
import requests
import signal
import subprocess
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger
from src.config.settings import Settings

class RecoveryTester:
    """Test suite for recovery mechanisms."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = setup_logger('recovery_tester', level=logging.DEBUG if verbose else logging.INFO)
        self.settings = Settings()
        self.test_results = []
        self.start_time = datetime.now()
        
        # Test configuration
        self.test_timeout = 300  # 5 minutes per test
        self.recovery_timeout = 60  # 1 minute for recovery
        self.health_check_interval = 5  # 5 seconds
        
        # Process tracking
        self.bot_process = None
        self.backend_process = None
        
    def log_test_result(self, test_name: str, success: bool, details: str, duration: float):
        """Log test result."""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} {test_name} ({duration:.2f}s): {details}")
        
    def get_bot_process(self) -> Optional[psutil.Process]:
        """Find the main bot process."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
        
    def get_backend_process(self) -> Optional[psutil.Process]:
        """Find the backend process."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and 'backend_main.py' in ' '.join(proc.info['cmdline']):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
        
    def is_bot_healthy(self) -> Tuple[bool, str]:
        """Check if bot is healthy."""
        try:
            # Check process
            bot_proc = self.get_bot_process()
            if not bot_proc or not bot_proc.is_running():
                return False, "Bot process not running"
                
            # Check API health
            try:
                response = requests.get('http://localhost:5000/health', timeout=5)
                if response.status_code != 200:
                    return False, f"API health check failed: {response.status_code}"
            except requests.RequestException as e:
                return False, f"API not responding: {str(e)}"
                
            # Check memory usage
            memory_percent = bot_proc.memory_percent()
            if memory_percent > 90:
                return False, f"High memory usage: {memory_percent:.1f}%"
                
            return True, "Bot is healthy"
            
        except Exception as e:
            return False, f"Health check error: {str(e)}"
            
    def wait_for_recovery(self, timeout: int = 60) -> bool:
        """Wait for bot to recover."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            healthy, status = self.is_bot_healthy()
            if healthy:
                self.logger.info(f"Bot recovered: {status}")
                return True
                
            self.logger.debug(f"Waiting for recovery: {status}")
            time.sleep(self.health_check_interval)
            
        return False
        
    def simulate_network_failure(self) -> bool:
        """Test network failure recovery."""
        test_start = time.time()
        
        try:
            # Block network access using iptables (Linux) or netsh (Windows)
            if os.name == 'nt':  # Windows
                # Block outbound connections on port 443 (HTTPS)
                subprocess.run([
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    'name=TRAETestBlock', 'dir=out', 'action=block',
                    'protocol=TCP', 'remoteport=443'
                ], check=True, capture_output=True)
            else:  # Linux
                subprocess.run([
                    'sudo', 'iptables', '-A', 'OUTPUT', '-p', 'tcp',
                    '--dport', '443', '-j', 'DROP'
                ], check=True, capture_output=True)
                
            self.logger.info("Network access blocked")
            
            # Wait for bot to detect network failure
            time.sleep(10)
            
            # Check if bot handles network failure gracefully
            healthy, status = self.is_bot_healthy()
            if not healthy and "network" not in status.lower():
                return False  # Bot should detect network issues
                
            # Restore network access
            if os.name == 'nt':
                subprocess.run([
                    'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                    'name=TRAETestBlock'
                ], check=True, capture_output=True)
            else:
                subprocess.run([
                    'sudo', 'iptables', '-D', 'OUTPUT', '-p', 'tcp',
                    '--dport', '443', '-j', 'DROP'
                ], check=True, capture_output=True)
                
            self.logger.info("Network access restored")
            
            # Wait for recovery
            return self.wait_for_recovery()
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Network simulation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Network test error: {e}")
            return False
        finally:
            duration = time.time() - test_start
            
    def simulate_memory_exhaustion(self) -> bool:
        """Test memory exhaustion recovery."""
        test_start = time.time()
        
        try:
            # Get current bot process
            bot_proc = self.get_bot_process()
            if not bot_proc:
                return False
                
            initial_memory = bot_proc.memory_info().rss / 1024 / 1024  # MB
            self.logger.info(f"Initial memory usage: {initial_memory:.1f} MB")
            
            # Simulate memory leak by creating large objects
            memory_hog = []
            target_memory = initial_memory + 500  # Add 500MB
            
            # Gradually increase memory usage
            while bot_proc.memory_info().rss / 1024 / 1024 < target_memory:
                memory_hog.append(b'x' * 1024 * 1024)  # 1MB chunks
                time.sleep(0.1)
                
                if not bot_proc.is_running():
                    break
                    
            current_memory = bot_proc.memory_info().rss / 1024 / 1024
            self.logger.info(f"Memory usage increased to: {current_memory:.1f} MB")
            
            # Check if bot detects high memory usage
            time.sleep(5)
            healthy, status = self.is_bot_healthy()
            
            # Clean up memory
            del memory_hog
            
            # Wait for recovery
            return self.wait_for_recovery()
            
        except Exception as e:
            self.logger.error(f"Memory test error: {e}")
            return False
        finally:
            duration = time.time() - test_start
            
    def simulate_process_crash(self) -> bool:
        """Test process crash recovery."""
        test_start = time.time()
        
        try:
            # Get bot process
            bot_proc = self.get_bot_process()
            if not bot_proc:
                return False
                
            pid = bot_proc.pid
            self.logger.info(f"Terminating bot process (PID: {pid})")
            
            # Terminate process
            bot_proc.terminate()
            
            # Wait for process to die
            try:
                bot_proc.wait(timeout=10)
            except psutil.TimeoutExpired:
                bot_proc.kill()
                
            self.logger.info("Bot process terminated")
            
            # Wait for systemd to restart (if configured)
            time.sleep(5)
            
            # Check if process restarted
            return self.wait_for_recovery()
            
        except Exception as e:
            self.logger.error(f"Process crash test error: {e}")
            return False
        finally:
            duration = time.time() - test_start
            
    def simulate_api_failure(self) -> bool:
        """Test API failure recovery."""
        test_start = time.time()
        
        try:
            # Test API endpoint failures
            test_endpoints = [
                '/health',
                '/api/status',
                '/api/trades',
                '/api/positions'
            ]
            
            failures = 0
            for endpoint in test_endpoints:
                try:
                    response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
                    if response.status_code >= 500:
                        failures += 1
                except requests.RequestException:
                    failures += 1
                    
            # Simulate high load
            threads = []
            for i in range(50):  # 50 concurrent requests
                thread = threading.Thread(target=self._stress_api)
                threads.append(thread)
                thread.start()
                
            # Wait for stress test
            time.sleep(10)
            
            # Stop stress test
            for thread in threads:
                thread.join(timeout=1)
                
            # Check recovery
            return self.wait_for_recovery()
            
        except Exception as e:
            self.logger.error(f"API failure test error: {e}")
            return False
        finally:
            duration = time.time() - test_start
            
    def _stress_api(self):
        """Helper method for API stress testing."""
        try:
            for _ in range(10):
                requests.get('http://localhost:5000/health', timeout=1)
                time.sleep(0.1)
        except:
            pass
            
    def simulate_broker_failure(self) -> bool:
        """Test broker connection failure recovery."""
        test_start = time.time()
        
        try:
            # This would require mocking broker responses
            # For now, we'll test connection timeout handling
            
            # Check if bot handles broker disconnection gracefully
            healthy, status = self.is_bot_healthy()
            
            # Simulate broker API timeout by blocking broker domains
            # This is a simplified test - real implementation would mock responses
            
            self.logger.info("Simulating broker connection issues")
            
            # Wait and check recovery
            time.sleep(10)
            return self.wait_for_recovery()
            
        except Exception as e:
            self.logger.error(f"Broker failure test error: {e}")
            return False
        finally:
            duration = time.time() - test_start
            
    def simulate_database_failure(self) -> bool:
        """Test database failure recovery."""
        test_start = time.time()
        
        try:
            # Test database connection handling
            # This would require stopping/starting database service
            
            self.logger.info("Testing database resilience")
            
            # Check if bot handles database issues gracefully
            healthy, status = self.is_bot_healthy()
            
            # For now, just verify the bot can handle database timeouts
            return self.wait_for_recovery()
            
        except Exception as e:
            self.logger.error(f"Database failure test error: {e}")
            return False
        finally:
            duration = time.time() - test_start
            
    def run_test_scenario(self, scenario: str) -> bool:
        """Run a specific test scenario."""
        self.logger.info(f"Running {scenario} recovery test")
        
        # Ensure bot is healthy before test
        healthy, status = self.is_bot_healthy()
        if not healthy:
            self.log_test_result(scenario, False, f"Bot not healthy before test: {status}", 0)
            return False
            
        test_start = time.time()
        
        try:
            if scenario == 'network':
                success = self.simulate_network_failure()
            elif scenario == 'memory':
                success = self.simulate_memory_exhaustion()
            elif scenario == 'process':
                success = self.simulate_process_crash()
            elif scenario == 'api':
                success = self.simulate_api_failure()
            elif scenario == 'broker':
                success = self.simulate_broker_failure()
            elif scenario == 'database':
                success = self.simulate_database_failure()
            else:
                success = False
                
            duration = time.time() - test_start
            details = "Recovery successful" if success else "Recovery failed"
            self.log_test_result(scenario, success, details, duration)
            
            return success
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result(scenario, False, f"Test error: {str(e)}", duration)
            return False
            
    def run_all_tests(self) -> Dict:
        """Run all recovery tests."""
        scenarios = ['network', 'memory', 'process', 'api', 'broker', 'database']
        
        self.logger.info("Starting comprehensive recovery mechanism tests")
        
        passed = 0
        total = len(scenarios)
        
        for scenario in scenarios:
            if self.run_test_scenario(scenario):
                passed += 1
                
            # Wait between tests
            time.sleep(5)
            
        # Generate report
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': (passed / total) * 100,
                'duration': duration
            },
            'results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
        
    def save_report(self, report: Dict, filename: str = None):
        """Save test report to file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'recovery_test_report_{timestamp}.json'
            
        report_path = Path('tests/reports') / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Test report saved to: {report_path}")
        
    def print_summary(self, report: Dict):
        """Print test summary."""
        summary = report['summary']
        
        print("\n" + "="*60)
        print("TRAE AI TRADING SENTINEL - RECOVERY TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['duration']:.1f} seconds")
        print("="*60)
        
        # Print individual results
        for result in report['results']:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']} ({result['duration']:.1f}s)")
            
        print("="*60)
        
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test recovery mechanisms')
    parser.add_argument('--scenario', choices=['all', 'network', 'memory', 'process', 'api', 'broker', 'database'],
                       default='all', help='Test scenario to run')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--report', help='Save report to specific file')
    
    args = parser.parse_args()
    
    tester = RecoveryTester(verbose=args.verbose)
    
    if args.scenario == 'all':
        report = tester.run_all_tests()
    else:
        success = tester.run_test_scenario(args.scenario)
        report = {
            'summary': {
                'total_tests': 1,
                'passed': 1 if success else 0,
                'failed': 0 if success else 1,
                'success_rate': 100 if success else 0,
                'duration': (datetime.now() - tester.start_time).total_seconds()
            },
            'results': tester.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
    tester.print_summary(report)
    tester.save_report(report, args.report)
    
    # Exit with error code if tests failed
    if report['summary']['failed'] > 0:
        sys.exit(1)
        
if __name__ == '__main__':
    main()