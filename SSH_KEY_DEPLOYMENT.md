# SSH Key Deployment Tool

## Overview
The SSH Key Deployment Tool automates the process of deploying SSH public keys to a VPS and configuring GitHub Actions secrets for CI/CD integration. This tool helps you establish secure, password-less SSH access to your server and prepares your repository for automated deployments.

## Features
- Automated SSH public key deployment to VPS
- GitHub Actions secrets configuration guidance
- Deployment script updates
- VPS SSH hardening (optional)
- Comprehensive error handling and validation

## Prerequisites
- PowerShell 5.1 or higher
- SSH client installed on your local machine
- Valid SSH key pair (RSA 4096-bit recommended)
- VPS with SSH access (password authentication initially required)

## Installation
No installation is required. Simply download the following files to your project directory:
- `deploy_ssh_key.ps1` - Main PowerShell script
- `deploy_ssh_key.bat` - Batch launcher for Windows users

## Usage

### Option 1: Using the Batch File (Windows)
Double-click the `deploy_ssh_key.bat` file to launch the tool with the correct execution policy.

### Option 2: Using PowerShell Directly
Open PowerShell and run:
```powershell
.\deploy_ssh_key.ps1
```

If you encounter execution policy restrictions, you can use:
```powershell
PowerShell.exe -ExecutionPolicy Bypass -File .\deploy_ssh_key.ps1
```

## Workflow
The tool guides you through the following steps:

1. **SSH Key Information**
   - Specify the paths to your SSH private and public key files
   - Default: `D:\anki\trae_vps` (private) and `D:\anki\trae_vps.pub` (public)

2. **VPS Information**
   - Enter your VPS IP address, username, and SSH port
   - Default: IP `161.97.112.146`, username `root`, port `22`

3. **SSH Key Deployment**
   - The tool will attempt to connect using the SSH key first
   - If that fails, it will guide you through the deployment process
   - For servers without `sshpass`, manual instructions are provided

4. **GitHub Actions Configuration**
   - Displays the secrets to add to your GitHub repository
   - Provides a sample workflow file for deployment

5. **Deployment Script Updates**
   - Updates any existing deployment scripts with the new SSH key information
   - Checks for `trae_deploy.ps1`, `trae_deploy.sh`, and GitHub workflow files

6. **VPS Hardening (Optional)**
   - Offers to disable password authentication on the VPS
   - Ensures only SSH key-based authentication is allowed

## Security Considerations
- The private key is never transmitted to the VPS
- Only the public key is added to the VPS's `authorized_keys` file
- Password authentication can be disabled after successful key deployment
- All temporary files are securely deleted after use

## Troubleshooting

### SSH Key Authentication Fails
If SSH key authentication fails after deployment:
1. Verify the key pair is valid: `ssh-keygen -y -f your_private_key`
2. Check permissions on the VPS: `~/.ssh` should be 700, `~/.ssh/authorized_keys` should be 600
3. Examine SSH server logs: `sudo journalctl -u ssh`
4. Try the VNC recovery tool if available: `.\ssh_vnc_recovery.ps1`

### GitHub Actions Deployment Issues
If GitHub Actions deployments fail:
1. Verify the secrets are correctly added to your repository
2. Check that the private key is properly formatted (including newlines)
3. Ensure the workflow file is correctly configured

## License
This tool is provided as-is under the MIT License.

## Support
For issues or questions, please open an issue in the repository.