#!/bin/bash
# Pre-commit hook: clean & guard before Git commit
echo "Installing pre-commit hook..."

echo '#!/bin/bash
echo "🔍 Running pre-commit checks..."

# 1. Clean null bytes
echo "🧹 Removing null bytes..."
find . -type f -name "*.py" -exec sed -i "s/\x0//g" {} +

# 2. Block .env commit
if git diff --cached --name-only | grep -q "^.env$"; then
  echo "❌ Cannot commit .env file — aborting!"
  exit 1
fi

# 3. Lint with flake8, format with black
echo "🧪 Running flake8..."
flake8 . || exit 1

echo "🎨 Checking black formatting..."
black --check . || exit 1

echo "✅ Pre-commit checks passed."
' > .git/hooks/pre-commit

chmod +x .git/hooks/pre-commit
echo "✅ Pre-commit hook installed successfully!"