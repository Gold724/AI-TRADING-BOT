# Bulenox API Examples for PowerShell

# Set your API key
$API_KEY = "your_api_key_here"

# Base URL
$BASE_URL = "http://localhost:5000"

# Common headers
$headers = @{
    "Authorization" = "Bearer $API_KEY"
    "Content-Type" = "application/json"
}

# 1. Health Check
function Test-BulenoxHealth {
    Invoke-RestMethod -Method GET -Uri "$BASE_URL/api/health"
}

# 2. Login
function Connect-Bulenox {
    param(
        [bool]$Debug = $true
    )
    
    $body = @{
        debug = $Debug
    } | ConvertTo-Json
    
    Invoke-RestMethod -Method POST -Uri "$BASE_URL/api/login" -Headers $headers -Body $body
}

# 3. Execute Trade
function New-BulenoxTrade {
    param(
        [string]$Symbol = "EURUSD",
        [string]$Direction = "buy",
        [double]$Quantity = 0.01,
        [double]$TakeProfit = 1.0800,
        [double]$StopLoss = 1.0700,
        [bool]$Debug = $true
    )
    
    $body = @{
        symbol = $Symbol
        direction = $Direction
        quantity = $Quantity
        tp = $TakeProfit
        sl = $StopLoss
        debug = $Debug
    } | ConvertTo-Json
    
    Invoke-RestMethod -Method POST -Uri "$BASE_URL/api/trade" -Headers $headers -Body $body
}

# 4. Send Webhook Signal
function Send-BulenoxSignal {
    param(
        [string]$AccountId = "BX64883",
        [string]$Symbol = "EURUSD",
        [string]$Side = "buy",
        [double]$Quantity = 0.01,
        [double]$StopLoss = $null,
        [double]$TakeProfit = $null
    )
    
    $signal = @{
        symbol = $Symbol
        side = $Side
        quantity = $Quantity
    }
    
    if ($StopLoss) { $signal.stopLoss = $StopLoss }
    if ($TakeProfit) { $signal.takeProfit = $TakeProfit }
    
    $body = @{
        account_id = $AccountId
        signal = $signal
    } | ConvertTo-Json -Depth 3
    
    Invoke-RestMethod -Method POST -Uri "$BASE_URL/api/webhook" -Headers $headers -Body $body
}

# 5. Logout
function Disconnect-Bulenox {
    Invoke-RestMethod -Method POST -Uri "$BASE_URL/api/logout" -Headers $headers
}

# Example usage
Write-Host "Testing Bulenox API Health..."
Test-BulenoxHealth

Write-Host "\nLogging into Bulenox..."
# Connect-Bulenox

Write-Host "\nExecuting a trade (commented out for safety)..."
# New-BulenoxTrade -Symbol "EURUSD" -Direction "buy" -Quantity 0.01

Write-Host "\nSending a webhook signal (commented out for safety)..."
# Send-BulenoxSignal -Symbol "BTCUSDT" -Side "buy" -Quantity 0.001

Write-Host "\nLogging out (commented out for safety)..."
# Disconnect-Bulenox

Write-Host "\nTo use these functions, uncomment the examples above or call them directly."
Write-Host "Remember to set your API key at the top of the script."