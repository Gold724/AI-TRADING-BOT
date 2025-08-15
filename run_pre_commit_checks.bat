@echo off
echo Running Trae Pre-Commit Checks...

:: Clean null bytes
echo Cleaning null bytes from Python files...
for /R %%F in (*.py) do (
    type "%%F" | find /v /c "" > nul
    powershell -command "(Get-Content %%F) -replace [char]0, '' | Set-Content %%F"
)

:: Check .env is not staged
echo Checking if .env is staged...
git diff --cached --name-only | findstr /i ".env"
IF %ERRORLEVEL% EQU 0 (
    echo ❌ ERROR: .env is staged. Remove before committing.
    exit /b 1
) else (
    echo ✅ No .env file staged.
)

:: Lint Python
echo Running flake8...
flake8 .
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Flake8 found issues.
    exit /b %ERRORLEVEL%
) else (
    echo ✅ Flake8 passed.
)

:: Format check with black
echo Checking black formatting...
black --check .
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Black formatting issues found.
    exit /b %ERRORLEVEL%
) else (
    echo ✅ Black formatting passed.
)

echo ✅ All checks passed.