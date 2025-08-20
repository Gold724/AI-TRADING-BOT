# TraeAI Trading Bot Setup Script
# This script performs comprehensive setup and checks for the TraeAI trading bot project

# Set console colors for better readability
$InformationColor = "Cyan"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$ErrorColor = "Red"
$PromptColor = "Magenta"

Write-Host "`nTraeAI Trading Bot Setup" -ForegroundColor $InformationColor
Write-Host "=====================" -ForegroundColor $InformationColor

# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Function to ensure Python packages are installed
function Ensure-PythonPackages {
    param (
        [string[]]$packages
    )
    
    $missingPackages = @()
    
    foreach ($package in $packages) {
        Write-Host "Checking for $package..." -NoNewline
        $result = python -c "import $package; print('OK')" 2>$null
        
        if ($result -ne "OK") {
            Write-Host "Not found" -ForegroundColor $WarningColor
            $missingPackages += $package
        } else {
            Write-Host "OK" -ForegroundColor $SuccessColor
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "`nInstalling missing packages: $($missingPackages -join ', ')" -ForegroundColor $InformationColor
        
        foreach ($package in $missingPackages) {
            Write-Host "Installing $package..." -NoNewline
            pip install $package 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "OK" -ForegroundColor $SuccessColor
            } else {
                Write-Host "Failed" -ForegroundColor $ErrorColor
            }
        }
    }
}

# Function to scan for null bytes in Python files
function Scan-NullBytes {
    Write-Host "`nScanning for null bytes in Python files..." -ForegroundColor $InformationColor
    $badFiles = @()

    Get-ChildItem -Recurse -Include *.py -Exclude venv*,node_modules*,.git*,__pycache*,chrome*,temp_chrome*,drivers,chrome_profile* | ForEach-Object {
        try {
            $bytes = Get-Content $_ -Encoding byte -ErrorAction SilentlyContinue
            if ($bytes -contains 0) {
                $badFiles += $_.FullName
            }
        } catch {
            # Skip files that can't be read
        }
    }

    if ($badFiles.Count -gt 0) {
        Write-Host "Null bytes detected in the following files:" -ForegroundColor $WarningColor
        $badFiles | ForEach-Object { Write-Host "  - $_" }
        
        $cleanFiles = Read-Host "Do you want to clean these files? (y/n)"
        if ($cleanFiles -eq "y") {
            foreach ($file in $badFiles) {
                Write-Host "Cleaning $file..." -NoNewline
                $content = Get-Content $file -Raw
                $content = $content -replace "\0", ""
                Set-Content -Path $file -Value $content -NoNewline
                Write-Host "Done" -ForegroundColor $SuccessColor
            }
        }
    } else {
        Write-Host "No null bytes found in Python files." -ForegroundColor $SuccessColor
    }
}

# Function to check if .env is in .gitignore
function Check-EnvGitignore {
    Write-Host "`nChecking if .env is properly ignored..." -ForegroundColor $InformationColor
    
    $gitignorePath = ".gitignore"
    $envIgnored = $false
    
    if (Test-Path $gitignorePath) {
        $gitignoreContent = Get-Content $gitignorePath
        $envIgnored = $gitignoreContent -contains ".env" -or $gitignoreContent -contains ".env*"
    }
    
    if (-not $envIgnored) {
        Write-Host ".env is not properly ignored in .gitignore" -ForegroundColor $WarningColor
        
        $addToGitignore = Read-Host "Do you want to add .env to .gitignore? (y/n)"
        if ($addToGitignore -eq "y") {
            if (-not (Test-Path $gitignorePath)) {
                New-Item -Path $gitignorePath -ItemType File | Out-Null
            }
            
            Add-Content -Path $gitignorePath -Value "`n# Environment variables`n.env`n.env.*"
            Write-Host ".env added to .gitignore" -ForegroundColor $SuccessColor
        }
    } else {
        Write-Host ".env is properly ignored in .gitignore" -ForegroundColor $SuccessColor
    }
}

