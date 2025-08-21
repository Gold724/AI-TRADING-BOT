# AI Trading Sentinel - Bulenox URL Cleanup Script
# Replace all incorrect bulenox.com URLs with bulenox.projectx.com/login

Write-Host "[INFO] Starting Bulenox URL cleanup..." -ForegroundColor Cyan

# URL mappings
$urlMappings = @{
    'https://bulenox.projectx.com/login' = 'https://bulenox.projectx.com/login'
    'https://bulenox.projectx.com/login' = 'https://bulenox.projectx.com/login'
    'https://bulenox.projectx.com/api' = 'https://bulenox.projectx.com/api'
    'https://bulenox.projectx.com' = 'https://bulenox.projectx.com'
    'https://bulenox.projectx.com' = 'https://bulenox.projectx.com'
    'bulenox.projectx.com/login' = 'bulenox.projectx.com/login'
    'bulenox.projectx.com/login' = 'bulenox.projectx.com/login'
    'bulenox.projectx.com/api' = 'bulenox.projectx.com/api'
}

# File extensions to process
$extensions = @('*.py', '*.js', '*.json', '*.md', '*.txt', '*.sh', '*.ps1', '*.yml', '*.yaml', '*.cfg', '*.conf')

# Directories to exclude
$excludeDirs = @('.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env', 'dist', 'build')

$totalReplacements = 0
$filesModified = 0

# Get all files to process
$allFiles = @()
foreach ($ext in $extensions) {
    $files = Get-ChildItem -Path . -Filter $ext -Recurse | Where-Object {
        $exclude = $false
        foreach ($dir in $excludeDirs) {
            if ($_.FullName -like "*\$dir\*") {
                $exclude = $true
                break
            }
        }
        return -not $exclude
    }
    $allFiles += $files
}

Write-Host "[INFO] Processing $($allFiles.Count) files..." -ForegroundColor Yellow

# Process each file
foreach ($file in $allFiles) {
    try {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
        $originalContent = $content
        $fileReplacements = 0
        
        # Apply all URL mappings
        foreach ($mapping in $urlMappings.GetEnumerator()) {
            $oldUrl = $mapping.Key
            $newUrl = $mapping.Value
            
            if ($content -match [regex]::Escape($oldUrl)) {
                $content = $content -replace [regex]::Escape($oldUrl), $newUrl
                $fileReplacements++
                Write-Host "  [OK] $($file.Name) - $oldUrl -> $newUrl" -ForegroundColor Green
            }
        }
        
        # Save file if modified
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -NoNewline
            $filesModified++
            $totalReplacements += $fileReplacements
        }
    }
    catch {
        Write-Host "  [ERROR] Failed to process $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n[SUCCESS] URL Cleanup Complete!" -ForegroundColor Green
Write-Host "[INFO] Files modified: $filesModified" -ForegroundColor Cyan
Write-Host "[INFO] Total replacements: $totalReplacements" -ForegroundColor Cyan

# Verify critical files
Write-Host "`n[VERIFY] Checking critical files..." -ForegroundColor Yellow
$criticalFiles = @(
    'health_check.py',
    'bulenox_trade_request.py',
    'stealth_executor.py',
    'login_diagnostic.py'
)

foreach ($criticalFile in $criticalFiles) {
    if (Test-Path $criticalFile) {
        $content = Get-Content -Path $criticalFile -Raw
        if ($content -match 'bulenox\.projectx\.com') {
            Write-Host "  [OK] $criticalFile - Uses correct projectx.com URLs" -ForegroundColor Green
        } elseif ($content -match 'bulenox\.com') {
            Write-Host "  [WARN] $criticalFile - Still contains old bulenox.com URLs" -ForegroundColor Yellow
        } else {
            Write-Host "  [INFO] $criticalFile - No Bulenox URLs found" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [ERROR] $criticalFile - File not found" -ForegroundColor Red
    }
}

Write-Host "`n[SUCCESS] Ready for deployment with correct Bulenox ProjectX URLs!" -ForegroundColor Green
Write-Host "[NEXT] Run health_check.py to verify system integrity" -ForegroundColor Cyan