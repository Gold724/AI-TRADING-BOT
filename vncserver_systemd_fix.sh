#!/bin/bash
# VNC Systemd Service Creation Script
# This script creates the missing vncserver@.service file for systemd management

echo "Creating VNC systemd service file..."

# Create the systemd service file
sudo tee /etc/systemd/system/vncserver@.service > /dev/null <<EOF
[Unit]
Description=Start TightVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/root

PIDFile=/root/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1280x800 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
EOF

echo "VNC systemd service file created successfully!"

# Reload systemd and enable the service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling VNC server service..."
sudo systemctl enable vncserver@1.service

echo "Starting VNC server service..."
sudo systemctl start vncserver@1.service

echo "Checking VNC service status..."
sudo systemctl status vncserver@1.service

echo "VNC server should now be running as a systemd service!"
echo "You can manage it with:"
echo "  sudo systemctl start vncserver@1.service"
echo "  sudo systemctl stop vncserver@1.service"
echo "  sudo systemctl restart vncserver@1.service"
echo "  sudo systemctl status vncserver@1.service"

echo "VNC server is accessible at: 161.97.112.146:5901"