# Setup Git hooks for AI Trading Sentinel

Write-Host "`n🔧 Setting up Git pre-commit hook..." -ForegroundColor Cyan

# Ensure .git/hooks directory exists
$hooksDir = ".git/hooks"
if (-not (Test-Path $hooksDir)) {
    Write-Host "Creating hooks directory..."
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

# Create pre-commit hook
$preCommitPath = ".git/hooks/pre-commit"
$preCommitContent = @"
#!/bin/sh
#
# Pre-commit hook to run CI/CD checks before committing

echo "Running pre-commit checks..."

# Run the pre-check script
powershell.exe -ExecutionPolicy Bypass -File ./ci_cd_precheck.ps1

# If the script exits with a non-zero status, prevent the commit
if [ \$? -ne 0 ]; then
  echo "CI/CD pre-checks failed. Commit aborted."
  exit 1
fi

exit 0
"@

# Write the pre-commit hook
Set-Content -Path $preCommitPath -Value $preCommitContent

# Make the hook executable (for Git Bash/WSL users)
if (Get-Command "chmod" -ErrorAction SilentlyContinue) {
    chmod +x $preCommitPath
} else {
    Write-Host "Note: For Git Bash/WSL users, you may need to make the hook executable with: chmod +x .git/hooks/pre-commit" -ForegroundColor Yellow
}

Write-Host "`n✅ Git pre-commit hook installed successfully!" -ForegroundColor Green
Write-Host "Now your code will be automatically checked before each commit." -ForegroundColor Cyan