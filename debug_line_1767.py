#!/usr/bin/env python3

def debug_line_1767():
    """Debug the specific line 1767 issue"""
    with open('tradebot_sentinel_playwright.py', 'rb') as f:
        content = f.read()
    
    # Convert to string and split into lines
    text = content.decode('utf-8')
    lines = text.split('\n')
    
    # Check lines around 1767
    for i in range(1764, min(1774, len(lines))):
        line = lines[i]
        print(f"Line {i+1}: {repr(line)}")
        
        # Check for triple quotes
        if '"""' in line:
            print(f"  -> Contains triple quotes at positions: {[j for j, c in enumerate(line) if line[j:j+3] == '\"\"\"']}")
    
    # Now let's fix it by replacing the problematic line
    print("\n🔧 Fixing the issue...")
    
    # Replace line 1767 (index 1766)
    if len(lines) > 1766:
        old_line = lines[1766]
        print(f"Old line 1767: {repr(old_line)}")
        
        # Create a clean docstring line
        lines[1766] = '    """Main entry point"""'
        print(f"New line 1767: {repr(lines[1766])}")
        
        # Write back to file
        new_content = '\n'.join(lines)
        with open('tradebot_sentinel_playwright.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ File updated!")
    else:
        print("❌ Line 1767 not found!")

if __name__ == "__main__":
    debug_line_1767()