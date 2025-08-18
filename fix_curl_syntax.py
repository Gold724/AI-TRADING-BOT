#!/usr/bin/env python3
"""
Fix syntax error in cURL command generation across all files
"""

import os
import re

def fix_curl_syntax_error(file_path):
    """Fix the unterminated string literal in cURL command generation"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the problematic pattern
        pattern = r"curl_command = ' \\\n  '\.join\(curl_parts\)"
        replacement = "curl_command = ' \\\\n  '.join(curl_parts)"
        
        if pattern in content:
            print(f"Fixing syntax error in {file_path}")
            content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {file_path}")
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
    return False

def main():
    """Fix syntax errors in all affected files"""
    files_to_fix = [
        'tradebot_sentinel_final.py',
        'request_interceptor.py',
        'tradebot_sentinel_stealth.py',
        'restore_from_git.py',
        'tradebot_sentinel_advanced_pro.py',
        'curl_converter.py',
        'vps_deployment/trading_scripts/tradebot_sentinel_advanced_pro.py'
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_curl_syntax_error(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()