#!/bin/bash
# Bulenox Sentinel Service Setup Script

set -e  # Exit on error

# Display banner
echo "=== Bulenox Sentinel Service Setup Script ==="
echo "This script will set up the Bulenox Sentinel as a systemd service"
echo ""

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Ask user which service file to use
echo "Which service configuration would you like to use?"
echo "1) Basic service (bulenox.service)"
echo "2) Service with logging (bulenox-with-logs.service)"
read -p "Enter your choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
    SERVICE_FILE="bulenox.service"
    echo "Using basic service configuration"
else
    SERVICE_FILE="bulenox-with-logs.service"
    echo "Using service configuration with logging"
    
    # Create log directory if it doesn't exist
    echo "Creating log directory..."
    mkdir -p /opt/bulenox
    touch /opt/bulenox/bulenox_output.log
    touch /opt/bulenox/bulenox_error.log
    chmod 644 /opt/bulenox/bulenox_output.log
    chmod 644 /opt/bulenox/bulenox_error.log
fi

# Copy the service file
echo "Copying $SERVICE_FILE to /etc/systemd/system/bulenox.service"
cp "$SERVICE_FILE" /etc/systemd/system/bulenox.service
chmod 644 /etc/systemd/system/bulenox.service

# Reload systemd
echo "Reloading systemd daemon"
systemctl daemon-reload

# Enable the service
echo "Enabling bulenox service"
systemctl enable bulenox.service

# Start the service
echo "Starting bulenox service"
systemctl restart bulenox.service

# Check service status
echo "Checking service status:"
systemctl status bulenox.service --no-pager

echo ""
echo "=== Setup Complete ==="
echo "To view logs, run: sudo journalctl -u bulenox -f"
if [ "$choice" != "1" ]; then
    echo "Or check the log files:"
    echo "  - Output log: tail -f /opt/bulenox/bulenox_output.log"
    echo "  - Error log: tail -f /opt/bulenox/bulenox_error.log"
fi