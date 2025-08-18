# TradeBot Sentinel - Windows Deployment Setup Script
# PowerShell script for setting up TradeBot Sentinel on Windows with WSL2

param(
    [string]$Environment = "development",
    [string]$WSLDistro = "Ubuntu-22.04",
    [switch]$InstallWSL = $false,
    [switch]$InstallDocker = $false,
    [switch]$SetupVirtualEnv = $true,
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"
$Purple = "Magenta"

# Logging functions
function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "INFO" { Write-Host $logMessage -ForegroundColor $Blue }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor $Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor $Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor $Red }
        "DEBUG" { if ($Verbose) { Write-Host $logMessage -ForegroundColor $Purple } }
        default { Write-Host $logMessage }
    }
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-WSLInstalled {
    try {
        $wslVersion = wsl --version 2>$null
        return $true
    }
    catch {
        return $false
    }
}

function Install-WSL2 {
    Write-Log "INFO" "Installing WSL2..."
    
    if ($DryRun) {
        Write-Log "INFO" "[DRY RUN] Would install WSL2 and $WSLDistro"
        return
    }
    
    # Enable WSL feature
    Write-Log "INFO" "Enabling WSL feature..."
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    
    # Enable Virtual Machine Platform
    Write-Log "INFO" "Enabling Virtual Machine Platform..."
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    
    # Set WSL 2 as default
    Write-Log "INFO" "Setting WSL 2 as default version..."
    wsl --set-default-version 2
    
    # Install Ubuntu distribution
    Write-Log "INFO" "Installing $WSLDistro..."
    wsl --install -d $WSLDistro
    
    Write-Log "SUCCESS" "WSL2 installation completed. Please restart your computer."
    Write-Log "WARNING" "After restart, run this script again to continue setup."
}

function Install-DockerDesktop {
    Write-Log "INFO" "Installing Docker Desktop..."
    
    if ($DryRun) {
        Write-Log "INFO" "[DRY RUN] Would install Docker Desktop"
        return
    }
    
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Write-Log "INFO" "Downloading Docker Desktop..."
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller
    
    Write-Log "INFO" "Installing Docker Desktop..."
    Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet" -Wait
    
    Remove-Item $dockerInstaller -Force
    
    Write-Log "SUCCESS" "Docker Desktop installed. Please restart your computer."
}

function Setup-PythonEnvironment {
    Write-Log "INFO" "Setting up Python virtual environment..."
    
    # Check if Python is installed
    try {
        $pythonVersion = python --version 2>$null
        Write-Log "INFO" "Found Python: $pythonVersion"
    }
    catch {
        Write-Log "ERROR" "Python not found. Please install Python 3.8+ from https://python.org"
        return $false
    }
    
    # Create virtual environment
    $venvPath = "venv"
    if (Test-Path $venvPath) {
        Write-Log "WARNING" "Virtual environment already exists at $venvPath"
    }
    else {
        Write-Log "INFO" "Creating virtual environment..."
        if ($DryRun) {
            Write-Log "INFO" "[DRY RUN] Would create virtual environment"
        }
        else {
            python -m venv $venvPath
        }
    }
    
    # Activate virtual environment and install dependencies
    if (-not $DryRun) {
        Write-Log "INFO" "Activating virtual environment and installing dependencies..."
        
        $activateScript = ".\venv\Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            & $activateScript
            
            # Upgrade pip
            python -m pip install --upgrade pip
            
            # Install requirements
            if (Test-Path "requirements.txt") {
                pip install -r requirements.txt
            }
            else {
                Write-Log "WARNING" "requirements.txt not found"
            }
            
            # Install Playwright browsers
            Write-Log "INFO" "Installing Playwright browsers..."
            playwright install chromium
        }
        else {
            Write-Log "ERROR" "Failed to find activation script"
            return $false
        }
    }
    
    Write-Log "SUCCESS" "Python environment setup completed"
    return $true
}

function Setup-WindowsServices {
    Write-Log "INFO" "Setting up Windows services..."
    
    if ($DryRun) {
        Write-Log "INFO" "[DRY RUN] Would setup Windows services"
        return
    }
    
    # Create service wrapper script
    $serviceScript = @'
# TradeBot Sentinel Service Wrapper
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectPath = Split-Path -Parent $scriptPath
$venvPath = Join-Path $projectPath "venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$mainScript = Join-Path $projectPath "main.py"

# Activate virtual environment and run main script
Set-Location $projectPath
& $pythonExe $mainScript
'@
    
    $serviceScriptPath = "service-wrapper.ps1"
    $serviceScript | Out-File -FilePath $serviceScriptPath -Encoding UTF8
    
    Write-Log "INFO" "Service wrapper created at $serviceScriptPath"
    Write-Log "INFO" "To run as Windows service, use NSSM or similar service wrapper"
    Write-Log "INFO" "Download NSSM from: https://nssm.cc/download"
}

