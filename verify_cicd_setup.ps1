# CI/CD Verification Script for AI Trading Sentinel (PowerShell version)
# This script helps verify and fix common CI/CD setup issues

# Color codes for PowerShell
$GREEN = "\e[32m"
$YELLOW = "\e[33m"
$RED = "\e[31m"
$BLUE = "\e[34m"
$NC = "\e[0m" # No Color

Write-Host "$BLUE=== AI Trading Sentinel - CI/CD Setup Verification ===$NC"
Write-Host "$YELLOWThis script will check and fix common CI/CD setup issues$NC"
Write-Host ""

# Check if .github/workflows directory exists
Write-Host "$GREEN[1/7] Checking for .github/workflows directory...$NC"
if (-not (Test-Path ".github\workflows")) {
    Write-Host "$RED❌ .github/workflows directory not found!$NC"
    Write-Host "$YELLOWCreating directory...$NC"
    New-Item -Path ".github\workflows" -ItemType Directory -Force | Out-Null
    Write-Host "$GREEN✅ Created .github/workflows directory$NC"
} else {
    Write-Host "$GREEN✅ .github/workflows directory exists$NC"
}

# Check if ci_cd_pipeline.yml exists
Write-Host "$GREEN[2/7] Checking for CI/CD workflow file...$NC"
if (-not (Test-Path ".github\workflows\ci_cd_pipeline.yml")) {
    Write-Host "$RED❌ ci_cd_pipeline.yml not found!$NC"
    Write-Host "$YELLOWPlease check if the file exists with a different name or create it.$NC"
    Write-Host "$YELLOWSee CI_CD_TROUBLESHOOTING.md for guidance.$NC"
} else {
    Write-Host "$GREEN✅ ci_cd_pipeline.yml exists$NC"
}

# Check if .github is in .gitignore
Write-Host "$GREEN[3/7] Checking if .github is in .gitignore...$NC"
if (Test-Path ".gitignore") {
    $gitignoreContent = Get-Content ".gitignore"
    if ($gitignoreContent -match "\.github/") {
        Write-Host "$RED❌ .github/ is in .gitignore!$NC"
        Write-Host "$YELLOWFixing .gitignore...$NC"
        
        # Create a new .gitignore without the .github/ line
        $newContent = $gitignoreContent | Where-Object { $_ -notmatch "\.github/" }
        
        # Add specific exclusion for secrets only
        $newContent += "# Only ignore GitHub secrets, not workflows"
        $newContent += ".github/secrets.env"
        
        # Write the new content
        $newContent | Set-Content ".gitignore"
        Write-Host "$GREEN✅ Fixed .gitignore$NC"
    } else {
        Write-Host "$GREEN✅ .github/ is not in .gitignore$NC"
    }
} else {
    Write-Host "$YELLOW⚠️ .gitignore file not found$NC"
}

# Check for YAML validation
Write-Host "$GREEN[4/7] Validating YAML syntax...$NC"
$yamllintExists = Get-Command yamllint -ErrorAction SilentlyContinue
if ($yamllintExists) {
    $result = yamllint .github/workflows/ci_cd_pipeline.yml 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$GREEN✅ YAML syntax is valid$NC"
    } else {
        Write-Host "$RED❌ YAML syntax errors found!$NC"
        Write-Host "$YELLOW$result$NC"
        Write-Host "$YELLOWPlease fix the errors above.$NC"
    }
} else {
    Write-Host "$YELLOW⚠️ yamllint not installed, skipping syntax validation$NC"
    Write-Host "$YELLOWInstall with: pip install yamllint$NC"
}

# Check if workflow file is committed
Write-Host "$GREEN[5/7] Checking if workflow file is committed...$NC"
$gitLog = git log -- .github/workflows/ci_cd_pipeline.yml 2>&1
if ($gitLog -match "commit") {
    Write-Host "$GREEN✅ Workflow file is committed$NC"
} else {
    Write-Host "$RED❌ Workflow file is not committed!$NC"
    Write-Host "$YELLOWCommitting workflow file...$NC"
    git add .github/workflows/ci_cd_pipeline.yml
    git commit -m "Add CI/CD workflow file"
    Write-Host "$GREEN✅ Committed workflow file$NC"
}

# Check if GitHub secrets are set (can only suggest)
Write-Host "$GREEN[6/7] Checking for GitHub secrets...$NC"
Write-Host "$YELLOW⚠️ Cannot check GitHub secrets locally$NC"
Write-Host "$YELLOWPlease ensure these secrets are set in your GitHub repository:$NC"
Write-Host "  - CONTABO_VPS_IP"
Write-Host "  - CONTABO_VPS_PASSWORD"
Write-Host "  - CONTABO_SSH_PORT"

# Offer to push changes
Write-Host "$GREEN[7/7] Checking for unpushed changes...$NC"
$status = git status --porcelain
if ($status) {
    Write-Host "$YELLOW⚠️ You have uncommitted changes$NC"
    Write-Host "$YELLOWConsider committing and pushing:$NC"
    Write-Host "  git add ."
    Write-Host "  git commit -m \"Fix CI/CD setup\""
    Write-Host "  git push origin main"
} else {
    Write-Host "$GREEN✅ No uncommitted changes$NC"
    
    # Check for unpushed commits
    try {
        $LOCAL = git rev-parse @
        $REMOTE = git rev-parse @{u} 2>$null
        
        if (-not $REMOTE) {
            Write-Host "$YELLOW⚠️ No upstream branch set$NC"
            Write-Host "$YELLOWSet upstream branch with:$NC"
            Write-Host "  git push -u origin main"
        } elseif ($LOCAL -ne $REMOTE) {
            Write-Host "$YELLOW⚠️ You have unpushed commits$NC"
            Write-Host "$YELLOWPush your changes with:$NC"
            Write-Host "  git push origin main"
        } else {
            Write-Host "$GREEN✅ All changes are pushed$NC"
        }
    } catch {
        Write-Host "$YELLOW⚠️ Could not determine push status$NC"
    }
}

Write-Host "$BLUE=== Verification Complete ===$NC"
Write-Host "$YELLOWFor more detailed troubleshooting, see:$NC"
Write-Host "  CI_CD_TROUBLESHOOTING.md"