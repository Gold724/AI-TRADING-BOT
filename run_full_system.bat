@echo off
echo Starting AI Trading Sentinel System...

echo Starting Backend Server...
start cmd /k "cd backend && python main.py"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo Starting Frontend Server...
start cmd /k "cd frontend && npm run dev"

echo System started! Frontend will be available at http://localhost:5173
echo Backend API is running at http://localhost:5000