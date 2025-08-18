#!/usr/bin/env python3

def fix_unterminated_fstrings(filename):
    """Fix unterminated f-strings in the file"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the first f-string issue around line 917-922
    # The f-string starts with f""" but the """ at line 922 is inside the string, not closing it
    content = content.replace(
        'print(python_code)\n"""\n            ], capture_output=True, text=True)',
        'print(python_code)\n"""\n            ], capture_output=True, text=True)'
    )
    
    # Fix the second f-string issue around line 1288-1293
    # Same issue - f-string starts but never properly closes
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for the pattern of unterminated f-strings
        if 'f"""' in line and 'import curlconverter' in lines[i+1] if i+1 < len(lines) else False:
            # This is the start of an f-string
            fixed_lines.append(line)
            i += 1
            
            # Copy lines until we find the print(python_code) line
            while i < len(lines) and 'print(python_code)' not in lines[i]:
                fixed_lines.append(lines[i])
                i += 1
            
            # Add the print line
            if i < len(lines):
                fixed_lines.append(lines[i])
                i += 1
            
            # Check if the next line has the closing """ followed by ]
            if i < len(lines) and lines[i].strip() == '"""' and i+1 < len(lines) and '], capture_output=True, text=True)' in lines[i+1]:
                # This is correct, add both lines
                fixed_lines.append(lines[i])  # the """ line
                i += 1
                fixed_lines.append(lines[i])  # the ] line
                i += 1
            elif i < len(lines) and '], capture_output=True, text=True)' in lines[i]:
                # Missing the closing """, add it
                fixed_lines.append('"""')
                fixed_lines.append(lines[i])  # the ] line
                i += 1
            else:
                # Continue normally
                if i < len(lines):
                    fixed_lines.append(lines[i])
                    i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    # Write back the fixed content
    fixed_content = '\n'.join(fixed_lines)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("File has been fixed!")

if __name__ == "__main__":
    fix_unterminated_fstrings("tradebot_sentinel_playwright.py")