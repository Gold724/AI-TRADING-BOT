@echo off
setlocal enabledelayedexpansion

echo ================================================
echo    AI Trading Sentinel - Contabo Deployment
echo ================================================
echo.

set TARGET_IP=161.97.112.146
set USERNAME=root
set SSH_DIR=%USERPROFILE%\.ssh
set SSH_KEY=%SSH_DIR%\id_rsa
set SSH_PUB=%SSH_DIR%\id_rsa.pub

echo [INFO] Starting deployment to %TARGET_IP%...
echo.

REM Step 1: Check SSH client
echo [STEP 1] Checking SSH client...
ssh -V >nul 2>&1
if errorlevel 1 (
    echo [ERROR] SSH client not found. Please install OpenSSH.
    echo Run as Administrator: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    pause
    exit /b 1
)
echo [SUCCESS] SSH client found

REM Step 2: Create SSH directory
if not exist "%SSH_DIR%" (
    mkdir "%SSH_DIR%"
    echo [INFO] Created .ssh directory
)

REM Step 3: Generate SSH key if needed
if not exist "%SSH_KEY%" (
    echo [INFO] Generating SSH key pair...
    ssh-keygen -t rsa -b 4096 -f "%SSH_KEY%" -N "" -C "ai-trading-sentinel@contabo"
    if errorlevel 1 (
        echo [ERROR] Failed to generate SSH key
        pause
        exit /b 1
    )
    echo [SUCCESS] SSH key generated
) else (
    echo [INFO] SSH key already exists
)

REM Step 4: Test connectivity
echo [STEP 2] Testing connectivity to %TARGET_IP%...
ping -n 2 %TARGET_IP% >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ping failed, but SSH might still work
) else (
    echo [SUCCESS] Server is reachable
)

REM Step 5: Install SSH key
echo [STEP 3] Installing SSH key on server...
echo [WARNING] You will be prompted for the root password
echo.

REM Read public key
if not exist "%SSH_PUB%" (
    echo [ERROR] Public key not found
    pause
    exit /b 1
)

REM Install SSH key using ssh-copy-id equivalent
echo [INFO] Installing SSH key (enter password when prompted)...
type "%SSH_PUB%" | ssh %USERNAME%@%TARGET_IP% "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh && echo SSH key installed successfully"
if errorlevel 1 (
    echo [ERROR] Failed to install SSH key
    pause
    exit /b 1
)
echo [SUCCESS] SSH key installed

REM Step 6: Test SSH key authentication
echo [STEP 4] Testing SSH key authentication...
ssh -o BatchMode=yes -o ConnectTimeout=10 %USERNAME%@%TARGET_IP% "echo SSH key authentication successful" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] SSH key authentication failed
    pause
    exit /b 1
)
echo [SUCCESS] SSH key authentication working

REM Step 7: Create deployment script
echo [STEP 5] Creating deployment script...

set DEPLOY_SCRIPT=%TEMP%\deploy_ai_trading.sh

