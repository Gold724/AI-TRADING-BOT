@echo off
echo.
echo 🚀 Running CI/CD Pre-Check Script...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0ci_cd_precheck.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Pre-check failed. Please fix the issues before committing.
    exit /b 1
) else (
    echo.
    echo 🎉 All checks passed. Safe to commit and push!
)