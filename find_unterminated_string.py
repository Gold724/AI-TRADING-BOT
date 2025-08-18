#!/usr/bin/env python3

def find_unterminated_strings(filename):
    """Find unterminated triple-quoted strings in a Python file"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Track triple quote state
    in_triple_quote = False
    quote_type = None
    start_line = None
    
    for i, line in enumerate(lines, 1):
        # Count triple quotes in this line
        double_quotes = line.count('"""')
        single_quotes = line.count("'''")
        
        # Process double quotes
        if double_quotes > 0:
            if not in_triple_quote:
                # Not in a triple quote, check if we're starting one
                if double_quotes % 2 == 1:  # Odd number means we start
                    in_triple_quote = True
                    quote_type = '"""'
                    start_line = i
                    print(f"Line {i}: Starting triple quote: {line.strip()[:100]}...")
            else:
                # We're in a triple quote
                if quote_type == '"""':
                    if double_quotes % 2 == 1:  # Odd number means we end
                        in_triple_quote = False
                        quote_type = None
                        print(f"Line {i}: Ending triple quote: {line.strip()[:100]}...")
                        start_line = None
        
        # Process single quotes
        if single_quotes > 0:
            if not in_triple_quote:
                # Not in a triple quote, check if we're starting one
                if single_quotes % 2 == 1:  # Odd number means we start
                    in_triple_quote = True
                    quote_type = "'''"
                    start_line = i
                    print(f"Line {i}: Starting triple quote: {line.strip()[:100]}...")
            else:
                # We're in a triple quote
                if quote_type == "'''":
                    if single_quotes % 2 == 1:  # Odd number means we end
                        in_triple_quote = False
                        quote_type = None
                        print(f"Line {i}: Ending triple quote: {line.strip()[:100]}...")
                        start_line = None
    
    if in_triple_quote:
        print(f"\n❌ UNTERMINATED TRIPLE QUOTE FOUND!")
        print(f"Started at line {start_line} with quote type: {quote_type}")
        print(f"File ends while still in triple quote")
        
        # Show context around the problematic line
        print(f"\nContext around line {start_line}:")
        start_context = max(1, start_line - 3)
        end_context = min(len(lines), start_line + 10)
        for j in range(start_context, end_context + 1):
            marker = ">>> " if j == start_line else "    "
            print(f"{marker}Line {j}: {lines[j-1]}")
        
        return start_line
    else:
        print(f"\n✅ All triple quotes are properly terminated")
        return None

if __name__ == "__main__":
    result = find_unterminated_strings("tradebot_sentinel_playwright.py")
    if result:
        print(f"\nCheck line {result} and surrounding lines for the unterminated string.")