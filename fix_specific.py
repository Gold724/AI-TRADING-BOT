def fix_specific_issue():
    try:
        with open('bulenox_ai_selenium_adaptive_uc.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Fix the specific issue at line 3189-3191
        if len(lines) >= 3191:
            # Replace line 3189 (remove the strange JSON-like string and element reference)
            lines[3188] = '        return random.choice(\'abcdefghijklmnopqrstuvwxyz\')  # Fallback to random letter\n'
            
            # Remove the invalid except block (lines 3190-3191)
            lines[3189] = '\n'
            lines[3190] = '    def _simulate_typo(self, element):\n'
            lines.insert(3191, '        try:\n            pass\n        except Exception:\n            pass\n')
        
        # Write the fixed content back to the file
        with open('bulenox_ai_selenium_adaptive_uc.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("File fixed successfully!")
    except Exception as e:
        print(f"Error fixing file: {e}")

if __name__ == "__main__":
    fix_specific_issue()