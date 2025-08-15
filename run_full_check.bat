@echo off
echo 🔍 Starting Full System Check (Windows)

REM Load environment variables
setlocal enabledelayedexpansion
for /f "delims=" %%a in (.env) do (
  set "%%a"
)

REM Create logs directory
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots

echo 🚀 SSH into %VAST_INSTANCE_IP%
ssh -i %SSH_KEY_PATH% %SSH_USER%@%VAST_INSTANCE_IP% ^
  "pkill -f cloud_main.py || true && ^
   nohup python3 cloud_main.py > flask.log 2>&1 & sleep 5"

echo 📡 Sending test trade...
curl -X POST http://%VAST_INSTANCE_IP%:%FLASK_PORT%/api/trade/stealth ^
  -H "Content-Type: application/json" ^
  -d "{ \"symbol\": \"GCZ25\", \"action\": \"buy\", \"lots\": 1, \"mode\": \"demo\", \"broker\": \"bulenox\" }"

echo 🖼️ Checking for screenshots...
ssh -i %SSH_KEY_PATH% %SSH_USER%@%VAST_INSTANCE_IP% "ls screenshots | tail -n 1"

echo ✅ Complete!

endlocal
exit /b 0