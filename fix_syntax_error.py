#!/usr/bin/env python3
"""
Fix syntax error in tradebot_sentinel.py
"""

def fix_syntax_error():
    file_path = 'tradebot_sentinel.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find and fix the problematic lines
        for i, line in enumerate(lines):
            if "curl_command = ' \\" in line and i + 1 < len(lines):
                # Check if next line is "'.join(curl_parts)"
                if "'.join(curl_parts)" in lines[i + 1]:
                    # Fix the broken string literal
                    lines[i] = "            curl_command = ' \\\\n'.join(curl_parts)\n"
                    lines[i + 1] = ""  # Remove the broken continuation line
                    break
        
        # Remove empty lines that were created
        lines = [line for line in lines if line.strip() != ""]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ Fixed syntax error in {file_path}")
        
        # Test compilation
        import py_compile
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"✅ {file_path} compiles successfully")
        except py_compile.PyCompileError as e:
            print(f"❌ Compilation error: {e}")
            
    except Exception as e:
        print(f"❌ Error fixing file: {e}")

if __name__ == '__main__':
    fix_syntax_error()