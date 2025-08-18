# TradeBot Sentinel - Windows Health Monitor
# PowerShell script for monitoring TradeBot Sentinel on Windows

param(
    [string]$Action = "monitor",
    [int]$IntervalSeconds = 60,
    [switch]$Daemon = $false,
    [switch]$Verbose = $false,
    [string]$ConfigFile = "health-config.json"
)

# Set error action preference
$ErrorActionPreference = "Continue"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"
$Purple = "Magenta"

# Global variables
$script:MonitoringActive = $false
$script:LogFile = "health-monitor-$(Get-Date -Format 'yyyyMMdd').log"
$script:PidFile = "health-monitor.pid"
$script:AlertCooldown = @{}

# Default configuration
$script:Config = @{
    thresholds = @{
        cpu_percent = 80
        memory_percent = 85
        disk_percent = 90
        api_timeout_seconds = 30
        max_failed_trades = 5
        error_rate_percent = 10
    }
    alerts = @{
        slack_webhook = $env:SLACK_WEBHOOK_URL
        email_smtp = $env:EMAIL_SMTP_SERVER
        email_from = $env:EMAIL_FROM
        email_to = $env:EMAIL_TO
        cooldown_minutes = 15
    }
    monitoring = @{
        check_interval = 60
        log_retention_days = 7
        enable_performance_counters = $true
        enable_api_checks = $true
        enable_process_monitoring = $true
    }
}

# Logging functions
function Write-Log {
    param(
        [string]$Level,
        [string]$Message,
        [switch]$NoConsole
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to log file
    Add-Content -Path $script:LogFile -Value $logMessage -ErrorAction SilentlyContinue
    
    # Write to console unless suppressed
    if (-not $NoConsole) {
        switch ($Level) {
            "INFO" { Write-Host $logMessage -ForegroundColor $Blue }
            "SUCCESS" { Write-Host $logMessage -ForegroundColor $Green }
            "WARNING" { Write-Host $logMessage -ForegroundColor $Yellow }
            "ERROR" { Write-Host $logMessage -ForegroundColor $Red }
            "DEBUG" { if ($Verbose) { Write-Host $logMessage -ForegroundColor $Purple } }
            "ALERT" { Write-Host $logMessage -ForegroundColor $Red -BackgroundColor Yellow }
            default { Write-Host $logMessage }
        }
    }
}

function Load-Config {
    if (Test-Path $ConfigFile) {
        try {
            $configJson = Get-Content $ConfigFile -Raw | ConvertFrom-Json
            # Merge with default config
            foreach ($section in $configJson.PSObject.Properties) {
                if ($script:Config.ContainsKey($section.Name)) {
                    foreach ($key in $section.Value.PSObject.Properties) {
                        $script:Config[$section.Name][$key.Name] = $key.Value
                    }
                }
            }
            Write-Log "INFO" "Configuration loaded from $ConfigFile"
        }
        catch {
            Write-Log "WARNING" "Could not load config file: $($_.Exception.Message)"
        }
    }
    else {
        Write-Log "INFO" "Using default configuration (no config file found)"
    }
}

function Save-Config {
    try {
        $script:Config | ConvertTo-Json -Depth 3 | Out-File $ConfigFile -Encoding UTF8
        Write-Log "INFO" "Configuration saved to $ConfigFile"
    }
    catch {
        Write-Log "ERROR" "Could not save config file: $($_.Exception.Message)"
    }
}

function Send-Alert {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Severity = "WARNING",
        [string]$AlertType = "general"
    )
    
    # Check cooldown
    $now = Get-Date
    $cooldownKey = "$AlertType-$Title"
    
    if ($script:AlertCooldown.ContainsKey($cooldownKey)) {
        $lastAlert = $script:AlertCooldown[$cooldownKey]
        $cooldownMinutes = $script:Config.alerts.cooldown_minutes
        if (($now - $lastAlert).TotalMinutes -lt $cooldownMinutes) {
            Write-Log "DEBUG" "Alert suppressed due to cooldown: $Title"
            return
        }
    }
    
    $script:AlertCooldown[$cooldownKey] = $now
    
    Write-Log "ALERT" "$Severity`: $Title - $Message"
    
    # Send Slack alert
    if ($script:Config.alerts.slack_webhook) {
        Send-SlackAlert -Title $Title -Message $Message -Severity $Severity
    }
    
    # Send email alert
    if ($script:Config.alerts.email_smtp -and $script:Config.alerts.email_to) {
        Send-EmailAlert -Title $Title -Message $Message -Severity $Severity
    }
}

