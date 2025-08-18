#!/bin/bash
# Direct VNC Systemd Service Creation (no file upload needed)
# Execute these commands directly on the VPS

echo "=== Creating VNC Systemd Service Directly ==="

# Create the systemd service file directly
cat > /etc/systemd/system/vncserver@.service << 'EOF'
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

echo "✅ VNC systemd service file created!"

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable the service
echo "🚀 Enabling VNC server service..."
systemctl enable vncserver@1.service

# Start the service
echo "▶️ Starting VNC server service..."
systemctl start vncserver@1.service

# Check status
echo "📊 VNC service status:"
systemctl status vncserver@1.service --no-pager

echo ""
echo "=== VNC Server Management Commands ==="
echo "Start:   systemctl start vncserver@1.service"
echo "Stop:    systemctl stop vncserver@1.service"
echo "Restart: systemctl restart vncserver@1.service"
echo "Status:  systemctl status vncserver@1.service"
echo ""
echo "🌐 VNC Access: 161.97.112.146:5901"
echo "✅ VNC server is now managed by systemd!"