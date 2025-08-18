#!/usr/bin/env python3
"""
TradeBot Sentinel - cURL to Python Converter
Converts saved cURL commands to Python requests code
"""

import os
import sys
from curlconverter import CurlConverter

def convert_curl_to_python(curl_file_path, output_file_path):
    """
    Convert cURL command from file to Python requests code
    """
    try:
        # Read the cURL command from file
        with open(curl_file_path, 'r', encoding='utf-8') as f:
            curl_command = f.read().strip()
        
        print(f"📄 Reading cURL from: {curl_file_path}")
        print(f"🔄 Converting to Python...")
        
        # Convert to Python
        converter = CurlConverter(curl_command)
        python_code = converter.convert()
        
        # Add imports and formatting
        full_python_code = f'''#!/usr/bin/env python3
"""
TradeBot Sentinel - Generated Trade Request
Auto-generated from captured cURL command
"""

import requests
import json

def execute_trade_request():
    """
    Execute the captured trade request
    """
    try:
{python_code}
        
        print(f"✅ Request executed successfully!")
        print(f"📊 Status Code: {{response.status_code}}")
        print(f"📋 Response: {{response.text[:500]}}...")
        
        return response
    
    except Exception as e:
        print(f"❌ Error executing request: {{e}}")
        return None

if __name__ == "__main__":
    print("🤖 TradeBot Sentinel - Trade Request Executor")
    print("=" * 50)
    response = execute_trade_request()
'''
        
        # Save to output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(full_python_code)
        
        print(f"✅ Python code saved to: {output_file_path}")
        print(f"📝 Code preview:")
        print("-" * 50)
        print(python_code[:300] + "..." if len(python_code) > 300 else python_code)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting cURL to Python: {e}")
        return False

if __name__ == "__main__":
    curl_file = "trade.sh"
    python_file = "trade_request_full.py"
    
    if os.path.exists(curl_file):
        print(f"🤖 TradeBot Sentinel - cURL to Python Converter")
        print("=" * 50)
        success = convert_curl_to_python(curl_file, python_file)
        
        if success:
            print(f"\n🎯 Conversion completed successfully!")
            print(f"📁 Files created:")
            print(f"   - cURL: {curl_file}")
            print(f"   - Python: {python_file}")
        else:
            print(f"\n❌ Conversion failed!")
            sys.exit(1)
    else:
        print(f"❌ cURL file not found: {curl_file}")
        print(f"💡 Make sure to run the network interceptor first to capture requests.")
        sys.exit(1)