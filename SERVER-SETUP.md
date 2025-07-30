# AI Trading Sentinel Server Setup Guide

## Overview

The AI Trading Sentinel consists of two main components:

1. **Backend Server**: A Flask API running on port 5000
2. **Frontend Server**: A React application running on port 5176

This guide provides instructions for starting, checking, and troubleshooting these servers.

## Quick Start

### Starting Both Servers

To start both the frontend and backend servers with a single command, run:

```powershell
.\start-servers.ps1
```

This script will:
- Check if the required ports are available
- Start the backend server on port 5000
- Start the frontend server on port 5176
- Provide URLs for accessing both servers

### Checking Server Status

To check if both servers are running correctly, run:

```powershell
.\check-server-status.ps1
```

This script will:
- Verify if the backend server is running on port 5000
- Test the backend API health endpoint
- Verify if the frontend server is running on port 5176
- Check the Vite proxy configuration
- Provide troubleshooting guidance if issues are detected

## Manual Server Management

### Starting the Backend Server

To manually start the backend server:

```powershell
cd .\backend
python main.py
```

### Starting the Frontend Server

To manually start the frontend server:

```powershell
cd .\frontend
npm run dev
```

## Common Issues and Solutions

### Connection Errors (`net::ERR_ABORTED`)

If you see errors like:
```
net::ERR_ABORTED http://localhost:5000/api/logs
net::ERR_ABORTED http://localhost:5000/api/strategy
net::ERR_ABORTED http://localhost:5000/api/signal
net::ERR_ABORTED http://localhost:5000/api/health
Error fetching signal: TypeError: Failed to fetch
```

**Possible causes and solutions:**

1. **Backend server is not running**
   - Start the backend server using the instructions above
   - Verify it's running on port 5000

2. **Incorrect proxy configuration**
   - Check `frontend/vite.config.ts` to ensure the proxy target is set to `http://localhost:5000`

3. **Port conflicts**
   - Ensure no other applications are using ports 5000 or 5176
   - Use `netstat -ano | findstr 5000` to check if port 5000 is in use

### PowerShell Command Syntax

Remember that PowerShell uses semicolons (`;`) for command chaining, not ampersands (`&&`):

```powershell
# Correct syntax for PowerShell
cd .\backend; python main.py

# Incorrect syntax (will cause errors)
cd .\backend && python main.py
```

## Important Notes

1. Always ensure both frontend and backend servers are running
2. The frontend proxy is configured to forward API requests to http://localhost:5000
3. The backend server must be running on port 5000 for the proxy configuration to work correctly
4. If you modify the Vite configuration, you'll need to restart the frontend server

## Architecture Reference

### Backend Components

- **API Endpoints**: Defined in `main.py` and various blueprint files
- **Strategy Mutation**: Managed by `api_strategy_mutation.py` and `strategies/strategy_mutation.py`
- **Signal Broadcasting**: Implemented in `broadcast.py`
- **Auto-Recovery Engine**: Implemented in `auto_recovery.py`
- **Dashboard API**: Implemented in `api_dashboard.py`

### Frontend Components

- **Vite Development Server**: Configured in `frontend/vite.config.ts`
- **API Proxy**: Routes `/api` requests to the backend server