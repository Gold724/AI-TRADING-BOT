# auto_news_cron.ps1 - PowerShell script to fetch and save upcoming economic news

# Navigate to the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptPath

# Set up logging
$logDir = Join-Path -Path $scriptPath -ChildPath "logs"
$logFile = Join-Path -Path $logDir -ChildPath ("news_fetch_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
}

# Log start time
Add-Content -Path $logFile -Value ("[{0}] Starting news fetch job" -f (Get-Date))

# Activate virtual environment if it exists
$venvPath = Join-Path -Path $scriptPath -ChildPath "venv\Scripts\Activate.ps1"
if (Test-Path -Path $venvPath) {
    & $venvPath
}

# Run the news fetcher
try {
    $fetchOutput = & python fetch_news.py 2>&1
    $fetchStatus = $LASTEXITCODE
    Add-Content -Path $logFile -Value $fetchOutput
} catch {
    $fetchStatus = 1
    Add-Content -Path $logFile -Value ("Error running fetch_news.py: {0}" -f $_.Exception.Message)
}

# Update banned periods based on fetched news
try {
    $bannedOutput = & python -c "from news_filter import update_banned_periods; update_banned_periods()" 2>&1
    $bannedStatus = $LASTEXITCODE
    Add-Content -Path $logFile -Value $bannedOutput
} catch {
    $bannedStatus = 1
    Add-Content -Path $logFile -Value ("Error updating banned periods: {0}" -f $_.Exception.Message)
}

# Log completion status
if (($fetchStatus -eq 0) -and ($bannedStatus -eq 0)) {
    Add-Content -Path $logFile -Value ("[{0}] News fetch job completed successfully" -f (Get-Date))
    
    # Send Slack notification if SLACK_WEBHOOK_URL is configured
    $slackWebhookUrl = $env:SLACK_WEBHOOK_URL
    if ($slackWebhookUrl) {
        # Count high impact events
        try {
            $newsData = Get-Content -Path (Join-Path -Path $scriptPath -ChildPath "data\forex_news.json") | ConvertFrom-Json
            $highImpactCount = ($newsData | Where-Object { $_.impact -eq "high" } | Measure-Object).Count
            
            # Send notification
            $payload = @{
                text = "📅 *ECONOMIC CALENDAR UPDATED* 📅`n• Calendar data refreshed successfully`n• Found $highImpactCount high-impact events`n• Trading filters updated"
            } | ConvertTo-Json
            
            Invoke-RestMethod -Uri $slackWebhookUrl -Method Post -Body $payload -ContentType "application/json"
        } catch {
            Add-Content -Path $logFile -Value ("Error sending Slack notification: {0}" -f $_.Exception.Message)
        }
    }
} else {
    Add-Content -Path $logFile -Value ("[{0}] News fetch job failed" -f (Get-Date))
    
    # Send failure notification if SLACK_WEBHOOK_URL is configured
    $slackWebhookUrl = $env:SLACK_WEBHOOK_URL
    if ($slackWebhookUrl) {
        try {
            $payload = @{
                text = "⚠️ *ECONOMIC CALENDAR UPDATE FAILED* ⚠️`nThe scheduled news data update failed. Please check the logs."
            } | ConvertTo-Json
            
            Invoke-RestMethod -Uri $slackWebhookUrl -Method Post -Body $payload -ContentType "application/json"
        } catch {
            Add-Content -Path $logFile -Value ("Error sending Slack notification: {0}" -f $_.Exception.Message)
        }
    }
}

# Deactivate virtual environment if it was activated
if (Test-Path -Path $venvPath) {
    deactivate
}