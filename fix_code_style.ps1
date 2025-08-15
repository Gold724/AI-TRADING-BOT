# Script to automatically fix code style issues

Write-Host "`nRunning Code Style Fixer..." -ForegroundColor Cyan

# Fix import sorting with isort
Write-Host "`nFixing import sorting with isort..." -ForegroundColor Yellow
try {
    isort --profile black .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Import sorting fixed successfully." -ForegroundColor Green
    } else {
        Write-Host "Error fixing import sorting." -ForegroundColor Red
    }
} catch {
    Write-Host "Error running isort: $_" -ForegroundColor Red
}

# Format code with black
Write-Host "`nFormatting code with black..." -ForegroundColor Yellow
try {
    black .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Code formatting completed successfully." -ForegroundColor Green
    } else {
        Write-Host "Error formatting code." -ForegroundColor Red
    }
} catch {
    Write-Host "Error running black: $_" -ForegroundColor Red
}

# Run flake8 to check for remaining issues
Write-Host "`nChecking for remaining issues with flake8..." -ForegroundColor Yellow
try {
    flake8 .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "No remaining flake8 issues found." -ForegroundColor Green
    } else {
        Write-Host "Some flake8 issues remain. Please fix them manually." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error running flake8: $_" -ForegroundColor Red
}

Write-Host "`nCode style fixing completed. Run ci_cd_precheck.ps1 to verify all issues are fixed." -ForegroundColor Cyan