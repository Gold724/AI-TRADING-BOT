<#
.SYNOPSIS
    SSH Key Deployment Tool - Deploys SSH keys to VPS and configures GitHub Actions
.DESCRIPTION
    This script automates the process of deploying SSH public keys to a VPS and
    configuring GitHub Actions secrets for CI/CD integration.
.NOTES
    Created by: Trae AI
    Version: 1.0
#>

# Script configuration
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "SSH Key Deployment Tool"

# Default values (can be overridden by parameters)
$DefaultPrivateKeyPath = "D:\anki\trae_vps"
$DefaultPublicKeyPath = "D:\anki\trae_vps.pub"
$DefaultVpsIp = "161.97.112.146"
$DefaultVpsUsername = "root"
$DefaultVpsPort = 22

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
    Write-ColorOutput "           SSH KEY DEPLOYMENT TOOL                " "Cyan"
    Write-ColorOutput "===================================================" "Cyan"
    Write-ColorOutput "Securely connecting your development pipeline..." "Yellow"
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

# Function to check if a file exists and is readable
function Test-KeyFile {
    param (
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    
    if (-not (Test-Path -Path $FilePath -PathType Leaf)) {
        return $false
    }
    
    try {
        $content = Get-Content -Path $FilePath -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Function to check if SSH public key is valid
function Test-SSHPublicKey {
    param (
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    
    if (-not (Test-Path -Path $FilePath -PathType Leaf)) {
        Write-ColorOutput "SSH public key file not found: $FilePath" "Red"
        return $false
    }
    
    try {
        # Try to read the file content
        $content = Get-Content -Path $FilePath -Raw -ErrorAction Stop
        
        # Check if the content starts with ssh-rsa, ssh-ed25519, or ecdsa-sha2
        if ($content -match "^\s*(ssh-rsa|ssh-ed25519|ecdsa-sha2)") {
            return $true
        } else {
            # Check if this might be a private key file
            if ($content -match "BEGIN .* PRIVATE KEY") {
                Write-ColorOutput "This appears to be a private key file, not a public key file" "Red"
                Write-ColorOutput "The public key file should have a .pub extension and start with 'ssh-rsa', 'ssh-ed25519', or 'ecdsa-sha2'" "Yellow"
                
                # Check if there might be a .pub.pub file
                $possiblePubPubFile = "$FilePath.pub"
                if (Test-Path -Path $possiblePubPubFile) {
                    $pubPubContent = Get-Content -Path $possiblePubPubFile -Raw -ErrorAction SilentlyContinue
                    if ($pubPubContent -match "^\s*(ssh-rsa|ssh-ed25519|ecdsa-sha2)") {
                        Write-ColorOutput "Found a valid public key at: $possiblePubPubFile" "Green"
                        Write-ColorOutput "Consider using this file instead" "Yellow"
                    }
                }
            } else {
                Write-ColorOutput "File does not contain a valid SSH public key format" "Red"
                Write-ColorOutput "Public key should start with 'ssh-rsa', 'ssh-ed25519', or 'ecdsa-sha2'" "Yellow"
            }
            return $false
        }
    } catch {
        Write-ColorOutput "Error reading SSH public key file: $_" "Red"
        return $false
    }
}

# Function to generate a new SSH key pair
function Generate-SSHKeyPair {
    param (
        [Parameter(Mandatory=$true)]
        [string]$KeyPath
    )
    
    try {
        # Check if ssh-keygen is available
        $sshKeygenAvailable = $null -ne (Get-Command "ssh-keygen" -ErrorAction SilentlyContinue)
        
        if (-not $sshKeygenAvailable) {
            Write-ColorOutput "ssh-keygen command not found. Please install OpenSSH or Git for Windows." "Red"
            return $false
        }
        
        # Generate the key pair
        Write-ColorOutput "Generating new SSH key pair at $KeyPath..." "Yellow"
        $keygenCommand = "ssh-keygen -t rsa -b 4096 -f `"$KeyPath`" -N `"`""
        
        # Execute the command
        Invoke-Expression $keygenCommand
        
        # Check if the key files were created
        if ((Test-Path -Path $KeyPath) -and (Test-Path -Path "$KeyPath.pub")) {
            Write-ColorOutput "SSH key pair generated successfully!" "Green"
            return $true
        } else {
            Write-ColorOutput "Failed to generate SSH key pair." "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "Error generating SSH key pair: $_" "Red"
        return $false
    }
}

# Function to deploy SSH key to VPS
function Deploy-SSHKey {
    param (
        [Parameter(Mandatory=$true)]
        [string]$PublicKeyPath,
        
        [Parameter(Mandatory=$true)]
        [string]$PrivateKeyPath,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsIp,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsUsername,
        
        [Parameter(Mandatory=$true)]
        [int]$VpsPort
    )
    
    # Read the public key content
    $publicKeyContent = Get-Content -Path $PublicKeyPath -Raw
    
    # Create a temporary script file for SSH commands
    $tempScriptPath = [System.IO.Path]::GetTempFileName()
    
    # Write SSH commands to the temporary script
    @"
mkdir -p ~/.ssh
echo "$publicKeyContent" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
echo "SSH key added successfully."
"@ | Out-File -FilePath $tempScriptPath -Encoding utf8
    
    # Deploy the key using scp and ssh
    try {
        # First try to connect with the key (in case it's already set up)
        Write-ColorOutput "Attempting to connect with SSH key..." "Yellow"
        $testResult = ssh -i "$PrivateKeyPath" -p $VpsPort -o "StrictHostKeyChecking=no" -o "BatchMode=yes" -o "ConnectTimeout=5" "$VpsUsername@$VpsIp" "echo 'SSH key authentication successful'"
        
        if ($testResult -match "SSH key authentication successful") {
            Write-ColorOutput "SSH key is already configured and working!" "Green"
            return $true
        }
    } catch {
        Write-ColorOutput "SSH key authentication not yet configured. Proceeding with setup..." "Yellow"
    }
    
    # If key authentication failed, try password authentication
    Write-ColorOutput "\nWe need to authenticate with a password to set up key-based authentication." "Yellow"
    $password = Read-Host "Enter the password for $VpsUsername@$VpsIp" -AsSecureString
    $passwordText = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
    
    # Use sshpass if available, otherwise guide the user
    $sshpassAvailable = $null -ne (Get-Command "sshpass" -ErrorAction SilentlyContinue)
    
    if ($sshpassAvailable) {
        # Use sshpass for non-interactive authentication
        Write-ColorOutput "Deploying SSH key using sshpass..." "Yellow"
        $env:SSHPASS = $passwordText
        sshpass -e scp -P $VpsPort -o "StrictHostKeyChecking=no" $tempScriptPath "$VpsUsername@${VpsIp}:/tmp/ssh_setup.sh"
        sshpass -e ssh -p $VpsPort -o "StrictHostKeyChecking=no" "$VpsUsername@$VpsIp" "bash /tmp/ssh_setup.sh && rm /tmp/ssh_setup.sh"
        Remove-Item env:SSHPASS
    } else {
        # Manual process with user interaction
        Write-ColorOutput "\nPlease follow these steps to deploy your SSH key:" "Yellow"
        Write-ColorOutput "1. Copy this public key:" "White"
        Write-ColorOutput $publicKeyContent "Cyan"
        Write-ColorOutput "\n2. Connect to your VPS using:" "White"
        Write-ColorOutput "   ssh $VpsUsername@$VpsIp -p $VpsPort" "Cyan"
        Write-ColorOutput "\n3. Once connected, run these commands:" "White"
        Write-ColorOutput "   mkdir -p ~/.ssh" "Cyan"
        Write-ColorOutput "   echo '$publicKeyContent' >> ~/.ssh/authorized_keys" "Cyan"
        Write-ColorOutput "   chmod 700 ~/.ssh" "Cyan"
        Write-ColorOutput "   chmod 600 ~/.ssh/authorized_keys" "Cyan"
        Write-ColorOutput "   exit" "Cyan"
        
        $manualConfirm = Read-Host "\nHave you completed these steps? (y/n)"
        if ($manualConfirm -ne "y") {
            Write-ColorOutput "SSH key deployment aborted." "Red"
            return $false
        }
    }
    
    # Clean up the temporary script
    Remove-Item -Path $tempScriptPath -Force
    
    # Test the SSH connection with the key
    try {
        Write-ColorOutput "\nTesting SSH key authentication..." "Yellow"
        $testResult = ssh -i "$PrivateKeyPath" -p $VpsPort -o "StrictHostKeyChecking=no" -o "BatchMode=yes" -o "ConnectTimeout=5" "$VpsUsername@$VpsIp" "echo 'SSH key authentication successful'"
        
        if ($testResult -match "SSH key authentication successful") {
            Write-ColorOutput "SSH key deployed successfully!" "Green"
            return $true
        } else {
            Write-ColorOutput "SSH key deployment may have failed. Please check manually." "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "SSH key deployment failed: $_" "Red"
        return $false
    }
}

# Function to configure GitHub Actions secrets
function Configure-GitHubSecrets {
    param (
        [Parameter(Mandatory=$true)]
        [string]$PrivateKeyPath,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsIp,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsUsername,
        
        [Parameter(Mandatory=$true)]
        [int]$VpsPort
    )
    
    # Read the private key content
    $privateKeyContent = Get-Content -Path $PrivateKeyPath -Raw
    
    # Display the GitHub Actions secrets
    Write-Host ""
    Write-ColorOutput "GitHub Actions Secrets Configuration" "Green"
    Write-ColorOutput "----------------------------------" "Green"
    Write-Host ""
    Write-ColorOutput "Add the following secrets to your GitHub repository:" "Yellow"
    Write-Host ""
    Write-ColorOutput "VPS_SSH_KEY:" "White"
    Write-ColorOutput $privateKeyContent "Cyan"
    Write-Host ""
    Write-ColorOutput "CONTABO_VPS_IP:" "White"
    Write-ColorOutput $VpsIp "Cyan"
    Write-Host ""
    Write-ColorOutput "CONTABO_USERNAME:" "White"
    Write-ColorOutput $VpsUsername "Cyan"
    Write-Host ""
    Write-ColorOutput "CONTABO_SSH_PORT:" "White"
    Write-ColorOutput $VpsPort "Cyan"
    Write-Host ""
    
    # Provide instructions for GitHub Actions workflow
    Write-ColorOutput "GitHub Actions Workflow Example:" "Yellow"
    Write-Host ""
    $workflowExample = @"
name: Deploy to VPS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up SSH key
        run: |
          mkdir -p ~/.ssh
          echo "\`${{ secrets.VPS_SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -p \`${{ secrets.CONTABO_SSH_PORT }} \`${{ secrets.CONTABO_VPS_IP }} >> ~/.ssh/known_hosts
      
      - name: Deploy to VPS
        run: |
          ssh -p \`${{ secrets.CONTABO_SSH_PORT }} \`${{ secrets.CONTABO_USERNAME }}@\`${{ secrets.CONTABO_VPS_IP }} '
            cd /path/to/deployment/directory && \
            git pull && \
            # Add your deployment commands here
            echo "Deployment successful!"
          '
"@
    Write-ColorOutput $workflowExample "Cyan"
    Write-Host ""
}

# Function to update deployment scripts
function Update-DeploymentScripts {
    param (
        [Parameter(Mandatory=$true)]
        [string]$PrivateKeyPath,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsIp,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsUsername,
        
        [Parameter(Mandatory=$true)]
        [int]$VpsPort
    )
    
    # Check if trae_deploy.ps1 exists
    $psDeployPath = Join-Path -Path $PSScriptRoot -ChildPath "trae_deploy.ps1"
    if (Test-Path -Path $psDeployPath) {
        Write-ColorOutput "Updating trae_deploy.ps1..." "Yellow"
        
        # Read the current content
        $psDeployContent = Get-Content -Path $psDeployPath -Raw
        
        # Update the SSH key path, IP, username, and port
        $psDeployContent = $psDeployContent -replace '(?<=\$SshKeyPath\s*=\s*")[^"]*(?=")', $PrivateKeyPath
        $psDeployContent = $psDeployContent -replace '(?<=\$VpsIp\s*=\s*")[^"]*(?=")', $VpsIp
        $psDeployContent = $psDeployContent -replace '(?<=\$VpsUsername\s*=\s*")[^"]*(?=")', $VpsUsername
        $psDeployContent = $psDeployContent -replace '(?<=\$VpsPort\s*=\s*)[0-9]+', $VpsPort.ToString()
        
        # Write the updated content back to the file
        $psDeployContent | Out-File -FilePath $psDeployPath -Encoding utf8
        
        Write-ColorOutput "trae_deploy.ps1 updated successfully!" "Green"
    }
    
    # Check if trae_deploy.sh exists
    $shDeployPath = Join-Path -Path $PSScriptRoot -ChildPath "trae_deploy.sh"
    if (Test-Path -Path $shDeployPath) {
        Write-ColorOutput "Updating trae_deploy.sh..." "Yellow"
        
        # Read the current content
        $shDeployContent = Get-Content -Path $shDeployPath -Raw
        
        # Update the SSH key path, IP, username, and port
        $shDeployContent = $shDeployContent -replace '(?<=SSH_KEY_PATH=)[^\r\n]*', $PrivateKeyPath.Replace('\', '/')
        $shDeployContent = $shDeployContent -replace '(?<=VPS_IP=)[^\r\n]*', $VpsIp
        $shDeployContent = $shDeployContent -replace '(?<=VPS_USERNAME=)[^\r\n]*', $VpsUsername
        $shDeployContent = $shDeployContent -replace '(?<=VPS_PORT=)[0-9]+', $VpsPort.ToString()
        
        # Write the updated content back to the file
        $shDeployContent | Out-File -FilePath $shDeployPath -Encoding utf8
        
        Write-ColorOutput "trae_deploy.sh updated successfully!" "Green"
    }
    
    # Check for GitHub workflow files
    $workflowsDir = Join-Path -Path $PSScriptRoot -ChildPath ".github\workflows"
    if (Test-Path -Path $workflowsDir) {
        $workflowFiles = Get-ChildItem -Path $workflowsDir -Filter "*.yml"
        
        foreach ($workflowFile in $workflowFiles) {
            Write-ColorOutput "Checking workflow file: $($workflowFile.Name)..." "Yellow"
            
            # Read the current content
            $workflowContent = Get-Content -Path $workflowFile.FullName -Raw
            
            # Check if the workflow contains SSH deployment steps
            if ($workflowContent -match "ssh") {
                Write-ColorOutput "Workflow file contains SSH deployment steps. Please update it manually with the GitHub secrets." "Yellow"
                Write-ColorOutput "Use the following secrets in your workflow:" "Yellow"
                Write-ColorOutput "  - \`${{ secrets.VPS_SSH_KEY }}" "Cyan"
                Write-ColorOutput "  - \`${{ secrets.CONTABO_VPS_IP }}" "Cyan"
                Write-ColorOutput "  - \`${{ secrets.CONTABO_USERNAME }}" "Cyan"
                Write-ColorOutput "  - \`${{ secrets.CONTABO_SSH_PORT }}" "Cyan"
            }
        }
    }
}

# Function to configure VPS hardening
function Configure-VpsHardening {
    param (
        [Parameter(Mandatory=$true)]
        [string]$PrivateKeyPath,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsIp,
        
        [Parameter(Mandatory=$true)]
        [string]$VpsUsername,
        
        [Parameter(Mandatory=$true)]
        [int]$VpsPort
    )
    
    Write-Host ""
    Write-ColorOutput "VPS SSH Hardening" "Green"
    Write-ColorOutput "----------------" "Green"
    Write-Host ""
    
    $confirmHardening = Read-Host "Do you want to disable password authentication on the VPS? (y/n)"
    
    if ($confirmHardening -ne "y") {
        Write-ColorOutput "VPS hardening skipped." "Yellow"
        return
    }
    
    # Create a temporary script file for SSH hardening
    $tempScriptPath = [System.IO.Path]::GetTempFileName()
    
    # Write SSH hardening commands to the temporary script
    @"
# Backup the SSH config file
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# Update SSH configuration to disable password authentication
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Ensure public key authentication is enabled
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Restart SSH service
systemctl restart sshd

echo "SSH hardening completed successfully."
"@ | Out-File -FilePath $tempScriptPath -Encoding utf8
    
    # Apply hardening using SSH key authentication
    try {
        Write-ColorOutput "Applying SSH hardening..." "Yellow"
        
        # Copy the script to the VPS
        scp -i "$PrivateKeyPath" -P $VpsPort -o "StrictHostKeyChecking=no" $tempScriptPath "$VpsUsername@${VpsIp}:/tmp/ssh_hardening.sh"
        
        # Execute the script on the VPS
        ssh -i "$PrivateKeyPath" -p $VpsPort -o "StrictHostKeyChecking=no" "$VpsUsername@$VpsIp" "chmod +x /tmp/ssh_hardening.sh && sudo /tmp/ssh_hardening.sh && rm /tmp/ssh_hardening.sh"
        
        Write-ColorOutput "VPS hardening completed successfully!" "Green"
        Write-ColorOutput "Password authentication has been disabled." "Yellow"
        Write-ColorOutput "Only SSH key-based authentication is now allowed." "Yellow"
    } catch {
        Write-ColorOutput "VPS hardening failed: $_" "Red"
        Write-ColorOutput "Please apply hardening manually by editing /etc/ssh/sshd_config on the VPS." "Yellow"
    }
    
    # Clean up the temporary script
    Remove-Item -Path $tempScriptPath -Force
}

# Main script execution
Show-Banner

# Step 1: Collect SSH key information
Write-Host ""
Write-ColorOutput "STEP 1: SSH KEY INFORMATION" "Green"
Write-ColorOutput "------------------------" "Green"

$privateKeyPath = Read-Host "Enter the path to your SSH private key file (default: $DefaultPrivateKeyPath)"
if ([string]::IsNullOrWhiteSpace($privateKeyPath)) {
    $privateKeyPath = $DefaultPrivateKeyPath
}

while (-not (Test-KeyFile -FilePath $privateKeyPath)) {
    Write-ColorOutput "Invalid SSH private key file. Please check the path and try again." "Red"
    $privateKeyPath = Read-Host "Enter the path to your SSH private key file"
}

$publicKeyPath = Read-Host "Enter the path to your SSH public key file (default: $DefaultPublicKeyPath)"
if ([string]::IsNullOrWhiteSpace($publicKeyPath)) {
    $publicKeyPath = $DefaultPublicKeyPath
}

while (-not (Test-SSHPublicKey -FilePath $publicKeyPath)) {
    Write-ColorOutput "Invalid SSH public key file. Please check the path and try again." "Red"
    
    # Check for common naming issues - automatically suggest .pub.pub file if it exists
    $possiblePubPubFile = "$publicKeyPath.pub"
    if (Test-Path -Path $possiblePubPubFile) {
        $pubPubContent = Get-Content -Path $possiblePubPubFile -Raw -ErrorAction SilentlyContinue
        if ($pubPubContent -match "^\s*(ssh-rsa|ssh-ed25519|ecdsa-sha2)") {
            Write-ColorOutput "Found a valid public key at: $possiblePubPubFile" "Green"
            $useCorrectFile = Read-Host "Would you like to use this file instead? (y/n)"
            if ($useCorrectFile -eq "y") {
                $publicKeyPath = $possiblePubPubFile
                continue
            }
        }
    }
    
    # Offer to display the file content to help diagnose the issue
    $showContent = Read-Host "Would you like to see the content of the file? (y/n)"
    if ($showContent -eq "y") {
        try {
            $content = Get-Content -Path $publicKeyPath -Raw -ErrorAction Stop
            Write-ColorOutput "\nFile content:" "Yellow"
            Write-ColorOutput $content "Cyan"
            Write-ColorOutput "\nA valid public key should start with 'ssh-rsa', 'ssh-ed25519', or 'ecdsa-sha2'" "Yellow"
            
            # If it looks like a private key, provide specific guidance
            if ($content -match "BEGIN .* PRIVATE KEY") {
                Write-ColorOutput "\nThis appears to be a private key file, not a public key file." "Red"
                Write-ColorOutput "The public key is typically in a file with the same name plus a .pub extension." "Yellow"
                Write-ColorOutput "For example, if your private key is 'id_rsa', the public key would be 'id_rsa.pub'." "Yellow"
                
                # Check if there's a file without the .pub extension that might be the private key
                $possiblePrivateKeyPath = $publicKeyPath -replace '\.pub$', ''
                if (Test-Path -Path $possiblePrivateKeyPath) {
                    Write-ColorOutput "\nFound a possible private key at: $possiblePrivateKeyPath" "Yellow"
                    Write-ColorOutput "The correct public key might be at: $possiblePrivateKeyPath.pub" "Yellow"
                }
            } else {
                Write-ColorOutput "If this is not a public key, please generate one using 'ssh-keygen' or check for the correct .pub file" "Yellow"
            }
        } catch {
            Write-ColorOutput "Could not read file content: $_" "Red"
        }
    }
    
    # Offer to generate a new SSH key pair
    $generateNew = Read-Host "Would you like to generate a new SSH key pair? (y/n)"
    if ($generateNew -eq "y") {
        $newKeyPath = Read-Host "Enter the path for the new SSH key (without .pub extension)"
        if ([string]::IsNullOrWhiteSpace($newKeyPath)) {
            $newKeyPath = Join-Path -Path $env:USERPROFILE -ChildPath ".ssh\id_rsa"
            Write-ColorOutput "Using default path: $newKeyPath" "Yellow"
        }
        
        # Generate the new key pair
        $keyGenSuccess = Generate-SSHKeyPair -KeyPath $newKeyPath
        
        if ($keyGenSuccess) {
            # Update the paths to use the new key pair
            $privateKeyPath = $newKeyPath
            $publicKeyPath = "$newKeyPath.pub"
            Write-ColorOutput "Using new key pair: $privateKeyPath and $publicKeyPath" "Green"
            break
        }
    }
    
    $publicKeyPath = Read-Host "Enter the path to your SSH public key file"
}

# Step 2: Collect VPS information
Write-Host ""
Write-ColorOutput "STEP 2: VPS INFORMATION" "Green"
Write-ColorOutput "---------------------" "Green"

$vpsIp = Read-Host "Enter your VPS IP address (default: $DefaultVpsIp)"
if ([string]::IsNullOrWhiteSpace($vpsIp)) {
    $vpsIp = $DefaultVpsIp
}

while (-not (Test-IPAddress -IPAddress $vpsIp)) {
    Write-ColorOutput "Invalid IP address format. Please try again." "Red"
    $vpsIp = Read-Host "Enter your VPS IP address"
}

$vpsUsername = Read-Host "Enter your VPS username (default: $DefaultVpsUsername)"
if ([string]::IsNullOrWhiteSpace($vpsUsername)) {
    $vpsUsername = $DefaultVpsUsername
}

$vpsPortStr = Read-Host "Enter your VPS SSH port (default: $DefaultVpsPort)"
if ([string]::IsNullOrWhiteSpace($vpsPortStr)) {
    $vpsPort = $DefaultVpsPort
} else {
    $vpsPort = [int]$vpsPortStr
}

# Step 3: Deploy SSH key to VPS
Write-Host ""
Write-ColorOutput "STEP 3: DEPLOYING SSH KEY" "Green"
Write-ColorOutput "----------------------" "Green"

$deploySuccess = Deploy-SSHKey -PublicKeyPath $publicKeyPath -PrivateKeyPath $privateKeyPath -VpsIp $vpsIp -VpsUsername $vpsUsername -VpsPort $vpsPort

if ($deploySuccess) {
    # Step 4: Configure GitHub Actions secrets
    Write-Host ""
    Write-ColorOutput "STEP 4: GITHUB ACTIONS CONFIGURATION" "Green"
    Write-ColorOutput "--------------------------------" "Green"
    
    Configure-GitHubSecrets -PrivateKeyPath $privateKeyPath -VpsIp $vpsIp -VpsUsername $vpsUsername -VpsPort $vpsPort
    
    # Step 5: Update deployment scripts
    Write-Host ""
    Write-ColorOutput "STEP 5: UPDATING DEPLOYMENT SCRIPTS" "Green"
    Write-ColorOutput "-------------------------------" "Green"
    
    Update-DeploymentScripts -PrivateKeyPath $privateKeyPath -VpsIp $vpsIp -VpsUsername $vpsUsername -VpsPort $vpsPort
    
    # Step 6: Configure VPS hardening
    Write-Host ""
    Write-ColorOutput "STEP 6: VPS HARDENING" "Green"
    Write-ColorOutput "------------------" "Green"
    
    Configure-VpsHardening -PrivateKeyPath $privateKeyPath -VpsIp $vpsIp -VpsUsername $vpsUsername -VpsPort $vpsPort
    
    # Final summary
    Write-Host ""
    Write-ColorOutput "DEPLOYMENT SUMMARY" "Green"
    Write-ColorOutput "-----------------" "Green"
    Write-Host ""
    Write-ColorOutput "✅ SSH key deployed to VPS" "Green"
    Write-ColorOutput "✅ GitHub Actions secrets configured" "Green"
    Write-ColorOutput "✅ Deployment scripts updated" "Green"
    Write-ColorOutput "✅ VPS hardening applied" "Green"
    Write-Host ""
    Write-ColorOutput "You can now use the following command to connect to your VPS:" "Yellow"
    Write-ColorOutput "ssh -i \"$privateKeyPath\" $vpsUsername@$vpsIp -p $vpsPort" "Cyan"
    Write-Host ""
} else {
    Write-ColorOutput "SSH key deployment failed. Please try again or use the VNC recovery tool." "Red"
    Write-Host ""
    Write-ColorOutput "You can use the SSH VNC Recovery Tool to manually deploy your SSH key:" "Yellow"
    Write-ColorOutput ".\ssh_vnc_recovery.ps1" "Cyan"
    Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")