function Send-SlackAlert {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Severity
    )
    
    try {
        $color = switch ($Severity) {
            "CRITICAL" { "danger" }
            "ERROR" { "danger" }
            "WARNING" { "warning" }
            default { "good" }
        }
        
        $payload = @{
            text = "TradeBot Sentinel Alert"
            attachments = @(
                @{
                    color = $color
                    title = $Title
                    text = $Message
                    fields = @(
                        @{
                            title = "Severity"
                            value = $Severity
                            short = $true
                        },
                        @{
                            title = "Server"
                            value = $env:COMPUTERNAME
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
        } | ConvertTo-Json -Depth 4
        
        Invoke-RestMethod -Uri $script:Config.alerts.slack_webhook -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 10
        Write-Log "DEBUG" "Slack alert sent: $Title"
    }
    catch {
        Write-Log "ERROR" "Failed to send Slack alert: $($_.Exception.Message)"
    }
}

function Send-EmailAlert {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Severity
    )
    
    try {
        $subject = "[$Severity] TradeBot Sentinel - $Title"
        $body = @"
TradeBot Sentinel Alert

Severity: $Severity
Title: $Title
Message: $Message

Server: $env:COMPUTERNAME
Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

This is an automated alert from TradeBot Sentinel health monitoring.
"@
        
        # Use Send-MailMessage if available
        if (Get-Command Send-MailMessage -ErrorAction SilentlyContinue) {
            Send-MailMessage -SmtpServer $script:Config.alerts.email_smtp -From $script:Config.alerts.email_from -To $script:Config.alerts.email_to -Subject $subject -Body $body
            Write-Log "DEBUG" "Email alert sent: $Title"
        }
        else {
            Write-Log "WARNING" "Send-MailMessage not available for email alerts"
        }
    }
    catch {
        Write-Log "ERROR" "Failed to send email alert: $($_.Exception.Message)"
    }
}

function Test-SystemResources {
    Write-Log "DEBUG" "Checking system resources..."
    
    # Check CPU usage
    try {
        $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $cpuPercent = [math]::Round($cpu.Average, 2)
        
        if ($cpuPercent -gt $script:Config.thresholds.cpu_percent) {
            Send-Alert "High CPU Usage" "CPU usage is ${cpuPercent}% (threshold: $($script:Config.thresholds.cpu_percent)%)" "WARNING" "cpu"
        }
        
        Write-Log "DEBUG" "CPU usage: ${cpuPercent}%"
    }
    catch {
        Write-Log "ERROR" "Could not check CPU usage: $($_.Exception.Message)"
    }
    
    # Check memory usage
    try {
        $memory = Get-WmiObject -Class Win32_OperatingSystem
        $totalMemory = $memory.TotalVisibleMemorySize
        $freeMemory = $memory.FreePhysicalMemory
        $usedPercent = [math]::Round((($totalMemory - $freeMemory) / $totalMemory) * 100, 2)
        
        if ($usedPercent -gt $script:Config.thresholds.memory_percent) {
            Send-Alert "High Memory Usage" "Memory usage is ${usedPercent}% (threshold: $($script:Config.thresholds.memory_percent)%)" "WARNING" "memory"
        }
        
        Write-Log "DEBUG" "Memory usage: ${usedPercent}%"
    }
    catch {
        Write-Log "ERROR" "Could not check memory usage: $($_.Exception.Message)"
    }
    
    # Check disk usage
    try {
        $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $usedPercent = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2)
        
        if ($usedPercent -gt $script:Config.thresholds.disk_percent) {
            Send-Alert "High Disk Usage" "Disk usage is ${usedPercent}% (threshold: $($script:Config.thresholds.disk_percent)%)" "WARNING" "disk"
        }
        
        Write-Log "DEBUG" "Disk usage: ${usedPercent}%"
    }
    catch {
        Write-Log "ERROR" "Could not check disk usage: $($_.Exception.Message)"
    }
}

function Test-TradeBotProcess {
    Write-Log "DEBUG" "Checking TradeBot process..."
    
    # Check if main process is running
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*main.py*" -or $_.MainWindowTitle -like "*TradeBot*"
    }
    
    if ($processes.Count -eq 0) {
        Send-Alert "TradeBot Process Down" "TradeBot main process is not running" "CRITICAL" "process"
        return $false
    }
    else {
        Write-Log "DEBUG" "TradeBot process found (PID: $($processes[0].Id))"
        
        # Check process health (memory, CPU)
        $process = $processes[0]
        $memoryMB = [math]::Round($process.WorkingSet64 / 1MB, 2)
        
        if ($memoryMB -gt 1000) {  # Alert if using more than 1GB
            Send-Alert "High Process Memory" "TradeBot process using ${memoryMB}MB memory" "WARNING" "process_memory"
        }
        
        Write-Log "DEBUG" "TradeBot process memory: ${memoryMB}MB"
        return $true
    }
}

