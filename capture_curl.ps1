# Bulenox cURL Command Capture Tool
Write-Host "Bulenox cURL Command Capture Tool" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

Write-Host "Setting environment variables..." -ForegroundColor Yellow
# Set your actual Bulenox credentials here
$env:BX64883 = "BX64883"  # Username
$env:XujhMzFf6K = "XujhMzFf6K"  # Password

Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install

Write-Host ""
Write-Host "Running Playwright script to capture cURL command..." -ForegroundColor Yellow
node bulenox_trade.js

Write-Host ""
if (Test-Path -Path "trade.sh") {
    Write-Host "cURL command captured successfully!" -ForegroundColor Green
    Write-Host "The command has been saved to trade.sh and trade_request.py" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can run the command with: bash trade.sh" -ForegroundColor Cyan
} else {
    Write-Host "Failed to capture cURL command." -ForegroundColor Red
    Write-Host "Please check the console output for errors." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")