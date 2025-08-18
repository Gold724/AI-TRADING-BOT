#!/usr/bin/env python3

# Fix the broken string literal in tradebot_sentinel_automation.py
with open('tradebot_sentinel_automation.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the broken multiline string with a proper single line
content = content.replace(
    "        return ' \\\\\\\\\n  '.join(curl_parts)",
    "        return ' \\\\\\\\\n  '.join(curl_parts)"
)

with open('tradebot_sentinel_automation.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed the string literal syntax error")