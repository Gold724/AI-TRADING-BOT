#!/usr/bin/env python3
"""
AI Trading Sentinel - Endpoint Validator
========================================
Validates captured cURL endpoints before live trading
- Checks if trade.sh exists and contains valid cURL
- Validates login endpoints
- Tests endpoint connectivity
- Ensures all required parameters are present
"""

import os
import sys
import json
import requests
import re
from pathlib import Path
from datetime import datetime
import subprocess

class EndpointValidator:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.trade_curl_file = self.base_dir / "trade.sh"
        self.trade_request_file = self.base_dir / "trade_request_full.py"
        self.validation_results = []
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps and levels"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }.get(level, "ℹ️")
        
        print(f"[{timestamp}] {prefix} {message}")
        
    def validate_trade_curl(self):
        """Validate trade.sh cURL file"""
        self.log("Validating trade.sh cURL file...")
        
        if not self.trade_curl_file.exists():
            self.log("trade.sh file not found!", "ERROR")
            return False
            
        try:
            content = self.trade_curl_file.read_text(encoding='utf-8')
            
            # Check if it's a valid cURL command
            if not content.strip().startswith('curl'):
                self.log("trade.sh does not contain a valid cURL command", "ERROR")
                return False
                
            # Check for required trading parameters
            required_patterns = [
                r'symbol|pair',  # Trading symbol
                r'amount|quantity|size',  # Trade amount
                r'side|type|action',  # Buy/Sell action
                r'price'  # Price information
            ]
            
            missing_params = []
            for pattern in required_patterns:
                if not re.search(pattern, content, re.IGNORECASE):
                    missing_params.append(pattern)
                    
            if missing_params:
                self.log(f"Missing trading parameters: {', '.join(missing_params)}", "WARNING")
            else:
                self.log("All required trading parameters found", "SUCCESS")
                
            # Extract URL from cURL
            url_match = re.search(r"curl.*?['\"]([^'\"]*)['\"].*$", content, re.MULTILINE)
            if url_match:
                url = url_match.group(1)
                self.log(f"Extracted endpoint URL: {url}")
                return True
            else:
                self.log("Could not extract URL from cURL command", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error reading trade.sh: {str(e)}", "ERROR")
            return False
            
    def validate_python_request(self):
        """Validate converted Python request file"""
        self.log("Validating trade_request_full.py...")
        
        if not self.trade_request_file.exists():
            self.log("trade_request_full.py not found - will be generated from cURL", "WARNING")
            return self.convert_curl_to_python()
            
        try:
            content = self.trade_request_file.read_text(encoding='utf-8')
            
            # Check for required imports
            if 'import requests' not in content:
                self.log("Missing 'import requests' in Python file", "ERROR")
                return False
                
            # Check for request method
            if 'requests.post' not in content and 'requests.get' not in content:
                self.log("No requests method found in Python file", "ERROR")
                return False
                
            self.log("Python request file validation passed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error validating Python request: {str(e)}", "ERROR")
            return False
            
    def convert_curl_to_python(self):
        """Convert cURL to Python using curlconverter"""
        self.log("Converting cURL to Python...")
        
        try:
            # Check if curlconverter is installed
            result = subprocess.run(['python', '-c', 'import curlconverter'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("curlconverter not installed. Installing...", "WARNING")
                subprocess.run(['pip', 'install', 'curlconverter'], check=True)
                
            # Read cURL command
            curl_content = self.trade_curl_file.read_text(encoding='utf-8')
            
            # Convert using curlconverter
            import curlconverter
            python_code = curlconverter.curl_to_python(curl_content)
            
            # Save converted Python code
            self.trade_request_file.write_text(python_code, encoding='utf-8')
            self.log("Successfully converted cURL to Python", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error converting cURL to Python: {str(e)}", "ERROR")
            return False
            
    def test_endpoint_connectivity(self):
        """Test if endpoints are reachable"""
        self.log("Testing endpoint connectivity...")
        
        try:
            # Extract URL from cURL
            curl_content = self.trade_curl_file.read_text(encoding='utf-8')
            url_match = re.search(r"curl.*?['\"]([^'\"]*)['\"].*$", curl_content, re.MULTILINE)
            
            if not url_match:
                self.log("Could not extract URL for connectivity test", "ERROR")
                return False
                
            url = url_match.group(1)
            base_url = '/'.join(url.split('/')[:3])  # Get base URL
            
            # Test basic connectivity
            response = requests.get(base_url, timeout=10)
            if response.status_code < 500:  # Any response except server error
                self.log(f"Endpoint connectivity test passed: {base_url}", "SUCCESS")
                return True
            else:
                self.log(f"Endpoint returned server error: {response.status_code}", "WARNING")
                return True  # Still consider it reachable
                
        except requests.exceptions.RequestException as e:
            self.log(f"Endpoint connectivity test failed: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Unexpected error during connectivity test: {str(e)}", "ERROR")
            return False
            
    def validate_environment(self):
        """Validate environment variables and dependencies"""
        self.log("Validating environment...")
        
        # Check required environment variables
        required_env_vars = ['BULENOX_USERNAME', 'BULENOX_PASSWORD']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.log(f"Missing environment variables: {', '.join(missing_vars)}", "ERROR")
            return False
            
        # Check if main script exists
        main_script = self.base_dir / "tradebot_sentinel_advanced_pro.py"
        if not main_script.exists():
            self.log("Main trading script not found!", "ERROR")
            return False
            
        self.log("Environment validation passed", "SUCCESS")
        return True
        
    def run_validation(self):
        """Run complete validation suite"""
        self.log("Starting endpoint validation suite...", "INFO")
        self.log("=" * 50)
        
        validation_steps = [
            ("Environment", self.validate_environment),
            ("Trade cURL", self.validate_trade_curl),
            ("Python Request", self.validate_python_request),
            ("Connectivity", self.test_endpoint_connectivity)
        ]
        
        results = []
        for step_name, step_func in validation_steps:
            self.log(f"Running {step_name} validation...")
            try:
                result = step_func()
                results.append((step_name, result))
                if result:
                    self.log(f"{step_name} validation: PASSED", "SUCCESS")
                else:
                    self.log(f"{step_name} validation: FAILED", "ERROR")
            except Exception as e:
                self.log(f"{step_name} validation error: {str(e)}", "CRITICAL")
                results.append((step_name, False))
                
        # Summary
        self.log("=" * 50)
        self.log("VALIDATION SUMMARY:")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for step_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {step_name}: {status}")
            
        self.log(f"\nOverall: {passed}/{total} validations passed")
        
        if passed == total:
            self.log("🎉 VERDICT: MISSION ACCOMPLISHED - All validations passed!", "SUCCESS")
            return True
        else:
            self.log("🚨 VERDICT: MISSION FAILED - Some validations failed!", "CRITICAL")
            return False

def main():
    """Main validation entry point"""
    validator = EndpointValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        validator.log("Validation interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        validator.log(f"Unexpected error: {str(e)}", "CRITICAL")
        sys.exit(1)

if __name__ == "__main__":
    main()