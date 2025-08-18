# Launch Chrome with Debug Mode for Bulenox Network Interception

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 LAUNCHING CHROME WITH DEBUG MODE" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Using Profile: Profile 13" -ForegroundColor Green
Write-Host "Debug Port: 9222" -ForegroundColor Green
Write-Host ""
Write-Host "After Chrome opens:" -ForegroundColor White
Write-Host "1. Navigate to Bulenox and login" -ForegroundColor Gray
Write-Host "2. Run: python bulenox_network_interceptor.py" -ForegroundColor Gray
Write-Host "3. Perform trading actions" -ForegroundColor Gray
Write-Host "4. Press Ctrl+C to stop and save logs" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Close any existing Chrome instances
Write-Host "🔄 Closing existing Chrome instances..." -ForegroundColor Yellow
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Chrome executable paths (try common locations)
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chromeExe = $null
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chromeExe = $path
        break
    }
}

if (-not $chromeExe) {
    Write-Host "❌ Chrome executable not found!" -ForegroundColor Red
    Write-Host "Please install Google Chrome or update the path in this script." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📍 Found Chrome: $chromeExe" -ForegroundColor Green

# Launch Chrome with debugging enabled
$arguments = @(
    "--remote-debugging-port=9222",
    "--user-data-dir=`"C:\Users\Admin\AppData\Local\Google\Chrome\User Data`"",
    "--profile-directory=`"Profile 13`"",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--no-first-run",
    "--disable-default-apps"
)

Write-Host "🚀 Launching Chrome with debugging..." -ForegroundColor Yellow

try {
    Start-Process -FilePath $chromeExe -ArgumentList $arguments -WindowStyle Normal
    
    Write-Host ""
    Write-Host "✅ Chrome launched with debugging enabled!" -ForegroundColor Green
    Write-Host "🌐 You can now navigate to Bulenox" -ForegroundColor Cyan
    Write-Host "🤖 Run the interceptor: python bulenox_network_interceptor.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Debug endpoint: http://localhost:9222" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to launch Chrome: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "Press Enter to continue"