#!/usr/bin/env python3

# Fix the syntax error in tradebot_sentinel_automation.py
with open('tradebot_sentinel_automation.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix line 177 (index 176)
for i, line in enumerate(lines):
    if i == 176 and "return ' \\" in line:
        # Replace the broken line with a proper single-line version
        lines[i] = "        return ' \\\\\\\\\n  '.join(curl_parts)\n"
        break

with open('tradebot_sentinel_automation.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed syntax error in tradebot_sentinel_automation.py")