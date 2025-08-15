# TRAE AI Trading Sentinel - Contabo VPS Deployment Script (PowerShell)
# This script prepares the local environment and deploys the TRAE AI Trading Sentinel to a Contabo VPS
# It sets up SSH keys, transfers files, and runs the deployment script on the remote server

# Configuration
$RemoteHost = "your-contabo-ip"
$RemoteUser = "root"
$RemotePort = 22
$LocalRepoPath = "$PSScriptRoot\.."
$RemoteAppDir = "/opt/trae-ai-sentinel"
$SshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    # Save the current color
    $previousForegroundColor = $host.UI.RawUI.ForegroundColor
    
    # Set the new color
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    
    # Write the output
    if ($args) {
        Write-Output $args
    } else {
        # If no arguments were passed, read from the pipeline
        $input | Write-Output
    }
    
    # Restore the original color
    $host.UI.RawUI.ForegroundColor = $previousForegroundColor
}

# Print banner
Write-ColorOutput Blue ""
Write-ColorOutput Blue "╔════════════════════════════════════════════════════════════╗"
Write-ColorOutput Blue "║                                                            ║"
Write-ColorOutput Blue "║             TRAE AI TRADING SENTINEL DEPLOYMENT            ║"
Write-ColorOutput Blue "║                                                            ║"
Write-ColorOutput Blue "║                  CONTABO VPS DEPLOYMENT                    ║"
Write-ColorOutput Blue "║                                                            ║"
Write-ColorOutput Blue "╚════════════════════════════════════════════════════════════╝"
Write-ColorOutput Blue ""

# Function to print section header
function Print-Section($title) {
    Write-ColorOutput Yellow ""
    Write-ColorOutput Yellow "==== $title ===="
    Write-ColorOutput Yellow ""
}

# Function to print status
function Print-Status($message) {
    Write-ColorOutput Green "[✓] $message"
}

# Function to print error
function Print-Error($message) {
    Write-ColorOutput Red "[✗] $message"
}

# Function to print info
function Print-Info($message) {
    Write-ColorOutput Blue "[i] $message"
}

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Print-Error "This script must be run as Administrator"
    exit 1
}

# Check for required tools
Print-Section "Checking Required Tools"

# Check for OpenSSH
$sshCommand = Get-Command ssh -ErrorAction SilentlyContinue
if ($null -eq $sshCommand) {
    Print-Error "OpenSSH is not installed. Please install OpenSSH Client from Windows Features."
    exit 1
}
else {
    Print-Status "OpenSSH is installed"
}

# Check for SCP
$scpCommand = Get-Command scp -ErrorAction SilentlyContinue
if ($null -eq $scpCommand) {
    Print-Error "SCP is not installed. Please install OpenSSH Client from Windows Features."
    exit 1
}
else {
    Print-Status "SCP is installed"
}

# Check for Git
$gitCommand = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $gitCommand) {
    Print-Error "Git is not installed. Please install Git from https://git-scm.com/"
    exit 1
}
else {
    Print-Status "Git is installed"
}

# Check for SSH key
Print-Section "Checking SSH Key"
if (-not (Test-Path $SshKeyPath)) {
    Print-Info "SSH key not found. Generating new SSH key..."
    
    # Create .ssh directory if it doesn't exist
    $sshDir = "$env:USERPROFILE\.ssh"
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir | Out-Null
    }
    
    # Generate SSH key
    ssh-keygen -t rsa -b 4096 -f $SshKeyPath -N '""'
    
    Print-Status "SSH key generated"
    
    # Display public key
    Print-Info "Please add the following public key to your Contabo VPS authorized_keys file:"
    Get-Content "$SshKeyPath.pub"
    
    # Ask user to confirm
    $confirmation = Read-Host "Have you added the SSH key to your Contabo VPS? (y/n)"
    if ($confirmation -ne 'y') {
        Print-Error "Please add the SSH key to your Contabo VPS and run this script again"
        exit 1
    }
}
else {
    Print-Status "SSH key found"
}