function Test-Prerequisites {
    Write-Log "INFO" "Checking prerequisites..."
    
    $issues = @()
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        $issues += "Script must be run as Administrator"
    }
    
    # Check Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -lt 10) {
        $issues += "Windows 10 or later required"
    }
    
    # Check available disk space (5GB minimum)
    $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
    if ($freeSpaceGB -lt 5) {
        $issues += "Insufficient disk space. Required: 5GB, Available: ${freeSpaceGB}GB"
    }
    
    # Check memory (4GB minimum)
    $totalMemoryGB = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    if ($totalMemoryGB -lt 4) {
        $issues += "Insufficient memory. Required: 4GB, Available: ${totalMemoryGB}GB"
    }
    
    if ($issues.Count -gt 0) {
        Write-Log "ERROR" "Prerequisites check failed:"
        foreach ($issue in $issues) {
            Write-Log "ERROR" "  - $issue"
        }
        return $false
    }
    
    Write-Log "SUCCESS" "All prerequisites checks passed"
    return $true
}

function Show-Usage {
    Write-Host "TradeBot Sentinel - Windows Deployment Setup" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Usage: .\setup-windows-deployment.ps1 [OPTIONS]" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Options:" -ForegroundColor $Yellow
    Write-Host "  -Environment <env>     Environment (development, production) [default: development]"
    Write-Host "  -WSLDistro <distro>    WSL distribution [default: Ubuntu-22.04]"
    Write-Host "  -InstallWSL           Install WSL2 and Ubuntu"
    Write-Host "  -InstallDocker        Install Docker Desktop"
    Write-Host "  -SetupVirtualEnv      Setup Python virtual environment [default: true]"
    Write-Host "  -DryRun               Show what would be done without executing"
    Write-Host "  -Verbose              Enable verbose output"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Yellow
    Write-Host "  .\setup-windows-deployment.ps1                    # Basic setup"
    Write-Host "  .\setup-windows-deployment.ps1 -InstallWSL        # Install WSL2"
    Write-Host "  .\setup-windows-deployment.ps1 -InstallDocker     # Install Docker"
    Write-Host "  .\setup-windows-deployment.ps1 -DryRun            # Preview actions"
    Write-Host ""
}

function Main {
    Write-Host "=" * 60 -ForegroundColor $Purple
    Write-Host "TradeBot Sentinel - Windows Deployment Setup" -ForegroundColor $Green
    Write-Host "=" * 60 -ForegroundColor $Purple
    Write-Host ""
    
    Write-Log "INFO" "Environment: $Environment"
    Write-Log "INFO" "WSL Distribution: $WSLDistro"
    
    if ($DryRun) {
        Write-Log "WARNING" "DRY RUN MODE - No changes will be made"
    }
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # Install WSL2 if requested
    if ($InstallWSL) {
        if (-not (Test-WSLInstalled)) {
            Install-WSL2
            Write-Log "WARNING" "Please restart your computer and run this script again"
            exit 0
        }
        else {
            Write-Log "INFO" "WSL2 is already installed"
        }
    }
    
    # Install Docker if requested
    if ($InstallDocker) {
        try {
            docker --version | Out-Null
            Write-Log "INFO" "Docker is already installed"
        }
        catch {
            Install-DockerDesktop
            Write-Log "WARNING" "Please restart your computer after Docker installation"
        }
    }
    
    # Setup Python virtual environment
    if ($SetupVirtualEnv) {
        if (-not (Setup-PythonEnvironment)) {
            Write-Log "ERROR" "Failed to setup Python environment"
            exit 1
        }
    }
    
    # Setup Windows services
    Setup-WindowsServices
    
    # Create environment file
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Log "INFO" "Created .env file from .env.example"
            Write-Log "WARNING" "Please configure .env file with your settings"
        }
    }
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor $Green
    Write-Host "WINDOWS SETUP COMPLETED SUCCESSFULLY" -ForegroundColor $Green
    Write-Host "=" * 60 -ForegroundColor $Green
    Write-Host ""
    
    Write-Log "SUCCESS" "TradeBot Sentinel Windows setup completed!"
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor $Yellow
    Write-Host "  1. Configure .env file with your trading credentials"
    Write-Host "  2. Test the bot: python main.py"
    Write-Host "  3. For production: Install NSSM and create Windows service"
    Write-Host "  4. For cloud deployment: Use WSL2 with Linux deployment scripts"
    Write-Host ""
    Write-Host "Quick Commands:" -ForegroundColor $Yellow
    Write-Host "  # Activate virtual environment"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host ""
    Write-Host "  # Run the bot"
    Write-Host "  python main.py"
    Write-Host ""
    Write-Host "  # Run tests"
    Write-Host "  python -m pytest"
    Write-Host ""
}

# Show help if requested
if ($args -contains "-h" -or $args -contains "--help") {
    Show-Usage
    exit 0
}

# Run main function
try {
    Main
}
catch {
    Write-Log "ERROR" "Setup failed: $($_.Exception.Message)"
    Write-Log "ERROR" "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}