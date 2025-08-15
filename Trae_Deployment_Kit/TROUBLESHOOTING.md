# Trae AI Trading Sentinel - Deployment Troubleshooting Guide

This guide provides solutions for common issues encountered during deployment of the Trae AI Trading Sentinel.

## SSH Connection Issues

### Problem: SSH connection fails

**Symptoms:**
- "Connection refused" error
- "Permission denied" error
- Timeout when connecting

**Solutions:**

1. **Verify VPS is running**
   - Check your VPS provider's dashboard to ensure the instance is active

2. **Check SSH key permissions**
   - On Linux/macOS: `chmod 600 /path/to/your/key`
   - On Windows: Right-click > Properties > Security > Advanced > Ensure only your user has permissions

3. **Verify SSH key path**
   - Ensure the path to your SSH key is correct
   - Try using the absolute path instead of a relative path

4. **Check firewall settings**
   - Ensure port 22 (or your custom SSH port) is open on your VPS

## File Transfer Issues

### Problem: rsync or scp fails

**Symptoms:**
- "Command not found" error for rsync
- Permission denied errors during file transfer
- Timeout during transfer

**Solutions:**

1. **Install rsync**
   - Windows: Install via Chocolatey or WSL
   - Linux: `sudo apt-get install rsync` or equivalent
   - macOS: `brew install rsync`

2. **Check disk space**
   - Ensure your VPS has sufficient disk space: `ssh user@vps "df -h"`

3. **Use scp fallback**
   - The deployment scripts automatically fall back to scp if rsync is not available

## Python Environment Issues

### Problem: Python virtual environment setup fails

**Symptoms:**
- "Command not found: python3" error
- pip installation errors
- Module import errors

**Solutions:**

1. **Install Python**
   - `ssh user@vps "sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip"`

2. **Check Python version**
   - `ssh user@vps "python3 --version"`
   - Ensure Python 3.8+ is installed

3. **Manual venv creation**
   - `ssh user@vps "cd ~/ai-trading-sentinel && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"`

## Node.js/npm Issues

### Problem: Frontend dependency installation fails

**Symptoms:**
- npm command not found
- npm install errors
- Node version incompatibility

**Solutions:**

1. **Install Node.js and npm**
   - `ssh user@vps "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"`

2. **Check Node.js version**
   - `ssh user@vps "node --version && npm --version"`

3. **Clear npm cache**
   - `ssh user@vps "cd ~/ai-trading-sentinel/frontend && npm cache clean --force && npm install"`

## Systemd Service Issues

### Problem: Service fails to start

**Symptoms:**
- "Failed to start trae.service" error
- Service starts but immediately exits
- Service status shows "failed"

**Solutions:**

1. **Check service logs**
   - `ssh user@vps "sudo journalctl -u trae -n 50"`

2. **Verify service file**
   - `ssh user@vps "cat /etc/systemd/system/trae.service"`
   - Ensure paths and user are correct

3. **Check permissions**
   - `ssh user@vps "sudo chown -R $USER:$USER ~/ai-trading-sentinel"`

4. **Manually start the application**
   - `ssh user@vps "cd ~/ai-trading-sentinel && source venv/bin/activate && python main.py"`
   - Look for any error messages

## Environment Variable Issues

### Problem: Missing or incorrect environment variables

**Symptoms:**
- Application fails with "Key error" or "Configuration error"
- Authentication failures
- API connection issues

**Solutions:**

1. **Verify .env file transfer**
   - `ssh user@vps "cat ~/ai-trading-sentinel/.env"`

2. **Check environment variables in service**
   - Add `Environment=KEY=VALUE` lines to the service file for critical variables

3. **Reload systemd and restart service**
   - `ssh user@vps "sudo systemctl daemon-reload && sudo systemctl restart trae"`

## Slack Notification Issues

### Problem: Slack notifications not being sent

**Symptoms:**
- No notifications appear in Slack
- Script reports webhook errors

**Solutions:**

1. **Verify webhook URL**
   - Ensure the webhook URL is correct and active
   - Test with a simple curl command: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test message"}' YOUR_WEBHOOK_URL`

2. **Check internet connectivity**
   - Ensure your VPS can reach external services

3. **Verify Python requests module**
   - `ssh user@vps "source ~/ai-trading-sentinel/venv/bin/activate && pip install requests"`

## GitHub Actions Issues

### Problem: GitHub Actions workflow fails

**Symptoms:**
- Workflow shows red X in GitHub
- Deployment step fails
- SSH connection errors in workflow logs

**Solutions:**

1. **Check GitHub secrets**
   - Verify all required secrets are set in repository settings
   - Ensure SSH_PRIVATE_KEY is properly formatted (includes BEGIN and END lines)

2. **Verify known_hosts format**
   - The KNOWN_HOSTS secret should contain the output of `ssh-keyscan your-vps-ip`

3. **Check workflow file syntax**
   - Validate the YAML syntax of your workflow file

4. **Review workflow logs**
   - Check detailed logs in GitHub Actions tab for specific error messages