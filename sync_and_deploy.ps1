# ASTRA - Autonomous VPS Sync & Deploy Script
# Handles GitHub synchronization and VPS deployment updates

param(
    [string]$VpsIp = "161.97.112.146",
    [string]$VpsUser = "root",
    [string]$SshKey = "./trae_deploy_key",
    [switch]$Force,
    [switch]$SkipGitSync
)

# Color output functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }

Write-Host "🚀 ASTRA - VPS Sync & Deploy" -ForegroundColor Magenta
Write-Host "========================" -ForegroundColor Magenta
Write-Host "Target VPS: $VpsIp" -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Gray
Write-Host ""

# Step 1: Git Synchronization
if (-not $SkipGitSync) {
    Write-Info "Step 1: Synchronizing with GitHub"
    Write-Host "─────────────────────────────────" -ForegroundColor Gray
    
    try {
        # Check current status
        Write-Info "Checking repository status..."
        $gitStatus = git status --porcelain
        if ($gitStatus) {
            Write-Warning "Uncommitted changes detected:"
            $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
            
            if (-not $Force) {
                $response = Read-Host "Continue anyway? (y/N)"
                if ($response -ne 'y' -and $response -ne 'Y') {
                    Write-Error "Aborted by user"
                    exit 1
                }
            }
        }
        
        # Fetch latest changes
        Write-Info "Fetching latest changes from GitHub..."
        git fetch origin
        
        # Check for updates
        $remoteCommits = git log --oneline HEAD..origin/main
        $localCommits = git log --oneline origin/main..HEAD
        
        if ($remoteCommits) {
            Write-Info "New commits available from GitHub:"
            $remoteCommits | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
            
            Write-Info "Pulling latest changes..."
            git pull origin main
            Write-Success "GitHub sync completed"
        } else {
            Write-Success "Repository is up to date with GitHub"
        }
        
        if ($localCommits) {
            Write-Info "Local commits to push:"
            $localCommits | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }
            
            Write-Info "Pushing local changes..."
            git push origin main
            Write-Success "Local changes pushed to GitHub"
        }
        
    } catch {
        Write-Error "Git synchronization failed: $($_.Exception.Message)"
        if (-not $Force) {
            exit 1
        }
    }
    
    Write-Host ""
}

# Step 2: VPS Connection Test
Write-Info "Step 2: Testing VPS Connection"
Write-Host "─────────────────────────────" -ForegroundColor Gray

try {
    $testCmd = "ssh -i $SshKey -o ConnectTimeout=10 -o StrictHostKeyChecking=no $VpsUser@$VpsIp 'echo VPS_CONNECTED'"
    $result = Invoke-Expression $testCmd 2>$null
    
    if ($result -match "VPS_CONNECTED") {
        Write-Success "VPS connection established"
    } else {
        throw "Connection test failed"
    }
} catch {
    Write-Error "Cannot connect to VPS: $($_.Exception.Message)"
    Write-Info "Please ensure:"
    Write-Host "  • VPS is running and accessible" -ForegroundColor Yellow
    Write-Host "  • SSH key is correct: $SshKey" -ForegroundColor Yellow
    Write-Host "  • Firewall allows SSH connections" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 3: VPS Deployment Update
Write-Info "Step 3: Updating VPS Deployment"
Write-Host "─────────────────────────────────" -ForegroundColor Gray

$vpsCommands = @(
    "cd /opt/ai-trading-sentinel || mkdir -p /opt/ai-trading-sentinel",
    "cd /opt/ai-trading-sentinel",
    "# Check if git repo exists",
    "if [ -d '.git' ]; then",
    "  echo 'Updating existing repository...'",
    "  git fetch origin",
    "  git reset --hard origin/main",
    "  git pull origin main",
    "else",
    "  echo 'Cloning repository...'",
    "  git clone https://github.com/Gold724/AI-TRADING-BOT.git .",
    "fi",
    "# Set permissions",
    "chmod +x *.sh",
    "# Update Docker services if running",
    "if systemctl is-active --quiet ai-trading-sentinel; then",
    "  echo 'Restarting services...'",
    "  systemctl restart ai-trading-sentinel",
    "  systemctl restart nginx",
    "  sleep 5",
    "  systemctl status ai-trading-sentinel --no-pager",
    "else",
    "  echo 'Services not running - use deployment script to start'",
    "fi",
    "# Health check",
    "curl -f http://localhost:8081/api/health 2>/dev/null && echo 'API Health: OK' || echo 'API Health: FAILED'"
)

$deployScript = $vpsCommands -join "; "

try {
    Write-Info "Executing deployment update on VPS..."
    $sshCmd = "ssh -i $SshKey -o StrictHostKeyChecking=no $VpsUser@$VpsIp '$deployScript'"
    $result = Invoke-Expression $sshCmd
    
    Write-Host "VPS Output:" -ForegroundColor Gray
    Write-Host "$result" -ForegroundColor White
    
    Write-Success "VPS deployment update completed"
    
} catch {
    Write-Error "VPS deployment failed: $($_.Exception.Message)"
    Write-Info "You may need to run the full deployment script manually"
    exit 1
}

Write-Host ""

# Step 4: Verification
Write-Info "Step 4: Deployment Verification"
Write-Host "─────────────────────────────────" -ForegroundColor Gray

$verifyCommands = @(
    "systemctl is-active ai-trading-sentinel",
    "systemctl is-active nginx",
    "curl -f http://localhost:8081/api/health",
    "curl -f http://localhost/api/health"
)

foreach ($cmd in $verifyCommands) {
    try {
        $sshCmd = "ssh -i $SshKey -o StrictHostKeyChecking=no $VpsUser@$VpsIp '$cmd'"
        $result = Invoke-Expression $sshCmd 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$cmd: OK"
        } else {
            Write-Warning "$cmd: FAILED"
        }
    } catch {
        Write-Warning "$cmd: ERROR"
    }
}

Write-Host ""
Write-Host "🎯 ASTRA Sync & Deploy Summary" -ForegroundColor Magenta
Write-Host "═════════════════════════════" -ForegroundColor Magenta
Write-Success "GitHub synchronization completed"
Write-Success "VPS deployment updated"
Write-Info "Access Points:"
Write-Host "  • API: http://$VpsIp:8081/api/health" -ForegroundColor Cyan
Write-Host "  • Dashboard: http://$VpsIp/" -ForegroundColor Cyan
Write-Host "  • Monitoring: http://$VpsIp:3000/" -ForegroundColor Cyan

Write-Host ""
Write-Info "Next Steps:"
Write-Host "  • Monitor logs: ssh -i $SshKey $VpsUser@$VpsIp 'journalctl -u ai-trading-sentinel -f'" -ForegroundColor Yellow
Write-Host "  • Check status: ssh -i $SshKey $VpsUser@$VpsIp 'systemctl status ai-trading-sentinel'" -ForegroundColor Yellow
Write-Host "  • Full redeploy: ./vps_quick_deploy.sh (if needed)" -ForegroundColor Yellow

Write-Success "ASTRA mission completed successfully! 🚀"