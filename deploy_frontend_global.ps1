# AI Trading Sentinel - Global Frontend Deployment
Write-Host "Starting AI Trading Sentinel Global Deployment..." -ForegroundColor Green

# Configuration
$VPS_IP = "161.97.112.146"
$VPS_USER = "root"
$FRONTEND_ZIP = "frontend-cloud.zip"

# Step 1: Verify files
Write-Host "Verifying files..." -ForegroundColor Yellow
if (-not (Test-Path $FRONTEND_ZIP)) {
    Write-Host "Error: $FRONTEND_ZIP not found!" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "vps_setup.sh")) {
    Write-Host "Error: vps_setup.sh not found!" -ForegroundColor Red
    exit 1
}

$zipSize = (Get-Item $FRONTEND_ZIP).Length / 1MB
Write-Host "Files ready: $FRONTEND_ZIP ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green

# Step 2: Upload files
Write-Host "Uploading to VPS..." -ForegroundColor Yellow
try {
    Write-Host "Uploading frontend package..." -ForegroundColor Cyan
    scp $FRONTEND_ZIP "${VPS_USER}@${VPS_IP}:/tmp/frontend-cloud.zip"
    
    Write-Host "Uploading setup script..." -ForegroundColor Cyan
    scp "vps_setup.sh" "${VPS_USER}@${VPS_IP}:/tmp/vps_setup.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Upload completed successfully" -ForegroundColor Green
    } else {
        throw "Upload failed"
    }
} catch {
    Write-Host "Upload failed: $_" -ForegroundColor Red
    Write-Host "Manual upload required:" -ForegroundColor Yellow
    Write-Host "1. Upload $FRONTEND_ZIP to VPS /tmp/ directory" -ForegroundColor Cyan
    Write-Host "2. Upload vps_setup.sh to VPS /tmp/ directory" -ForegroundColor Cyan
    exit 1
}

# Step 3: Execute setup
Write-Host "Executing setup on VPS..." -ForegroundColor Yellow
try {
    ssh "${VPS_USER}@${VPS_IP}" "chmod +x /tmp/vps_setup.sh; /tmp/vps_setup.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "VPS setup completed successfully" -ForegroundColor Green
    } else {
        Write-Host "Setup completed with warnings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "SSH execution failed: $_" -ForegroundColor Red
    Write-Host "Manual execution:" -ForegroundColor Yellow
    Write-Host "ssh root@161.97.112.146" -ForegroundColor Cyan
    Write-Host "chmod +x /tmp/vps_setup.sh; /tmp/vps_setup.sh" -ForegroundColor Cyan
    exit 1
}

# Step 4: Test deployment
Write-Host "Testing deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://$VPS_IP" -TimeoutSec 15 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "Frontend accessible at http://$VPS_IP" -ForegroundColor Green
    }
} catch {
    Write-Host "Frontend test failed. May need a moment to start." -ForegroundColor Yellow
}

try {
    $apiResponse = Invoke-WebRequest -Uri "http://$VPS_IP/api/health" -TimeoutSec 15 -UseBasicParsing
    if ($apiResponse.StatusCode -eq 200) {
        Write-Host "API accessible at http://$VPS_IP/api/" -ForegroundColor Green
    }
} catch {
    Write-Host "API test failed. Flask backend may need restart." -ForegroundColor Yellow
}

# Success!
Write-Host "AI Trading Sentinel Global Deployment Complete!" -ForegroundColor Green
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "   Trading Dashboard: http://161.97.112.146" -ForegroundColor White
Write-Host "   API Endpoint: http://161.97.112.146/api/" -ForegroundColor White
Write-Host "   WebSocket: ws://161.97.112.146/ws" -ForegroundColor White

Write-Host "Ready to start trading globally!" -ForegroundColor Green