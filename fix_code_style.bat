@echo off
echo.
echo Running Code Style Fixer...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0fix_code_style.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some issues could not be fixed automatically. Please check the output.
) else (
    echo.
    echo Code style fixing completed successfully!
)