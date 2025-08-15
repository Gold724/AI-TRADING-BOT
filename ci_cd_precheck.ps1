# Run this script before pushing to GitHub to ensure clean CI/CD

Write-Host "`nRunning CI/CD Pre-Check Script..." -ForegroundColor Cyan

# Step 1: Detect Python files with null bytes
Write-Host "`nScanning for null bytes in Python files..." -ForegroundColor Yellow
$badFiles = @()

Get-ChildItem -Recurse -Include *.py | ForEach-Object {
    $bytes = Get-Content $_ -Encoding byte
    if ($bytes -contains 0) {
        $badFiles += $_.FullName
    }
}

if ($badFiles.Count -gt 0) {
    Write-Host "`nNull bytes detected in the following files:" -ForegroundColor Red
    $badFiles | ForEach-Object { Write-Host "  - $_" }
    Write-Host "`nFix or delete these files before pushing to GitHub."
    exit 1
}

Write-Host "No null bytes found in Python files." -ForegroundColor Green

# Step 2: Run Flake8, Black, Isort
Write-Host "`nLinting and formatting check (flake8, black, isort)..." -ForegroundColor Yellow

$success = $true

# Run flake8
try {
    flake8 .
    if ($LASTEXITCODE -ne 0) { 
        $success = $false
        Write-Host "Flake8 check failed" -ForegroundColor Red
    }
} catch {
    $success = $false
    Write-Host "Error running flake8: $_" -ForegroundColor Red
}

# Run black
try {
    black --check .
    if ($LASTEXITCODE -ne 0) { 
        $success = $false
        Write-Host "Black format check failed" -ForegroundColor Red
    }
} catch {
    $success = $false
    Write-Host "Error running black: $_" -ForegroundColor Red
}

# Run isort
try {
    isort --check-only --profile black .
    if ($LASTEXITCODE -ne 0) { 
        $success = $false
        Write-Host "Isort check failed" -ForegroundColor Red
    }
} catch {
    $success = $false
    Write-Host "Error running isort: $_" -ForegroundColor Red
}

if ($success) {
    Write-Host "`nCode style checks passed." -ForegroundColor Green
    Write-Host "`nAll checks passed. Safe to commit and push!" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "`nFix lint errors before commit." -ForegroundColor Red
    exit 1
}