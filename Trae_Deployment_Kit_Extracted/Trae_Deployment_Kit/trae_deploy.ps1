# PowerShell script for deploying Trae AI Trading Sentinel to a VPS

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
    [switch]$NotifySlack,
    
    [Parameter(Mandatory=$false)]
    [string]$SlackWebhookUrl
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Define colors for console output
$colorSuccess = "Green"
$colorError = "Red"
$colorInfo = "Cyan"
$colorWarning = "Yellow"

# Function to display colored messages
function Write-ColoredMessage {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

# Function to send Slack notifications
function Send-SlackNotification {
    param (
        [string]$Message,
        [string]$Status = "info",
        [string]$WebhookUrl = $SlackWebhookUrl
    )
    
    if (-not $NotifySlack -or [string]::IsNullOrEmpty($WebhookUrl)) {
        return
    }
    
    # Determine color based on status
    $color = switch ($Status) {
        "success" { "good" }
        "error" { "danger" }
        default { "#0000FF" } # Blue for info
    }
    
    $payload = @{
        attachments = @(
            @{
                color = $color
                text = $Message
                fields = @(
                    @{
                        title = "Environment"
                        value = "Production"
                        short = $true
                    },
                    @{
                        title = "Time"
                        value = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
                        short = $true
                    }
                )
            }
        )
    } | ConvertTo-Json -Depth 10
    
    try {
        Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload -ContentType "application/json"
    } catch {
        Write-ColoredMessage "Failed to send Slack notification: $_" $colorError
    }
}

# Validate SSH parameters
if ([string]::IsNullOrEmpty($SshKeyPath)) {
    Write-ColoredMessage "No SSH key path provided. Will attempt to use password authentication or default key." $colorWarning
    $SshKeyParam = ""
} else {
    if (-not (Test-Path $SshKeyPath)) {
        Write-ColoredMessage "SSH key file not found at path: $SshKeyPath" $colorError
        exit 1
    }
    $SshKeyParam = "-i '$SshKeyPath'"
}

# Check if rsync is available
$rsyncAvailable = $null -ne (Get-Command "rsync" -ErrorAction SilentlyContinue)

# Start deployment
Write-ColoredMessage "Starting deployment to VPS: $VpsIp" $colorInfo
Send-SlackNotification -Message "Starting deployment to VPS: $VpsIp" -Status "info"

# Create remote directory structure
try {
    Write-ColoredMessage "Creating remote directory structure..." $colorInfo
    ssh -p $SshPort $SshKeyParam "$VpsUser@$VpsIp" "mkdir -p ~/ai-trading-sentinel"
} catch {
    $errorMessage = "Failed to create remote directory structure: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Transfer files
try {
    Write-ColoredMessage "Transferring files to VPS..." $colorInfo
    
    if ($rsyncAvailable) {
        # Use rsync for file transfer (more efficient)
        rsync -avz --exclude '.git' --exclude '__pycache__' --exclude 'venv' --exclude 'node_modules' -e "ssh -p $SshPort $SshKeyParam" ./ "$VpsUser@$VpsIp:~/ai-trading-sentinel"
    } else {
        # Fallback to scp
        Write-ColoredMessage "rsync not found, falling back to scp (slower)" $colorWarning
        scp -P $SshPort $SshKeyParam -r ./* "$VpsUser@$VpsIp:~/ai-trading-sentinel"
    }
} catch {
    $errorMessage = "Failed to transfer files: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Transfer environment file if specified
if (-not [string]::IsNullOrEmpty($EnvFilePath)) {
    try {
        Write-ColoredMessage "Transferring environment file..." $colorInfo
        scp -P $SshPort $SshKeyParam "$EnvFilePath" "$VpsUser@$VpsIp:~/ai-trading-sentinel/.env"
    } catch {
        $errorMessage = "Failed to transfer environment file: $_"
        Write-ColoredMessage $errorMessage $colorError
        Send-SlackNotification -Message $errorMessage -Status "error"
        exit 1
    }
}

# Set up Python environment and install dependencies
try {
    Write-ColoredMessage "Setting up Python environment and installing dependencies..." $colorInfo
    ssh -p $SshPort $SshKeyParam "$VpsUser@$VpsIp" "cd ~/ai-trading-sentinel && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
} catch {
    $errorMessage = "Failed to set up Python environment: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Set up frontend dependencies
try {
    Write-ColoredMessage "Setting up frontend dependencies..." $colorInfo
    ssh -p $SshPort $SshKeyParam "$VpsUser@$VpsIp" "cd ~/ai-trading-sentinel/frontend && npm install"
} catch {
    $errorMessage = "Failed to set up frontend dependencies: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Create and move systemd service file
try {
    Write-ColoredMessage "Setting up systemd service..." $colorInfo
    ssh -p $SshPort $SshKeyParam "$VpsUser@$VpsIp" "sudo cp ~/ai-trading-sentinel/trae.service /etc/systemd/system/"
} catch {
    $errorMessage = "Failed to set up systemd service: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Enable and start the service
try {
    Write-ColoredMessage "Enabling and starting the service..." $colorInfo
    ssh -p $SshPort $SshKeyParam "$VpsUser@$VpsIp" "sudo systemctl daemon-reload && sudo systemctl enable trae && sudo systemctl restart trae"
} catch {
    $errorMessage = "Failed to enable and start the service: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Check service status
try {
    Write-ColoredMessage "Checking service status..." $colorInfo
    $serviceStatus = ssh -p $SshPort $SshKeyParam "$VpsUser@$VpsIp" "sudo systemctl status trae"
    Write-ColoredMessage $serviceStatus $colorInfo
} catch {
    $errorMessage = "Failed to check service status: $_"
    Write-ColoredMessage $errorMessage $colorError
    Send-SlackNotification -Message $errorMessage -Status "error"
    exit 1
}

# Deployment successful
Write-ColoredMessage "Deployment completed successfully!" $colorSuccess
Send-SlackNotification -Message "Deployment to VPS $VpsIp completed successfully!" -Status "success"