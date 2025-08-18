#!/usr/bin/env python3
"""
CURL to Python Requests Converter
Converts saved cURL commands to Python requests code
"""

import re
import json
import os
import sys

def convert_curl_to_python():
    """Convert cURL command from trade.sh to Python requests code"""
    
    if not os.path.exists('trade.sh'):
        print("[ERROR] trade.sh file not found")
        return False
    
    try:
        with open('trade.sh', 'r', encoding='utf-8') as f:
            curl_command = f.read().strip()
        
        print(f"[INFO] Processing cURL command: {curl_command[:100]}...")
        
        # Extract URL
        url_match = re.search(r"curl\s+(?:-X\s+POST\s+)?['\"]([^'\"]+)['\"]|curl\s+(?:-X\s+POST\s+)?([^\s]+)", curl_command)
        if not url_match:
            print("[ERROR] Could not extract URL from cURL command")
            return False
        
        url = url_match.group(1) or url_match.group(2)
        print(f"[INFO] Extracted URL: {url}")
        
        # Extract headers
        headers = {}
        header_matches = re.findall(r"-H\s+['\"]([^'\"]+)['\"]|--header\s+['\"]([^'\"]+)['\"]", curl_command)
        
        for match in header_matches:
            header = match[0] or match[1]
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
        
        print(f"[INFO] Extracted {len(headers)} headers")
        
        # Extract data - try multiple patterns
        data = None
        data_patterns = [
            r"--data-raw\s+['\"]([^'\"]*(?:[^\\]['\"]|\\.['\"])*)['\"]?",
            r"--data\s+['\"]([^'\"]*(?:[^\\]['\"]|\\.['\"])*)['\"]?",
            r"-d\s+['\"]([^'\"]*(?:[^\\]['\"]|\\.['\"])*)['\"]?"
        ]
        
        for pattern in data_patterns:
            data_match = re.search(pattern, curl_command, re.DOTALL)
            if data_match:
                data = data_match.group(1)
                break
        
        if data:
            print(f"[INFO] Extracted data: {len(data)} characters")
        else:
            print("[INFO] No POST data found")
            data = ""
        
        # Generate Python code using safe string handling
        python_code = generate_python_code(url, headers, data)
        
        # Save to files
        output_files = ['bulenox_trade_api.py', 'trade_request_full.py']
        
        for filename in output_files:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(python_code)
            print(f"[SUCCESS] Python code saved to {filename}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to convert cURL: {e}")
        return False

def generate_python_code(url, headers, data):
    """Generate clean Python requests code"""
    
    # Format headers for Python dict
    headers_lines = []
    for key, value in headers.items():
        headers_lines.append(f'    "{key}": "{value}",')
    headers_str = '\n'.join(headers_lines)
    
    # Handle data safely
    if data:
        # Try to parse as JSON first
        try:
            json_data = json.loads(data)
            data_section = f"""# JSON data
data = {json.dumps(json_data, indent=4)}

response = requests.post(url, headers=headers, json=data)"""
        except json.JSONDecodeError:
            # Fallback to raw string data
            data_section = f"""# Raw data
data = {repr(data)}

response = requests.post(url, headers=headers, data=data)"""
    else:
        data_section = "response = requests.post(url, headers=headers)"
    
    python_code = f"""#!/usr/bin/env python3
\"\"\"
Bulenox Trading API Request
Generated from cURL command
\"\"\"

import requests
import json

# API endpoint
url = "{url}"

# Request headers
headers = {{
{headers_str}
}}

{data_section}

# Execute request
try:
    print(f"Making request to: {{url}}")
    print(f"Status Code: {{response.status_code}}")
    print(f"Response Headers: {{dict(response.headers)}}")
    print(f"Response Body: {{response.text}}")
    
    if response.status_code == 200:
        print("[SUCCESS] Request completed successfully")
    else:
        print(f"[WARNING] Request returned status code: {{response.status_code}}")
        
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed: {{e}}")
except Exception as e:
    print(f"[ERROR] Unexpected error: {{e}}")
"""
    
    return python_code

if __name__ == "__main__":
    print("[INFO] Starting cURL to Python conversion...")
    success = convert_curl_to_python()
    if success:
        print("[SUCCESS] Conversion completed successfully")
    else:
        print("[ERROR] Conversion failed")
        sys.exit(1)