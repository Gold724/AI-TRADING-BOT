import os
import ast
import autopep8
from pathlib import Path

# ✅ Set this to your actual project path (edit this line only)
PROJECT_DIR = Path("C:/Users/Admin/Downloads/ai-trading-sentinel")

# Track files that were modified or had issues
fixed_files = []

def analyze_and_fix_python_files(base_dir: Path):
    for filepath in base_dir.rglob("*.py"):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                original_code = file.read()

            # Check for syntax validity
            syntax_ok = True
            try:
                ast.parse(original_code)
            except SyntaxError as e:
                print(f"[❌ SYNTAX ERROR] {filepath}: {e}")
                syntax_ok = False

            # Auto-format with autopep8
            fixed_code = autopep8.fix_code(original_code)

            if fixed_code != original_code or not syntax_ok:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(fixed_code)
                fixed_files.append(str(filepath))

        except Exception as e:
            print(f"[⚠️ ERROR] Could not process {filepath}: {e}")

    print(f"\n✅ Completed. Fixed {len(fixed_files)} file(s).")
    if fixed_files:
        for f in fixed_files:
            print(f" - {f}")
    else:
        print("No issues found.")

# Main entry point
if __name__ == "__main__":
    if not PROJECT_DIR.exists():
        print(f"[❌] PROJECT_DIR does not exist: {PROJECT_DIR}")
    else:
        analyze_and_fix_python_files(PROJECT_DIR)
