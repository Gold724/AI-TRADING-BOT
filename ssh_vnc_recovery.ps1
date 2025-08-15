<#
.SYNOPSIS
    SSH VNC Recovery Tool - Helps restore SSH access to VPS when authentication fails
.DESCRIPTION
    This script guides users through the process of using VNC console access to manually
    inject their SSH public key and restart the SSH service when normal SSH access fails.
.NOTES
    Created by: Trae AI
    Version: 1.0
#>

# Script configuration
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "SSH VNC Recovery Tool"

# Function to display colored messages
function Write-ColorOutput {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )
    
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# Function to display a banner
function Show-Banner {
    Clear-Host
    Write-ColorOutput "===================================================" "Cyan"
    Write-ColorOutput "           SSH VNC RECOVERY TOOL                  " "Cyan"
    Write-ColorOutput "===================================================" "Cyan"
    Write-ColorOutput "When SSH fails, the builder enters through the backdoor..." "Yellow"
    Write-ColorOutput "===================================================" "Cyan"
    Write-Host ""
}

# Function to validate IP address format
function Test-IPAddress {
    param (
        [Parameter(Mandatory=$true)]
        [string]$IPAddress
    )
    
    $ipRegex = "^([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])(\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
    return $IPAddress -match $ipRegex
}

# Function to validate port number
function Test-Port {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Port
    )
    
    $portNumber = 0
    if ([int]::TryParse($Port, [ref]$portNumber)) {
        return $portNumber -ge 1 -and $portNumber -le 65535
    }
    return $false
}

# Function to check if a file exists and is readable
function Test-SSHKeyFile {
    param (
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    
    if (-not (Test-Path -Path $FilePath -PathType Leaf)) {
        return $false
    }
    
    try {
        $content = Get-Content -Path $FilePath -ErrorAction Stop
        return $content -match "ssh-rsa|ssh-ed25519|ecdsa-sha2"
    } catch {
        return $false
    }
}

# Main script execution
Show-Banner

# Step 1: Collect VPS information
Write-Host ""
Write-ColorOutput "STEP 1: VPS INFORMATION" "Green"
Write-ColorOutput "------------------" "Green"

$vpsIP = Read-Host "Enter your VPS IP address"
while (-not (Test-IPAddress -IPAddress $vpsIP)) {
    Write-ColorOutput "Invalid IP address format. Please try again." "Red"
    $vpsIP = Read-Host "Enter your VPS IP address"
}

$vncIP = Read-Host "Enter your VNC IP address"
while (-not (Test-IPAddress -IPAddress $vncIP)) {
    Write-ColorOutput "Invalid IP address format. Please try again." "Red"
    $vncIP = Read-Host "Enter your VNC IP address"
}

$vncPort = Read-Host "Enter your VNC port number"
while (-not (Test-Port -Port $vncPort)) {
    Write-ColorOutput "Invalid port number. Please enter a number between 1-65535." "Red"
    $vncPort = Read-Host "Enter your VNC port number"
}

# Step 2: SSH Key Selection
Write-Host ""
Write-ColorOutput "STEP 2: SSH PUBLIC KEY" "Green"
Write-ColorOutput "------------------" "Green"

$sshKeyPath = Read-Host "Enter the path to your SSH public key file (e.g., D:\path\to\key.pub)"
while (-not (Test-SSHKeyFile -FilePath $sshKeyPath)) {
    Write-ColorOutput "Invalid SSH public key file. Please check the path and try again." "Red"
    $sshKeyPath = Read-Host "Enter the path to your SSH public key file"
}

$sshKeyContent = Get-Content -Path $sshKeyPath -Raw

# Step 3: Display VNC Connection Instructions
Write-Host ""
Write-ColorOutput "STEP 3: VNC CONNECTION INSTRUCTIONS" "Green"
Write-ColorOutput "-----------------------------" "Green"

Write-Host ""
Write-ColorOutput "VPS Details:" "Yellow"
Write-ColorOutput "  - VPS IP: $vpsIP" "White"
Write-ColorOutput "  - VNC IP: $vncIP" "White"
Write-ColorOutput "  - VNC Port: $vncPort" "White"
Write-ColorOutput "  - Username: root" "White"
Write-ColorOutput "  - VNC Password: (from Contabo > Manage > VNC Password)" "White"

Write-Host ""
Write-ColorOutput "How to Connect:" "Yellow"
Write-ColorOutput "1. Install a VNC client (UltraVNC / RealVNC / TigerVNC)" "White"
Write-ColorOutput "2. Connect using:" "White"
$connectionString = "   -> IP:Port -> $vncIP`:$vncPort"
Write-ColorOutput $connectionString "Cyan"
Write-ColorOutput "   -> Username: root" "Cyan"
Write-ColorOutput "   -> VNC Password: (from Contabo > Manage > VNC Password)" "Cyan"

Write-Host ""
Write-ColorOutput "Note: VNC is **not encrypted** - use only for recovery, and log out before exiting!" "Red"

# Step 4: Display commands to run in VNC
Write-Host ""
Write-ColorOutput "STEP 4: COMMANDS TO RUN IN VNC TERMINAL" "Green"
Write-ColorOutput "----------------------------------" "Green"

$commandsToRun = @"
# Step 1: Prepare authorized_keys
mkdir -p ~/.ssh

# Step 2: Add your public key
echo "$sshKeyContent" > ~/.ssh/authorized_keys

# Step 3: Secure it & restart SSH
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
systemctl restart ssh
"@

Write-Host ""
Write-ColorOutput "Run these commands in the VNC terminal:" "Yellow"
Write-ColorOutput $commandsToRun "Cyan"

# Step 5: Test SSH connection
Write-Host ""
Write-ColorOutput "STEP 5: TEST SSH CONNECTION" "Green"
Write-ColorOutput "----------------------" "Green"

$privateKeyPath = $sshKeyPath -replace '\.pub$', ''
$sshTestCommand = "ssh -i `"$privateKeyPath`" root@$vpsIP"

Write-Host ""
Write-ColorOutput "After completing the steps above, test your SSH connection with:" "Yellow"
Write-ColorOutput $sshTestCommand "Cyan"

# Step 6: Security reminder
Write-Host ""
Write-ColorOutput "STEP 6: SECURITY REMINDER" "Green"
Write-ColorOutput "---------------------" "Green"

Write-Host ""
Write-ColorOutput "WARNING: VNC is not encrypted." "Red"
Write-Host ""
Write-ColorOutput "If SSH now works:" "Yellow"
Write-ColorOutput "  - Disable VNC in your Contabo panel (optional)" "White"
Write-ColorOutput "  - Reset your VNC password for safety" "White"

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")