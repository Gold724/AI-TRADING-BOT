def check_line():
    try:
        with open('bulenox_ai_selenium_adaptive_uc.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Print the problematic line and surrounding context
        start_line = max(3185, 0)
        end_line = min(3195, len(lines))
        
        print(f"File has {len(lines)} lines total")
        print(f"Showing lines {start_line+1} to {end_line}:")
        
        for i in range(start_line, end_line):
            print(f"Line {i+1}: {repr(lines[i])}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_line()