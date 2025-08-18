# PowerShell script to view Bulenox logs on Windows

param (
    [Parameter(Mandatory=$false)]
    [string]$LogType = "output",
    
    [Parameter(Mandatory=$false)]
    [int]$Lines = 50,
    
    [Parameter(Mandatory=$false)]
    [switch]$Follow = $false
)

# Define log file paths
$outputLogPath = "C:\opt\bulenox\bulenox_output.log"
$errorLogPath = "C:\opt\bulenox\bulenox_error.log"

# Determine which log file to view
$logPath = if ($LogType -eq "error") { $errorLogPath } else { $outputLogPath }

# Create directory and log files if they don't exist
if (-not (Test-Path "C:\opt\bulenox")) {
    New-Item -ItemType Directory -Path "C:\opt\bulenox" -Force | Out-Null
    Write-Host "Created directory: C:\opt\bulenox"
}

foreach ($path in @($outputLogPath, $errorLogPath)) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType File -Path $path -Force | Out-Null
        Write-Host "Created log file: $path"
    }
}

# Function to display log content
function Show-Log {
    param (
        [string]$Path,
        [int]$Lines
    )
    
    if (Test-Path $Path) {
        Get-Content -Path $Path -Tail $Lines
    } else {
        Write-Host "Log file not found: $Path" -ForegroundColor Red
    }
}

# Display log header
$logTypeDisplay = if ($LogType -eq "error") { "Error" } else { "Output" }
Write-Host "=== Viewing Bulenox $logTypeDisplay Log (Last $Lines lines) ===" -ForegroundColor Cyan

# If follow mode is enabled, continuously monitor the log file
if ($Follow) {
    Write-Host "Monitoring log file. Press Ctrl+C to stop..." -ForegroundColor Yellow
    
    # Get initial content
    $lastContent = if (Test-Path $logPath) { Get-Content -Path $logPath -Tail $Lines } else { @() }
    $lastContent | ForEach-Object { Write-Host $_ }
    
    # Monitor for changes
    try {
        while ($true) {
            Start-Sleep -Seconds 1
            $currentContent = if (Test-Path $logPath) { Get-Content -Path $logPath } else { @() }
            
            # Find new lines
            if ($currentContent.Count -gt $lastContent.Count) {
                $newLines = $currentContent | Select-Object -Skip $lastContent.Count
                $newLines | ForEach-Object { Write-Host $_ }
            }
            
            $lastContent = $currentContent
        }
    } catch {
        Write-Host "Monitoring stopped." -ForegroundColor Yellow
    }
} else {
    # Just show the log once
    Show-Log -Path $logPath -Lines $Lines
}

# Usage examples
Write-Host ""
Write-Host "Usage Examples:" -ForegroundColor Green
Write-Host "  View output log (default):  .\view_bulenox_logs.ps1" -ForegroundColor Gray
Write-Host "  View error log:              .\view_bulenox_logs.ps1 -LogType error" -ForegroundColor Gray
Write-Host "  View last 100 lines:         .\view_bulenox_logs.ps1 -Lines 100" -ForegroundColor Gray
Write-Host "  Monitor log in real-time:    .\view_bulenox_logs.ps1 -Follow" -ForegroundColor Gray