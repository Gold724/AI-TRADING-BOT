#!/usr/bin/env pwsh
# AI Trading Sentinel - VNC Remote Setup Script

Write-Host "AI Trading Sentinel - VNC Remote Setup" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$VPS_IP = "161.97.112.146"

Write-Host "VNC Setup Instructions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Connect to VPS manually:" -ForegroundColor White
Write-Host "   ssh root@$VPS_IP" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Copy and paste these commands one by one:" -ForegroundColor White
Write-Host ""

Write-Host "# Update system" -ForegroundColor Green
Write-Host "apt update" -ForegroundColor Gray
Write-Host "apt upgrade -y" -ForegroundColor Gray
Write-Host ""

Write-Host "# Install desktop and VNC" -ForegroundColor Green
Write-Host "apt install -y xfce4 xfce4-goodies tightvncserver firefox nginx unzip curl git python3-pip" -ForegroundColor Gray
Write-Host ""

Write-Host "# Configure VNC (will prompt for password)" -ForegroundColor Green
Write-Host "vncserver :1" -ForegroundColor Gray
Write-Host "vncserver -kill :1" -ForegroundColor Gray
Write-Host ""

Write-Host "# Create VNC startup script" -ForegroundColor Green
Write-Host "cat > ~/.vnc/xstartup << 'EOF'" -ForegroundColor Gray
Write-Host "#!/bin/bash" -ForegroundColor Gray
Write-Host "xrdb \$HOME/.Xresources" -ForegroundColor Gray
Write-Host "startxfce4 &" -ForegroundColor Gray
Write-Host "EOF" -ForegroundColor Gray
Write-Host "chmod +x ~/.vnc/xstartup" -ForegroundColor Gray
Write-Host ""

Write-Host "# Enable VNC service" -ForegroundColor Green
Write-Host "systemctl daemon-reload" -ForegroundColor Gray
Write-Host "systemctl enable vncserver@1.service" -ForegroundColor Gray
Write-Host "systemctl start vncserver@1.service" -ForegroundColor Gray
Write-Host ""

Write-Host "# Configure firewall" -ForegroundColor Green
Write-Host "ufw allow 5901/tcp" -ForegroundColor Gray
Write-Host "ufw allow 80/tcp" -ForegroundColor Gray
Write-Host "ufw allow 443/tcp" -ForegroundColor Gray
Write-Host "ufw allow 5000/tcp" -ForegroundColor Gray
Write-Host "ufw --force enable" -ForegroundColor Gray
Write-Host ""

Write-Host "3. After setup completes:" -ForegroundColor White
Write-Host "   - Download VNC Viewer from: https://www.realvnc.com/en/connect/download/viewer/" -ForegroundColor Gray
Write-Host "   - Connect to: $VPS_IP:5901" -ForegroundColor Gray
Write-Host "   - Use the VNC password you set" -ForegroundColor Gray
Write-Host ""

Write-Host "Frontend Deployment via VNC:" -ForegroundColor Yellow
Write-Host "1. Connect to VNC desktop" -ForegroundColor White
Write-Host "2. Open Firefox and download frontend-cloud.zip" -ForegroundColor White
Write-Host "3. Extract to /var/www/html/" -ForegroundColor White
Write-Host "4. Configure Nginx (see VNC_DEPLOYMENT_GUIDE.md)" -ForegroundColor White
Write-Host "5. Access trading dashboard at: http://$VPS_IP" -ForegroundColor White
Write-Host ""

Write-Host "Ready for VNC deployment! No SSH authentication issues!" -ForegroundColor Green