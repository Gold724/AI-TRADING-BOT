# Trae AI Trading Bot Health Check Script
# This script checks if the trae service is running and sends Slack notifications if it fails

param (
    [string]$SlackWebhookUrl = $env:SLACK_WEBHOOK_URL,
    [switch]$RestartOnFailure = $false,
    [string]$ServiceName = "trae",
    [int]$MaxRetries = 3,
    [int]$RetryDelay = 30  # seconds
)

# Colors for console output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

# Function to send Slack notification
function Send-SlackNotification {
    param (
        [string]$Message,
        [string]$WebhookUrl,
        [string]$Status = "failure"  # "success", "failure", "warning"
    )

    if ([string]::IsNullOrEmpty($WebhookUrl)) {
        Write-Host "Slack webhook URL not provided. Skipping notification." -ForegroundColor $WarningColor
        return $false
    }

    try {
        # Get hostname and timestamp
        $Hostname = [System.Net.Dns]::GetHostName()
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        # Set emoji based on status
        $Emoji = switch ($Status) {
            "success" { ":white_check_mark:" }
            "warning" { ":warning:" }
            "failure" { ":x:" }
            default { ":information_source:" }
        }
        
        # Format message
        $FormattedMessage = "$Emoji *Trae AI Trading Bot Health Check* $Emoji\n"
        $FormattedMessage += "*Status:* $Status\n"
        $FormattedMessage += "*Host:* $Hostname\n"
        $FormattedMessage += "*Time:* $Timestamp\n"
        $FormattedMessage += "*Message:* $Message"
        
        # Prepare payload
        $Payload = @{
            text = $FormattedMessage
        } | ConvertTo-Json
        
        # Send to Slack
        $Response = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $Payload -ContentType "application/json"
        Write-Host "Slack notification sent." -ForegroundColor $InfoColor
        return $true
    }
    catch {
        Write-Host "Error sending Slack notification: $_" -ForegroundColor $ErrorColor
        return $false
    }
}

# Function to check service status
function Check-ServiceStatus {
    param (
        [string]$ServiceName
    )
    
    try {
        $Service = Get-Service -Name $ServiceName -ErrorAction Stop
        return $Service
    }
    catch {
        Write-Host "Error checking service status: $_" -ForegroundColor $ErrorColor
        return $null
    }
}

# Function to restart service
function Restart-TraeService {
    param (
        [string]$ServiceName,
        [int]$MaxRetries,
        [int]$RetryDelay
    )
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        Write-Host "Attempting to restart service (Attempt $i of $MaxRetries)..." -ForegroundColor $InfoColor
        
        try {
            Restart-Service -Name $ServiceName -Force -ErrorAction Stop
            Start-Sleep -Seconds 5  # Wait for service to start
            
            $Service = Get-Service -Name $ServiceName -ErrorAction Stop
            if ($Service.Status -eq "Running") {
                Write-Host "Service restarted successfully." -ForegroundColor $SuccessColor
                return $true
            }
            else {
                Write-Host "Service failed to restart. Status: $($Service.Status)" -ForegroundColor $WarningColor
            }
        }
        catch {
            Write-Host "Error restarting service: $_" -ForegroundColor $ErrorColor
        }
        
        if ($i -lt $MaxRetries) {
            Write-Host "Waiting $RetryDelay seconds before next retry..." -ForegroundColor $InfoColor
            Start-Sleep -Seconds $RetryDelay
        }
    }
    
    Write-Host "Failed to restart service after $MaxRetries attempts." -ForegroundColor $ErrorColor
    return $false
}

# Main health check logic
Write-Host "Starting Trae AI Trading Bot health check..." -ForegroundColor $InfoColor

# Check if service exists and get its status
$Service = Check-ServiceStatus -ServiceName $ServiceName

if ($null -eq $Service) {
    $ErrorMessage = "Service '$ServiceName' not found. Please check if it's installed correctly."
    Write-Host $ErrorMessage -ForegroundColor $ErrorColor
    Write-Host ""
    Write-Host "To set up the service, run the setup_windows_service.ps1 script as Administrator:" -ForegroundColor $InfoColor
    Write-Host "  .\setup_windows_service.ps1" -ForegroundColor $InfoColor
    Write-Host ""
    Write-Host "For more information, see WINDOWS_SERVICE_SETUP.md" -ForegroundColor $InfoColor
    Send-SlackNotification -Message $ErrorMessage -WebhookUrl $SlackWebhookUrl -Status "failure"
    exit 1
}

# Check service status
if ($Service.Status -eq "Running") {
    $SuccessMessage = "Service '$ServiceName' is running normally."
    Write-Host $SuccessMessage -ForegroundColor $SuccessColor
    # Uncomment to send success notifications (may be noisy for scheduled tasks)
    # Send-SlackNotification -Message $SuccessMessage -WebhookUrl $SlackWebhookUrl -Status "success"
    exit 0
}
else {
    $ErrorMessage = "Service '$ServiceName' is not running. Current status: $($Service.Status)"
    Write-Host $ErrorMessage -ForegroundColor $ErrorColor
    
    # Send notification
    Send-SlackNotification -Message $ErrorMessage -WebhookUrl $SlackWebhookUrl -Status "failure"
    
    # Attempt to restart if enabled
    if ($RestartOnFailure) {
        Write-Host "Attempting to restart service..." -ForegroundColor $InfoColor
        $RestartSuccess = Restart-TraeService -ServiceName $ServiceName -MaxRetries $MaxRetries -RetryDelay $RetryDelay
        
        if ($RestartSuccess) {
            $RecoveryMessage = "Service '$ServiceName' was successfully restarted."
            Write-Host $RecoveryMessage -ForegroundColor $SuccessColor
            Send-SlackNotification -Message $RecoveryMessage -WebhookUrl $SlackWebhookUrl -Status "success"
            exit 0
        }
        else {
            $FatalMessage = "Failed to restart service '$ServiceName' after multiple attempts. Manual intervention required."
            Write-Host $FatalMessage -ForegroundColor $ErrorColor
            Send-SlackNotification -Message $FatalMessage -WebhookUrl $SlackWebhookUrl -Status "failure"
            exit 2
        }
    }
    else {
        Write-Host "Automatic restart is disabled. Use -RestartOnFailure to enable." -ForegroundColor $InfoColor
        exit 1
    }
}