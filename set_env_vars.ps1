# Set environment variables for TradeBot Sentinel
# Replace with your actual Bulenox credentials

$env:BULENOX_USERNAME = "your_username_here"
$env:BULENOX_PASSWORD = "your_password_here"

Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "BULENOX_USERNAME: $env:BULENOX_USERNAME" -ForegroundColor Cyan
Write-Host "BULENOX_PASSWORD: [HIDDEN]" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now you can run:" -ForegroundColor Yellow
Write-Host "python tradebot_sentinel_playwright.py" -ForegroundColor White
Write-Host "or" -ForegroundColor White
Write-Host "python tradebot_sentinel_playwright.py --headful" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")