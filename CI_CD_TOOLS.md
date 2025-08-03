# CI/CD Tools for AI Trading Sentinel

## Pre-Commit Checks

This project includes tools to help maintain code quality and prevent common issues that might break CI/CD pipelines.

### Available Tools

1. **CI/CD Pre-Check Script** (`ci_cd_precheck.ps1`)
   - Detects null bytes in Python files that can cause CI failures
   - Runs linting tools (flake8, black, isort) to ensure code quality
   - Helps catch issues before they reach GitHub Actions

2. **Batch Wrapper** (`ci_cd_precheck.bat`)
   - Windows batch file wrapper for the PowerShell script
   - Provides an easy way to run checks from Command Prompt

3. **Git Hooks Setup** (`setup_git_hooks.ps1`)
   - Installs a pre-commit hook to automatically run checks before each commit
   - Prevents committing code that would fail CI/CD checks

### How to Use

#### Manual Pre-Commit Check

Run the pre-check script manually before committing:

```powershell
# PowerShell
./ci_cd_precheck.ps1

# Or using the batch file
ci_cd_precheck.bat
```

#### Automatic Pre-Commit Checks

Set up Git hooks to run checks automatically before each commit:

```powershell
./setup_git_hooks.ps1
```

After setting up the hooks, Git will automatically run the checks before each commit. If any issues are found, the commit will be aborted with an error message.

### Troubleshooting

#### PowerShell Execution Policy

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then try running the script again.

#### Missing Python Tools

If you get errors about missing tools (flake8, black, isort), install them:

```bash
pip install flake8 black isort
```

#### Git Hook Not Working

For Git Bash or WSL users, you may need to make the hook executable:

```bash
chmod +x .git/hooks/pre-commit
```