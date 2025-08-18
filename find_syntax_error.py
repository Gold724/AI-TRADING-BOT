#!/usr/bin/env python3

import ast
import sys

def find_syntax_error(filename):
    """Find the exact location of syntax errors in a Python file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        print(f"✅ No syntax errors found in {filename}")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error in {filename}:")
        print(f"   Line {e.lineno}: {e.text.strip() if e.text else 'N/A'}")
        print(f"   Error: {e.msg}")
        
        # Show context around the error
        lines = content.split('\n')
        start = max(0, e.lineno - 5)
        end = min(len(lines), e.lineno + 5)
        
        print(f"\n📍 Context around line {e.lineno}:")
        for i in range(start, end):
            marker = ">>> " if i + 1 == e.lineno else "    "
            print(f"{marker}{i+1:4d}: {lines[i]}")
        
        return False
    
    except Exception as e:
        print(f"❌ Error reading file {filename}: {e}")
        return False

if __name__ == "__main__":
    filename = "tradebot_sentinel_playwright.py"
    find_syntax_error(filename)