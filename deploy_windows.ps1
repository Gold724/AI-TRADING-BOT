# AI Trading Sentinel - Windows Deployment Script
# Requires: PowerShell 5.1+ and Administrator privileges for service installation

param(
    [switch]$Local,
    [switch]$Service,
    [switch]$Help
)

if ($Help) {
    Write-Host "AI Trading Sentinel - Windows Deployment" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\deploy_windows.ps1 -Local    # Local development setup"
    Write-Host "  .\deploy_windows.ps1 -Service  # Install as Windows service (requires admin)"
    Write-Host "  .\deploy_windows.ps1 -Help     # Show this help"
    Write-Host ""
    exit 0
}

Write-Host "AI Trading Sentinel - Windows Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "Error: main.py not found. Please run from project root." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "Setting up dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Dependencies installed" -ForegroundColor Green

# Set up environment variables
Write-Host "Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example" -ForegroundColor Green
    } else {
        $envContent = @'
# AI Trading Sentinel Environment
ENVIRONMENT=development
HEADLESS=false
AUTO_EXECUTION_ENABLED=false
DEBUG=true
LOG_LEVEL=INFO

# Browser Settings
BROWSER_TIMEOUT=30
PAGE_LOAD_TIMEOUT=30

# Trading Settings
RISK_MANAGEMENT=true
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENTAGE=2.0

# Logging
LOG_FILE=logs\trading.log
LOG_ROTATION=daily

# Windows Specific
CHROME_BINARY_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

# Broker Credentials (REQUIRED - ADD YOUR CREDENTIALS)
# BROKER_USERNAME=
# BROKER_PASSWORD=
# BROKER_API_KEY=
# BROKER_SECRET=
'@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "Created default .env file" -ForegroundColor Green
    }
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
$directories = @("logs", "data\accounts", "data\signals", "data\backtest", "chrome_profiles")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "Directories created" -ForegroundColor Green

# Test browser setup
Write-Host "Testing browser configuration..." -ForegroundColor Yellow
try {
    python -c "from browser_config import setup_browser; print('Browser setup OK')"
    Write-Host "Browser setup OK" -ForegroundColor Green
} catch {
    Write-Host "Browser setup needs attention" -ForegroundColor Yellow
    Write-Host "Make sure Chrome is installed and accessible" -ForegroundColor Cyan
}

# Run basic health check
Write-Host "Running health check..." -ForegroundColor Yellow
try {
    python -c "import main; print('Main module imports OK')"
    Write-Host "Main module imports OK" -ForegroundColor Green
} catch {
    Write-Host "Main module has issues - check dependencies" -ForegroundColor Yellow
}

if ($Service) {
    Write-Host "Installing Windows Service..." -ForegroundColor Yellow
    
    # Check if running as administrator
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "Administrator privileges required for service installation" -ForegroundColor Red
        Write-Host "Run PowerShell as Administrator and try again" -ForegroundColor Cyan
        exit 1
    }
    
    # Use deployment\windows\service-wrapper.ps1 if available
    if (Test-Path "deployment\windows\service-wrapper.ps1") {
        Write-Host "Using service wrapper..." -ForegroundColor Yellow
        & ".\deployment\windows\service-wrapper.ps1" install
        & ".\deployment\windows\service-wrapper.ps1" start
        Write-Host "Service installed and started" -ForegroundColor Green
    } else {
        Write-Host "Service wrapper not found. Manual service setup required." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Windows deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your broker credentials"
Write-Host "2. Test browser: python test_browser.py"
Write-Host "3. Run bot: python main.py"
Write-Host "4. Monitor logs: Get-Content logs\trading.log -Wait"
Write-Host ""
Write-Host "Development Commands:" -ForegroundColor Cyan
Write-Host "• Activate venv: .\venv\Scripts\Activate.ps1"
Write-Host "• Start bot: python main.py"
Write-Host "• Run tests: python -m pytest tests\"
Write-Host "• Check health: python health_check.py"
Write-Host "• View logs: Get-Content logs\trading.log -Wait"
Write-Host ""
if (-not $Service) {
    Write-Host "Service Installation:" -ForegroundColor Cyan
    Write-Host "• Install service: .\deploy_windows.ps1 -Service (requires admin)"
    Write-Host "• Or use: .\deployment\windows\run-as-admin.bat"
}
Write-Host ""
Write-Host "For cloud deployment, use deploy_cloud.sh on your VPS" -ForegroundColor Cyan

# Deactivate virtual environment
deactivate 2>$null

Write-Host "Setup complete! Happy trading!" -ForegroundColor Green