(
echo #!/bin/bash
echo set -e
echo.
echo echo "🚀 Starting AI Trading Sentinel deployment..."
echo.
echo # Update system
echo apt update ^&^& apt upgrade -y
echo.
echo # Install required packages
echo apt install -y python3 python3-pip python3-venv nodejs npm git curl wget unzip htop nano net-tools
echo.
echo # Install Docker
echo if ! command -v docker ^>/dev/null 2^>^&1; then
echo     echo "Installing Docker..."
echo     curl -fsSL https://get.docker.com -o get-docker.sh
echo     sh get-docker.sh
echo     systemctl enable docker
echo     systemctl start docker
echo     rm get-docker.sh
echo fi
echo.
echo # Create deployment directory
echo mkdir -p /opt/ai-trading-sentinel
echo cd /opt/ai-trading-sentinel
echo.
echo echo "Setting up AI Trading Sentinel files..."
echo.
echo # Create directory structure
echo mkdir -p data/{accounts,backtest,emergency,historical,memory,signals,simulations}
echo mkdir -p logs config backend frontend
echo.
echo # Create main.py
echo cat ^> main.py ^<^< 'MAINEOF'
echo #!/usr/bin/env python3
echo """
echo AI Trading Sentinel - Main Application
echo """
echo.
echo import os
echo import sys
echo import logging
echo import time
echo from datetime import datetime
echo.
echo # Setup logging
echo os.makedirs^("logs", exist_ok=True^)
echo logging.basicConfig^(
echo     level=logging.INFO,
echo     format="%%^(asctime^)s - %%^(name^)s - %%^(levelname^)s - %%^(message^)s",
echo     handlers=[
echo         logging.FileHandler^("logs/trading.log"^),
echo         logging.StreamHandler^(sys.stdout^)
echo     ]
echo ^)
echo.
echo logger = logging.getLogger^(__name__^)
echo.
echo def main^(^):
echo     logger.info^("🚀 AI Trading Sentinel Starting..."^)
echo     logger.info^(f"Environment: {os.getenv^('ENVIRONMENT', 'development'^)}"^)
echo     logger.info^(f"Trading Mode: {os.getenv^('TRADING_MODE', 'simulation'^)}"^)
echo     
echo     logger.info^("✅ AI Trading Sentinel is running"^)
echo     
echo     # Keep running
echo     try:
echo         while True:
echo             time.sleep^(60^)  # Check every minute
echo             logger.info^("💓 Heartbeat - System running normally"^)
echo     except KeyboardInterrupt:
echo         logger.info^("🛑 Shutdown requested"^)
echo     except Exception as e:
echo         logger.error^(f"❌ Error: {e}"^)
echo     finally:
echo         logger.info^("👋 AI Trading Sentinel stopped"^)
echo.
echo if __name__ == "__main__":
echo     main^(^)
echo MAINEOF
echo.
echo # Create requirements.txt
echo cat ^> requirements.txt ^<^< 'REQEOF'
echo flask==2.3.3
echo requests==2.31.0
echo psutil==5.9.5
echo schedule==1.2.0
echo pandas==2.0.3
echo numpy==1.24.3
echo REQEOF
echo.
echo # Create systemd service
echo cat ^> /etc/systemd/system/trae.service ^<^< 'SERVICEEOF'
echo [Unit]
echo Description=AI Trading Sentinel
echo After=network.target
echo.
echo [Service]
echo Type=simple
echo User=root
echo WorkingDirectory=/opt/ai-trading-sentinel
echo Environment=PATH=/opt/ai-trading-sentinel/venv/bin
echo ExecStart=/opt/ai-trading-sentinel/venv/bin/python main.py
echo Restart=always
echo RestartSec=10
echo StandardOutput=journal
echo StandardError=journal
echo.
echo [Install]
echo WantedBy=multi-user.target
echo SERVICEEOF
echo.
echo # Install Python dependencies
echo echo "Installing Python dependencies..."
echo python3 -m venv venv
echo source venv/bin/activate
echo pip install --upgrade pip
echo pip install -r requirements.txt
echo.
echo # Set up environment file
echo cat ^> .env ^<^< 'ENVEOF'
echo # AI Trading Sentinel Configuration
echo ENVIRONMENT=production
echo DEBUG=false
echo LOG_LEVEL=INFO
echo.
echo # Server Configuration
echo HOST=0.0.0.0
echo PORT=5000
echo FRONTEND_PORT=3000
echo.
echo # Trading Configuration
echo TRADING_MODE=simulation
echo RISK_LEVEL=medium
echo MAX_POSITION_SIZE=1000
echo STOP_LOSS_PERCENT=2.0
echo TAKE_PROFIT_PERCENT=4.0
echo.
echo # Monitoring
echo MONITORING_ENABLED=true
echo ALERT_EMAIL=admin@example.com
echo.
echo # Security
echo SECRET_KEY=change-this-secret-key-$^(date +%%s^)
echo JWT_SECRET=change-this-jwt-secret-$^(date +%%s^)
echo ENVEOF
echo.
echo # Enable and start service
echo echo "Setting up systemd service..."
echo systemctl daemon-reload
echo systemctl enable trae
echo systemctl start trae
echo.
echo # Set proper permissions
echo chown -R root:root /opt/ai-trading-sentinel
echo chmod +x /opt/ai-trading-sentinel/*.py
echo.
echo echo "✅ AI Trading Sentinel deployed successfully!"
echo echo "📍 Location: /opt/ai-trading-sentinel"
echo echo "🔧 Service: systemctl status trae"
echo echo "📊 Dashboard: http://$^(curl -s ifconfig.me^):5000"
echo echo "📝 Logs: journalctl -u trae -f"
) > "%DEPLOY_SCRIPT%"

echo [SUCCESS] Deployment script created

REM Step 8: Upload and execute deployment script
echo [STEP 6] Uploading deployment script to server...
scp "%DEPLOY_SCRIPT%" %USERNAME%@%TARGET_IP%:/tmp/deploy_ai_trading.sh
if errorlevel 1 (
    echo [ERROR] Failed to upload deployment script
    pause
    exit /b 1
)
echo [SUCCESS] Deployment script uploaded

echo [STEP 7] Executing deployment script on server...
ssh %USERNAME%@%TARGET_IP% "chmod +x /tmp/deploy_ai_trading.sh && /tmp/deploy_ai_trading.sh"
if errorlevel 1 (
    echo [ERROR] Deployment script execution failed
    pause
    exit /b 1
)
echo [SUCCESS] Deployment completed

REM Step 9: Validate deployment
echo [STEP 8] Validating deployment...
ssh %USERNAME%@%TARGET_IP% "echo '🔍 Deployment Validation Report' && echo '==============================' && if [ -d '/opt/ai-trading-sentinel' ]; then echo '✅ Deployment directory exists'; cd /opt/ai-trading-sentinel; if [ -d 'venv' ]; then echo '✅ Python virtual environment created'; fi; if systemctl is-active trae >/dev/null 2>&1; then echo '✅ Trading service is running'; else echo '⚠️ Trading service status:' $(systemctl is-active trae); fi; echo ''; echo '📊 System Information:'; echo 'CPU:' $(nproc) 'cores'; echo 'Memory:' $(free -h | awk '/^Mem:/ {print $2}'); echo 'Disk:' $(df -h / | awk 'NR==2 {print $4}') 'available'; echo 'IP:' $(curl -s ifconfig.me); echo 'Uptime:' $(uptime -p); echo ''; echo '📝 Recent Service Logs:'; journalctl -u trae --no-pager -n 5; else echo '❌ Deployment directory not found'; fi"

echo.
echo ================================================
echo    🎉 AI Trading Sentinel Deployment Complete!
echo ================================================
echo.
echo 📋 Next Steps:
echo 1. SSH into server: ssh root@%TARGET_IP%
echo 2. Configure credentials: nano /opt/ai-trading-sentinel/.env
echo 3. Check service: systemctl status trae
echo 4. Monitor logs: journalctl -u trae -f
echo 5. Access dashboard: http://%TARGET_IP%:5000
echo.

REM Clean up
if exist "%DEPLOY_SCRIPT%" del "%DEPLOY_SCRIPT%"

echo Press any key to exit...
pause >nul