#!/usr/bin/env python3

def fix_docstring_issue():
    """Fix the docstring issue at line 1767"""
    with open('tradebot_sentinel_playwright.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find line 1767 and fix it
    for i, line in enumerate(lines):
        if i == 1766:  # Line 1767 (0-indexed)
            print(f"Original line {i+1}: {repr(line)}")
            # Replace with a clean docstring
            lines[i] = '    """Main entry point"""\n'
            print(f"Fixed line {i+1}: {repr(lines[i])}")
            break
    
    # Write the fixed content back
    with open('tradebot_sentinel_playwright.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fixed the docstring issue!")

if __name__ == "__main__":
    fix_docstring_issue()