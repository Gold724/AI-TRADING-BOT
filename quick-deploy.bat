@echo off
REM 🚀 AI Trading Sentinel - Quick 5-Step Production Deployment (Windows)
REM TRAE-SentinelOps: Complete automated deployment for Windows servers

setlocal enabledelayedexpansion

REM Configuration
set SERVER_IP=%1
if "%SERVER_IP%"=="" set SERVER_IP=localhost
set ENVIRONMENT=production

REM Colors (Windows compatible)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set PURPLE=[95m
set NC=[0m

echo %PURPLE%
echo ██████╗ ██████╗  █████╗ ███████╗    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
echo ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
echo    ██║   ██████╔╝███████║█████╗      ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
echo    ██║   ██╔══██╗██╔══██║██╔══╝      ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
echo    ██║   ██║  ██║██║  ██║███████╗    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
echo    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
echo %NC%
echo %BLUE%🚀 AI Trading Sentinel - 5-Step Production Deployment (Windows)%NC%
echo %BLUE%TRAE-SentinelOps: Automated 24/7 Trading Operations%NC%
echo.

if "%SERVER_IP%"=="localhost" (
    echo %YELLOW%⚠ Using localhost - for remote deployment, run: quick-deploy.bat YOUR_SERVER_IP%NC%
)

REM ============================================================================
REM STEP 1: Deploy to Server
REM ============================================================================
echo.
echo %PURPLE%STEP 1: Deploy to Server%NC%
echo %PURPLE%========================%NC%

echo %BLUE%[%time%] Running production deployment...%NC%

if exist "deploy\deploy-production.sh" (
    echo %BLUE%[%time%] Found Linux deployment script%NC%
    echo %YELLOW%⚠ For Windows deployment, ensure WSL is available or use Docker%NC%
    
    REM Check if WSL is available
    wsl --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo %BLUE%[%time%] Running deployment via WSL...%NC%
        wsl chmod +x deploy/deploy-production.sh
        wsl sudo ./deploy/deploy-production.sh
    ) else (
        echo %YELLOW%⚠ WSL not available - manual setup required%NC%
        echo %YELLOW%  Please install required components manually:%NC%
        echo %YELLOW%  - Python 3.10+%NC%
        echo %YELLOW%  - Node.js 18+%NC%
        echo %YELLOW%  - Redis%NC%
        echo %YELLOW%  - PostgreSQL%NC%
        echo %YELLOW%  - Docker Desktop%NC%
    )
) else (
    echo %RED%✗ deploy/deploy-production.sh not found%NC%
    goto :error
)

echo %GREEN%✓ Production deployment completed%NC%

REM ============================================================================
REM STEP 2: Configure Credentials
REM ============================================================================
echo.
echo %PURPLE%STEP 2: Configure Credentials%NC%
echo %PURPLE%==============================%NC%

set ENV_FILE=.env
set ENV_TEMPLATE=.env.template

if not exist "%ENV_TEMPLATE%" (
    echo %RED%✗ .env.template not found%NC%
    goto :error
)

if not exist "%ENV_FILE%" (
    echo %BLUE%[%time%] Creating .env file from template...%NC%
    copy "%ENV_TEMPLATE%" "%ENV_FILE%" >nul
    
    REM Generate secure keys (Windows compatible)
    for /f "delims=" %%i in ('powershell -command "[System.Web.Security.Membership]::GeneratePassword(32, 0)"') do set SECRET_KEY=%%i
    for /f "delims=" %%i in ('powershell -command "[System.Web.Security.Membership]::GeneratePassword(32, 0)"') do set JWT_SECRET=%%i
    for /f "delims=" %%i in ('powershell -command "[System.Web.Security.Membership]::GeneratePassword(32, 0)"') do set ENCRYPTION_KEY=%%i
    
    REM Update .env with generated keys
    powershell -command "(Get-Content '%ENV_FILE%') -replace 'your-secret-key-here', '%SECRET_KEY%' | Set-Content '%ENV_FILE%'"
    powershell -command "(Get-Content '%ENV_FILE%') -replace 'your-jwt-secret-key-here', '%JWT_SECRET%' | Set-Content '%ENV_FILE%'"
    powershell -command "(Get-Content '%ENV_FILE%') -replace 'your-encryption-key-here', '%ENCRYPTION_KEY%' | Set-Content '%ENV_FILE%'"
    
    REM Set production environment
    powershell -command "(Get-Content '%ENV_FILE%') -replace 'ENVIRONMENT=.*', 'ENVIRONMENT=production' | Set-Content '%ENV_FILE%'"
    powershell -command "(Get-Content '%ENV_FILE%') -replace 'DEBUG=.*', 'DEBUG=false' | Set-Content '%ENV_FILE%'"
    powershell -command "(Get-Content '%ENV_FILE%') -replace 'TRADING_ENABLED=.*', 'TRADING_ENABLED=false' | Set-Content '%ENV_FILE%'"
    
    echo %GREEN%✓ .env file created with secure keys%NC%
) else (
    echo %GREEN%✓ .env file already exists%NC%
)

echo.
echo %YELLOW%⚠ IMPORTANT: Update broker credentials in .env file:%NC%
echo %YELLOW%  - BROKER_USERNAME=your-broker-username%NC%
echo %YELLOW%  - BROKER_PASSWORD=your-broker-password%NC%
echo %YELLOW%  - BROKER_URL=https://your-broker-platform.com%NC%
echo %YELLOW%  - BROKER_API_KEY=your-api-key%NC%
echo %YELLOW%  - BROKER_API_SECRET=your-api-secret%NC%
echo.
pause

REM ============================================================================
REM STEP 3: Validate Deployment
REM ============================================================================
echo.
echo %PURPLE%STEP 3: Validate Deployment%NC%
echo %PURPLE%===========================%NC%

echo %BLUE%[%time%] Running deployment validation...%NC%

if exist "scripts\validate_deployment.py" (
    python scripts\validate_deployment.py --environment production
    if !errorlevel! equ 0 (
        echo %GREEN%✓ Deployment validation passed%NC%
    ) else (
        echo %RED%✗ Deployment validation failed - fix issues before proceeding%NC%
        goto :error
    )
) else (
    echo %YELLOW%⚠ Validation script not found, skipping validation%NC%
)

REM ============================================================================
REM STEP 4: Monitor System
REM ============================================================================
echo.
echo %PURPLE%STEP 4: Monitor System%NC%
echo %PURPLE%======================%NC%

echo %BLUE%[%time%] Setting up monitoring access...%NC%

REM Start monitoring stack if Docker is available
docker --version >nul 2>&1
if !errorlevel! equ 0 (
    if exist "docker-compose.monitoring.yml" (
        echo %BLUE%[%time%] Starting monitoring stack...%NC%
        docker-compose -f docker-compose.monitoring.yml up -d
        timeout /t 10 /nobreak >nul
        echo %GREEN%✓ Monitoring stack started%NC%
    )
) else (
    echo %YELLOW%⚠ Docker not available - install Docker Desktop for monitoring%NC%
)

REM Check if services are accessible
curl -s "http://localhost:3000" >nul 2>&1
if !errorlevel! equ 0 (
    echo %GREEN%✓ Grafana is accessible at http://%SERVER_IP%:3000%NC%
    echo %BLUE%  Default login: admin/admin%NC%
    echo %YELLOW%  ⚠ Change default password after first login%NC%
) else (
    echo %YELLOW%⚠ Grafana not accessible - check monitoring stack%NC%
)

curl -s "http://localhost:9090" >nul 2>&1
if !errorlevel! equ 0 (
    echo %GREEN%✓ Prometheus is accessible at http://%SERVER_IP%:9090%NC%
) else (
    echo %YELLOW%⚠ Prometheus not accessible%NC%
)

echo.
echo %BLUE%Key Monitoring URLs:%NC%
echo %BLUE%  • Grafana Dashboard: http://%SERVER_IP%:3000%NC%
echo %BLUE%  • Prometheus Metrics: http://%SERVER_IP%:9090%NC%
echo %BLUE%  • Alertmanager: http://%SERVER_IP%:9093%NC%
echo %BLUE%  • Application Health: http://%SERVER_IP%/health%NC%

REM ============================================================================
REM STEP 5: Start Trading
REM ============================================================================
echo.
echo %PURPLE%STEP 5: Start Trading%NC%
echo %PURPLE%=====================%NC%

echo %BLUE%[%time%] Preparing to start trading operations...%NC%

REM Start application services
if exist "backend_main.py" (
    echo %BLUE%[%time%] Starting backend service...%NC%
    start "AI Trading Backend" python backend_main.py
    timeout /t 3 /nobreak >nul
    echo %GREEN%✓ Backend started%NC%
)

if exist "main.py" (
    echo %BLUE%[%time%] Starting main bot (trading disabled)...%NC%
    start "AI Trading Bot" python main.py
    timeout /t 3 /nobreak >nul
    echo %GREEN%✓ Main bot started (trading disabled)%NC%
)

REM Check service health
echo %BLUE%[%time%] Checking service health...%NC%
timeout /t 10 /nobreak >nul

curl -s "http://localhost:5000/api/health" >nul 2>&1
if !errorlevel! equ 0 (
    echo %GREEN%✓ API health check passed%NC%
) else (
    echo %YELLOW%⚠ API health check failed - check service logs%NC%
)

echo.
echo %RED%⚠ TRADING IS CURRENTLY DISABLED FOR SAFETY%NC%
echo.
echo %YELLOW%To enable live trading:%NC%
echo %YELLOW%1. Monitor system for 24 hours to ensure stability%NC%
echo %YELLOW%2. Verify all broker credentials are working%NC%
echo %YELLOW%3. Test with small position sizes first%NC%
echo %YELLOW%4. Set TRADING_ENABLED=true in .env file%NC%
echo %YELLOW%5. Restart the services%NC%

REM ============================================================================
REM DEPLOYMENT COMPLETE
REM ============================================================================
echo.
echo %PURPLE%🚀 DEPLOYMENT COMPLETE%NC%
echo %PURPLE%======================%NC%

echo.
echo %GREEN%AI Trading Sentinel has been successfully deployed!%NC%
echo.

echo %BLUE%📊 Access URLs:%NC%
echo   • Frontend: http://%SERVER_IP%
echo   • API: http://%SERVER_IP%/api
echo   • Health Check: http://%SERVER_IP%/health
echo   • Grafana: http://%SERVER_IP%:3000 (admin/admin)
echo   • Prometheus: http://%SERVER_IP%:9090

echo.
echo %BLUE%🔧 Useful Commands:%NC%
echo   • Check processes: tasklist ^| findstr python
echo   • View logs: type logs\backend.log
echo   • Restart services: Ctrl+C in service windows, then restart
echo   • Validate: python scripts\validate_deployment.py --environment production

echo.
echo %RED%⚠️  IMPORTANT NEXT STEPS:%NC%
echo   1. Change Grafana default password (admin/admin)
echo   2. Update broker credentials in .env file
echo   3. Monitor system stability for 24 hours
echo   4. Test with demo account before live trading
echo   5. Enable trading: TRADING_ENABLED=true in .env

echo.
echo %GREEN%🎉 Ready for 24/7 automated trading operations!%NC%
echo.

goto :end

:error
echo.
echo %RED%❌ Deployment failed! Please check the errors above.%NC%
exit /b 1

:end
echo %BLUE%Deployment completed successfully! 🎉%NC%
pause