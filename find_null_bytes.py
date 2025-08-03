#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Null Byte Detector and Fixer for AI Trading Sentinel

This script scans Python files for null bytes (\x00) which can cause issues
with various tools and libraries. It can also fix these files by removing
the null bytes and creating backups of the original files.
"""

import os
import sys
import argparse
from pathlib import Path
import shutil

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
NC = '\033[0m'  # No Color

def print_colored(text, color):
    """Print colored text if supported by the terminal"""
    if sys.platform == 'win32':
        # Windows may not support ANSI colors in all terminals
        print(text)
    else:
        print(f"{color}{text}{NC}")

def contains_null_bytes(file_path):
    """Check if a file contains null bytes"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            return b'\x00' in content
    except Exception as e:
        print_colored(f"Error reading file: {file_path} - {str(e)}", RED)
        return False

def remove_null_bytes(file_path):
    """Remove null bytes from a file and create a backup"""
    try:
        # Create backup
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Remove null bytes
        new_content = content.replace(b'\x00', b'')
        
        # Write cleaned content back
        with open(file_path, 'wb') as f:
            f.write(new_content)
        
        print_colored(f"Fixed file: {file_path} (Backup created at {backup_path})", GREEN)
        return True
    except Exception as e:
        print_colored(f"Error fixing file: {file_path} - {str(e)}", RED)
        return False

def find_python_files(directory, exclude_dirs=None):
    """Find all Python files in a directory, excluding specified directories"""
    if exclude_dirs is None:
        exclude_dirs = ['venv', '.git', '__pycache__', 'node_modules']
    
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    parser = argparse.ArgumentParser(description='Find and fix null bytes in Python files')
    parser.add_argument('--fix', action='store_true', help='Fix files with null bytes')
    parser.add_argument('--dir', type=str, default='.', help='Directory to scan (default: current directory)')
    args = parser.parse_args()
    
    print_colored("=== AI Trading Sentinel - Null Byte Detector ===", BLUE)
    print_colored("This script will find files with null bytes that can cause issues", YELLOW)
    print()
    
    # Step 1: Find Python files
    print_colored("[1/3] Scanning for Python files...", BLUE)
    python_files = find_python_files(args.dir)
    print_colored(f"Found {len(python_files)} Python files to check", GREEN)
    
    # Step 2: Check for null bytes
    print_colored("[2/3] Checking for null bytes...", BLUE)
    files_with_null_bytes = []
    
    for file_path in python_files:
        if contains_null_bytes(file_path):
            files_with_null_bytes.append(file_path)
            print_colored(f" ❌ Found null bytes in: {file_path}", YELLOW)
    
    # Step 3: Show results and fix if requested
    print()
    print_colored("[3/3] Results:", BLUE)
    
    if not files_with_null_bytes:
        print_colored(" ✅ No files with null bytes found!", GREEN)
    else:
        print_colored(f"Found {len(files_with_null_bytes)} files with null bytes:", YELLOW)
        for file_path in files_with_null_bytes:
            print(f"   - {file_path}")
        
        fix_files = args.fix
        if not fix_files:
            print()
            response = input("Do you want to fix these files? (y/n): ")
            fix_files = response.lower() in ['y', 'yes']
        
        if fix_files:
            fixed_count = 0
            for file_path in files_with_null_bytes:
                if remove_null_bytes(file_path):
                    fixed_count += 1
            
            print()
            print_colored(f"Fixed {fixed_count} out of {len(files_with_null_bytes)} files", GREEN)
            print_colored("Backups were created with .backup extension", YELLOW)
        else:
            print_colored("No files were modified", YELLOW)
    
    print()
    print_colored("=== Scan Complete ===", BLUE)

if __name__ == "__main__":
    main()