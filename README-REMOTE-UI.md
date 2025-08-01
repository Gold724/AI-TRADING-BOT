# AI Trading Sentinel Remote UI

The Remote UI provides a web-based interface for monitoring and controlling the AI Trading Sentinel system. It consists of a React frontend and a Flask backend API that communicates with the trading system.

## Features

- **Heartbeat Monitoring**: Real-time status of the trading sentinel heartbeat
- **Trade Execution Controls**: Manually trigger trades or control automated trading
- **Session Management**: View and manage active trading sessions
- **Performance Statistics**: View daily trading statistics and performance metrics
- **Symbol Status**: Monitor the status of different trading symbols
- **Compounding Tracker**: Track compounding growth of trading account

## Architecture

The Remote UI consists of two main components:

1. **Frontend**: React application with TypeScript and Tailwind CSS
2. **Backend API**: Flask-based RESTful API that interfaces with the trading system

Both components are containerized using Docker for easy deployment and development.

## Development Setup

### Prerequisites

- Docker and Docker Compose installed
- Git repository cloned locally

### Starting the Development Environment

#### Windows

```bash
.\start_remote_ui_dev.bat
```

#### Linux/macOS

```bash
# Make the script executable (first time only)
chmod +x start_remote_ui_dev.sh

# Run the script
./start_remote_ui_dev.sh
```

This will start both the frontend and backend services in development mode with hot-reloading enabled.

- Frontend will be available at: http://localhost:3000
- Backend API will be available at: http://localhost:5000

## API Endpoints

The backend API provides the following endpoints:

- `/api/health`: Health check endpoint
- `/api/login`: Login to broker account
- `/api/trade`: Execute trades
- `/api/sessions`: Manage trading sessions
- `/api/status`: Get system status
- `/api/strategy`: Configure trading strategies
- `/api/logs`: Access system logs
- `/api/heartbeat/status`: Get heartbeat status

## Production Deployment

For production deployment, use the standard Docker Compose file without the override:

```bash
docker-compose up -d
```

## Component Overview

### Frontend Components

- **HeartbeatMonitor**: Displays the current status of the trading sentinel
- **HeartbeatStatus**: Shows detailed heartbeat status with visual indicators
- **RemoteControlPanel**: Provides controls for manual trading operations
- **DailyStats**: Displays daily trading statistics
- **SymbolStatusPanel**: Shows status of different trading symbols
- **CompoundingTracker**: Tracks account growth over time

### Backend Services

- **cloud_main.py**: Main Flask application with API endpoints
- **cloud_trade_executor.py**: Handles trade execution in the cloud environment

## Troubleshooting

### Common Issues

1. **Docker not running**: Ensure Docker Desktop (Windows/Mac) or Docker service (Linux) is running
2. **Port conflicts**: Make sure ports 3000 and 5000 are not in use by other applications
3. **Connection issues**: Check that the API URL in the frontend environment is correctly configured

### Logs

To view logs for troubleshooting:

```bash
docker-compose logs -f
```

Or to view logs for a specific service:

```bash
docker-compose logs -f frontend
# or
docker-compose logs -f sentinel-bot
```