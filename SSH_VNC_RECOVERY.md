# SSH VNC Recovery Tool

## Overview

The SSH VNC Recovery Tool is designed to help you regain SSH access to your VPS when normal SSH authentication fails. It provides a guided process to connect to your server using VNC console access and inject your SSH public key to restore secure access.

## When to Use This Tool

Use this tool when:
- You receive SSH authentication errors
- Your SSH keys are not being accepted
- You need to reset or update SSH access
- You're locked out of your server via normal SSH methods

## Prerequisites

1. A VNC client installed on your computer (UltraVNC, RealVNC, or TigerVNC)
2. Your VPS details (IP address, VNC IP, VNC port)
3. VNC password (from your Contabo control panel)
4. Your SSH public key file (.pub)

## How to Use

### Option 1: Run the Batch File

Simply double-click the `ssh_vnc_recovery.bat` file to launch the tool with the correct PowerShell execution policy.

### Option 2: Run the PowerShell Script Directly

Open PowerShell and run:

```powershell
.\ssh_vnc_recovery.ps1
```

## Tool Workflow

The tool will guide you through these steps:

1. **Collect VPS Information**: Enter your VPS IP, VNC IP, and VNC port
2. **SSH Key Selection**: Specify the path to your SSH public key file
3. **VNC Connection Instructions**: Detailed steps to connect via VNC
4. **Commands to Run**: Commands to paste into the VNC terminal
5. **Test SSH Connection**: Command to test your restored SSH access
6. **Security Reminder**: Important security steps after recovery

## Security Considerations

⚠️ **Important Security Notes**:

- VNC is **not encrypted** - use only for recovery purposes
- Always log out of VNC when finished
- Consider disabling VNC access in your Contabo panel after recovery
- Reset your VNC password after use

## Troubleshooting

If you encounter issues:

1. **VNC Connection Fails**: Verify your VNC IP, port, and password
2. **Black Screen in VNC**: Click on the VNC window and press Enter
3. **SSH Still Fails**: Ensure your public key was properly added and SSH service restarted

## Support

If you continue to experience issues, contact your VPS provider's support team for assistance.