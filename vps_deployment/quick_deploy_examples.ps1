# Quick Deployment Examples for AI Trading Sentinel (PowerShell)
# Choose the scenario that matches your VPS setup

Write-Host "🚀 AI Trading Sentinel - Quick Deploy Examples" -ForegroundColor Green
Write-Host "Choose your deployment scenario:" -ForegroundColor Yellow
Write-Host "1. Standard Contambo VPS (root user)" -ForegroundColor White
Write-Host "2. Custom VPS with different user" -ForegroundColor White
Write-Host "3. VPS with custom SSH port" -ForegroundColor White
Write-Host "4. VPS with SSH key authentication" -ForegroundColor White
Write-Host "5. Manual step-by-step deployment" -ForegroundColor White
Write-Host "6. Verify existing deployment" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "📋 Standard Contambo VPS Deployment" -ForegroundColor Cyan
        Write-Host "Edit deploy_to_vps.sh and set:" -ForegroundColor Yellow
        Write-Host 'VPS_HOST="your-contambo-ip"' -ForegroundColor White
        Write-Host 'VPS_USER="root"' -ForegroundColor White
        Write-Host 'VPS_DIR="/root/AI-TRADING-BOT"' -ForegroundColor White
        Write-Host ""
        Write-Host "Then run: bash deploy_to_vps.sh" -ForegroundColor Green
        Write-Host "Or use WSL: wsl bash deploy_to_vps.sh" -ForegroundColor Green
    }
    "2" {
        Write-Host "👤 Custom User Deployment" -ForegroundColor Cyan
        $vps_ip = Read-Host "Enter VPS IP"
        $username = Read-Host "Enter username"
        
        $VPS_HOST = $vps_ip
        $VPS_USER = $username
        $VPS_DIR = "/home/$username/AI-TRADING-BOT"
        
        Write-Host "🚀 Deploying to $VPS_HOST as $VPS_USER..." -ForegroundColor Green
        
        Write-Host "📁 Creating remote directory..." -ForegroundColor Yellow
        ssh "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_DIR"
        
        Write-Host "📤 Copying files..." -ForegroundColor Yellow
        scp -r "trading_scripts/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -r "launchers/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -r "utilities/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp "vps_environment_check.py" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        
        Write-Host "🔧 Setting permissions..." -ForegroundColor Yellow
        ssh "$VPS_USER@$VPS_HOST" "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"
        
        Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
        ssh "$VPS_USER@$VPS_HOST" "cd $VPS_DIR; pip3 install -r requirements.txt"
        ssh "$VPS_USER@$VPS_HOST" "cd $VPS_DIR; python3 -m playwright install"
        
        Write-Host "✅ Deployment completed to $VPS_HOST`:$VPS_DIR" -ForegroundColor Green
    }
    "3" {
        Write-Host "🔌 Custom SSH Port Deployment" -ForegroundColor Cyan
        $vps_ip = Read-Host "Enter VPS IP"
        $ssh_port = Read-Host "Enter SSH port"
        $username = Read-Host "Enter username (default: root)"
        if ([string]::IsNullOrEmpty($username)) { $username = "root" }
        
        $VPS_HOST = $vps_ip
        $VPS_USER = $username
        $VPS_DIR = "/root/AI-TRADING-BOT"
        $SSH_PORT = $ssh_port
        
        Write-Host "🚀 Deploying to $VPS_HOST`:$SSH_PORT as $VPS_USER..." -ForegroundColor Green
        
        Write-Host "📁 Creating remote directory..." -ForegroundColor Yellow
        ssh -p $SSH_PORT "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_DIR"
        
        Write-Host "📤 Copying files..." -ForegroundColor Yellow
        scp -P $SSH_PORT -r "trading_scripts/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -P $SSH_PORT -r "launchers/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -P $SSH_PORT -r "utilities/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -P $SSH_PORT "vps_environment_check.py" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        
        Write-Host "🔧 Setting permissions and installing..." -ForegroundColor Yellow
        ssh -p $SSH_PORT "$VPS_USER@$VPS_HOST" "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"
        ssh -p $SSH_PORT "$VPS_USER@$VPS_HOST" "cd $VPS_DIR; pip3 install -r requirements.txt"
        ssh -p $SSH_PORT "$VPS_USER@$VPS_HOST" "cd $VPS_DIR; python3 -m playwright install"
        
        Write-Host "✅ Deployment completed to $VPS_HOST`:$SSH_PORT`:$VPS_DIR" -ForegroundColor Green
    }
    "4" {
        Write-Host "🔑 SSH Key Authentication Deployment" -ForegroundColor Cyan
        $vps_ip = Read-Host "Enter VPS IP"
        $key_path = Read-Host "Enter SSH key path (default: ~/.ssh/id_rsa)"
        if ([string]::IsNullOrEmpty($key_path)) { $key_path = "~/.ssh/id_rsa" }
        $username = Read-Host "Enter username (default: root)"
        if ([string]::IsNullOrEmpty($username)) { $username = "root" }
        
        $VPS_HOST = $vps_ip
        $VPS_USER = $username
        $VPS_DIR = "/root/AI-TRADING-BOT"
        $SSH_KEY = $key_path
        
        Write-Host "🚀 Deploying to $VPS_HOST with key $SSH_KEY as $VPS_USER..." -ForegroundColor Green
        
        Write-Host "🔍 Testing SSH connection..." -ForegroundColor Yellow
        ssh -i $SSH_KEY "$VPS_USER@$VPS_HOST" "echo 'SSH connection successful'"
        
        Write-Host "📁 Creating remote directory..." -ForegroundColor Yellow
        ssh -i $SSH_KEY "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_DIR"
        
        Write-Host "📤 Copying files..." -ForegroundColor Yellow
        scp -i $SSH_KEY -r "trading_scripts/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -i $SSH_KEY -r "launchers/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -i $SSH_KEY -r "utilities/*" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        scp -i $SSH_KEY "vps_environment_check.py" "$VPS_USER@$VPS_HOST`:$VPS_DIR/"
        
        Write-Host "🔧 Setting permissions and installing..." -ForegroundColor Yellow
        ssh -i $SSH_KEY "$VPS_USER@$VPS_HOST" "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"
        ssh -i $SSH_KEY "$VPS_USER@$VPS_HOST" "cd $VPS_DIR; pip3 install -r requirements.txt"
        ssh -i $SSH_KEY "$VPS_USER@$VPS_HOST" "cd $VPS_DIR; python3 -m playwright install"
        
        Write-Host "✅ Deployment completed to $VPS_HOST`:$VPS_DIR" -ForegroundColor Green
    }
    "5" {
        Write-Host "📋 Manual Step-by-Step Deployment" -ForegroundColor Cyan
        $vps_ip = Read-Host "Enter VPS IP"
        $username = Read-Host "Enter username (default: root)"
        if ([string]::IsNullOrEmpty($username)) { $username = "root" }
        
        Write-Host ""
        Write-Host "🔧 Manual Deployment Steps:" -ForegroundColor Yellow
        Write-Host "1. Create directory:" -ForegroundColor White
        Write-Host "   ssh $username@$vps_ip 'mkdir -p /root/AI-TRADING-BOT'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Copy trading scripts:" -ForegroundColor White
        Write-Host "   scp trading_scripts/* $username@$vps_ip`:/root/AI-TRADING-BOT/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Copy launchers:" -ForegroundColor White
        Write-Host "   scp launchers/* $username@$vps_ip`:/root/AI-TRADING-BOT/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "4. Copy utilities:" -ForegroundColor White
        Write-Host "   scp utilities/* $username@$vps_ip`:/root/AI-TRADING-BOT/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "5. Copy environment checker:" -ForegroundColor White
        Write-Host "   scp vps_environment_check.py $username@$vps_ip`:/root/AI-TRADING-BOT/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "6. Set permissions:" -ForegroundColor White
        Write-Host "   ssh $username@$vps_ip 'chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "7. Install dependencies:" -ForegroundColor White
        Write-Host "   ssh $username@$vps_ip 'cd /root/AI-TRADING-BOT; pip3 install -r requirements.txt'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "8. Install Playwright:" -ForegroundColor White
        Write-Host "   ssh $username@$vps_ip 'cd /root/AI-TRADING-BOT; python3 -m playwright install'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "9. Verify deployment:" -ForegroundColor White
        Write-Host "   ssh $username@$vps_ip 'cd /root/AI-TRADING-BOT; python3 vps_environment_check.py'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "10. Set credentials:" -ForegroundColor White
        Write-Host "    ssh $username@$vps_ip" -ForegroundColor Gray
        Write-Host "    cd /root/AI-TRADING-BOT" -ForegroundColor Gray
        Write-Host "    echo 'BULENOX_USERNAME=your_username' > .env" -ForegroundColor Gray
        Write-Host "    echo 'BULENOX_PASSWORD=your_password' >> .env" -ForegroundColor Gray
        Write-Host "    chmod 600 .env" -ForegroundColor Gray
        Write-Host ""
        Write-Host "11. Test deployment:" -ForegroundColor White
        Write-Host "    ./live_trading_launcher.sh" -ForegroundColor Gray
    }
    "6" {
        Write-Host "🔍 Verify Existing Deployment" -ForegroundColor Cyan
        $vps_ip = Read-Host "Enter VPS IP"
        $username = Read-Host "Enter username (default: root)"
        if ([string]::IsNullOrEmpty($username)) { $username = "root" }
        
        Write-Host "🔍 Checking deployment on $vps_ip..." -ForegroundColor Yellow
        
        # Check if directory exists
        try {
            ssh "$username@$vps_ip" "test -d /root/AI-TRADING-BOT"
            Write-Host "✅ Directory exists: /root/AI-TRADING-BOT" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Directory missing: /root/AI-TRADING-BOT" -ForegroundColor Red
            exit 1
        }
        
        # Check core files
        Write-Host "📁 Checking core files..." -ForegroundColor Yellow
        ssh "$username@$vps_ip" "ls -la /root/AI-TRADING-BOT/"
        
        # Run environment check
        Write-Host "🔧 Running environment validation..." -ForegroundColor Yellow
        ssh "$username@$vps_ip" "cd /root/AI-TRADING-BOT; python3 vps_environment_check.py"
        
        Write-Host "✅ Verification completed" -ForegroundColor Green
    }
    default {
        Write-Host "❌ Invalid choice. Please run the script again and choose 1-6." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Deployment process completed!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. SSH to your VPS: ssh username@vps_ip" -ForegroundColor White
Write-Host "2. Navigate to: cd /root/AI-TRADING-BOT" -ForegroundColor White
Write-Host "3. Set credentials: echo 'BULENOX_USERNAME=your_user' > .env" -ForegroundColor White
Write-Host "4. Add password: echo 'BULENOX_PASSWORD=your_pass' >> .env" -ForegroundColor White
Write-Host "5. Secure file: chmod 600 .env" -ForegroundColor White
Write-Host "6. Start trading: ./live_trading_launcher.sh" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitor logs: tail -f /root/AI-TRADING-BOT/logs/trading.log" -ForegroundColor Cyan
Write-Host "🔍 Health check: python3 vps_environment_check.py" -ForegroundColor Cyan

# Pause to keep window open
Read-Host "Press Enter to exit"