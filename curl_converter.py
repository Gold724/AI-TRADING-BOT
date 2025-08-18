#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cURL Command Generator and Python Requests Converter for TradeBot Sentinel

This module provides functionality to generate cURL commands from intercepted
network requests and convert them to Python requests code using curlconverter.

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import json
import logging
import subprocess
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import re
from urllib.parse import urlparse, parse_qs

class CurlConverter:
    """Handles cURL command generation and Python requests conversion."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the cURL converter.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._ensure_curlconverter()
    
    def _ensure_curlconverter(self) -> None:
        """Ensure curlconverter package is installed."""
        try:
            import curlconverter
            self.logger.debug("curlconverter package is available")
        except ImportError:
            self.logger.info("Installing curlconverter package...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'curlconverter'])
                self.logger.info("curlconverter package installed successfully")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to install curlconverter: {e}")
                raise
    
    def generate_curl_command(self, request_data: Dict[str, Any]) -> str:
        """Generate a cURL command from request data.
        
        Args:
            request_data: Dictionary containing request information
            
        Returns:
            cURL command as string
        """
        try:
            url = request_data.get('url', '')
            method = request_data.get('method', 'GET')
            headers = request_data.get('headers', {})
            post_data = request_data.get('post_data', '')
            
            # Build cURL command parts
            curl_parts = ['curl']
            
            # Add method if not GET
            if method.upper() != 'GET':
                curl_parts.append(f'-X {method.upper()}')
            
            # Add headers
            for header_name, header_value in headers.items():
                # Skip headers that curl adds automatically or are problematic
                skip_headers = [
                    'content-length', 'host', 'connection', 'accept-encoding',
                    'user-agent'  # We'll add a custom user-agent
                ]
                
                if header_name.lower() not in skip_headers:
                    # Escape quotes in header values
                    escaped_value = str(header_value).replace('"', '\\"')
                    curl_parts.append(f'-H "{header_name}: {escaped_value}"')
            
            # Add a user-agent
            curl_parts.append('-H "User-Agent: TradeBot-Sentinel/1.0"')
            
            # Add POST data if present
            if post_data:
                # Try to format JSON data nicely
                try:
                    json_data = json.loads(post_data)
                    formatted_data = json.dumps(json_data, separators=(',', ':'))
                    escaped_data = formatted_data.replace('"', '\\"')
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, escape as-is
                    escaped_data = str(post_data).replace('"', '\\"')
                
                curl_parts.append(f'-d "{escaped_data}"')
            
            # Add URL (always last)
            curl_parts.append(f'"{url}"')
            
            # Join with line continuations for readability
            curl_command = ' \\
  '.join(curl_parts)
            
            self.logger.debug(f"Generated cURL command: {len(curl_command)} characters")
            return curl_command
            
        except Exception as e:
            self.logger.error(f"Error generating cURL command: {e}")
            return ""
    
    def save_curl_to_file(self, curl_command: str, filename: str = "trade.sh", 
                         request_data: Optional[Dict[str, Any]] = None) -> bool:
        """Save cURL command to a shell script file.
        
        Args:
            curl_command: The cURL command to save
            filename: Output filename
            request_data: Optional request data for metadata
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8', newline='\n') as f:
                f.write('#!/bin/bash\n')
                f.write('# Generated cURL command for trade execution\n')
                f.write('# Created by TradeBot Sentinel\n')
                
                if request_data:
                    f.write(f'# Timestamp: {time.ctime(request_data.get("timestamp", time.time()))}\n')
                    f.write(f'# Method: {request_data.get("method", "Unknown")}\n')
                    f.write(f'# URL: {request_data.get("url", "Unknown")}\n')
                
                f.write('\n')
                f.write('# Execute the trade request\n')
                f.write(curl_command)
                f.write('\n')
            
            # Make the file executable on Unix-like systems
            try:
                import stat
                Path(filename).chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass  # Windows or permission issues
            
            self.logger.info(f"cURL command saved to: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving cURL command to file: {e}")
            return False
    
    def convert_curl_to_python(self, curl_command: str) -> str:
        """Convert cURL command to Python requests code.
        
        Args:
            curl_command: cURL command string
            
        Returns:
            Python requests code as string
        """
        try:
            import curlconverter
            
            # Convert cURL to Python requests
            python_code = curlconverter.to_python(curl_command)
            
            # Add some enhancements to the generated code
            enhanced_code = self._enhance_python_code(python_code)
            
            self.logger.debug("Successfully converted cURL to Python requests")
            return enhanced_code
            
        except ImportError:
            self.logger.error("curlconverter package not available")
            return self._generate_fallback_python_code(curl_command)
        except Exception as e:
            self.logger.error(f"Error converting cURL to Python: {e}")
            return self._generate_fallback_python_code(curl_command)
    
    def _enhance_python_code(self, python_code: str) -> str:
        """Enhance the generated Python code with additional features.
        
        Args:
            python_code: Original Python code from curlconverter
            
        Returns:
            Enhanced Python code
        """
        try:
            # Add header comment
            header = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generated Python Requests Code for Trade Execution
Created by TradeBot Sentinel

