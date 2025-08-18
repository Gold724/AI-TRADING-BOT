# AI Trading Sentinel - Health Monitor
# Monitors bot performance, logs, and system resources

param(
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Report,
    [int]$CheckInterval = 60  # seconds
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir "logs"
$HealthLog = Join-Path $LogDir "health.log"
$AlertLog = Join-Path $LogDir "alerts.log"
$PidFile = Join-Path $ScriptDir "health_monitor.pid"
$BotPidFile = Join-Path $ScriptDir "bot.pid"

# Health thresholds
$Thresholds = @{
    CPUPercent = 80
    MemoryMB = 1000
    DiskSpaceGB = 5
    LogSizeMB = 100
    MaxErrors = 10
    ResponseTimeMs = 5000
}

# Ensure logs directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-HealthLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $HealthLog -Value $logEntry
    
    if ($Level -eq "ERROR" -or $Level -eq "CRITICAL") {
        Add-Content -Path $AlertLog -Value $logEntry
        Write-Host $logEntry -ForegroundColor Red
    } elseif ($Level -eq "WARNING") {
        Write-Host $logEntry -ForegroundColor Yellow
    } else {
        Write-Host $logEntry -ForegroundColor Green
    }
}

function Test-HealthMonitorRunning {
    if (Test-Path $PidFile) {
        $monitorPid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($monitorPid -and (Get-Process -Id $monitorPid -ErrorAction SilentlyContinue)) {
            return $true
        }
    }
    return $false
}

function Test-BotHealth {
    $healthStatus = @{
        BotRunning = $false
        CPUUsage = 0
        MemoryUsage = 0
        DiskSpace = 0
        LogSize = 0
        ErrorCount = 0
        LastActivity = $null
        Issues = @()
    }
    
    # Check if bot is running
    if (Test-Path $BotPidFile) {
        $botPid = Get-Content $BotPidFile -ErrorAction SilentlyContinue
        if ($botPid) {
            $botProcess = Get-Process -Id $botPid -ErrorAction SilentlyContinue
            if ($botProcess) {
                $healthStatus.BotRunning = $true
                $healthStatus.CPUUsage = [math]::Round($botProcess.CPU, 2)
                $healthStatus.MemoryUsage = [math]::Round($botProcess.WorkingSet64 / 1MB, 2)
                
                # Check CPU usage
                if ($healthStatus.CPUUsage -gt $Thresholds.CPUPercent) {
                    $healthStatus.Issues += "High CPU usage: $($healthStatus.CPUUsage)%"
                }
                
                # Check memory usage
                if ($healthStatus.MemoryUsage -gt $Thresholds.MemoryMB) {
                    $healthStatus.Issues += "High memory usage: $($healthStatus.MemoryUsage)MB"
                }
            }
        }
    }
    
    if (-not $healthStatus.BotRunning) {
        $healthStatus.Issues += "Bot is not running"
    }
    
    # Check disk space
    $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
    $healthStatus.DiskSpace = $freeSpaceGB
    
    if ($freeSpaceGB -lt $Thresholds.DiskSpaceGB) {
        $healthStatus.Issues += "Low disk space: ${freeSpaceGB}GB"
    }
    
    # Check log file sizes
    $mainLog = Join-Path $LogDir "main.log"
    if (Test-Path $mainLog) {
        $logSizeMB = [math]::Round((Get-Item $mainLog).Length / 1MB, 2)
        $healthStatus.LogSize = $logSizeMB
        
        if ($logSizeMB -gt $Thresholds.LogSizeMB) {
            $healthStatus.Issues += "Large log file: ${logSizeMB}MB"
        }
        
        # Check for recent errors in logs
        $recentErrors = Select-String -Path $mainLog -Pattern "ERROR|CRITICAL" | Select-Object -Last 10
        $healthStatus.ErrorCount = $recentErrors.Count
        
        if ($healthStatus.ErrorCount -gt $Thresholds.MaxErrors) {
            $healthStatus.Issues += "High error count: $($healthStatus.ErrorCount) recent errors"
        }
        
        # Check last activity
        $lastLine = Get-Content $mainLog -Tail 1 -ErrorAction SilentlyContinue
        if ($lastLine -match "\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})") {
            $healthStatus.LastActivity = [DateTime]::ParseExact($matches[1], "yyyy-MM-dd HH:mm:ss", $null)
            $timeSinceActivity = (Get-Date) - $healthStatus.LastActivity
            
            if ($timeSinceActivity.TotalMinutes -gt 10) {
                $healthStatus.Issues += "No recent activity: $([math]::Round($timeSinceActivity.TotalMinutes, 1)) minutes ago"
            }
        }
    }
    
    return $healthStatus
}

function Send-Alert {
    param([string]$Message, [string]$Level = "WARNING")
    
    Write-HealthLog $Message $Level
    
    # Here you could add email, Slack, or other notification methods
    # For now, just log to alerts file
    $alertEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $AlertLog -Value $alertEntry
}

