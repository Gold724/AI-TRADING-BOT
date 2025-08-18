# AI Trading Sentinel - Windows Service Alternative
# PowerShell script for 24/7 bot operation with monitoring

param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Logs
)

# Configuration
$BotName = "AI Trading Sentinel"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ScriptDir "logs"
$ServiceLog = Join-Path $LogDir "service.log"
$PidFile = Join-Path $ScriptDir "bot.pid"
$MaxRestarts = 10
$RestartDelay = 30

# Ensure logs directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-ServiceLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $ServiceLog -Value $logEntry
    Write-Host $logEntry -ForegroundColor $(if($Level -eq "ERROR"){"Red"} elseif($Level -eq "WARNING"){"Yellow"} else {"Green"})
}

function Test-BotRunning {
    if (Test-Path $PidFile) {
        $botPid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($botPid -and (Get-Process -Id $botPid -ErrorAction SilentlyContinue)) {
            return $true
        }
    }
    return $false
}

function Start-Bot {
    Write-ServiceLog "Starting $BotName..."
    
    if (Test-BotRunning) {
        Write-ServiceLog "Bot is already running" "WARNING"
        return
    }
    
    # Change to script directory
    Set-Location $ScriptDir
    
    # Activate virtual environment if exists
    $venvActivate = Join-Path $ScriptDir "venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-ServiceLog "Activating virtual environment..."
        & $venvActivate
    }
    
    # Start bot process
    $process = Start-Process -FilePath "python" -ArgumentList "main.py" -PassThru -WindowStyle Hidden
    
    if ($process) {
        $process.Id | Out-File -FilePath $PidFile
        Write-ServiceLog "Bot started with PID: $($process.Id)"
        return $process
    } else {
        Write-ServiceLog "Failed to start bot" "ERROR"
        return $null
    }
}

function Stop-Bot {
    Write-ServiceLog "Stopping $BotName..."
    
    if (Test-Path $PidFile) {
        $botPid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($botPid -and (Get-Process -Id $botPid -ErrorAction SilentlyContinue)) {
            Stop-Process -Id $botPid -Force
            Write-ServiceLog "Bot stopped (PID: $botPid)"
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    } else {
        Write-ServiceLog "Bot is not running" "WARNING"
    }
}

function Get-BotStatus {
    if (Test-BotRunning) {
        $botPid = Get-Content $PidFile
        $process = Get-Process -Id $botPid -ErrorAction SilentlyContinue
        if ($process) {
            Write-ServiceLog "Bot is RUNNING (PID: $botPid, CPU: $($process.CPU), Memory: $([math]::Round($process.WorkingSet64/1MB, 2))MB)"
        }
    } else {
        Write-ServiceLog "Bot is STOPPED"
    }
}

function Start-ServiceMode {
    Write-ServiceLog "Starting $BotName in service mode..."
    Write-ServiceLog "Maximum restarts: $MaxRestarts"
    Write-ServiceLog "Restart delay: $RestartDelay seconds"
    
    $restartCount = 0
    
    while ($restartCount -lt $MaxRestarts) {
        try {
            $process = Start-Bot
            
            if ($process) {
                # Monitor the process
                $process.WaitForExit()
                $exitCode = $process.ExitCode
                
                Write-ServiceLog "Bot exited with code: $exitCode" $(if($exitCode -eq 0){"INFO"} else {"ERROR"})
                
                if ($exitCode -eq 0) {
                    Write-ServiceLog "Bot exited normally, stopping service mode"
                    break
                } else {
                    $restartCount++
                    Write-ServiceLog "Restart attempt $restartCount of $MaxRestarts" "WARNING"
                    
                    if ($restartCount -lt $MaxRestarts) {
                        Write-ServiceLog "Waiting $RestartDelay seconds before restart..."
                        Start-Sleep -Seconds $RestartDelay
                    }
                }
            } else {
                Write-ServiceLog "Failed to start bot, stopping service mode" "ERROR"
                break
            }
        }
        catch {
            Write-ServiceLog "Error in service loop: $($_.Exception.Message)" "ERROR"
            $restartCount++
            
            if ($restartCount -lt $MaxRestarts) {
                Start-Sleep -Seconds $RestartDelay
            }
        }
    }
    
    if ($restartCount -ge $MaxRestarts) {
        Write-ServiceLog "Maximum restart attempts reached, stopping service" "ERROR"
    }
    
    Write-ServiceLog "Service mode stopped"
}

function Install-StartupTask {
    Write-ServiceLog "Installing startup task..."
    
    $taskName = "AITradingSentinel"
    $scriptPath = $MyInvocation.MyCommand.Path
    
    # Create startup shortcut (alternative to Task Scheduler)
    $startupFolder = [Environment]::GetFolderPath("Startup")
    $shortcutPath = Join-Path $startupFolder "$taskName.lnk"
    
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$scriptPath`" -Start"
    $shortcut.WorkingDirectory = $ScriptDir
    $shortcut.WindowStyle = 7  # Minimized
    $shortcut.Save()
    
    Write-ServiceLog "Startup shortcut created at: $shortcutPath"
    Write-ServiceLog "Bot will start automatically on user login"
}

function Show-Logs {
    if (Test-Path $ServiceLog) {
        Get-Content $ServiceLog -Tail 50
    } else {
        Write-Host "No service logs found" -ForegroundColor Yellow
    }
}

# Main execution
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "AI Trading Sentinel - Service Manager" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

switch ($true) {
    $Install { Install-StartupTask }
    $Start { Start-ServiceMode }
    $Stop { Stop-Bot }
    $Status { Get-BotStatus }
    $Logs { Show-Logs }
    default {
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\run_bot_service.ps1 -Install   # Install startup task"
        Write-Host "  .\run_bot_service.ps1 -Start     # Start service mode"
        Write-Host "  .\run_bot_service.ps1 -Stop      # Stop bot"
        Write-Host "  .\run_bot_service.ps1 -Status    # Check status"
        Write-Host "  .\run_bot_service.ps1 -Logs      # View logs"
        Write-Host ""
        Write-Host "For 24/7 operation, use: .\run_bot_service.ps1 -Start" -ForegroundColor Green
    }
}