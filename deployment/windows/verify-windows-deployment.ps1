# TradeBot Sentinel - Windows Deployment Verification Script
# PowerShell script for verifying TradeBot Sentinel setup on Windows

param(
    [switch]$Verbose = $false,
    [switch]$SkipBrowserTest = $false,
    [switch]$SkipAPITest = $false,
    [string]$Environment = "development"
)

# Set error action preference
$ErrorActionPreference = "Continue"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"
$Purple = "Magenta"

# Test results tracking
$script:TestResults = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Tests = @()
}

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

function Test-Result {
    param(
        [string]$TestName,
        [bool]$Success,
        [string]$Message = "",
        [bool]$IsWarning = $false
    )
    
    $result = @{
        Name = $TestName
        Success = $Success
        Message = $Message
        IsWarning = $IsWarning
        Timestamp = Get-Date
    }
    
    $script:TestResults.Tests += $result
    
    if ($IsWarning) {
        $script:TestResults.Warnings++
        Write-Log "WARNING" "⚠️  $TestName - $Message"
    }
    elseif ($Success) {
        $script:TestResults.Passed++
        Write-Log "SUCCESS" "✅ $TestName - $Message"
    }
    else {
        $script:TestResults.Failed++
        Write-Log "ERROR" "❌ $TestName - $Message"
    }
}

function Test-PythonEnvironment {
    Write-Log "INFO" "Testing Python environment..."
    
    # Test Python installation
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
            $version = [Version]$matches[1]
            if ($version -ge [Version]"3.8.0") {
                Test-Result "Python Version" $true "Found $pythonVersion"
            }
            else {
                Test-Result "Python Version" $false "Python 3.8+ required, found $pythonVersion"
            }
        }
        else {
            Test-Result "Python Version" $false "Could not determine Python version"
        }
    }
    catch {
        Test-Result "Python Installation" $false "Python not found or not accessible"
    }
    
    # Test virtual environment
    if (Test-Path "venv\Scripts\python.exe") {
        Test-Result "Virtual Environment" $true "Virtual environment found"
        
        # Test if virtual environment is activated
        if ($env:VIRTUAL_ENV) {
            Test-Result "Virtual Environment Activation" $true "Virtual environment is activated"
        }
        else {
            Test-Result "Virtual Environment Activation" $false "Virtual environment not activated" $true
        }
    }
    else {
        Test-Result "Virtual Environment" $false "Virtual environment not found at venv/Scripts/python.exe"
    }
    
    # Test pip packages
    try {
        $pipList = pip list 2>$null
        if ($pipList) {
            $packages = @("selenium", "playwright", "requests", "python-dotenv")
            foreach ($package in $packages) {
                if ($pipList -match $package) {
                    Test-Result "Package: $package" $true "Installed"
                }
                else {
                    Test-Result "Package: $package" $false "Not installed"
                }
            }
        }
    }
    catch {
        Test-Result "Pip Packages" $false "Could not check installed packages"
    }
}

function Test-ProjectFiles {
    Write-Log "INFO" "Testing project files..."
    
    $requiredFiles = @(
        "main.py",
        "requirements.txt",
        ".env.example"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Test-Result "File: $file" $true "Found"
        }
        else {
            Test-Result "File: $file" $false "Missing"
        }
    }
    
    # Test .env file
    if (Test-Path ".env") {
        Test-Result "Environment File" $true "Found .env file"
        
        # Check if .env has required variables
        $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
        $requiredVars = @("TRADING_PLATFORM", "TRADING_USERNAME")
        
        foreach ($var in $requiredVars) {
            if ($envContent -match "^$var=") {
                Test-Result "Env Var: $var" $true "Configured"
            }
            else {
                Test-Result "Env Var: $var" $false "Not configured" $true
            }
        }
    }
    else {
        Test-Result "Environment File" $false "No .env file found" $true
    }
}

