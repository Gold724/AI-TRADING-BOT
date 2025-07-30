#!/bin/bash

echo "Starting AI Trading Sentinel System..."

echo "Starting Backend Server..."
cd backend && python main.py &
BACKEND_PID=$!

echo "Waiting for backend to initialize..."
sleep 5

echo "Starting Frontend Server..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo "System started! Frontend will be available at http://localhost:5173"
echo "Backend API is running at http://localhost:5000"
echo "Press Ctrl+C to stop all servers"

# Handle graceful shutdown
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait