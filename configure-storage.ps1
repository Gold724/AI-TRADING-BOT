# AI Trading Sentinel - Storage Redirection Configuration
# Run as Administrator

Write-Host "Configuring TRAE.ai Storage Redirection..." -ForegroundColor Green

# Create directory structure
$directories = @(
    "D:\trae-data",
    "D:\trae-downloads", 
    "D:\pip-cache",
    "D:\docker-data",
    "D:\actions-runner\_work",
    "E:\trae-logs",
    "E:\checkpoints"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created: $dir" -ForegroundColor Yellow
    }
}

# Configure pip cache location
[Environment]::SetEnvironmentVariable("PIP_CACHE_DIR", "D:\pip-cache", "User")
Write-Host "Set PIP_CACHE_DIR to D:\pip-cache" -ForegroundColor Green

# Configure Playwright downloads
[Environment]::SetEnvironmentVariable("PLAYWRIGHT_BROWSERS_PATH", "D:\trae-downloads\playwright", "User")
Write-Host "Set PLAYWRIGHT_BROWSERS_PATH to D:\trae-downloads\playwright" -ForegroundColor Green

# Configure TRAE data directories
[Environment]::SetEnvironmentVariable("TRAE_DATA_DIR", "D:\trae-data", "User")
[Environment]::SetEnvironmentVariable("TRAE_LOGS_DIR", "E:\trae-logs", "User")
[Environment]::SetEnvironmentVariable("TRAE_CACHE_DIR", "D:\trae-data\cache", "User")
[Environment]::SetEnvironmentVariable("TRAE_DOWNLOADS_DIR", "D:\trae-downloads", "User")

Write-Host "TRAE environment variables configured" -ForegroundColor Green

# Configure Docker data-root (requires Docker Desktop restart)
$dockerConfigPath = "$env:USERPROFILE\.docker\daemon.json"
$dockerConfig = @{
    "data-root" = "D:\docker-data"
    "log-driver" = "json-file"
    "log-opts" = @{
        "max-size" = "10m"
        "max-file" = "3"
    }
}

if (!(Test-Path (Split-Path $dockerConfigPath))) {
    New-Item -ItemType Directory -Path (Split-Path $dockerConfigPath) -Force
}

$dockerConfig | ConvertTo-Json -Depth 3 | Set-Content $dockerConfigPath
Write-Host "Docker data-root configured to D:\docker-data" -ForegroundColor Green
Write-Host "Please restart Docker Desktop for changes to take effect" -ForegroundColor Yellow

# Configure GitHub Actions runner (if exists)
if (Test-Path "C:\actions-runner") {
    [Environment]::SetEnvironmentVariable("RUNNER_WORK_FOLDER", "D:\actions-runner\_work", "User")
    Write-Host "GitHub Actions runner work folder set to D:\actions-runner\_work" -ForegroundColor Green
}

Write-Host "Storage redirection configuration completed!" -ForegroundColor Green
Write-Host "Please restart your terminal/IDE to apply environment variable changes" -ForegroundColor Yellow