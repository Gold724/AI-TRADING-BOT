@echo off
echo Starting TRAE AI Trading Sentinel in LiveOps mode...

:: Create logs directory if it doesn't exist
if not exist logs\liveops mkdir logs\liveops

:: Set Python path - adjust if needed
set PYTHONPATH=%PYTHONPATH%;%~dp0

:: Start the main application with LiveOps flag
python main.py --liveops --webhook

echo TRAE LiveOps service started. Check logs\liveops\operations.log for status.