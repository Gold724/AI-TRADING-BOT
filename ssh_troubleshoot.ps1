# 🔐 SSH Troubleshooting & Auto-Setup Script for AI Trading Sentinel (Windows)
# Usage: .\ssh_troubleshoot.ps1 -TargetIP "161.97.112.146" -Username "root"

param(
    [string]$TargetIP = "161.97.112.146",
    [string]$Username = "root",
    [string]$SSHKeyPath = "$env:USERPROFILE\.ssh\id_rsa"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor $Blue
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor $Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor $Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor $Red
}

Write-Host "🔐 AI Trading Sentinel - SSH Troubleshooter (Windows)" -ForegroundColor $Blue
Write-Host "========================================================" -ForegroundColor $Blue
Write-Host "Target: $Username@$TargetIP" -ForegroundColor $Yellow
Write-Host ""

# Step 1: Check if SSH client is available
Write-Info "Step 1: Checking SSH client availability..."
try {
    $sshVersion = ssh -V 2>&1
    Write-Success "SSH client found: $sshVersion"
} catch {
    Write-Error "SSH client not found. Please install OpenSSH or use WSL."
    Write-Info "To install OpenSSH on Windows 10/11:"
    Write-Host "  Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor $Yellow
    exit 1
}

# Step 2: Basic connectivity test
Write-Info "Step 2: Testing basic connectivity..."
try {
    $pingResult = Test-Connection -ComputerName $TargetIP -Count 3 -Quiet
    if ($pingResult) {
        Write-Success "Server is reachable via ping"
    } else {
        Write-Error "Server is not reachable via ping"
        exit 1
    }
} catch {
    Write-Error "Ping test failed: $_"
    exit 1
}

# Step 3: Check SSH port
Write-Info "Step 3: Checking SSH port 22..."
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($TargetIP, 22, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
    
    if ($wait -and $tcpClient.Connected) {
        Write-Success "SSH port 22 is open"
        $tcpClient.Close()
    } else {
        Write-Warning "SSH port 22 is not accessible"
        $tcpClient.Close()
        
        # Try alternative ports
        Write-Info "Trying alternative SSH ports..."
        $alternativePorts = @(2222, 22022, 2200)
        foreach ($port in $alternativePorts) {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connect = $tcpClient.BeginConnect($TargetIP, $port, $null, $null)
            $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
            
            if ($wait -and $tcpClient.Connected) {
                Write-Success "SSH found on port $port"
                $SSHPort = $port
                $tcpClient.Close()
                break
            }
            $tcpClient.Close()
        }
    }
} catch {
    Write-Error "Port check failed: $_"
}