# Function to run code quality tools
function Run-CodeQualityTools {
    param (
        [switch]$autoFix
    )
    
    Write-Host "`nRunning code quality checks..." -ForegroundColor $InformationColor
    $success = $true
    
    # Run isort
    if (Test-CommandExists "isort") {
        Write-Host "Running isort..." -NoNewline
        if ($autoFix) {
            isort --profile black . | Out-Null
            Write-Host "Fixed" -ForegroundColor $SuccessColor
        } else {
            isort --check-only --profile black . | Out-Null
            if ($LASTEXITCODE -ne 0) {
                $success = $false
                Write-Host "Issues found" -ForegroundColor $WarningColor
            } else {
                Write-Host "OK" -ForegroundColor $SuccessColor
            }
        }
    } else {
        Write-Host "isort not found. Skipping." -ForegroundColor $WarningColor
    }
    
    # Run black
    if (Test-CommandExists "black") {
        Write-Host "Running black..." -NoNewline
        if ($autoFix) {
            black . | Out-Null
            Write-Host "Fixed" -ForegroundColor $SuccessColor
        } else {
            black --check . | Out-Null
            if ($LASTEXITCODE -ne 0) {
                $success = $false
                Write-Host "Issues found" -ForegroundColor $WarningColor
            } else {
                Write-Host "OK" -ForegroundColor $SuccessColor
            }
        }
    } else {
        Write-Host "black not found. Skipping." -ForegroundColor $WarningColor
    }
    
    # Run flake8
    if (Test-CommandExists "flake8") {
        Write-Host "Running flake8..." -NoNewline
        flake8 . | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $success = $false
            Write-Host "Issues found" -ForegroundColor $WarningColor
        } else {
            Write-Host "OK" -ForegroundColor $SuccessColor
        }
    } else {
        Write-Host "flake8 not found. Skipping." -ForegroundColor $WarningColor
    }
    
    return $success
}

# Function to set up pre-commit hooks
function Setup-GitHooks {
    Write-Host "`nSetting up Git pre-commit hooks..." -ForegroundColor $InformationColor
    
    # Ensure .git/hooks directory exists
    $hooksDir = ".git/hooks"
    if (-not (Test-Path $hooksDir)) {
        Write-Host "Creating hooks directory..." -NoNewline
        New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
        Write-Host "Done" -ForegroundColor $SuccessColor
    }
    
    # Create pre-commit hook
    $preCommitPath = ".git/hooks/pre-commit"
    $preCommitContent = @'
#!/bin/sh
#
# Pre-commit hook to run CI/CD checks before committing

echo "Running pre-commit checks..."

# Clean null bytes
echo "Cleaning null bytes..."
find . -type f -name "*.py" -exec sed -i "s/\x0//g" {} \;

# Block .env commit
if git diff --cached --name-only | grep -q "^.env$"; then
  echo "Cannot commit .env file — aborting!"
  exit 1
fi

# Run the pre-check script
powershell.exe -ExecutionPolicy Bypass -File ./trae_setup.ps1 -preCommitMode

# If the script exits with a non-zero status, prevent the commit
if [ $? -ne 0 ]; then
  echo "CI/CD pre-checks failed. Commit aborted."
  exit 1
fi

exit 0
'@
    
    Write-Host "Creating pre-commit hook..." -NoNewline
    Set-Content -Path $preCommitPath -Value $preCommitContent
    Write-Host "Done" -ForegroundColor $SuccessColor
    
    # Make the hook executable (for Git Bash/WSL users)
    try {
        if (Get-Command "chmod" -ErrorAction Stop) {
            chmod +x $preCommitPath
            Write-Host "Made hook executable with chmod." -ForegroundColor $SuccessColor
        }
    } catch {
        Write-Host "Note: For Git Bash/WSL users, you may need to make the hook executable with: chmod +x .git/hooks/pre-commit" -ForegroundColor $WarningColor
    }
    
    Write-Host "Git pre-commit hook installed successfully!" -ForegroundColor $SuccessColor
}

# Function to check GitHub Actions workflow
function Check-GitHubActions {
    Write-Host "`nChecking GitHub Actions workflow..." -ForegroundColor $InformationColor
    
    $workflowDir = ".github/workflows"
    $workflowFile = "$workflowDir/ci_cd_pipeline.yml"
    
    if (-not (Test-Path $workflowDir)) {
        Write-Host "Creating .github/workflows directory..." -NoNewline
        New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null
        Write-Host "Done" -ForegroundColor $SuccessColor
    }
    
    if (-not (Test-Path $workflowFile)) {
        Write-Host "CI/CD pipeline workflow file not found." -ForegroundColor $WarningColor
        Write-Host "Please ensure the file exists at: $workflowFile" -ForegroundColor $WarningColor
    } else {
        Write-Host "CI/CD pipeline workflow file found." -ForegroundColor $SuccessColor
        
        # Check if workflow file is committed
        $gitStatus = git status --porcelain "$workflowFile"
        if ($gitStatus) {
            Write-Host "Workflow file has uncommitted changes." -ForegroundColor $WarningColor
            
            $commitWorkflow = Read-Host "Do you want to commit the workflow file? (y/n)"
            if ($commitWorkflow -eq "y") {
                git add "$workflowFile"
                git commit -m "chore: update CI/CD workflow"
                Write-Host "Workflow file committed." -ForegroundColor $SuccessColor
            }
        } else {
            Write-Host "Workflow file is committed to the repository." -ForegroundColor $SuccessColor
        }
    }
}

