# Script to find and optionally fix files with null bytes

# Color codes for PowerShell
$GREEN = "\e[32m"
$YELLOW = "\e[33m"
$RED = "\e[31m"
$BLUE = "\e[34m"
$NC = "\e[0m" # No Color

Write-Host "$BLUE=== AI Trading Sentinel - Null Byte Detector ===$NC"
Write-Host "$YELLOWThis script will find files with null bytes that can cause issues$NC"
Write-Host ""

# Function to check if a file contains null bytes
function Test-FileContainsNullBytes {
    param (
        [string]$FilePath
    )
    
    try {
        $content = [System.IO.File]::ReadAllBytes($FilePath)
        return $content -contains 0
    } catch {
        Write-Host "$RED Error reading file: $FilePath $NC"
        return $false
    }
}

# Function to fix a file with null bytes
function Remove-NullBytes {
    param (
        [string]$FilePath
    )
    
    try {
        # Read the file as bytes
        $content = [System.IO.File]::ReadAllBytes($FilePath)
        
        # Remove null bytes
        $newContent = $content | Where-Object { $_ -ne 0 }
        
        # Create backup
        $backupPath = "$FilePath.backup"
        [System.IO.File]::WriteAllBytes($backupPath, $content)
        
        # Write the cleaned content back to the file
        [System.IO.File]::WriteAllBytes($FilePath, $newContent)
        
        Write-Host "$GREEN Fixed file: $FilePath (Backup created at $backupPath) $NC"
        return $true
    } catch {
        Write-Host "$RED Error fixing file: $FilePath - $($_.Exception.Message) $NC"
        return $false
    }
}

# Get all Python files, excluding venv directory
Write-Host "$BLUE[1/3] Scanning for Python files...$NC"
$pythonFiles = Get-ChildItem -Path . -Filter *.py -Recurse | Where-Object { $_.FullName -notlike "*\venv\*" }
Write-Host "$GREEN Found $($pythonFiles.Count) Python files to check $NC"

# Check each file for null bytes
Write-Host "$BLUE[2/3] Checking for null bytes...$NC"
$filesWithNullBytes = @()

foreach ($file in $pythonFiles) {
    $hasNullBytes = Test-FileContainsNullBytes -FilePath $file.FullName
    if ($hasNullBytes) {
        $filesWithNullBytes += $file.FullName
        Write-Host "$YELLOW ❌ Found null bytes in: $($file.FullName) $NC"
    }
}

Write-Host ""
Write-Host "$BLUE[3/3] Results:$NC"
if ($filesWithNullBytes.Count -eq 0) {
    Write-Host "$GREEN ✅ No files with null bytes found! $NC"
} else {
    Write-Host "$YELLOW Found $($filesWithNullBytes.Count) files with null bytes: $NC"
    foreach ($file in $filesWithNullBytes) {
        Write-Host "   - $file"
    }
    
    Write-Host ""
    $fixFiles = Read-Host "Do you want to fix these files? (y/n)"
    
    if ($fixFiles -eq "y" -or $fixFiles -eq "Y") {
        $fixedCount = 0
        foreach ($file in $filesWithNullBytes) {
            $success = Remove-NullBytes -FilePath $file
            if ($success) {
                $fixedCount++
            }
        }
        
        Write-Host ""
        Write-Host "$GREEN Fixed $fixedCount out of $($filesWithNullBytes.Count) files $NC"
        Write-Host "$YELLOW Backups were created with .backup extension $NC"
    } else {
        Write-Host "$YELLOW No files were modified $NC"
    }
}

Write-Host ""
Write-Host "$BLUE=== Scan Complete ===$NC"