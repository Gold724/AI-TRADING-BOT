#!/usr/bin/env python3
"""
Unified Launcher System Test Script
Tests all components of the unified launcher system
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

class UnifiedSystemTester:
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {message}")
        
    def test_environment_variables(self):
        """Test if required environment variables are set"""
        required_vars = ['BULENOX_USERNAME', 'BULENOX_PASSWORD']
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                self.log_test(f"Environment Variable {var}", True, f"Set to: {value[:3]}***")
            else:
                self.log_test(f"Environment Variable {var}", False, "Not set")
                
    def test_file_existence(self):
        """Test if all required files exist"""
        required_files = [
            'live_trading_unified.ps1',
            'live_trading_unified.sh',
            'tradebot_sentinel_advanced_pro.py',
            'tradebot_sentinel.py',
            'README_UNIFIED_LAUNCHER.md'
        ]
        
        for file in required_files:
            if Path(file).exists():
                size = Path(file).stat().st_size
                self.log_test(f"File {file}", True, f"Exists ({size} bytes)")
            else:
                self.log_test(f"File {file}", False, "Missing")
                
    def test_python_dependencies(self):
        """Test if required Python packages are installed"""
        required_packages = ['playwright', 'requests']
        
        for package in required_packages:
            try:
                __import__(package)
                self.log_test(f"Python Package {package}", True, "Installed")
            except ImportError:
                self.log_test(f"Python Package {package}", False, "Not installed")
                
    def test_playwright_browsers(self):
        """Test if Playwright browsers are installed"""
        try:
            result = subprocess.run(['playwright', 'install', '--dry-run'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.log_test("Playwright Browsers", True, "Available")
            else:
                self.log_test("Playwright Browsers", False, "Need installation")
        except Exception as e:
            self.log_test("Playwright Browsers", False, f"Error: {e}")
            
    def test_network_connectivity(self):
        """Test network connectivity to trading platform"""
        try:
            import requests
            response = requests.get('https://bulenox.projectx.com', timeout=10)
            if response.status_code == 200:
                self.log_test("Network Connectivity", True, "Can reach trading platform")
            else:
                self.log_test("Network Connectivity", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Network Connectivity", False, f"Error: {e}")
            
    def test_log_directories(self):
        """Test if log directories can be created"""
        log_dirs = ['logs', 'logs/errors', 'logs/updates', 'logs/session', 'logs/trades']
        
        for log_dir in log_dirs:
            try:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
                if Path(log_dir).exists():
                    self.log_test(f"Log Directory {log_dir}", True, "Created/Exists")
                else:
                    self.log_test(f"Log Directory {log_dir}", False, "Cannot create")
            except Exception as e:
                self.log_test(f"Log Directory {log_dir}", False, f"Error: {e}")
                
    def test_script_permissions(self):
        """Test if scripts have proper permissions (Unix/Linux)"""
        if os.name != 'nt':  # Not Windows
            script_files = ['live_trading_unified.sh']
            
            for script in script_files:
                if Path(script).exists():
                    # Check if executable
                    if os.access(script, os.X_OK):
                        self.log_test(f"Script Permissions {script}", True, "Executable")
                    else:
                        self.log_test(f"Script Permissions {script}", False, "Not executable")
                        # Try to make executable
                        try:
                            os.chmod(script, 0o755)
                            self.log_test(f"Script Permissions {script} (Fixed)", True, "Made executable")
                        except Exception as e:
                            self.log_test(f"Script Permissions {script} (Fix)", False, f"Cannot fix: {e}")
        else:
            self.log_test("Script Permissions", True, "Windows - N/A")
            
    def test_git_repository(self):
        """Test if this is a git repository and can pull updates"""
        try:
            # Check if .git exists
            if Path('.git').exists():
                self.log_test("Git Repository", True, "Is a git repository")
                
                # Test git commands
                result = subprocess.run(['git', 'status'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log_test("Git Status", True, "Git working")
                else:
                    self.log_test("Git Status", False, "Git command failed")
            else:
                self.log_test("Git Repository", False, "Not a git repository")
        except Exception as e:
            self.log_test("Git Repository", False, f"Error: {e}")
            
    def test_monitor_mode_dry_run(self):
        """Test monitor mode with dry run (no actual login)"""
        try:
            # Create a simple test to see if the script can be imported
            test_code = """
import sys
sys.path.append('.')
try:
    from tradebot_sentinel_advanced_pro import TradeBotSentinelPro
    bot = TradeBotSentinelPro(headless=True, monitor_mode=True)
    print("SUCCESS: Bot can be instantiated")
except Exception as e:
    print(f"ERROR: {e}")
"""
            
            result = subprocess.run([sys.executable, '-c', test_code], 
                                  capture_output=True, text=True, timeout=30)
            
            if "SUCCESS" in result.stdout:
                self.log_test("Monitor Mode Dry Run", True, "Bot can be instantiated")
            else:
                self.log_test("Monitor Mode Dry Run", False, f"Error: {result.stderr}")
                
        except Exception as e:
            self.log_test("Monitor Mode Dry Run", False, f"Error: {e}")
            
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("UNIFIED LAUNCHER SYSTEM - COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Test started at: {self.start_time}")
        print()
        
        # Run all tests
        self.test_environment_variables()
        self.test_file_existence()
        self.test_python_dependencies()
        self.test_playwright_browsers()
        self.test_network_connectivity()
        self.test_log_directories()
        self.test_script_permissions()
        self.test_git_repository()
        self.test_monitor_mode_dry_run()
        
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate test summary"""
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['status'] == 'PASS')
        failed = sum(1 for result in self.test_results if result['status'] == 'FAIL')
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        print(f"Test Duration: {duration.total_seconds():.1f} seconds")
        
        # Show failed tests
        if failed > 0:
            print()
            print("FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"❌ {result['test']}: {result['message']}")
        
        # Show recommendations
        print()
        print("RECOMMENDATIONS:")
        print("-" * 40)
        
        if failed == 0:
            print("✅ All tests passed! The unified launcher system is ready to use.")
            print("✅ You can now run the launcher with confidence.")
        else:
            print("⚠️  Some tests failed. Please address the issues above before running the launcher.")
            
            # Specific recommendations
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    test_name = result['test']
                    if 'Environment Variable' in test_name:
                        print(f"💡 Set {test_name.split()[-1]} environment variable")
                    elif 'Python Package' in test_name:
                        package = test_name.split()[-1]
                        print(f"💡 Install missing package: pip install {package}")
                    elif 'Playwright Browsers' in test_name:
                        print(f"💡 Install Playwright browsers: playwright install")
                    elif 'Network Connectivity' in test_name:
                        print(f"💡 Check your internet connection")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'success_rate': (passed/total)*100,
                    'duration_seconds': duration.total_seconds(),
                    'start_time': self.start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        if failed == 0:
            print("\n🚀 Ready to launch! Run the unified launcher:")
            if os.name == 'nt':
                print("   .\\live_trading_unified.ps1")
            else:
                print("   ./live_trading_unified.sh")

def main():
    tester = UnifiedSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()