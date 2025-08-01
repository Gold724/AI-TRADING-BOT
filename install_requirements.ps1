# AI Trading Sentinel - Requirements Installation Script

# Display header
Write-Host "`n===== AI Trading Sentinel - Requirements Installation =====`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match '(\d+\.\d+\.\d+)') {
        $version = [version]$matches[1]
        if ($version -ge [version]"3.10") {
            Write-Host "[✓] Python $version installed" -ForegroundColor Green
            $pythonInstalled = $true
        } else {
            Write-Host "[✗] Python $version detected, but version 3.10+ is required" -ForegroundColor Red
            $pythonInstalled = $false
        }
    }
} catch {
    Write-Host "[✗] Python not found" -ForegroundColor Red
    $pythonInstalled = $false
}

if (-not $pythonInstalled) {
    Write-Host "[!] Please install Python 3.10 or higher from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "[!] Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
}

# Check Git installation
Write-Host "`nChecking Git..." -ForegroundColor Cyan
try {
    $gitVersion = git --version 2>&1
    if ($gitVersion -match 'git version') {
        Write-Host "[✓] $gitVersion installed" -ForegroundColor Green
        $gitInstalled = $true
    }
} catch {
    Write-Host "[✗] Git not found" -ForegroundColor Red
    $gitInstalled = $false
}

if (-not $gitInstalled) {
    Write-Host "[!] Please install Git from https://git-scm.com/download/win" -ForegroundColor Yellow
}

# Check Chrome installation
Write-Host "`nChecking Google Chrome..." -ForegroundColor Cyan
$chromePath = Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty '(Default)' -ErrorAction SilentlyContinue

if ($chromePath) {
    try {
        $chromeVersion = (Get-Item $chromePath).VersionInfo.ProductVersion
        Write-Host "[✓] Google Chrome $chromeVersion installed" -ForegroundColor Green
        $chromeInstalled = $true
    } catch {
        Write-Host "[✓] Google Chrome installed, but couldn't determine version" -ForegroundColor Yellow
        $chromeInstalled = $true
    }
} else {
    Write-Host "[✗] Google Chrome not found" -ForegroundColor Red
    $chromeInstalled = $false
}

if (-not $chromeInstalled) {
    Write-Host "[!] Please install Google Chrome from https://www.google.com/chrome/" -ForegroundColor Yellow
}

# Check ChromeDriver installation
Write-Host "`nChecking ChromeDriver..." -ForegroundColor Cyan
$driverPath = "$PSScriptRoot\drivers\chromedriver-win64\chromedriver.exe"

if (Test-Path $driverPath) {
    try {
        $driverVersion = & $driverPath --version 2>&1
        if ($driverVersion -match 'ChromeDriver') {
            Write-Host "[✓] $driverVersion installed" -ForegroundColor Green
            $chromeDriverInstalled = $true
        }
    } catch {
        Write-Host "[?] ChromeDriver found but couldn't determine version" -ForegroundColor Yellow
        $chromeDriverInstalled = $true
    }
} else {
    Write-Host "[✗] ChromeDriver not found in drivers directory" -ForegroundColor Red
    $chromeDriverInstalled = $false
}

if (-not $chromeDriverInstalled -and $chromeInstalled) {
    Write-Host "`nChrome is installed but ChromeDriver is missing." -ForegroundColor Yellow
    Write-Host "[!] Please download ChromeDriver manually from https://googlechromelabs.github.io/chrome-for-testing/" -ForegroundColor Yellow
    Write-Host "[!] Extract it to the 'drivers' directory in this project" -ForegroundColor Yellow
}

# Check Python packages
Write-Host "`nChecking Python packages..." -ForegroundColor Cyan
$requiredPackages = @("selenium", "python-dotenv", "requests")
$missingPackages = @()

if ($pythonInstalled) {
    foreach ($package in $requiredPackages) {
        try {
            $packageInfo = pip show $package 2>&1
            if ($packageInfo -match "Name: $package") {
                $version = ($packageInfo | Select-String "Version: (.+)").Matches.Groups[1].Value
                Write-Host "[✓] $package $version installed" -ForegroundColor Green
            } else {
                Write-Host "[✗] $package not installed" -ForegroundColor Red
                $missingPackages += $package
            }
        } catch {
            Write-Host "[✗] $package not installed" -ForegroundColor Red
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "`nSome Python packages are missing." -ForegroundColor Yellow
        Write-Host "[!] Install them with: pip install $($missingPackages -join ' ')" -ForegroundColor Yellow
    }
}

# Final status
Write-Host "`n===== Installation Check Complete =====`n" -ForegroundColor Cyan

$allInstalled = $pythonInstalled -and $gitInstalled -and $chromeInstalled -and $chromeDriverInstalled -and ($missingPackages.Count -eq 0)

if ($allInstalled) {
    Write-Host "All requirements are installed and ready to use!" -ForegroundColor Green
    Write-Host "You can now run the AI Trading Sentinel system." -ForegroundColor Green
} else {
    Write-Host "Some requirements are missing. Please install them before running the system." -ForegroundColor Yellow
}

Write-Host ""
$null = Read-Host "Press Enter to exit"