This code replicates the intercepted trade request using Python requests.
"""

'''
            
            # Add imports if not present
            imports = '''import requests
import json
import time
from typing import Dict, Any, Optional

'''
            
            # Add error handling wrapper
            wrapper_start = '''def execute_trade_request(timeout: int = 30, retries: int = 3) -> Optional[Dict[str, Any]]:
    """Execute the trade request with error handling and retries.
    
    Args:
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        
    Returns:
        Response data if successful, None otherwise
    """
    for attempt in range(retries):
        try:
            print(f"Executing trade request (attempt {attempt + 1}/{retries})...")
            
'''
            
            wrapper_end = '''
            
            # Check response
            if response.status_code == 200:
                print(f"✅ Trade request successful: {response.status_code}")
                try:
                    return response.json()
                except:
                    return {"status": "success", "text": response.text}
            else:
                print(f"❌ Trade request failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return None

if __name__ == "__main__":
    # Execute the trade request
    result = execute_trade_request()
    if result:
        print("Trade executed successfully!")
        print(json.dumps(result, indent=2))
    else:
        print("Trade execution failed!")
'''
            
            # Indent the original code
            indented_code = '\n'.join('    ' + line if line.strip() else line 
                                    for line in python_code.split('\n'))
            
            # Combine all parts
            enhanced = header + imports + wrapper_start + indented_code + wrapper_end
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Error enhancing Python code: {e}")
            return python_code
    
    def _generate_fallback_python_code(self, curl_command: str) -> str:
        """Generate basic Python requests code as fallback.
        
        Args:
            curl_command: cURL command string
            
        Returns:
            Basic Python requests code
        """
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fallback Python Requests Code for Trade Execution
Created by TradeBot Sentinel

Original cURL command:
{curl_command}
"""

import requests
import json

def execute_trade_request():
    """Execute the trade request - MANUAL IMPLEMENTATION REQUIRED.
    
    Please manually convert the cURL command above to Python requests.
    """
    print("Manual implementation required!")
    print("Original cURL command:")
    print("{curl_command}")
    
    # TODO: Implement the actual request
    # Example:
    # response = requests.post(
    #     url="YOUR_URL_HERE",
    #     headers={{"Content-Type": "application/json"}},
    #     json={{"your": "data"}}
    # )
    # return response.json()
    
    return None

if __name__ == "__main__":
    execute_trade_request()
'''
    
    def save_python_code_to_file(self, python_code: str, 
                                filename: str = "trade_request_full.py") -> bool:
        """Save Python requests code to a file.
        
        Args:
            python_code: Python code to save
            filename: Output filename
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8', newline='\n') as f:
                f.write(python_code)
            
            self.logger.info(f"Python requests code saved to: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving Python code to file: {e}")
            return False
    
    def process_trade_request(self, request_data: Dict[str, Any], 
                            curl_filename: str = "trade.sh",
                            python_filename: str = "trade_request_full.py") -> Dict[str, bool]:
        """Process a trade request: generate cURL and convert to Python.
        
        Args:
            request_data: Request data dictionary
            curl_filename: Output filename for cURL script
            python_filename: Output filename for Python script
            
        Returns:
            Dictionary with success status for each operation
        """
        results = {
            'curl_generated': False,
            'curl_saved': False,
            'python_converted': False,
            'python_saved': False
        }
        
        try:
            # Generate cURL command
            curl_command = self.generate_curl_command(request_data)
            if curl_command:
                results['curl_generated'] = True
                self.logger.info("✅ cURL command generated successfully")
                
                # Save cURL to file
                if self.save_curl_to_file(curl_command, curl_filename, request_data):
                    results['curl_saved'] = True
                    self.logger.info(f"✅ cURL saved to {curl_filename}")
                
                # Convert to Python
                python_code = self.convert_curl_to_python(curl_command)
                if python_code:
                    results['python_converted'] = True
                    self.logger.info("✅ Python requests code generated successfully")
                    
                    # Save Python code to file
                    if self.save_python_code_to_file(python_code, python_filename):
                        results['python_saved'] = True
                        self.logger.info(f"✅ Python code saved to {python_filename}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing trade request: {e}")
            return results
    
    def batch_process_requests(self, requests_list: List[Dict[str, Any]], 
                              output_dir: str = ".") -> List[Dict[str, Any]]:
        """Process multiple trade requests in batch.
        
        Args:
            requests_list: List of request data dictionaries
            output_dir: Output directory for generated files
            
        Returns:
            List of processing results
        """
        results = []
        
        for i, request_data in enumerate(requests_list):
            self.logger.info(f"Processing request {i + 1}/{len(requests_list)}...")
            
            # Generate unique filenames
            timestamp = int(request_data.get('timestamp', time.time()))
            curl_filename = f"{output_dir}/trade_{timestamp}.sh"
            python_filename = f"{output_dir}/trade_request_{timestamp}.py"
            
            # Process the request
            result = self.process_trade_request(
                request_data, curl_filename, python_filename
            )
            result['request_index'] = i
            result['timestamp'] = timestamp
            results.append(result)
        
        self.logger.info(f"Batch processing completed: {len(results)} requests processed")
        return results

def create_curl_converter(logger: Optional[logging.Logger] = None) -> CurlConverter:
    """Convenience function to create a CurlConverter instance.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        CurlConverter instance
    """
    return CurlConverter(logger)

if __name__ == "__main__":
    # Test the curl converter module
    print("cURL Converter module loaded successfully!")
    
    # Example usage
    converter = create_curl_converter()
    
    # Test with sample request data
    sample_request = {
        'timestamp': time.time(),
        'method': 'POST',
        'url': 'https://api.example.com/trade',
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123'
        },
        'post_data': json.dumps({
            'symbol': 'BTCUSD',
            'amount': 0.01,
            'side': 'buy',
            'orderType': 'market'
        })
    }
    
    print("\nTesting with sample request...")
    results = converter.process_trade_request(sample_request)
    print(f"Results: {results}")