function Test-BrowserSetup {
    if ($SkipBrowserTest) {
        Write-Log "INFO" "Skipping browser tests (--SkipBrowserTest flag)"
        return
    }
    
    Write-Log "INFO" "Testing browser setup..."
    
    # Test Playwright installation
    try {
        $playwrightVersion = playwright --version 2>$null
        if ($playwrightVersion) {
            Test-Result "Playwright CLI" $true "Found: $playwrightVersion"
        }
        else {
            Test-Result "Playwright CLI" $false "Playwright CLI not found"
        }
    }
    catch {
        Test-Result "Playwright CLI" $false "Playwright not accessible"
    }
    
    # Test Chromium browser
    $chromiumPaths = @(
        "$env:USERPROFILE\AppData\Local\ms-playwright\chromium-*\chrome-win\chrome.exe",
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    )
    
    $chromiumFound = $false
    foreach ($path in $chromiumPaths) {
        $resolvedPaths = Get-ChildItem $path -ErrorAction SilentlyContinue
        if ($resolvedPaths) {
            $chromiumFound = $true
            Test-Result "Chromium Browser" $true "Found at $($resolvedPaths[0].FullName)"
            break
        }
    }
    
    if (-not $chromiumFound) {
        Test-Result "Chromium Browser" $false "Chromium not found in expected locations"
    }
    
    # Test browser automation script
    if (Test-Path "test_browser.py") {
        Write-Log "INFO" "Running browser automation test..."
        try {
            $testOutput = python test_browser.py 2>&1
            if ($LASTEXITCODE -eq 0) {
                Test-Result "Browser Automation Test" $true "Test passed"
            }
            else {
                Test-Result "Browser Automation Test" $false "Test failed: $testOutput"
            }
        }
        catch {
            Test-Result "Browser Automation Test" $false "Could not run test: $($_.Exception.Message)"
        }
    }
    else {
        Test-Result "Browser Test Script" $false "test_browser.py not found" $true
    }
}

function Test-APIEndpoints {
    if ($SkipAPITest) {
        Write-Log "INFO" "Skipping API tests (--SkipAPITest flag)"
        return
    }
    
    Write-Log "INFO" "Testing API endpoints..."
    
    # Start the application in background for testing
    $appProcess = $null
    try {
        Write-Log "INFO" "Starting application for API testing..."
        $appProcess = Start-Process -FilePath "python" -ArgumentList "main.py" -PassThru -WindowStyle Hidden
        
        # Wait for application to start
        Start-Sleep -Seconds 5
        
        # Test health endpoint
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Test-Result "Health Endpoint" $true "API responding on port 8000"
            }
            else {
                Test-Result "Health Endpoint" $false "Unexpected status code: $($response.StatusCode)"
            }
        }
        catch {
            Test-Result "Health Endpoint" $false "API not responding: $($_.Exception.Message)"
        }
        
        # Test other endpoints if available
        $endpoints = @("/api/status", "/api/config")
        foreach ($endpoint in $endpoints) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -TimeoutSec 5 -ErrorAction Stop
                Test-Result "Endpoint: $endpoint" $true "Status: $($response.StatusCode)"
            }
            catch {
                Test-Result "Endpoint: $endpoint" $false "Not accessible" $true
            }
        }
    }
    catch {
        Test-Result "Application Startup" $false "Could not start application: $($_.Exception.Message)"
    }
    finally {
        # Clean up - stop the application
        if ($appProcess -and -not $appProcess.HasExited) {
            Write-Log "INFO" "Stopping test application..."
            $appProcess.Kill()
            $appProcess.WaitForExit(5000)
        }
    }
}

