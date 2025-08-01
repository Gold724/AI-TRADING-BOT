@echo off
setlocal enabledelayedexpansion

:: CI/CD Verification Script for AI Trading Sentinel (Windows version)
:: This script helps verify and fix common CI/CD setup issues

:: Color codes for Windows terminal
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set BLUE=[94m
set NC=[0m

echo %BLUE%=== AI Trading Sentinel - CI/CD Setup Verification ===%NC%
echo %YELLOW%This script will check and fix common CI/CD setup issues%NC%
echo.

:: Check if .github/workflows directory exists
echo %GREEN%[1/7] Checking for .github/workflows directory...%NC%
if not exist ".github\workflows" (
    echo %RED%❌ .github/workflows directory not found!%NC%
    echo %YELLOW%Creating directory...%NC%
    mkdir ".github\workflows"
    echo %GREEN%✅ Created .github/workflows directory%NC%
) else (
    echo %GREEN%✅ .github/workflows directory exists%NC%
)

:: Check if ci_cd_pipeline.yml exists
echo %GREEN%[2/7] Checking for CI/CD workflow file...%NC%
if not exist ".github\workflows\ci_cd_pipeline.yml" (
    echo %RED%❌ ci_cd_pipeline.yml not found!%NC%
    echo %YELLOW%Please check if the file exists with a different name or create it.%NC%
    echo %YELLOW%See CI_CD_TROUBLESHOOTING.md for guidance.%NC%
) else (
    echo %GREEN%✅ ci_cd_pipeline.yml exists%NC%
)

:: Check if .github is in .gitignore
echo %GREEN%[3/7] Checking if .github is in .gitignore...%NC%
findstr /C:".github/" .gitignore >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %RED%❌ .github/ is in .gitignore!%NC%
    echo %YELLOW%Fixing .gitignore...%NC%
    
    :: Create a temporary file without the .github/ line
    type nul > .gitignore.tmp
    for /f "tokens=*" %%a in (.gitignore) do (
        echo %%a | findstr /C:".github/" >nul 2>&1
        if %ERRORLEVEL% NEQ 0 (
            echo %%a >> .gitignore.tmp
        )
    )
    
    :: Add specific exclusion for secrets only
    echo # Only ignore GitHub secrets, not workflows >> .gitignore.tmp
    echo .github/secrets.env >> .gitignore.tmp
    
    :: Replace original file
    move /y .gitignore.tmp .gitignore
    echo %GREEN%✅ Fixed .gitignore%NC%
) else (
    echo %GREEN%✅ .github/ is not in .gitignore%NC%
)

:: Cannot validate YAML syntax easily in Windows batch
echo %GREEN%[4/7] Validating YAML syntax...%NC%
echo %YELLOW%⚠️ YAML validation not available in Windows batch script%NC%
echo %YELLOW%Consider installing yamllint via Python: pip install yamllint%NC%

:: Check if workflow file is committed
echo %GREEN%[5/7] Checking if workflow file is committed...%NC%
git log -- .github/workflows/ci_cd_pipeline.yml 2>nul | findstr /C:"commit" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %GREEN%✅ Workflow file is committed%NC%
) else (
    echo %RED%❌ Workflow file is not committed!%NC%
    echo %YELLOW%Committing workflow file...%NC%
    git add .github/workflows/ci_cd_pipeline.yml
    git commit -m "Add CI/CD workflow file"
    echo %GREEN%✅ Committed workflow file%NC%
)

:: Check if GitHub secrets are set (can only suggest)
echo %GREEN%[6/7] Checking for GitHub secrets...%NC%
echo %YELLOW%⚠️ Cannot check GitHub secrets locally%NC%
echo %YELLOW%Please ensure these secrets are set in your GitHub repository:%NC%
echo   - CONTABO_VPS_IP
echo   - CONTABO_VPS_PASSWORD
echo   - CONTABO_SSH_PORT

:: Offer to push changes
echo %GREEN%[7/7] Checking for unpushed changes...%NC%
git status --porcelain >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %YELLOW%⚠️ You have uncommitted changes%NC%
    echo %YELLOW%Consider committing and pushing:%NC%
    echo   git add .
    echo   git commit -m "Fix CI/CD setup"
    echo   git push origin main
) else (
    echo %GREEN%✅ No uncommitted changes%NC%
    
    :: Check for unpushed commits
    for /f "tokens=*" %%a in ('git rev-parse @') do set LOCAL=%%a
    for /f "tokens=*" %%a in ('git rev-parse @{u} 2^>nul') do set REMOTE=%%a
    
    if not defined REMOTE (
        echo %YELLOW%⚠️ No upstream branch set%NC%
        echo %YELLOW%Set upstream branch with:%NC%
        echo   git push -u origin main
    ) else if not "!LOCAL!"=="!REMOTE!" (
        echo %YELLOW%⚠️ You have unpushed commits%NC%
        echo %YELLOW%Push your changes with:%NC%
        echo   git push origin main
    ) else (
        echo %GREEN%✅ All changes are pushed%NC%
    )
)

echo %BLUE%=== Verification Complete ===%NC%
echo %YELLOW%For more detailed troubleshooting, see:%NC%
echo   CI_CD_TROUBLESHOOTING.md

endlocal