# SSH Deployment Fix for AI Trading Sentinel

## Critical Issues Identified

### 1. SSH Authentication Failure
```
Load key "/home/runner/.ssh/id_rsa": error in libcrypto
Permission denied, please try again.
root@161.97.112.146: Permission denied (publickey,password).
```

### 2. Slack Webhook Error
```
Error: An HTTP protocol error occurred: statusCode = 404
```

## Immediate Fix Steps

### Step 1: Generate New SSH Key Pair

```bash
# On your local machine or GitHub Codespaces
ssh-keygen -t rsa -b 4096 -f ~/.ssh/trae_deploy_key -N ""
```

### Step 2: Add Public Key to VPS

```bash
# Copy public key to VPS (replace with your actual key)
ssh-copy-id -i ~/.ssh/trae_deploy_key.pub root@161.97.112.146

# Or manually add to authorized_keys
cat ~/.ssh/trae_deploy_key.pub | ssh root@161.97.112.146 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Step 3: Update GitHub Secrets

1. **CONTABO_SSH_PRIVATE_KEY**: Copy content of `~/.ssh/trae_deploy_key`
2. **SLACK_WEBHOOK_URL**: Get new webhook from Slack app settings
3. **CONTABO_VPS_HOST**: Ensure it's `161.97.112.146`
4. **CONTABO_VPS_USER**: Should be `root`

### Step 4: Test SSH Connection

```bash
# Test SSH connection with new key
ssh -i ~/.ssh/trae_deploy_key root@161.97.112.146 "echo 'SSH connection successful'"
```

## Updated GitHub Actions Workflow

### Fixed SSH Setup Section

```yaml
- name: Setup SSH Key
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.CONTABO_SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H 161.97.112.146 >> ~/.ssh/known_hosts
    
- name: Test SSH Connection
  run: |
    ssh -o StrictHostKeyChecking=no root@161.97.112.146 "echo 'SSH test successful'"
    
- name: Deploy to VPS
  run: |
    ssh -o StrictHostKeyChecking=no root@161.97.112.146 'bash /opt/trae/trae_deploy.sh --auto'
```

### Fixed Slack Notification

```yaml
- name: Notify Success
  if: success()
  uses: 8398a7/action-slack@v3
  with:
    status: success
    text: '✅ AI Trading Sentinel deployed successfully to VPS'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
    
- name: Notify Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: '❌ AI Trading Sentinel deployment failed'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## VPS Deployment Script Requirements

Ensure `/opt/trae/trae_deploy.sh` exists on VPS:

```bash
#!/bin/bash
# /opt/trae/trae_deploy.sh

set -e

echo "Starting AI Trading Sentinel deployment..."

# Create directories
mkdir -p /opt/trae/{logs,backups,config}

# Stop existing services
systemctl stop trae-trading-bot || true

# Backup current deployment
if [ -d "/opt/trae/current" ]; then
    cp -r /opt/trae/current /opt/trae/backups/backup-$(date +%Y%m%d-%H%M%S)
fi

# Update from GitHub
cd /opt/trae
git pull origin main || git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git current

# Install dependencies
cd /opt/trae/current
pip3 install -r requirements.txt

# Update systemd service
cp deploy/trae-trading-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable trae-trading-bot
systemctl start trae-trading-bot

echo "Deployment completed successfully"
systemctl status trae-trading-bot
```

## Emergency Recovery Commands

### If SSH still fails:

```bash
# Use password authentication as fallback
sshpass -p 'YOUR_VPS_PASSWORD' ssh root@161.97.112.146 'bash /opt/trae/trae_deploy.sh --auto'
```

### Manual deployment:

```bash
# Create deployment package locally
tar -czf deployment.tar.gz src/ requirements.txt main.py config/ deploy/

# Upload to VPS
scp deployment.tar.gz root@161.97.112.146:/tmp/

# Extract and deploy on VPS
ssh root@161.97.112.146 '
  cd /opt/trae
  tar -xzf /tmp/deployment.tar.gz
  pip3 install -r requirements.txt
  systemctl restart trae-trading-bot
'
```

## Verification Steps

1. **SSH Connection**: `ssh root@161.97.112.146 "uptime"`
2. **Service Status**: `ssh root@161.97.112.146 "systemctl status trae-trading-bot"`
3. **API Health**: `curl http://161.97.112.146:5000/health`
4. **Logs**: `ssh root@161.97.112.146 "journalctl -u trae-trading-bot -f"`

## Next Steps

1. ✅ Generate new SSH key pair
2. ✅ Add public key to VPS authorized_keys
3. ✅ Update GitHub secrets with new private key
4. ✅ Get valid Slack webhook URL
5. ✅ Test SSH connection manually
6. ✅ Run GitHub Actions workflow
7. ✅ Verify deployment success
8. ✅ Monitor trading bot operation

## Security Notes

- Use dedicated SSH key for deployment only
- Rotate SSH keys regularly
- Monitor VPS access logs
- Use strong passwords for VPS root account
- Consider using SSH certificates for enhanced security