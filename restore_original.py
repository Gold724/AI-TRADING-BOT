#!/usr/bin/env python3

def restore_original_file():
    """Restore the original file by removing duplicated content"""
    with open('tradebot_sentinel_playwright.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Find where the duplication starts by looking for the main function again
    main_function_lines = []
    for i, line in enumerate(lines):
        if 'async def main():' in line:
            main_function_lines.append(i + 1)  # 1-indexed
    
    print(f"Found 'async def main():' at lines: {main_function_lines}")
    
    if len(main_function_lines) > 1:
        # Take only the first half of the file (up to the first duplication)
        split_point = main_function_lines[1] - 1  # 0-indexed
        original_lines = lines[:split_point]
        
        print(f"Splitting at line {split_point}, keeping first {len(original_lines)} lines")
        
        # Write the restored content
        restored_content = '\n'.join(original_lines)
        with open('tradebot_sentinel_playwright.py', 'w', encoding='utf-8') as f:
            f.write(restored_content)
        
        print("✅ File restored to original size!")
        
        # Verify the restoration
        with open('tradebot_sentinel_playwright.py', 'r', encoding='utf-8') as f:
            new_lines = f.readlines()
        print(f"New file has {len(new_lines)} lines")
    else:
        print("❌ No duplication detected")

if __name__ == "__main__":
    restore_original_file()