function Test-SystemResources {
    Write-Log "INFO" "Testing system resources..."
    
    # Test available memory
    $totalMemoryGB = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    if ($totalMemoryGB -ge 4) {
        Test-Result "System Memory" $true "${totalMemoryGB}GB available"
    }
    else {
        Test-Result "System Memory" $false "${totalMemoryGB}GB available (4GB+ recommended)" $true
    }
    
    # Test available disk space
    $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
    if ($freeSpaceGB -ge 5) {
        Test-Result "Disk Space" $true "${freeSpaceGB}GB free"
    }
    else {
        Test-Result "Disk Space" $false "${freeSpaceGB}GB free (5GB+ recommended)" $true
    }
    
    # Test CPU cores
    $cpuCores = (Get-WmiObject -Class Win32_Processor).NumberOfCores
    if ($cpuCores -ge 2) {
        Test-Result "CPU Cores" $true "$cpuCores cores available"
    }
    else {
        Test-Result "CPU Cores" $false "$cpuCores cores (2+ recommended)" $true
    }
    
    # Test network connectivity
    try {
        $ping = Test-NetConnection -ComputerName "google.com" -Port 443 -InformationLevel Quiet
        if ($ping) {
            Test-Result "Network Connectivity" $true "Internet connection available"
        }
        else {
            Test-Result "Network Connectivity" $false "No internet connection"
        }
    }
    catch {
        Test-Result "Network Connectivity" $false "Could not test connectivity: $($_.Exception.Message)"
    }
}

function Test-WindowsServices {
    Write-Log "INFO" "Testing Windows services setup..."
    
    # Check if service wrapper exists
    if (Test-Path "service-wrapper.ps1") {
        Test-Result "Service Wrapper" $true "Found service-wrapper.ps1"
    }
    else {
        Test-Result "Service Wrapper" $false "service-wrapper.ps1 not found" $true
    }
    
    # Check for NSSM (if installed)
    try {
        $nssmVersion = nssm --version 2>$null
        if ($nssmVersion) {
            Test-Result "NSSM Service Manager" $true "NSSM installed"
        }
        else {
            Test-Result "NSSM Service Manager" $false "NSSM not installed (optional)" $true
        }
    }
    catch {
        Test-Result "NSSM Service Manager" $false "NSSM not found (optional)" $true
    }
    
    # Check Windows Task Scheduler (alternative to services)
    try {
        $taskExists = Get-ScheduledTask -TaskName "TradeBotSentinel" -ErrorAction SilentlyContinue
        if ($taskExists) {
            Test-Result "Scheduled Task" $true "TradeBotSentinel task found"
        }
        else {
            Test-Result "Scheduled Task" $false "No scheduled task found (optional)" $true
        }
    }
    catch {
        Test-Result "Scheduled Task" $false "Could not check scheduled tasks" $true
    }
}

