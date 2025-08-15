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

4. **Bash Pre-Commit Setup** (`setup_pre_commit.sh`)
   - Installs a bash-based pre-commit hook that:
     - Cleans null bytes from Python files
     - Blocks .env files from being committed
     - Runs flake8 and black for code quality checks
   - Useful for Linux/Mac users or Git Bash on Windows

5. **Pre-Commit Checks Batch Script** (`run_pre_commit_checks.bat`)
   - Standalone Windows batch script to run pre-commit checks
   - Cleans null bytes, blocks .env commits, runs flake8 and black
   - Can be run manually before committing

6. **Code Style Fixer** (`fix_code_style.ps1`)
   - Automatically fixes common code style issues
   - Runs isort to fix import sorting
   - Runs black to format code according to PEP 8
   - Checks for remaining issues with flake8

7. **Code Style Fixer Batch Wrapper** (`fix_code_style.bat`)
   - Windows batch file wrapper for the code style fixer
   - Provides an easy way to fix code style issues from Command Prompt

8. **GitHub Secrets Setup Guide** (`GITHUB_SECRETS_SETUP.md`)
   - Instructions for setting up GitHub secrets for VPS deployment
   - Explains required secrets for CI/CD pipeline

### How to Use

#### Manual Pre-Commit Check

Run the pre-check script manually before committing:

```powershell
# PowerShell
./ci_cd_precheck.ps1

# Or using the batch file
ci_cd_precheck.bat

# Or using the standalone batch script
run_pre_commit_checks.bat
```

#### Automatic Pre-Commit Checks

Set up Git hooks to run checks automatically before each commit:

```powershell
# For PowerShell users
./setup_git_hooks.ps1

# For Bash/Linux/Mac users
./setup_pre_commit.sh
```

After setting up the hooks, Git will automatically run the checks before each commit. If any issues are found, the commit will be aborted with an error message.

#### Fixing Code Style Issues

If the pre-commit check fails due to code style issues, you can automatically fix most of them with:

```powershell
# PowerShell
./fix_code_style.ps1

# Or using the batch file
fix_code_style.bat
```

This will:
1. Fix import sorting with isort
2. Format code with black
3. Check for remaining issues with flake8

After running the fixer, run the pre-check script again to verify all issues are fixed.

### GitHub Secrets and Deployment

For setting up CI/CD deployment to a VPS, refer to the `GITHUB_SECRETS_SETUP.md` file, which includes:

1. Instructions for setting up GitHub repository secrets
2. Required secrets for VPS deployment:
   - `CONTABO_VPS_IP`
   - `CONTABO_VPS_PASSWORD`
   - `CONTABO_SSH_PORT`
3. Steps to trigger a full CI/CD pipeline deployment

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

#### Code Style Fixer Not Working

If the code style fixer fails to fix all issues:

1. **Null Bytes**: These must be fixed manually. Use the pre-check script to identify files with null bytes.

2. **Complex Flake8 Issues**: Some flake8 issues require manual intervention, such as:
   - Reducing function complexity
   - Fixing logical errors
   - Addressing unused imports that can't be automatically removed

3. **Conflicting Configurations**: If you have custom configurations for black or isort in your project, they might conflict with the default settings used by the fixer scripts.