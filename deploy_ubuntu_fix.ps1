#!/usr/bin/env pwsh
# Ubuntu Dependencies Fix Deployment Script
# This script deploys the Ubuntu dependency fixes to your VPS

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsHost,
    
    [Parameter(Mandatory=$true)]
    [string]$VpsUser,
    
    [Parameter(Mandatory=$true)]
    [string]$VpsDir,
    
    [Parameter(Mandatory=$false)]
    [string]$VpsPassword = "JfAJZ38VwU8j42LKa84PqIxVx"
)

# Validate parameters
if (-not $VpsHost -or -not $VpsUser -or -not $VpsDir) {
    Write-Host "Error: Missing required parameters" -ForegroundColor Red
    Write-Host "Usage: .\deploy_ubuntu_fix.ps1 -VpsHost <host> -VpsUser <user> -VpsDir <directory>" -ForegroundColor Yellow
    exit 1
}

# Test SSH connection
Write-Host "Testing SSH connection to $VpsUser@$VpsHost..." -ForegroundColor Blue
Write-Host "Using password authentication..." -ForegroundColor Yellow

# Create temporary expect script for SSH authentication
$expectScript = @"
#!/usr/bin/expect -f
set timeout 30
spawn ssh -o StrictHostKeyChecking=no $VpsUser@$VpsHost "echo 'SSH connection successful'"
expect {
    "password:" {
        send "$VpsPassword\r"
        exp_continue
    }
    "SSH connection successful" {
        exit 0
    }
    timeout {
        exit 1
    }
    eof {
        exit 0
    }
}
"@

$expectScript | Out-File -FilePath "temp_ssh_test.exp" -Encoding ASCII
if (Get-Command "expect" -ErrorAction SilentlyContinue) {
    expect temp_ssh_test.exp
} else {
    Write-Host "Expect not available, trying direct SSH with password prompt..." -ForegroundColor Yellow
    Write-Host "You may need to enter the password manually: $VpsPassword" -ForegroundColor Cyan
    ssh -o StrictHostKeyChecking=no $VpsUser@$VpsHost "echo 'SSH connection successful'"
}
Remove-Item "temp_ssh_test.exp" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host "SSH connection successful!" -ForegroundColor Green
} else {
    Write-Host "SSH connection failed. Please check your credentials and network." -ForegroundColor Red
    exit 1
}

$sshTarget = "$VpsUser@$VpsHost"

# Copy the fix script to VPS
Write-Host "Copying Ubuntu dependencies fix script to VPS..." -ForegroundColor Blue

# Create expect script for SCP
$scpExpectScript = @"
#!/usr/bin/expect -f
set timeout 60
spawn scp -o StrictHostKeyChecking=no "./vps_deployment/fix_ubuntu_dependencies.sh" "${sshTarget}:${VpsDir}/"
expect {
    "password:" {
        send "$VpsPassword\r"
        exp_continue
    }
    eof {
        exit 0
    }
    timeout {
        exit 1
    }
}
"@

$scpExpectScript | Out-File -FilePath "temp_scp.exp" -Encoding ASCII
if (Get-Command "expect" -ErrorAction SilentlyContinue) {
    expect temp_scp.exp
} else {
    Write-Host "Expect not available, you may need to enter password manually: $VpsPassword" -ForegroundColor Cyan
    scp -o StrictHostKeyChecking=no "./vps_deployment/fix_ubuntu_dependencies.sh" "${sshTarget}:${VpsDir}/"
}
Remove-Item "temp_scp.exp" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host "Fix script copied successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to copy fix script to VPS" -ForegroundColor Red
    exit 1
}

# Make the script executable
Write-Host "Making fix script executable..." -ForegroundColor Blue

# Create expect script for chmod
$chmodExpectScript = @"
#!/usr/bin/expect -f
set timeout 30
spawn ssh -o StrictHostKeyChecking=no $sshTarget "chmod +x $VpsDir/fix_ubuntu_dependencies.sh"
expect {
    "password:" {
        send "$VpsPassword\r"
        exp_continue
    }
    eof {
        exit 0
    }
    timeout {
        exit 1
    }
}
"@

$chmodExpectScript | Out-File -FilePath "temp_chmod.exp" -Encoding ASCII
if (Get-Command "expect" -ErrorAction SilentlyContinue) {
    expect temp_chmod.exp
} else {
    Write-Host "Expect not available, you may need to enter password manually: $VpsPassword" -ForegroundColor Cyan
    ssh -o StrictHostKeyChecking=no $sshTarget "chmod +x $VpsDir/fix_ubuntu_dependencies.sh"
}
Remove-Item "temp_chmod.exp" -ErrorAction SilentlyContinue

# Execute the fix script on VPS
Write-Host "Executing Ubuntu dependencies fix on VPS..." -ForegroundColor Blue
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Create expect script for execution
$execExpectScript = @"
#!/usr/bin/expect -f
set timeout 300
spawn ssh -o StrictHostKeyChecking=no $sshTarget "cd $VpsDir && ./fix_ubuntu_dependencies.sh"
expect {
    "password:" {
        send "$VpsPassword\r"
        exp_continue
    }
    eof {
        exit 0
    }
    timeout {
        exit 1
    }
}
"@

$execExpectScript | Out-File -FilePath "temp_exec.exp" -Encoding ASCII
if (Get-Command "expect" -ErrorAction SilentlyContinue) {
    expect temp_exec.exp
} else {
    Write-Host "Expect not available, you may need to enter password manually: $VpsPassword" -ForegroundColor Cyan
    ssh -o StrictHostKeyChecking=no $sshTarget "cd $VpsDir && ./fix_ubuntu_dependencies.sh"
}
Remove-Item "temp_exec.exp" -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Ubuntu dependencies fix completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps on your VPS:" -ForegroundColor Cyan
    Write-Host "1. SSH to VPS: ssh $VpsUser@$VpsHost" -ForegroundColor Yellow
    Write-Host "2. Navigate to directory: cd $VpsDir" -ForegroundColor Yellow
    Write-Host "3. Install Python requirements: pip3 install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "4. Install Playwright: python3 -m playwright install" -ForegroundColor Yellow
    Write-Host "5. Install Playwright deps: python3 -m playwright install-deps" -ForegroundColor Yellow
    Write-Host "6. Set environment variables and run TradeBot Sentinel" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Ubuntu dependencies fix failed" -ForegroundColor Red
    Write-Host "Please check the error messages above and try manual installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Deployment completed!" -ForegroundColor Green