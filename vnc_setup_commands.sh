#!/bin/bash
# AI Trading Sentinel - VNC Setup Commands
# Run these commands on your VPS (161.97.112.146)

echo "🚀 AI Trading Sentinel - VNC Setup Starting..."

# Update system
echo "📦 Updating system packages..."
apt update
apt upgrade -y

# Install desktop environment and VNC
echo "🖥️ Installing desktop environment and VNC server..."
apt install -y xfce4 xfce4-goodies tightvncserver firefox nginx unzip curl git python3-pip

# Configure VNC server
echo "🔧 Configuring VNC server..."
echo "⚠️  You will be prompted to set a VNC password - remember this!"
vncserver :1

# Stop VNC to configure startup script
vncserver -kill :1

# Create VNC startup script
echo "📝 Creating VNC startup script..."
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF

# Make startup script executable
chmod +x ~/.vnc/xstartup

# Create systemd service for VNC auto-start
echo "⚙️ Creating VNC systemd service..."
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
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1920x1080 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
EOF

# Enable and start VNC service
echo "🔄 Enabling VNC service..."
systemctl daemon-reload
systemctl enable vncserver@1.service
systemctl start vncserver@1.service

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 5901/tcp  # VNC
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5000/tcp  # Flask API
ufw --force enable

# Verify VNC service status
echo "✅ Checking VNC service status..."
systemctl status vncserver@1.service

echo ""
echo "🎉 VNC Server setup complete!"
echo "🖥️  VNC Access: 161.97.112.146:5901"
echo "🌐 Web Access: http://161.97.112.146 (after frontend deployment)"
echo ""
echo "📋 Next steps:"
echo "1. Download VNC Viewer: https://www.realvnc.com/en/connect/download/viewer/"
echo "2. Connect to: 161.97.112.146:5901"
echo "3. Use the VNC password you just set"
echo "4. Deploy frontend via VNC desktop interface"
echo ""
echo "🚀 Ready for global trading access via VNC! 🚀"