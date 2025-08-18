def fix_file():
    try:
        # Let's directly modify the line with the indentation error
        with open('bulenox_ai_selenium_adaptive_uc.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find line 3190 (1-indexed)
        if len(lines) >= 3190:
            # Check if this is the problematic line
            if 'except Exception:' in lines[3189]:
                # Fix the indentation
                lines[3189] = '        except Exception:\n'
                if len(lines) > 3190 and 'pass' in lines[3190]:
                    lines[3190] = '            pass\n'
        
        # Write the fixed content back to the file
        with open('bulenox_ai_selenium_adaptive_uc.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("File fixed successfully!")
    except Exception as e:
        print(f"Error fixing file: {e}")

if __name__ == "__main__":
    fix_file()