function Test-APIHealth {
    if (-not $script:Config.monitoring.enable_api_checks) {
        return
    }
    
    Write-Log "DEBUG" "Checking API health..."
    
    $endpoints = @(
        @{ url = "http://localhost:8000/health"; name = "Health" },
        @{ url = "http://localhost:8000/api/status"; name = "Status" }
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.url -TimeoutSec $script:Config.thresholds.api_timeout_seconds -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                Write-Log "DEBUG" "$($endpoint.name) endpoint OK"
            }
            else {
                Send-Alert "API Endpoint Error" "$($endpoint.name) endpoint returned status $($response.StatusCode)" "ERROR" "api"
            }
        }
        catch {
            Send-Alert "API Endpoint Down" "$($endpoint.name) endpoint not responding: $($_.Exception.Message)" "CRITICAL" "api"
        }
    }
}

function Test-TradingPerformance {
    Write-Log "DEBUG" "Checking trading performance..."
    
    # Check for recent log files
    $logFiles = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($logFiles.Count -eq 0) {
        Send-Alert "No Trading Logs" "No trading log files found" "WARNING" "trading"
        return
    }
    
    # Analyze recent log file
    $recentLog = $logFiles[0]
    $logContent = Get-Content $recentLog.FullName -Tail 100 -ErrorAction SilentlyContinue
    
    if ($logContent) {
        # Count errors in recent logs
        $errorCount = ($logContent | Where-Object { $_ -match "ERROR|CRITICAL|EXCEPTION" }).Count
        $totalLines = $logContent.Count
        
        if ($totalLines -gt 0) {
            $errorRate = [math]::Round(($errorCount / $totalLines) * 100, 2)
            
            if ($errorRate -gt $script:Config.thresholds.error_rate_percent) {
                Send-Alert "High Error Rate" "Error rate is ${errorRate}% in recent logs (threshold: $($script:Config.thresholds.error_rate_percent)%)" "ERROR" "trading"
            }
            
            Write-Log "DEBUG" "Recent log error rate: ${errorRate}%"
        }
        
        # Check for failed trades
        $failedTrades = ($logContent | Where-Object { $_ -match "TRADE.*FAILED|EXECUTION.*ERROR" }).Count
        
        if ($failedTrades -gt $script:Config.thresholds.max_failed_trades) {
            Send-Alert "Multiple Failed Trades" "$failedTrades failed trades detected in recent logs (threshold: $($script:Config.thresholds.max_failed_trades))" "ERROR" "trading"
        }
        
        Write-Log "DEBUG" "Recent failed trades: $failedTrades"
    }
}

function Test-SecurityEvents {
    Write-Log "DEBUG" "Checking security events..."
    
    # Check Windows Event Log for security events
    try {
        $recentTime = (Get-Date).AddHours(-1)
        
        # Check for failed logon attempts
        $failedLogons = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625; StartTime=$recentTime} -ErrorAction SilentlyContinue
        
        if ($failedLogons.Count -gt 10) {
            Send-Alert "Multiple Failed Logons" "$($failedLogons.Count) failed logon attempts in the last hour" "WARNING" "security"
        }
        
        Write-Log "DEBUG" "Failed logons in last hour: $($failedLogons.Count)"
    }
    catch {
        Write-Log "DEBUG" "Could not check security events: $($_.Exception.Message)"
    }
}

function Start-Monitoring {
    Write-Log "INFO" "Starting TradeBot Sentinel health monitoring..."
    Write-Log "INFO" "Monitoring interval: $IntervalSeconds seconds"
    Write-Log "INFO" "Log file: $script:LogFile"
    
    # Save PID for daemon mode
    if ($Daemon) {
        $PID | Out-File $script:PidFile
        Write-Log "INFO" "Daemon mode - PID saved to $script:PidFile"
    }
    
    $script:MonitoringActive = $true
    
    while ($script:MonitoringActive) {
        try {
            Write-Log "DEBUG" "Running health checks..."
            
            Test-SystemResources
            $processRunning = Test-TradeBotProcess
            
            if ($processRunning) {
                Test-APIHealth
                Test-TradingPerformance
            }
            
            Test-SecurityEvents
            
            Write-Log "DEBUG" "Health check cycle completed"
        }
        catch {
            Write-Log "ERROR" "Error during health check: $($_.Exception.Message)"
        }
        
        # Wait for next cycle
        Start-Sleep -Seconds $IntervalSeconds
    }
    
    Write-Log "INFO" "Health monitoring stopped"
}

