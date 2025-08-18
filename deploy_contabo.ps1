# AI Trading Sentinel - Contabo VPS Deployment Script
# This script creates a deployment script for your Contabo VPS

param([switch]$SkipConfirmation)

# Color functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Status { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Read .env file
function Get-EnvVar($name) {
    if (Test-Path ".env") {
        $content = Get-Content ".env"
        foreach ($line in $content) {
            if ($line -match "^$name=(.*)$") {
                return $matches[1].Trim('"').Trim("'")
            }
        }
    }
    return $null
}

# Get Contabo credentials
$contaboIP = Get-EnvVar "CONTABO_VPS_IP"
$contaboUser = Get-EnvVar "CONTABO_USERNAME"
$contaboPassword = Get-EnvVar "CONTABO_PASSWORD"
$contaboPort = Get-EnvVar "CONTABO_SSH_PORT"
$gitRepo = Get-EnvVar "GITHUB_REPO"
$githubPAT = Get-EnvVar "GITHUB_PAT"

# Validate credentials
if (-not $contaboIP -or -not $contaboUser -or -not $contaboPassword) {
    Write-Error "Missing Contabo VPS credentials in .env file!"
    Write-Host "Required: CONTABO_VPS_IP, CONTABO_USERNAME, CONTABO_PASSWORD" -ForegroundColor Yellow
    exit 1
}

# Display configuration
Write-Host "AI Trading Sentinel - Contabo VPS Deployment" -ForegroundColor Magenta
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host ""
Write-Status "Contabo VPS Configuration:"
Write-Host "  VPS IP: $contaboIP" -ForegroundColor White
Write-Host "  Username: $contaboUser" -ForegroundColor White
Write-Host "  Port: $contaboPort" -ForegroundColor White
Write-Host "  Git Repo: $gitRepo" -ForegroundColor White
Write-Host ""

# Confirmation
if (-not $SkipConfirmation) {
    $confirm = Read-Host "Create deployment script for Contabo VPS? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Warning "Script creation cancelled by user."
        exit 0
    }
}

# Create deployment script lines
$scriptLines = @(
    "#!/bin/bash",
    "set -e",
    "",
    "echo 'Starting AI Trading Sentinel deployment...'",
    "",
    "# Update system",
    "echo 'Updating system packages...'",
    "apt update",
    "apt upgrade -y",
    "",
    "# Install Docker",
    "echo 'Installing Docker...'",
    "curl -fsSL https://get.docker.com -o get-docker.sh",
    "sh get-docker.sh",
    "systemctl start docker",
    "systemctl enable docker",
    "",
    "# Install Docker Compose",
    "echo 'Installing Docker Compose...'",
    "curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-'`$(uname -s)'-'`$(uname -m) -o /usr/local/bin/docker-compose",
    "chmod +x /usr/local/bin/docker-compose",
    "",
    "# Clone repository",
    "echo 'Cloning repository...'",
    "cd /opt",
    "if [ -d 'ai-trading-sentinel' ]; then",
    "    rm -rf ai-trading-sentinel",
    "fi",
    "git clone https://github.com/Gold724/AI-TRADING-BOT.git ai-trading-sentinel",
    "cd ai-trading-sentinel",
    "",
    "# Set up environment",
    "echo 'Setting up environment...'",
    "if [ -f .env.example ]; then",
    "    cp .env.example .env",
    "else",
    "    echo '# AI Trading Sentinel Environment' > .env",
    "fi",
    "echo 'ENVIRONMENT=production' >> .env",
    "echo 'HEADLESS=true' >> .env",
    "echo 'AUTO_EXECUTION_ENABLED=true' >> .env",
    "",
    "# Build and start containers",
    "echo 'Building and starting containers...'",
    "docker-compose up -d --build",
    "",
    "# Set up firewall",
    "echo 'Configuring firewall...'",
    "ufw allow 22/tcp",
    "ufw allow 3000/tcp",
    "ufw allow 8080/tcp",
    "ufw --force enable",
    "",
    "# Create systemd service file",
    "echo 'Creating systemd service...'",
    "cat > /etc/systemd/system/ai-trading-sentinel.service << 'SERVICEEOF'",
    "[Unit]",
    "Description=AI Trading Sentinel",
    "Requires=docker.service",
    "After=docker.service",
    "",
    "[Service]",
    "Type=oneshot",
    "RemainAfterExit=yes",
    "WorkingDirectory=/opt/ai-trading-sentinel",
    "ExecStart=/usr/local/bin/docker-compose up -d",
    "ExecStop=/usr/local/bin/docker-compose down",
    "TimeoutStartSec=0",
    "",
    "[Install]",
    "WantedBy=multi-user.target",
    "SERVICEEOF",
    "",
    "systemctl enable ai-trading-sentinel.service",
    "systemctl start ai-trading-sentinel.service",
    "",
    "echo 'AI Trading Sentinel deployed successfully!'",
    "echo 'Access URLs:'",
    "echo '  Dashboard: http://'`$(curl -s ifconfig.me)':3000'",
    "echo '  Trading Interface: http://'`$(curl -s ifconfig.me)':8080'",
    "echo '  SSH: ssh root@'`$(curl -s ifconfig.me)"
)

# Save the deployment script
$scriptFile = "contabo_deploy.sh"
$scriptLines | Out-File -FilePath $scriptFile -Encoding UTF8

Write-Success "Deployment script created: $scriptFile"
Write-Host ""

# Display deployment instructions
Write-Host "Deployment Instructions:" -ForegroundColor Yellow
Write-Host "1. Upload the script to your Contabo VPS:" -ForegroundColor White
Write-Host "   scp -P $contaboPort $scriptFile ${contaboUser}@${contaboIP}:/tmp/deploy.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. SSH to your Contabo VPS:" -ForegroundColor White
Write-Host "   ssh -p $contaboPort ${contaboUser}@${contaboIP}" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Run the deployment script:" -ForegroundColor White
Write-Host "   chmod +x /tmp/deploy.sh" -ForegroundColor Cyan
Write-Host "   /tmp/deploy.sh" -ForegroundColor Cyan
Write-Host ""

# Display access information
Write-Host "After deployment, access your AI Trading Sentinel at:" -ForegroundColor Green
Write-Host "  Dashboard: http://$contaboIP:3000" -ForegroundColor White
Write-Host "  Trading Interface: http://$contaboIP:8080" -ForegroundColor White
Write-Host "  SSH Access: ssh ${contaboUser}@${contaboIP}" -ForegroundColor White
Write-Host ""
Write-Success "Ready for 24/7 cloud trading on Contabo VPS!"