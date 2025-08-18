#!/bin/bash

# TRAE Backend Manual Start Script
# Quick start for Flask backend on VPS

set -e

echo "🚀 Starting TRAE Backend..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Run this script from ai-trading-sentinel directory"
    echo "Usage: cd ~/ai-trading-sentinel && ./start_backend.sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install flask flask-cors python-dotenv requests

# Load environment variables
if [ -f ".env" ]; then
    echo "🔑 Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env file not found"
fi

# Start Flask backend
echo "🌐 Starting Flask backend on 0.0.0.0:5000..."
echo "📡 Access URL: http://$(curl -s ifconfig.me):5000"
echo "🛑 Press Ctrl+C to stop"
echo "================================"

cd backend
python main.py