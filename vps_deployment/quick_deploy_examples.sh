#!/bin/bash
# Quick Deployment Examples for AI Trading Sentinel
# Choose the scenario that matches your VPS setup

set -e

echo "🚀 AI Trading Sentinel - Quick Deploy Examples"
echo "Choose your deployment scenario:"
echo "1. Standard Contambo VPS (root user)"
echo "2. Custom VPS with different user"
echo "3. VPS with custom SSH port"
echo "4. VPS with SSH key authentication"
echo "5. Manual step-by-step deployment"
echo "6. Verify existing deployment"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo "📋 Standard Contambo VPS Deployment"
        echo "Edit deploy_to_vps.sh and set:"
        echo "VPS_HOST=\"your-contambo-ip\""
        echo "VPS_USER=\"root\""
        echo "VPS_DIR=\"/root/AI-TRADING-BOT\""
        echo ""
        echo "Then run: ./deploy_to_vps.sh"
        ;;
    2)
        echo "👤 Custom User Deployment"
        read -p "Enter VPS IP: " vps_ip
        read -p "Enter username: " username
        
        VPS_HOST="$vps_ip"
        VPS_USER="$username"
        VPS_DIR="/home/$username/AI-TRADING-BOT"
        
        echo "🚀 Deploying to $VPS_HOST as $VPS_USER..."
        
        # Create remote directory
        ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"
        
        # Copy files
        scp -r trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -r launchers/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -r utilities/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp vps_environment_check.py $VPS_USER@$VPS_HOST:$VPS_DIR/
        
        # Set permissions
        ssh $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"
        
        # Install dependencies
        ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && pip3 install -r requirements.txt"
        ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 -m playwright install"
        
        echo "✅ Deployment completed to $VPS_HOST:$VPS_DIR"
        ;;
    3)
        echo "🔌 Custom SSH Port Deployment"
        read -p "Enter VPS IP: " vps_ip
        read -p "Enter SSH port: " ssh_port
        read -p "Enter username (default: root): " username
        username=${username:-root}
        
        VPS_HOST="$vps_ip"
        VPS_USER="$username"
        VPS_DIR="/root/AI-TRADING-BOT"
        SSH_PORT="$ssh_port"
        
        echo "🚀 Deploying to $VPS_HOST:$SSH_PORT as $VPS_USER..."
        
        # Create remote directory
        ssh -p $SSH_PORT $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"
        
        # Copy files
        scp -P $SSH_PORT -r trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -P $SSH_PORT -r launchers/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -P $SSH_PORT -r utilities/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -P $SSH_PORT vps_environment_check.py $VPS_USER@$VPS_HOST:$VPS_DIR/
        
        # Set permissions and install
        ssh -p $SSH_PORT $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"
        ssh -p $SSH_PORT $VPS_USER@$VPS_HOST "cd $VPS_DIR && pip3 install -r requirements.txt"
        ssh -p $SSH_PORT $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 -m playwright install"
        
        echo "✅ Deployment completed to $VPS_HOST:$SSH_PORT:$VPS_DIR"
        ;;
    4)
        echo "🔑 SSH Key Authentication Deployment"
        read -p "Enter VPS IP: " vps_ip
        read -p "Enter SSH key path (default: ~/.ssh/id_rsa): " key_path
        key_path=${key_path:-~/.ssh/id_rsa}
        read -p "Enter username (default: root): " username
        username=${username:-root}
        
        VPS_HOST="$vps_ip"
        VPS_USER="$username"
        VPS_DIR="/root/AI-TRADING-BOT"
        SSH_KEY="$key_path"
        
        echo "🚀 Deploying to $VPS_HOST with key $SSH_KEY as $VPS_USER..."
        
        # Test connection first
        ssh -i $SSH_KEY $VPS_USER@$VPS_HOST "echo 'SSH connection successful'"
        
        # Create remote directory
        ssh -i $SSH_KEY $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"
        
        # Copy files
        scp -i $SSH_KEY -r trading_scripts/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -i $SSH_KEY -r launchers/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -i $SSH_KEY -r utilities/* $VPS_USER@$VPS_HOST:$VPS_DIR/
        scp -i $SSH_KEY vps_environment_check.py $VPS_USER@$VPS_HOST:$VPS_DIR/
        
        # Set permissions and install
        ssh -i $SSH_KEY $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"
        ssh -i $SSH_KEY $VPS_USER@$VPS_HOST "cd $VPS_DIR && pip3 install -r requirements.txt"
        ssh -i $SSH_KEY $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 -m playwright install"
        
        echo "✅ Deployment completed to $VPS_HOST:$VPS_DIR"
        ;;
    5)
        echo "📋 Manual Step-by-Step Deployment"
        read -p "Enter VPS IP: " vps_ip
        read -p "Enter username (default: root): " username
        username=${username:-root}
        
        echo ""
        echo "🔧 Manual Deployment Steps:"
        echo "1. Create directory:"
        echo "   ssh $username@$vps_ip \"mkdir -p /root/AI-TRADING-BOT\""
        echo ""
        echo "2. Copy trading scripts:"
        echo "   scp trading_scripts/* $username@$vps_ip:/root/AI-TRADING-BOT/"
        echo ""
        echo "3. Copy launchers:"
        echo "   scp launchers/* $username@$vps_ip:/root/AI-TRADING-BOT/"
        echo ""
        echo "4. Copy utilities:"
        echo "   scp utilities/* $username@$vps_ip:/root/AI-TRADING-BOT/"
        echo ""
        echo "5. Copy environment checker:"
        echo "   scp vps_environment_check.py $username@$vps_ip:/root/AI-TRADING-BOT/"
        echo ""
        echo "6. Set permissions:"
        echo "   ssh $username@$vps_ip \"chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh\""
        echo ""
        echo "7. Install dependencies:"
        echo "   ssh $username@$vps_ip \"cd /root/AI-TRADING-BOT && pip3 install -r requirements.txt\""
        echo ""
        echo "8. Install Playwright:"
        echo "   ssh $username@$vps_ip \"cd /root/AI-TRADING-BOT && python3 -m playwright install\""
        echo ""
        echo "9. Verify deployment:"
        echo "   ssh $username@$vps_ip \"cd /root/AI-TRADING-BOT && python3 vps_environment_check.py\""
        echo ""
        echo "10. Set credentials:"
        echo "    ssh $username@$vps_ip"
        echo "    cd /root/AI-TRADING-BOT"
        echo "    echo \"BULENOX_USERNAME=your_username\" > .env"
        echo "    echo \"BULENOX_PASSWORD=your_password\" >> .env"
        echo "    chmod 600 .env"
        echo ""
        echo "11. Test deployment:"
        echo "    ./live_trading_launcher.sh"
        ;;
    6)
        echo "🔍 Verify Existing Deployment"
        read -p "Enter VPS IP: " vps_ip
        read -p "Enter username (default: root): " username
        username=${username:-root}
        
        echo "🔍 Checking deployment on $vps_ip..."
        
        # Check if directory exists
        if ssh $username@$vps_ip "test -d /root/AI-TRADING-BOT"; then
            echo "✅ Directory exists: /root/AI-TRADING-BOT"
        else
            echo "❌ Directory missing: /root/AI-TRADING-BOT"
            exit 1
        fi
        
        # Check core files
        echo "📁 Checking core files..."
        ssh $username@$vps_ip "ls -la /root/AI-TRADING-BOT/"
        
        # Run environment check
        echo "🔧 Running environment validation..."
        ssh $username@$vps_ip "cd /root/AI-TRADING-BOT && python3 vps_environment_check.py"
        
        echo "✅ Verification completed"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1-6."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process completed!"
echo "📋 Next steps:"
echo "1. SSH to your VPS: ssh $username@$vps_ip"
echo "2. Navigate to: cd /root/AI-TRADING-BOT"
echo "3. Set credentials: echo 'BULENOX_USERNAME=your_user' > .env"
echo "4. Add password: echo 'BULENOX_PASSWORD=your_pass' >> .env"
echo "5. Secure file: chmod 600 .env"
echo "6. Start trading: ./live_trading_launcher.sh"
echo ""
echo "📊 Monitor logs: tail -f /root/AI-TRADING-BOT/logs/trading.log"
echo "🔍 Health check: python3 vps_environment_check.py"