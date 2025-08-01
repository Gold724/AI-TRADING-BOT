# PowerShell Scripts for AI Trading Sentinel Remote UI

This document provides information about the PowerShell scripts available for managing the AI Trading Sentinel Remote UI on Windows systems.

## Available Scripts

### 1. `start_remote_ui_dev.ps1`

Starts the AI Trading Sentinel Remote UI in development mode using Docker Compose.

**Usage:**
```powershell
.\start_remote_ui_dev.ps1
```

**Features:**
- Checks if Docker is running
- Starts the frontend and backend services using docker-compose
- Provides URLs for accessing the frontend and backend
- Offers an option to view logs

### 2. `stop_remote_ui.ps1`

Stops the AI Trading Sentinel Remote UI services.

**Usage:**
```powershell
.\stop_remote_ui.ps1
```

**Features:**
- Checks if Docker is running
- Stops all services using docker-compose down

### 3. `check_remote_ui_status.ps1`

Checks the status of the AI Trading Sentinel Remote UI services.

**Usage:**
```powershell
.\check_remote_ui_status.ps1
```

**Features:**
- Checks if Docker is running
- Displays the status of all services
- Shows the last 10 lines of logs for each service

## Requirements

- Windows PowerShell 5.1 or later
- Docker Desktop for Windows
- Docker Compose

## Execution Policy

If you encounter issues running the scripts due to execution policy restrictions, you may need to adjust your PowerShell execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or run the scripts with the bypass flag:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\start_remote_ui_dev.ps1
```

## Troubleshooting

1. **Docker not running**: Ensure Docker Desktop is running before executing the scripts.
2. **Port conflicts**: Make sure ports 3000 and 5000 are not in use by other applications.
3. **Permission issues**: Run PowerShell as Administrator if you encounter permission problems.