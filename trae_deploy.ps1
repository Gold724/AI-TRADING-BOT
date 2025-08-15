# Trae AI Trading Sentinel Deployment Script for Windows
# This script automates the deployment process to a Contabo VPS

param (
    [Parameter(Mandatory=$false)]
    [string]$VpsIp = "161.97.112.146",
    
    [Parameter(Mandatory=$false)]
    [string]$VpsUser = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$SshPort = "22",
    
    [Parameter(Mandatory=$false)]
    [string]$SshKeyPath,
    
    [Parameter(Mandatory=$false)]
    [string]$EnvFilePath,
    
    [Parameter(Mandatory=$false)]
    [switch]$NotifySlack = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$SlackWebhookUrl
)

$ErrorActionPreference = "Stop"
$deploymentStartTime = Get-Date

# Function to send Slack notifications
function Send-SlackNotification {
    param (
        [string]$message,
        [string]$status = "info" # info, success, error
    )
    
    if (-not $NotifySlack -or [string]::IsNullOrEmpty($SlackWebhookUrl)) {
        return
    }
    
    $color = switch ($status) {
        "success" { "good" }
        "error" { "danger" }
        default { "#0000FF" } # info - blue
    }
    
    $payload = @{
        attachments = @(
            @{
                fallback = $message
                color = $color
                text = $message
                fields = @(
                    @{
                        title = "Environment"
                        value = "Production"
                        short = $true
                    },
                    @{
                        title = "Timestamp"
                        value = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                        short = $true
                    }
                )
            }
        )
    } | ConvertTo-Json -Depth 4
    
    try {
        Invoke-RestMethod -Uri $SlackWebhookUrl -Method Post -Body $payload -ContentType "application/json"
        Write-Host "Slack notification sent: $message"
    } catch {
        Write-Host "Failed to send Slack notification: $_" -ForegroundColor Red
    }
}

# Validate SSH connection parameters
if ([string]::IsNullOrEmpty($SshKeyPath)) {
    Write-Host "No SSH key provided. Will use password authentication." -ForegroundColor Yellow
    $sshParams = "-o StrictHostKeyChecking=no"
} else {
    if (-not (Test-Path $SshKeyPath)) {
        Write-Host "SSH key file not found at: $SshKeyPath" -ForegroundColor Red
        exit 1
    }
    $sshParams = "-i `"$SshKeyPath`" -o StrictHostKeyChecking=no"
}

# Check if rsync is available
$rsyncAvailable = $null -ne (Get-Command "rsync" -ErrorAction SilentlyContinue)
if (-not $rsyncAvailable) {
    Write-Host "rsync not found. Will use scp for file transfer." -ForegroundColor Yellow
}

try {
    # Start deployment
    Write-Host "Starting deployment to $VpsIp..." -ForegroundColor Cyan
    Send-SlackNotification -message "🚀 Starting deployment of Trae AI Trading Sentinel to $VpsIp"
    
    # Create remote directory structure
    Write-Host "Creating remote directory structure..." -ForegroundColor Cyan
    $sshTarget = "${VpsUser}@${VpsIp}"
    $mkdirCommand = "mkdir -p ~/ai-trading-sentinel/logs"
    ssh $sshParams -p $SshPort "$sshTarget" "$mkdirCommand"
    
    # Transfer files
    Write-Host "Transferring files to VPS..." -ForegroundColor Cyan
    if ($rsyncAvailable) {
        # Using rsync for efficient file transfer
        $excludeParams = "--exclude '.git' --exclude '__pycache__' --exclude 'venv' --exclude 'node_modules'"
        $remoteDestination = "${VpsUser}@${VpsIp}:~/ai-trading-sentinel/"
        $command = "rsync -avz $excludeParams -e \"ssh $sshParams -p $SshPort\" . `"$remoteDestination`""
        Invoke-Expression $command
    } else {
        # Fallback to scp
        $remoteDestination = "${VpsUser}@${VpsIp}:~/ai-trading-sentinel/"
        scp $sshParams -P $SshPort -r ./* "$remoteDestination"
    }
    
    # Transfer environment file if specified
    if (-not [string]::IsNullOrEmpty($EnvFilePath)) {
        if (Test-Path $EnvFilePath) {
            Write-Host "Transferring environment file..." -ForegroundColor Cyan
            $envDestination = "${VpsUser}@${VpsIp}:~/ai-trading-sentinel/.env"
            scp $sshParams -P $SshPort "$EnvFilePath" "$envDestination"
        } else {
            Write-Host "Environment file not found at: $EnvFilePath" -ForegroundColor Red
            Send-SlackNotification -message "⚠️ Environment file not found at: $EnvFilePath" -status "error"
        }
    }
    
    # Setup virtual environment and install dependencies
    Write-Host "Setting up virtual environment and installing dependencies..." -ForegroundColor Cyan
    $sshTarget = "${VpsUser}@${VpsIp}"
    $setupCommand = "cd ~/ai-trading-sentinel && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    ssh $sshParams -p $SshPort "$sshTarget" "$setupCommand"
    
    # Setup frontend dependencies
    Write-Host "Setting up frontend dependencies..." -ForegroundColor Cyan
    $sshTarget = "${VpsUser}@${VpsIp}"
    $frontendCommand = "cd ~/ai-trading-sentinel/frontend && npm install"
    ssh $sshParams -p $SshPort "$sshTarget" "$frontendCommand"
    
    # Create systemd service file
    Write-Host "Creating systemd service file..." -ForegroundColor Cyan
    $serviceFileContent = @"
[Unit]
Description=Trae AI Trading Bot
After=network.target

[Service]
User=$VpsUser
WorkingDirectory=/home/$VpsUser/ai-trading-sentinel
ExecStart=/home/$VpsUser/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"@
    
    $sshTarget = "${VpsUser}@${VpsIp}"
    $serviceFileContent | ssh $sshParams -p $SshPort "$sshTarget" "cat > ~/trae.service"
    ssh $sshParams -p $SshPort "$sshTarget" "sudo mv ~/trae.service /etc/systemd/system/trae.service"
    
    # Enable and start the service
    Write-Host "Enabling and starting the service..." -ForegroundColor Cyan
    $serviceCommand = "sudo systemctl daemon-reload && sudo systemctl enable trae && sudo systemctl restart trae"
    ssh $sshParams -p $SshPort "$sshTarget" "$serviceCommand"
    
    # Check service status
    Write-Host "Checking service status..." -ForegroundColor Cyan
    $statusCommand = "sudo systemctl status trae"
    ssh $sshParams -p $SshPort "$sshTarget" "$statusCommand"
    
    # Deployment completed
    $deploymentEndTime = Get-Date
    $deploymentDuration = $deploymentEndTime - $deploymentStartTime
    $durationMessage = "Deployment completed in {0:mm} minutes and {0:ss} seconds" -f $deploymentDuration
    
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
    Write-Host $durationMessage -ForegroundColor Green
    Send-SlackNotification -message "✅ Trae AI Trading Sentinel deployed successfully to $VpsIp! $durationMessage" -status "success"
    
} catch {
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    Send-SlackNotification -message "❌ Deployment failed: $_" -status "error"
    exit 1
}