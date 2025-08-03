# Run this script before pushing to GitHub to ensure clean CI/CD

Write-Host "`n🚀 Running CI/CD Pre-Check Script..." -ForegroundColor Cyan

# Step 1: Detect Python files with null bytes
Write-Host "`n🔍 Scanning for null bytes in Python files..." -ForegroundColor Yellow
$badFiles = @()
Get-ChildItem -Recurse -Include *.py | ForEach-Object {
    $bytes = Get-Content $_ -Encoding byte
    if ($bytes -contains 0) {
        $badFiles += $_.FullName
    }
}

if ($badFiles.Count -gt 0) {
    Write-Host "`n⛔ Null bytes detected in the following files:" -ForegroundColor Red
    $badFiles | ForEach-Object { Write-Host "  - $_" }
    Write-Host "`n❗ Fix or delete these files before pushing to GitHub."
    exit 1
} else {
    Write-Host "✅ No null bytes found in Python files." -ForegroundColor Green
}

# Step 2: Run Flake8, Black, Isort
Write-Host "`n📏 Linting and formatting check (flake8, black, isort)..." -ForegroundColor Yellow

try {
    flake8 .
    if ($LASTEXITCODE -ne 0) { throw "Flake8 failed" }

    black --check .
    if ($LASTEXITCODE -ne 0) { throw "Black format check failed" }

    isort --check-only --profile black .
    if ($LASTEXITCODE -ne 0) { throw "Isort check failed" }

    Write-Host "`n✅ Code style checks passed." -ForegroundColor Green
}
catch {
    Write-Host "`n⛔ $_" -ForegroundColor Red
    Write-Host "❗ Fix lint errors before commit." -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 All checks passed. Safe to commit and push!" -ForegroundColor Cyan