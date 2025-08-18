#!/usr/bin/env python3

def find_unterminated_quotes(filename):
    """Find unterminated triple quotes in a Python file"""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    triple_quote_stack = []
    issues = []
    
    for i, line in enumerate(lines, 1):
        # Count triple quotes in this line
        line_content = line.rstrip()
        
        # Find all triple quote occurrences
        pos = 0
        while True:
            # Look for triple quotes
            double_pos = line_content.find('"""', pos)
            single_pos = line_content.find("'''", pos)
            
            # Find the next occurrence
            next_pos = -1
            quote_type = None
            
            if double_pos != -1 and (single_pos == -1 or double_pos < single_pos):
                next_pos = double_pos
                quote_type = '"""'
            elif single_pos != -1:
                next_pos = single_pos
                quote_type = "'''"
            
            if next_pos == -1:
                break
                
            # Check if this is inside a string or comment
            before_quote = line_content[:next_pos]
            
            # Simple check - if we have an odd number of single/double quotes before this,
            # we might be inside a string
            single_count = before_quote.count("'")
            double_count = before_quote.count('"')
            
            # Skip if we're likely inside a string
            if (quote_type == '"""' and double_count % 2 == 1) or \
               (quote_type == "'''" and single_count % 2 == 1):
                pos = next_pos + 3
                continue
            
            # Check if this opens or closes a triple quote
            if triple_quote_stack and triple_quote_stack[-1][1] == quote_type:
                # This closes the last opened triple quote
                opened = triple_quote_stack.pop()
                print(f"✅ Closed {quote_type} at line {i} (opened at line {opened[0]})")
            else:
                # This opens a new triple quote
                triple_quote_stack.append((i, quote_type))
                print(f"📖 Opened {quote_type} at line {i}: {line_content.strip()}")
            
            pos = next_pos + 3
    
    # Check for unterminated quotes
    if triple_quote_stack:
        print(f"\n❌ Found {len(triple_quote_stack)} unterminated triple quote(s):")
        for line_num, quote_type in triple_quote_stack:
            print(f"   Line {line_num}: {quote_type} - {lines[line_num-1].strip()}")
            
            # Show context
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 3)
            print(f"   Context:")
            for j in range(start, end):
                marker = ">>> " if j + 1 == line_num else "    "
                print(f"   {marker}{j+1:4d}: {lines[j].rstrip()}")
            print()
        return False
    else:
        print("\n✅ All triple quotes are properly matched!")
        return True

if __name__ == "__main__":
    find_unterminated_quotes("tradebot_sentinel_playwright.py")