function Show-Summary {
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor $Purple
    Write-Host "VERIFICATION SUMMARY" -ForegroundColor $Green
    Write-Host "=" * 80 -ForegroundColor $Purple
    Write-Host ""
    
    Write-Host "Test Results:" -ForegroundColor $Yellow
    Write-Host "  ✅ Passed: $($script:TestResults.Passed)" -ForegroundColor $Green
    Write-Host "  ❌ Failed: $($script:TestResults.Failed)" -ForegroundColor $Red
    Write-Host "  ⚠️  Warnings: $($script:TestResults.Warnings)" -ForegroundColor $Yellow
    Write-Host "  📊 Total: $($script:TestResults.Tests.Count)" -ForegroundColor $Blue
    Write-Host ""
    
    # Show failed tests
    if ($script:TestResults.Failed -gt 0) {
        Write-Host "Failed Tests:" -ForegroundColor $Red
        foreach ($test in $script:TestResults.Tests | Where-Object { -not $_.Success -and -not $_.IsWarning }) {
            Write-Host "  ❌ $($test.Name): $($test.Message)" -ForegroundColor $Red
        }
        Write-Host ""
    }
    
    # Show warnings
    if ($script:TestResults.Warnings -gt 0) {
        Write-Host "Warnings:" -ForegroundColor $Yellow
        foreach ($test in $script:TestResults.Tests | Where-Object { $_.IsWarning }) {
            Write-Host "  ⚠️  $($test.Name): $($test.Message)" -ForegroundColor $Yellow
        }
        Write-Host ""
    }
    
    # Overall status
    if ($script:TestResults.Failed -eq 0) {
        Write-Host "🎉 VERIFICATION PASSED" -ForegroundColor $Green
        Write-Host "TradeBot Sentinel is ready to run!" -ForegroundColor $Green
    }
    elseif ($script:TestResults.Failed -le 2) {
        Write-Host "⚠️  VERIFICATION PASSED WITH WARNINGS" -ForegroundColor $Yellow
        Write-Host "TradeBot Sentinel should work, but please address the warnings." -ForegroundColor $Yellow
    }
    else {
        Write-Host "❌ VERIFICATION FAILED" -ForegroundColor $Red
        Write-Host "Please fix the failed tests before running TradeBot Sentinel." -ForegroundColor $Red
    }
    
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor $Yellow
    Write-Host "  1. Fix any failed tests or warnings"
    Write-Host "  2. Configure .env file with your trading credentials"
    Write-Host "  3. Test manually: python main.py"
    Write-Host "  4. For production: Setup Windows service with NSSM"
    Write-Host ""
    
    # Generate report file
    $reportFile = "verification-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $report = @()
    $report += "TradeBot Sentinel - Windows Verification Report"
    $report += "Generated: $(Get-Date)"
    $report += "Environment: $Environment"
    $report += ""
    $report += "Summary:"
    $report += "  Passed: $($script:TestResults.Passed)"
    $report += "  Failed: $($script:TestResults.Failed)"
    $report += "  Warnings: $($script:TestResults.Warnings)"
    $report += ""
    $report += "Detailed Results:"
    
    foreach ($test in $script:TestResults.Tests) {
        $status = if ($test.IsWarning) { "WARNING" } elseif ($test.Success) { "PASS" } else { "FAIL" }
        $report += "  [$status] $($test.Name): $($test.Message)"
    }
    
    $report | Out-File -FilePath $reportFile -Encoding UTF8
    Write-Host "📄 Detailed report saved to: $reportFile" -ForegroundColor $Blue
}

function Main {
    Write-Host "=" * 80 -ForegroundColor $Purple
    Write-Host "TradeBot Sentinel - Windows Deployment Verification" -ForegroundColor $Green
    Write-Host "=" * 80 -ForegroundColor $Purple
    Write-Host ""
    
    Write-Log "INFO" "Starting verification for environment: $Environment"
    Write-Log "INFO" "Current directory: $(Get-Location)"
    Write-Host ""
    
    # Run all tests
    Test-SystemResources
    Test-PythonEnvironment
    Test-ProjectFiles
    Test-BrowserSetup
    Test-APIEndpoints
    Test-WindowsServices
    
    # Show summary
    Show-Summary
    
    # Return exit code based on results
    if ($script:TestResults.Failed -eq 0) {
        exit 0
    }
    else {
        exit 1
    }
}

# Show help if requested
if ($args -contains "-h" -or $args -contains "--help") {
    Write-Host "TradeBot Sentinel - Windows Deployment Verification" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Usage: .\verify-windows-deployment.ps1 [OPTIONS]" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Options:" -ForegroundColor $Yellow
    Write-Host "  -Environment <env>     Environment to verify [default: development]"
    Write-Host "  -SkipBrowserTest      Skip browser automation tests"
    Write-Host "  -SkipAPITest          Skip API endpoint tests"
    Write-Host "  -Verbose              Enable verbose output"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Yellow
    Write-Host "  .\verify-windows-deployment.ps1                    # Full verification"
    Write-Host "  .\verify-windows-deployment.ps1 -SkipBrowserTest   # Skip browser tests"
    Write-Host "  .\verify-windows-deployment.ps1 -Verbose           # Verbose output"
    Write-Host ""
    exit 0
}

# Run main function
try {
    Main
}
catch {
    Write-Log "ERROR" "Verification failed: $($_.Exception.Message)"
    Write-Log "ERROR" "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}