function Start-HealthMonitoring {
    if (Test-HealthMonitorRunning) {
        Write-HealthLog "Health monitor is already running" "WARNING"
        return
    }
    
    Write-HealthLog "Starting health monitoring (interval: $CheckInterval seconds)..."
    
    # Save monitor PID
    $PID | Out-File -FilePath $PidFile
    
    $consecutiveIssues = 0
    $maxConsecutiveIssues = 3
    
    try {
        while ($true) {
            $health = Test-BotHealth
            
            if ($health.Issues.Count -eq 0) {
                Write-HealthLog "Health check passed - Bot: $($health.BotRunning), CPU: $($health.CPUUsage)%, Memory: $($health.MemoryUsage)MB, Disk: $($health.DiskSpace)GB"
                $consecutiveIssues = 0
            } else {
                $consecutiveIssues++
                $issueText = $health.Issues -join ", "
                
                if ($consecutiveIssues -ge $maxConsecutiveIssues) {
                    Send-Alert "CRITICAL: Persistent issues detected: $issueText" "CRITICAL"
                    
                    # Auto-restart bot if it's not running
                    if (-not $health.BotRunning) {
                        Write-HealthLog "Attempting to restart bot..." "WARNING"
                        & "$ScriptDir\run_bot_service.ps1" -Start
                    }
                } else {
                    Write-HealthLog "Health issues detected ($consecutiveIssues/$maxConsecutiveIssues): $issueText" "WARNING"
                }
            }
            
            Start-Sleep -Seconds $CheckInterval
        }
    }
    catch {
        Write-HealthLog "Health monitoring stopped: $($_.Exception.Message)" "ERROR"
    }
    finally {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
}

function Stop-HealthMonitoring {
    if (Test-Path $PidFile) {
        $monitorPid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($monitorPid -and (Get-Process -Id $monitorPid -ErrorAction SilentlyContinue)) {
            Stop-Process -Id $monitorPid -Force
            Write-HealthLog "Health monitoring stopped (PID: $monitorPid)"
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    } else {
        Write-HealthLog "Health monitor is not running" "WARNING"
    }
}

function Get-HealthStatus {
    $health = Test-BotHealth
    
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host "AI Trading Sentinel - Health Status" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    Write-Host "Bot Running: " -NoNewline
    Write-Host $health.BotRunning -ForegroundColor $(if($health.BotRunning){"Green"} else {"Red"})
    
    if ($health.BotRunning) {
        Write-Host "CPU Usage: $($health.CPUUsage)%" -ForegroundColor $(if($health.CPUUsage -gt $Thresholds.CPUPercent){"Red"} else {"Green"})
        Write-Host "Memory Usage: $($health.MemoryUsage)MB" -ForegroundColor $(if($health.MemoryUsage -gt $Thresholds.MemoryMB){"Red"} else {"Green"})
    }
    
    Write-Host "Disk Space: $($health.DiskSpace)GB" -ForegroundColor $(if($health.DiskSpace -lt $Thresholds.DiskSpaceGB){"Red"} else {"Green"})
    Write-Host "Log Size: $($health.LogSize)MB" -ForegroundColor $(if($health.LogSize -gt $Thresholds.LogSizeMB){"Yellow"} else {"Green"})
    Write-Host "Recent Errors: $($health.ErrorCount)" -ForegroundColor $(if($health.ErrorCount -gt $Thresholds.MaxErrors){"Red"} else {"Green"})
    
    if ($health.LastActivity) {
        $timeSince = (Get-Date) - $health.LastActivity
        Write-Host "Last Activity: $([math]::Round($timeSince.TotalMinutes, 1)) minutes ago" -ForegroundColor $(if($timeSince.TotalMinutes -gt 10){"Yellow"} else {"Green"})
    }
    
    if ($health.Issues.Count -gt 0) {
        Write-Host "
Issues Detected:" -ForegroundColor Red
        foreach ($issue in $health.Issues) {
            Write-Host "  - $issue" -ForegroundColor Red
        }
    } else {
        Write-Host "
All systems healthy!" -ForegroundColor Green
    }
    
    Write-Host "Monitor Running: " -NoNewline
    Write-Host (Test-HealthMonitorRunning) -ForegroundColor $(if(Test-HealthMonitorRunning){"Green"} else {"Yellow"})
}

function Show-HealthReport {
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "AI Trading Sentinel - Health Report" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # Show recent health logs
    if (Test-Path $HealthLog) {
        Write-Host "
Recent Health Logs:" -ForegroundColor Yellow
        Get-Content $HealthLog -Tail 20
    }
    
    # Show recent alerts
    if (Test-Path $AlertLog) {
        Write-Host "
Recent Alerts:" -ForegroundColor Red
        Get-Content $AlertLog -Tail 10
    }
    
    # Show current status
    Write-Host "
Current Status:" -ForegroundColor Yellow
    Get-HealthStatus
}

# Main execution
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "AI Trading Sentinel - Health Monitor" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

switch ($true) {
    $Start { Start-HealthMonitoring }
    $Stop { Stop-HealthMonitoring }
    $Status { Get-HealthStatus }
    $Report { Show-HealthReport }
    default {
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\health_monitor.ps1 -Start                    # Start monitoring"
        Write-Host "  .\health_monitor.ps1 -Stop                     # Stop monitoring"
        Write-Host "  .\health_monitor.ps1 -Status                   # Check current status"
        Write-Host "  .\health_monitor.ps1 -Report                   # Show detailed report"
        Write-Host "  .\health_monitor.ps1 -Start -CheckInterval 30  # Custom check interval"
        Write-Host ""
        Write-Host "For continuous monitoring, use: .\health_monitor.ps1 -Start" -ForegroundColor Green
    }
}