# Function to check GitHub Secrets
function Check-GitHubSecrets {
    Write-Host "`nChecking GitHub Secrets for deployment..." -ForegroundColor $InformationColor
    
    Write-Host "Please ensure the following secrets are set in your GitHub repository:" -ForegroundColor $WarningColor
    Write-Host "  - CONTABO_VPS_IP" -ForegroundColor $WarningColor
    Write-Host "  - CONTABO_VPS_PASSWORD" -ForegroundColor $WarningColor
    Write-Host "  - CONTABO_SSH_PORT" -ForegroundColor $WarningColor
    
    Write-Host "`nFor detailed instructions, see GITHUB_SECRETS_SETUP.md" -ForegroundColor $InformationColor
}

# Function to prepare Git operations
function Prepare-Git {
    Write-Host "`nPreparing Git operations..." -ForegroundColor $InformationColor
    
    # Check if there are any changes to commit
    $gitStatus = git status --porcelain
    if (-not $gitStatus) {
        Write-Host "No changes to commit." -ForegroundColor $InformationColor
        return
    }
    
    # Show changes
    Write-Host "`nChanges to be committed:" -ForegroundColor $WarningColor
    git status --short
    
    $addAll = Read-Host "Do you want to add all changes? (y/n)"
    if ($addAll -eq "y") {
        git add .
        Write-Host "All changes added." -ForegroundColor $SuccessColor
        
        $commitMessage = Read-Host "Enter commit message"
        if ($commitMessage) {
            git commit -m $commitMessage
            Write-Host "Changes committed." -ForegroundColor $SuccessColor
            
            $pushChanges = Read-Host "Do you want to push changes? (y/n)"
            if ($pushChanges -eq "y") {
                $currentBranch = git rev-parse --abbrev-ref HEAD
                git push origin $currentBranch
                Write-Host "Changes pushed to $currentBranch." -ForegroundColor $SuccessColor
            }
        }
    }
}

