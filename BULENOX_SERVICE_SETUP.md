# Bulenox Sentinel Service Setup

This guide explains how to set up the Bulenox Sentinel (Adaptive Selenium) as a service on your system.

## Linux/Unix Setup

### Available Service Files

#### 1. Basic Service (`bulenox.service`)

This is a basic systemd service configuration that will run the Bulenox Sentinel and restart it automatically if it crashes.

#### 2. Service with Logging (`bulenox-with-logs.service`)

This enhanced service configuration includes automatic log saving to make debugging easier. It will:
- Log output to the systemd journal
- Save standard output to `/opt/bulenox/bulenox_output.log`
- Save error output to `/opt/bulenox/bulenox_error.log`
- Implement progressive backoff for restarts to prevent excessive restart attempts

### Installation Instructions (Linux)

#### Using the Basic Service

```bash
# Copy the service file to systemd
sudo cp bulenox.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable bulenox.service

# Start the service
sudo systemctl restart bulenox.service

# Check the service status
sudo systemctl status bulenox.service -l
```

#### Using the Service with Logging

```bash
# Copy the service file to systemd
sudo cp bulenox-with-logs.service /etc/systemd/system/bulenox.service

# Create log directory if it doesn't exist
sudo mkdir -p /opt/bulenox

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable bulenox.service

# Start the service
sudo systemctl restart bulenox.service

# Check the service status
sudo systemctl status bulenox.service -l
```

#### Automated Installation (Linux)

For convenience, you can use the provided setup script:

```bash
# Make the script executable
chmod +x setup_bulenox_service.sh

# Run the script as root
sudo ./setup_bulenox_service.sh
```

The script will ask which service configuration you want to use and handle the installation process automatically.

### Viewing Logs (Linux)

#### Systemd Journal Logs

```bash
# View all logs
sudo journalctl -u bulenox

# Follow logs in real-time
sudo journalctl -u bulenox -f

# View logs since a specific time
sudo journalctl -u bulenox --since "2023-01-01"

# View only error logs
sudo journalctl -u bulenox -p err
```

#### File Logs (if using bulenox-with-logs.service)

```bash
# View output logs
tail -f /opt/bulenox/bulenox_output.log

# View error logs
tail -f /opt/bulenox/bulenox_error.log
```

## Windows Setup

### Windows Service Installation

For Windows systems, we provide a batch script that uses NSSM (Non-Sucking Service Manager) to create a Windows service:

1. Download NSSM from [https://nssm.cc/download](https://nssm.cc/download) if you don't have it installed
2. Extract the zip file and copy `nssm.exe` to `C:\Windows\System32`
3. Run the setup script as Administrator:
   ```
   Right-click on setup_bulenox_service_windows.bat and select "Run as administrator"
   ```

The script will:
- Create necessary directories at `C:\opt\bulenox`
- Set up log files
- Create a Windows service named "BulenoxSentinel"
- Configure automatic restart on failure

### Viewing Logs (Windows)

Since Windows doesn't have the `tail` command, we provide a PowerShell script to view logs:

```powershell
# View output log (default)
.\view_bulenox_logs.ps1

# View error log
.\view_bulenox_logs.ps1 -LogType error

# View last 100 lines
.\view_bulenox_logs.ps1 -Lines 100

# Monitor log in real-time (similar to tail -f)
.\view_bulenox_logs.ps1 -Follow
```

### Managing the Windows Service

```
# Start the service
net start BulenoxSentinel

# Stop the service
net stop BulenoxSentinel

# Remove the service
nssm remove BulenoxSentinel
```

## Testing Chrome Installation

Before setting up the service, you can verify that Chrome is working properly on your system:

```bash
# Linux
python test_chrome_vps.py
```

```powershell
# Windows
python test_chrome_vps.py
```

This script will:
- Initialize Chrome in headless mode
- Navigate to Google
- Take a screenshot
- Display Chrome and ChromeDriver versions

If the test completes successfully, Chrome is properly configured for use with Selenium.

## Troubleshooting

If the service fails to start:

### Linux

1. Check the logs for errors:
   ```bash
   sudo journalctl -u bulenox -n 50
   ```

2. Verify that the Python script exists at the specified path:
   ```bash
   ls -la /opt/bulenox/bulenox_ai_selenium_adaptive_uc.py
   ```

3. Ensure the virtual environment is properly set up:
   ```bash
   ls -la /opt/bulenox/venv/bin/python
   ```

4. Try running the script manually to see if there are any errors:
   ```bash
   cd /opt/bulenox
   ./venv/bin/python bulenox_ai_selenium_adaptive_uc.py
   ```

5. Check if Chrome is installed and working properly:
   ```bash
   google-chrome --version
   ```

### Windows

1. Check the service status in the Windows Services manager:
   ```
   services.msc
   ```

2. View the log files:
   ```powershell
   .\view_bulenox_logs.ps1 -LogType error
   ```

3. Verify that the Python script exists at the specified path:
   ```powershell
   Test-Path "C:\opt\bulenox\bulenox_ai_selenium_adaptive_uc.py"
   ```

4. Ensure the virtual environment is properly set up:
   ```powershell
   Test-Path "C:\opt\bulenox\venv\Scripts\python.exe"
   ```

5. Try running the script manually to see if there are any errors:
   ```powershell
   cd C:\opt\bulenox
   .\venv\Scripts\python.exe bulenox_ai_selenium_adaptive_uc.py
   ```

6. Check if Chrome is installed and working properly:
   ```powershell
   python test_chrome_vps.py
   ```