# Prepare deployment package
Print-Section "Preparing Deployment Package"

# Create temporary directory
$tempDir = "$env:TEMP\trae-ai-sentinel-deploy"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy files to temporary directory
Print-Info "Copying files to temporary directory..."
Copy-Item -Recurse -Path "$LocalRepoPath\*" -Destination $tempDir

# Remove unnecessary files
Print-Info "Removing unnecessary files..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$tempDir\.git"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$tempDir\.vscode"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$tempDir\__pycache__"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$tempDir\venv"

# Create deployment archive
Print-Info "Creating deployment archive..."
$deploymentZip = "$env:TEMP\trae-ai-sentinel-deploy.zip"
if (Test-Path $deploymentZip) {
    Remove-Item -Force $deploymentZip
}
Compress-Archive -Path "$tempDir\*" -DestinationPath $deploymentZip

Print-Status "Deployment package prepared"

# Connect to remote server
Print-Section "Connecting to Remote Server"

# Test SSH connection
Print-Info "Testing SSH connection..."
try {
    $sshTest = ssh -i $SshKeyPath -p $RemotePort -o "StrictHostKeyChecking=no" "$RemoteUser@$RemoteHost" "echo 'Connection successful'"
    if ($sshTest -ne "Connection successful") {
        throw "SSH connection test failed"
    }
    Print-Status "SSH connection successful"
}
catch {
    Print-Error "SSH connection failed: $_"
    exit 1
}

# Transfer files
Print-Section "Transferring Files"
Print-Info "Transferring deployment package..."
try {
    scp -i $SshKeyPath -P $RemotePort $deploymentZip "$RemoteUser@$RemoteHost:/tmp/trae-ai-sentinel-deploy.zip"
    Print-Status "Deployment package transferred"
}
catch {
    Print-Error "File transfer failed: $_"
    exit 1
}

# Execute deployment script
Print-Section "Executing Deployment Script"
Print-Info "Preparing remote environment..."

# Create commands to execute on remote server
$remoteCommands = @"
mkdir -p $RemoteAppDir
cd /tmp
unzip -o trae-ai-sentinel-deploy.zip -d $RemoteAppDir
chmod +x $RemoteAppDir/deploy/contabo_deploy.sh
cd $RemoteAppDir
./deploy/contabo_deploy.sh
"@

# Execute commands on remote server
try {
    $remoteOutput = ssh -i $SshKeyPath -p $RemotePort "$RemoteUser@$RemoteHost" $remoteCommands
    Write-Output $remoteOutput
    Print-Status "Deployment script executed successfully"
}
catch {
    Print-Error "Deployment script execution failed: $_"
    exit 1
}

# Clean up
Print-Section "Cleaning Up"
Print-Info "Removing temporary files..."
Remove-Item -Recurse -Force $tempDir
Remove-Item -Force $deploymentZip
Print-Status "Temporary files removed"

# Print summary
Print-Section "Deployment Summary"
Write-ColorOutput Green "TRAE AI Trading Sentinel has been deployed successfully!"
Write-Output ""
Write-ColorOutput Blue "Remote Server:" -NoNewline
Write-Output " $RemoteHost"
Write-ColorOutput Blue "Application Directory:" -NoNewline
Write-Output " $RemoteAppDir"
Write-ColorOutput Blue "API URL:" -NoNewline
Write-Output " http://$RemoteHost/api"
Write-ColorOutput Blue "Dashboard URL:" -NoNewline
Write-Output " http://$RemoteHost/"
Write-Output ""
Write-ColorOutput Yellow "Important Notes:"
Write-Output "1. Update the Bulenox credentials in $RemoteAppDir/.env"
Write-Output "2. Logs are stored in $RemoteAppDir/logs"
Write-Output "3. To monitor the application, SSH into the server and use: supervisorctl status trae:"
Write-Output ""
Write-ColorOutput Green "Thank you for using TRAE AI Trading Sentinel!"