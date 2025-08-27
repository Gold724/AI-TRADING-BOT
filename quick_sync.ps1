# Quick VPS Sync - Fast update for existing deployments
# Usage: .\quick_sync.ps1

$VpsIp = "161.97.112.146"
$VpsUser = "root"
$SshKey = "./trae_deploy_key"

Write-Host "⚡ Quick VPS Sync" -ForegroundColor Yellow
Write-Host "Target: $VpsIp" -ForegroundColor Cyan

# Test connection
Write-Host "Testing connection..." -ForegroundColor Gray
$testResult = ssh -i $SshKey -o ConnectTimeout=5 -o StrictHostKeyChecking=no $VpsUser@$VpsIp "echo 'Connected'" 2>$null

if ($testResult -match "Connected") {
    Write-Host "✅ Connection OK" -ForegroundColor Green
    
    # Quick update commands
    $updateCmd = @"
cd /opt/ai-trading-sentinel && \
git fetch origin && \
git reset --hard origin/main && \
git pull origin main && \
echo 'Repository updated' && \
if systemctl is-active --quiet ai-trading-sentinel; then \
  systemctl restart ai-trading-sentinel && \
  echo 'Service restarted'; \
else \
  echo 'Service not running'; \
fi && \
curl -f http://localhost:8081/api/health 2>/dev/null && echo 'Health: OK' || echo 'Health: FAILED'
"@
    
    Write-Host "Updating VPS..." -ForegroundColor Gray
    $result = ssh -i $SshKey -o StrictHostKeyChecking=no $VpsUser@$VpsIp $updateCmd
    
    Write-Host "Result:" -ForegroundColor Cyan
    Write-Host $result -ForegroundColor White
    
    Write-Host "✅ Quick sync completed" -ForegroundColor Green
} else {
    Write-Host "❌ Cannot connect to VPS" -ForegroundColor Red
    Write-Host "Try: .\sync_and_deploy.ps1 for full sync" -ForegroundColor Yellow
}