# Function to generate a secure random key for Flask
function Generate-FlaskSecretKey {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

# Function to generate a Fernet key for encryption
function Generate-FernetKey {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

# Function to check/create .env.example files and .env file
function Check-EnvExample {
    Write-Host "`nChecking .env.example files..." -ForegroundColor $InformationColor
    
    $envPath = ".env"
    $envExamplePath = ".env.example"
    $frontendEnvExamplePath = "frontend/.env.example"
    
    # Function to update .env file with secure keys
    function Update-EnvWithSecureKeys {
        param (
            [string]$envFilePath
        )
        
        # Generate security keys
        $flaskKey = Generate-FlaskSecretKey
        $fernetKey = Generate-FernetKey
        
        # Update the .env file with generated keys
        $envContent = Get-Content -Path $envFilePath -Raw
        
        # Update FLASK_SECRET_KEY if it exists and has default value
        if ($envContent -match "FLASK_SECRET_KEY=generate_a_secure_random_key_here") {
            $envContent = $envContent -replace "FLASK_SECRET_KEY=generate_a_secure_random_key_here", "FLASK_SECRET_KEY=$flaskKey"
            Write-Host "Updated FLASK_SECRET_KEY with a secure random key." -ForegroundColor $SuccessColor
        }
        
        # Add or update ENCRYPTION_KEY
        if ($envContent -notmatch "ENCRYPTION_KEY=") {
            $envContent += "`nENCRYPTION_KEY=$fernetKey`n"
            Write-Host "Added ENCRYPTION_KEY with a secure Fernet key." -ForegroundColor $SuccessColor
        } elseif ($envContent -match "ENCRYPTION_KEY=generate_a_secure_fernet_key") {
            $envContent = $envContent -replace "ENCRYPTION_KEY=generate_a_secure_fernet_key", "ENCRYPTION_KEY=$fernetKey"
            Write-Host "Updated ENCRYPTION_KEY with a secure Fernet key." -ForegroundColor $SuccessColor
        }
        
        Set-Content -Path $envFilePath -Value $envContent
    }
    
    # Check if .env file exists
    if (-not (Test-Path $envPath) -and (Test-Path $envExamplePath)) {
        Write-Host ".env file not found, but .env.example exists." -ForegroundColor $WarningColor
        $createEnv = Read-Host "Do you want to create a .env file from .env.example? (y/n)"
        if ($createEnv -eq "y") {
            Copy-Item -Path $envExamplePath -Destination $envPath
            Update-EnvWithSecureKeys -envFilePath $envPath
            Write-Host "Created .env file from .env.example with secure keys generated." -ForegroundColor $SuccessColor
            Write-Host "Please update it with your actual credentials." -ForegroundColor $WarningColor
        }
    } elseif (Test-Path $envPath) {
        Write-Host ".env file found. Checking for security keys..." -ForegroundColor $InformationColor
        $envContent = Get-Content -Path $envPath -Raw
        
        # Check if security keys need to be updated
        if ($envContent -match "FLASK_SECRET_KEY=generate_a_secure_random_key_here" -or 
            $envContent -match "ENCRYPTION_KEY=generate_a_secure_fernet_key" -or 
            $envContent -notmatch "ENCRYPTION_KEY=") {
            
            $updateKeys = Read-Host "Security keys in .env file need to be updated. Do you want to generate secure keys? (y/n)"
            if ($updateKeys -eq "y") {
                Update-EnvWithSecureKeys -envFilePath $envPath
            }
        } else {
            Write-Host "Security keys in .env file are already set." -ForegroundColor $SuccessColor
        }
    }
    
    # Check main .env.example
    if (-not (Test-Path $envExamplePath)) {
        Write-Host "Main .env.example file not found." -ForegroundColor $WarningColor
        
        $createEnvExample = Read-Host "Do you want to create a default .env.example file? (y/n)"
        if ($createEnvExample -eq "y") {
            $envExampleContent = @'
# AI Trading Sentinel Environment Variables
# Replace these placeholder values with your actual credentials
# DO NOT commit the actual .env file with real values to Git

# API Keys and Credentials
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
BULENOX_API_KEY=your_bulenox_api_key_here
BULENOX_API_SECRET=your_bulenox_api_secret_here

# Trading Accounts
TRADING_ACCOUNT_TYPE=binance_futures  # Options: binance_futures, binance_spot, bulenox
TRADING_ACCOUNT_NAME=your_account_name

# Binance Settings
BINANCE_TESTNET=True  # Set to False for real trading
BINANCE_FUTURES_TESTNET=True  # Set to False for real trading

# Bulenox Settings
BULENOX_TESTNET=True  # Set to False for real trading

# Chrome Profile Settings
CHROME_PROFILE_PATH=/path/to/chrome/profile
CHROME_PROFILE_NAME=Default

# Vast.ai Settings
VAST_API_KEY=your_vast_ai_api_key_here
VAST_MACHINE_ID=your_vast_machine_id

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=your_username/your_repo_name

# Flask Application Settings
FLASK_APP=cloud_main.py
FLASK_ENV=development  # Options: development, production
FLASK_DEBUG=True  # Set to False in production
FLASK_SECRET_KEY=generate_a_secure_random_key_here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Slack Integration
SLACK_VERIFICATION_TOKEN=your_slack_verification_token_here
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_CHANNEL_ID=your_slack_channel_id_here

# Logging Settings
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_PATH=logs/trading_bot.log

# Trading Bot Settings
TRADING_PAIRS=BTCUSDT,ETHUSDT,SOLUSDT  # Comma-separated list of trading pairs
MAX_OPEN_TRADES=3
RISK_PER_TRADE=0.02  # Percentage of account balance (0.02 = 2%)
STRATEGY_NAME=default_strategy

# Backtesting Settings
BACKTEST_START_DATE=2023-01-01
BACKTEST_END_DATE=2023-12-31

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=False
EMAIL_SENDER=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_RECIPIENT=recipient@example.com
SMTP_SERVER=smtp.example.com
SMTP_PORT=587

# Deployment Settings
CONTABO_VPS_IP=your_vps_ip_address
CONTABO_SSH_PORT=22
CONTABO_USERNAME=root
# Do not store actual password in this file
# CONTABO_PASSWORD=your_vps_password
'@
            
            Set-Content -Path $envExamplePath -Value $envExampleContent
            Write-Host "Created .env.example file." -ForegroundColor $SuccessColor
        }
    } else {
        Write-Host "Main .env.example file found." -ForegroundColor $SuccessColor
    }
    
    # Check frontend .env.example if frontend directory exists
    if (Test-Path "frontend") {
        if (-not (Test-Path $frontendEnvExamplePath)) {
            Write-Host "Frontend .env.example file not found." -ForegroundColor $WarningColor
            
            $createFrontendEnvExample = Read-Host "Do you want to create a default frontend .env.example file? (y/n)"
            if ($createFrontendEnvExample -eq "y") {
                $frontendEnvExampleContent = @'
# Frontend Environment Variables
# Replace these placeholder values with your actual values
# DO NOT commit the actual .env file with real values to Git

# API Configuration
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_WS_URL=ws://localhost:5000/ws

# Feature Flags
REACT_APP_ENABLE_MOCK_DATA=true
REACT_APP_ENABLE_NOTIFICATIONS=true

# UI Configuration
REACT_APP_THEME=dark
REACT_APP_REFRESH_INTERVAL=5000
'@
                
                # Create frontend directory if it doesn't exist
                if (-not (Test-Path "frontend")) {
                    New-Item -ItemType Directory -Path "frontend" -Force | Out-Null
                }
                
                Set-Content -Path $frontendEnvExamplePath -Value $frontendEnvExampleContent
                Write-Host "Created frontend .env.example file." -ForegroundColor $SuccessColor
            }
        } else {
        Write-Host "Frontend .env.example file found." -ForegroundColor $SuccessColor
        
        # Check if frontend .env file exists
        $frontendEnvPath = "frontend/.env"
        if (-not (Test-Path $frontendEnvPath) -and (Test-Path $frontendEnvExamplePath)) {
            Write-Host "Frontend .env file not found, but frontend/.env.example exists." -ForegroundColor $WarningColor
            $createFrontendEnv = Read-Host "Do you want to create a frontend .env file from frontend/.env.example? (y/n)"
            if ($createFrontendEnv -eq "y") {
                Copy-Item -Path $frontendEnvExamplePath -Destination $frontendEnvPath
                Write-Host "Created frontend .env file from frontend/.env.example. Please update it with your actual values." -ForegroundColor $SuccessColor
            }
        }
    }
}
}

# Main script execution

# Parse command line arguments
param (
    [switch]$preCommitMode,
    [switch]$autoFix,
    [switch]$skipGit,
    [switch]$skipHooks
)

# Check Python installation
if (-not (Test-CommandExists "python")) {
    Write-Host "Python is not installed or not in your PATH." -ForegroundColor $ErrorColor
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor $WarningColor
    exit 1
}

# Check Git installation
if (-not (Test-CommandExists "git")) {
    Write-Host "Git is not installed or not in your PATH." -ForegroundColor $ErrorColor
    Write-Host "Please install Git from https://git-scm.com/downloads" -ForegroundColor $WarningColor
    exit 1
}

# Check if we're in a Git repository
if (-not (Test-Path ".git")) {
    Write-Host "Not in a Git repository. Please run this script from the root of your Git repository." -ForegroundColor $ErrorColor
    exit 1
}

# Ensure required Python packages are installed
Ensure-PythonPackages @("flake8", "black", "isort")

# Check if .env is in .gitignore
Check-EnvGitignore

# Check/create .env.example files
Check-EnvExample

# Scan for null bytes in Python files
Scan-NullBytes

# Run code quality tools
$codeQualitySuccess = Run-CodeQualityTools -autoFix:$autoFix

if (-not $codeQualitySuccess -and -not $autoFix) {
    $fixIssues = Read-Host "Do you want to automatically fix code style issues? (y/n)"
    if ($fixIssues -eq "y") {
        Run-CodeQualityTools -autoFix
    }
}

# Set up Git hooks if not in pre-commit mode and not skipping hooks
if (-not $preCommitMode -and -not $skipHooks) {
    Setup-GitHooks
}

# Check GitHub Actions workflow
Check-GitHubActions

# Check GitHub Secrets
Check-GitHubSecrets

# Prepare Git operations if not in pre-commit mode and not skipping Git
if (-not $preCommitMode -and -not $skipGit) {
    Prepare-Git
}

# Final message
if ($preCommitMode) {
    # In pre-commit mode, exit with appropriate code
    if ($codeQualitySuccess) {
        Write-Host "`nPre-commit checks passed." -ForegroundColor $SuccessColor
        exit 0
    } else {
        Write-Host "`nPre-commit checks failed. Please fix the issues before committing." -ForegroundColor $ErrorColor
        exit 1
    }
} else {
    # Normal mode
    Write-Host "`nTraeAI setup completed." -ForegroundColor $SuccessColor
    
    if (-not $codeQualitySuccess) {
        Write-Host "Some code quality issues were found. Please fix them before committing." -ForegroundColor $WarningColor
    } else {
        Write-Host "All checks passed. Your code is ready to commit." -ForegroundColor $SuccessColor
    }
}