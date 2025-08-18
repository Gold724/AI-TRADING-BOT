# AI Trading Sentinel - VPS Activation Guide (Windows)
# This script helps you activate all services on your Contabo VPS

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "🤖 AI Trading Sentinel - VPS Activation Guide" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$VPS_IP = "161.97.112.146"
$VNC_PORT = "5901"
$SCRIPT_NAME = "vps_activation_script.sh"

Write-Host "📋 ACTIVATION STEPS OVERVIEW" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor Yellow
Write-Host "1. ✅ VNC Connection Setup"
Write-Host "2. 📁 Upload Activation Script"
Write-Host "3. 🔧 Execute VPS Activation"
Write-Host "4. 🌐 Upload Frontend Files"
Write-Host "5. ✅ Verify Deployment"
Write-Host ""

Write-Host "🖥️  STEP 1: VNC CONNECTION" -ForegroundColor Magenta
Write-Host "---------------------------" -ForegroundColor Magenta
Write-Host "VNC Server: $VPS_IP`:$VNC_PORT" -ForegroundColor White
Write-Host "Password: [Your VNC password]" -ForegroundColor White
Write-Host ""
Write-Host "📥 Download VNC Viewer:" -ForegroundColor Cyan
Write-Host "https://www.realvnc.com/en/connect/download/viewer/" -ForegroundColor Blue
Write-Host ""
Write-Host "🔗 Connection String: vnc://$VPS_IP`:$VNC_PORT" -ForegroundColor Green
Write-Host ""

Write-Host "📁 STEP 2: UPLOAD ACTIVATION SCRIPT" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor Magenta
Write-Host "Option A - Using Local File Server:" -ForegroundColor Cyan
Write-Host "1. Run: python local_file_server.py" -ForegroundColor White
Write-Host "2. In VNC terminal:" -ForegroundColor White
Write-Host "   cd /tmp" -ForegroundColor Gray
Write-Host "   wget http://YOUR_WINDOWS_IP:8000/$SCRIPT_NAME" -ForegroundColor Gray
Write-Host "   chmod +x $SCRIPT_NAME" -ForegroundColor Gray
Write-Host ""
Write-Host "Option B - Copy/Paste Method:" -ForegroundColor Cyan
Write-Host "1. Open VNC terminal" -ForegroundColor White
Write-Host "2. Run: nano /tmp/$SCRIPT_NAME" -ForegroundColor White
Write-Host "3. Copy content from $SCRIPT_NAME and paste" -ForegroundColor White
Write-Host "4. Save with Ctrl+X, Y, Enter" -ForegroundColor White
Write-Host "5. Run: chmod +x /tmp/$SCRIPT_NAME" -ForegroundColor White
Write-Host ""

Write-Host "🔧 STEP 3: EXECUTE VPS ACTIVATION" -ForegroundColor Magenta
Write-Host "----------------------------------" -ForegroundColor Magenta
Write-Host "In VNC terminal, run:" -ForegroundColor Cyan
Write-Host "sudo /tmp/$SCRIPT_NAME" -ForegroundColor Green
Write-Host ""
Write-Host "⏱️  Expected duration: 5-10 minutes" -ForegroundColor Yellow
Write-Host "📋 The script will:" -ForegroundColor Cyan
Write-Host "   ✅ Update system packages" -ForegroundColor White
Write-Host "   ✅ Configure VNC server with systemd" -ForegroundColor White
Write-Host "   ✅ Setup Nginx web server" -ForegroundColor White
Write-Host "   ✅ Deploy Flask backend API" -ForegroundColor White
Write-Host "   ✅ Configure firewall rules" -ForegroundColor White
Write-Host "   ✅ Create service monitoring" -ForegroundColor White
Write-Host ""

Write-Host "🌐 STEP 4: UPLOAD FRONTEND FILES" -ForegroundColor Magenta
Write-Host "----------------------------------" -ForegroundColor Magenta
Write-Host "After activation script completes:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. On Windows, run: python local_file_server.py" -ForegroundColor White
Write-Host "2. In VNC terminal:" -ForegroundColor White
Write-Host "   cd /var/www/html" -ForegroundColor Gray
Write-Host "   wget http://YOUR_WINDOWS_IP:8000/frontend-cloud.zip" -ForegroundColor Gray
Write-Host "   unzip -o frontend-cloud.zip" -ForegroundColor Gray
Write-Host "   rm frontend-cloud.zip" -ForegroundColor Gray
Write-Host "   chown -R www-data:www-data /var/www/html" -ForegroundColor Gray
Write-Host "   systemctl reload nginx" -ForegroundColor Gray
Write-Host ""

Write-Host "✅ STEP 5: VERIFY DEPLOYMENT" -ForegroundColor Magenta
Write-Host "-----------------------------" -ForegroundColor Magenta
Write-Host "Run verification from Windows:" -ForegroundColor Cyan
Write-Host "python verify_deployment.py" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Test URLs:" -ForegroundColor Cyan
Write-Host "• Trading Dashboard: http://$VPS_IP" -ForegroundColor Blue
Write-Host "• API Health Check: http://$VPS_IP/api/health" -ForegroundColor Blue
Write-Host "• Bot Status: http://$VPS_IP/api/status" -ForegroundColor Blue
Write-Host "• VNC Access: vnc://$VPS_IP`:$VNC_PORT" -ForegroundColor Blue
Write-Host ""

Write-Host "🔧 TROUBLESHOOTING COMMANDS" -ForegroundColor Red
Write-Host "---------------------------" -ForegroundColor Red
Write-Host "Check services status:" -ForegroundColor Cyan
Write-Host "systemctl status vncserver@1 nginx ai-trading-backend" -ForegroundColor Gray
Write-Host ""
Write-Host "View service logs:" -ForegroundColor Cyan
Write-Host "journalctl -u ai-trading-backend -f" -ForegroundColor Gray
Write-Host "journalctl -u nginx -f" -ForegroundColor Gray
Write-Host ""
Write-Host "Restart services:" -ForegroundColor Cyan
Write-Host "systemctl restart vncserver@1 nginx ai-trading-backend" -ForegroundColor Gray
Write-Host ""
Write-Host "Check open ports:" -ForegroundColor Cyan
Write-Host "netstat -tuln | grep -E ':(80|5000|5901) '" -ForegroundColor Gray
Write-Host ""
Write-Host "View activation log:" -ForegroundColor Cyan
Write-Host "cat /tmp/vps_activation.log" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 READY TO ACTIVATE VPS!" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green
Write-Host "1. Connect to VNC: vnc://$VPS_IP`:$VNC_PORT" -ForegroundColor Yellow
Write-Host "2. Upload and run activation script" -ForegroundColor Yellow
Write-Host "3. Upload frontend files" -ForegroundColor Yellow
Write-Host "4. Verify deployment" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Tip: Keep this window open for reference during activation!" -ForegroundColor Cyan

# Pause to let user read
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Optional: Start local file server
$startServer = Read-Host "\nStart local file server now? (y/n)"
if ($startServer -eq 'y' -or $startServer -eq 'Y') {
    Write-Host "\n🌐 Starting local file server..." -ForegroundColor Green
    Write-Host "Files will be served from current directory" -ForegroundColor Cyan
    Write-Host "Access URL: http://YOUR_WINDOWS_IP:8000/" -ForegroundColor Blue
    Write-Host "\nPress Ctrl+C to stop the server when done" -ForegroundColor Yellow
    python local_file_server.py
}

Write-Host "\n✅ VPS Activation Guide Complete!" -ForegroundColor Green