# Step 4: Check existing SSH keys
Write-Info "Step 4: Checking SSH keys..."
if (Test-Path $SSHKeyPath) {
    Write-Success "SSH private key found: $SSHKeyPath"
} else {
    Write-Warning "No SSH key found. Generating new key pair..."
    
    # Create .ssh directory if it doesn't exist
    $sshDir = Split-Path $SSHKeyPath
    if (!(Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }
    
    # Generate SSH key
    $hostname = $env:COMPUTERNAME
    ssh-keygen -t rsa -b 4096 -f $SSHKeyPath -N "" -C "trae-deployment@$hostname"
    
    if (Test-Path $SSHKeyPath) {
        Write-Success "New SSH key pair generated"
    } else {
        Write-Error "Failed to generate SSH key"
        exit 1
    }
}

# Step 5: Test SSH connection
Write-Info "Step 5: Testing SSH connection..."

$sshCmd = "ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=no"
if ($SSHPort) {
    $sshCmd += " -p $SSHPort"
}

# Test key-based authentication
Write-Info "Testing key-based authentication..."
try {
    $result = & cmd /c "$sshCmd $Username@$TargetIP echo 'SSH key auth successful' 2>nul"
    if ($LASTEXITCODE -eq 0) {
        Write-Success "SSH key authentication works!"
        $SSHAuthMethod = "key"
    } else {
        Write-Warning "SSH key authentication failed"
    }
} catch {
    Write-Warning "SSH key test failed: $_"
}

# Step 6: Generate deployment scripts
Write-Info "Step 6: Generating deployment scripts..."

if ($SSHAuthMethod -eq "key") {
    Write-Success "SSH access established! Generating deployment commands..."
    
    # Create PowerShell deployment script
    $deployScript = @'
# Auto-generated SSH deployment script for Windows
# Deploy AI Trading Sentinel to {0}@{1}

$sshCmd = "ssh {0}@{1}"
if ($SSHPort) {{
    $sshCmd = "ssh -p $SSHPort {0}@{1}"
}}

Write-Host "Deploying AI Trading Sentinel..." -ForegroundColor Green

# Execute remote commands
$remoteCommands = @"
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip nodejs npm git docker.io docker-compose curl

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Clone repository (replace with your actual repo URL)
if [ ! -d "ai-trading-sentinel" ]; then
    git clone https://github.com/your-username/ai-trading-sentinel.git
fi

cd ai-trading-sentinel

# Make scripts executable
chmod +x deploy/deploy-production.sh
chmod +x quick-deploy.sh

# Run deployment
./deploy/deploy-production.sh

echo "Deployment completed! Services starting..."
"@

# Execute the remote commands
Invoke-Expression "$sshCmd `"$remoteCommands`""

Write-Host "Deployment script completed!" -ForegroundColor Green
'@ -f $Username, $TargetIP
    
    $deployScript | Out-File -FilePath "ssh_deploy_commands.ps1" -Encoding UTF8
    Write-Success "Deployment script created: ssh_deploy_commands.ps1"
    
} else {
    Write-Error "Could not establish SSH connection"
    Write-Info "Manual steps required:"
    Write-Host ""
    Write-Host "1. Contact Contabo support for console access" -ForegroundColor $Yellow
    Write-Host "2. Reset root password via control panel" -ForegroundColor $Yellow
    Write-Host "3. Add your SSH key manually:" -ForegroundColor $Yellow
    
    if (Test-Path "$SSHKeyPath.pub") {
        Write-Host "   Your public key:" -ForegroundColor $Yellow
        Get-Content "$SSHKeyPath.pub"
        Write-Host "   # Copy the above and add to ~/.ssh/authorized_keys on target server" -ForegroundColor $Yellow
    }
    
    Write-Host ""
    Write-Host "4. Or deploy on current server instead:" -ForegroundColor $Yellow
    Write-Host "   .\quick-deploy.bat localhost" -ForegroundColor $Yellow
}

# Step 7: Create connection helper
Write-Info "Step 7: Creating connection helper..."

$connectionScript = @'
# Quick connection script for AI Trading Sentinel
param(
    [string]$Action = "connect"
)

$sshCmd = "ssh {0}@{1}"
if ($SSHPort) {{
    $sshCmd = "ssh -p $SSHPort {0}@{1}"
}}

switch ($Action) {{
    "deploy" {{
        Write-Host "Running deployment..." -ForegroundColor Green
        .\ssh_deploy_commands.ps1
    }}
    "logs" {{
        Write-Host "Viewing logs..." -ForegroundColor Green
        Invoke-Expression "$sshCmd `"tail -f ai-trading-sentinel/logs/trading.log`""
    }}
    "status" {{
        Write-Host "Checking status..." -ForegroundColor Green
        Invoke-Expression "$sshCmd `"cd ai-trading-sentinel && python3 deployment_validator.py`""
    }}
    "connect" {{
        Write-Host "Connecting to server..." -ForegroundColor Green
        Invoke-Expression $sshCmd
    }}
    default {{
        Write-Host "Usage: .\connect_server.ps1 [connect|deploy|logs|status]" -ForegroundColor Yellow
    }}
}}
'@ -f $Username, $TargetIP

$connectionScript | Out-File -FilePath "connect_server.ps1" -Encoding UTF8
Write-Success "Connection helper created: connect_server.ps1"

Write-Host ""
Write-Success "SSH troubleshooting completed!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor $Yellow
if ($SSHAuthMethod -eq "key") {
    Write-Host "1. Run deployment: .\ssh_deploy_commands.ps1" -ForegroundColor $Green
    Write-Host "2. Connect to server: .\connect_server.ps1" -ForegroundColor $Green
    Write-Host "3. Check status: .\connect_server.ps1 -Action status" -ForegroundColor $Green
    Write-Host "4. View logs: .\connect_server.ps1 -Action logs" -ForegroundColor $Green
} else {
    Write-Host "1. Resolve SSH access issues (see manual steps above)" -ForegroundColor $Yellow
    Write-Host "2. Or deploy locally: .\quick-deploy.bat localhost" -ForegroundColor $Yellow
}
Write-Host ""
Write-Host "🚀 Ready for AI Trading Sentinel deployment!" -ForegroundColor $Green

# Display current SSH key for manual setup if needed
if (Test-Path "$SSHKeyPath.pub") {
    Write-Host ""
    Write-Host "Your SSH Public Key (for manual setup):" -ForegroundColor $Blue
    Write-Host "===========================================" -ForegroundColor $Blue
    Get-Content "$SSHKeyPath.pub"
    Write-Host "===========================================" -ForegroundColor $Blue
}