function Stop-Monitoring {
    Write-Log "INFO" "Stopping health monitoring..."
    $script:MonitoringActive = $false
    
    # Remove PID file
    if (Test-Path $script:PidFile) {
        Remove-Item $script:PidFile -Force
    }
}

function Get-MonitoringStatus {
    if (Test-Path $script:PidFile) {
        $pid = Get-Content $script:PidFile -ErrorAction SilentlyContinue
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "Health monitoring is running (PID: $pid)" -ForegroundColor $Green
            return $true
        }
        else {
            Write-Host "Health monitoring PID file exists but process not found" -ForegroundColor $Yellow
            Remove-Item $script:PidFile -Force
            return $false
        }
    }
    else {
        Write-Host "Health monitoring is not running" -ForegroundColor $Red
        return $false
    }
}

function Test-AlertSystem {
    Write-Log "INFO" "Testing alert system..."
    
    Send-Alert "Test Alert" "This is a test alert from TradeBot Sentinel health monitor" "INFO" "test"
    
    Write-Host "Test alert sent. Check your configured alert channels." -ForegroundColor $Green
}

function Show-Help {
    Write-Host "TradeBot Sentinel - Windows Health Monitor" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Usage: .\health-monitor-windows.ps1 [ACTION] [OPTIONS]" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor $Yellow
    Write-Host "  monitor          Start monitoring (default)"
    Write-Host "  start            Start monitoring in background"
    Write-Host "  stop             Stop background monitoring"
    Write-Host "  status           Check monitoring status"
    Write-Host "  test-alert       Send test alert"
    Write-Host "  config           Show current configuration"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor $Yellow
    Write-Host "  -IntervalSeconds <n>    Monitoring interval [default: 60]"
    Write-Host "  -ConfigFile <file>      Configuration file [default: health-config.json]"
    Write-Host "  -Daemon                 Run in background mode"
    Write-Host "  -Verbose                Enable verbose output"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Yellow
    Write-Host "  .\health-monitor-windows.ps1                    # Start monitoring"
    Write-Host "  .\health-monitor-windows.ps1 start -Daemon      # Start in background"
    Write-Host "  .\health-monitor-windows.ps1 status             # Check status"
    Write-Host "  .\health-monitor-windows.ps1 test-alert         # Test alerts"
    Write-Host ""
}

function Main {
    # Load configuration
    Load-Config
    
    switch ($Action.ToLower()) {
        "monitor" {
            Start-Monitoring
        }
        "start" {
            if (Get-MonitoringStatus) {
                Write-Host "Health monitoring is already running" -ForegroundColor $Yellow
            }
            else {
                if ($Daemon) {
                    # Start in background
                    $scriptPath = $MyInvocation.MyCommand.Path
                    Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$scriptPath`" monitor -Daemon -IntervalSeconds $IntervalSeconds -ConfigFile `"$ConfigFile`"" -WindowStyle Hidden
                    Write-Host "Health monitoring started in background" -ForegroundColor $Green
                }
                else {
                    Start-Monitoring
                }
            }
        }
        "stop" {
            if (Test-Path $script:PidFile) {
                $pid = Get-Content $script:PidFile -ErrorAction SilentlyContinue
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                
                if ($process) {
                    Stop-Process -Id $pid -Force
                    Write-Host "Health monitoring stopped (PID: $pid)" -ForegroundColor $Green
                }
                
                Remove-Item $script:PidFile -Force -ErrorAction SilentlyContinue
            }
            else {
                Write-Host "Health monitoring is not running" -ForegroundColor $Yellow
            }
        }
        "status" {
            Get-MonitoringStatus
        }
        "test-alert" {
            Test-AlertSystem
        }
        "config" {
            Write-Host "Current Configuration:" -ForegroundColor $Green
            $script:Config | ConvertTo-Json -Depth 3 | Write-Host
        }
        "help" {
            Show-Help
        }
        default {
            Write-Host "Unknown action: $Action" -ForegroundColor $Red
            Show-Help
            exit 1
        }
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-Monitoring
}

# Show help if requested
if ($args -contains "-h" -or $args -contains "--help") {
    Show-Help
    exit 0
}

# Run main function
try {
    Main
}
catch {
    Write-Log "ERROR" "Health monitor failed: $($_.Exception.Message)"
    Write-Log "ERROR" "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}