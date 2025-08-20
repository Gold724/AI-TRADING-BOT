# 🤖 GitHub Actions CI/CD Pipeline

## Overview
This directory contains the fixed and optimized GitHub Actions workflows for the AI Trading Sentinel project. All previous errors have been resolved.

## 🚀 Available Workflows

### 1. `main.yml` - Primary CI/CD Pipeline
- **Triggers**: Push to `main`/`master` branches, pull requests
- **Features**: 
  - Code quality checks (flake8, black, isort, bandit)
  - Security scanning
  - Comprehensive testing with Playwright
  - Automated deployment to Contabo VPS
  - Slack notifications
  - Artifact retention (30 days)

### 2. `validate.yml` - Quick Validation
- **Triggers**: Pull requests, manual dispatch
- **Features**:
  - Fast repository validation
  - Python syntax checking
  - Essential file verification

## 🔧 Required Secrets

Configure these in your GitHub repository settings:

### VPS Deployment
```
CONTABO_SSH_PRIVATE_KEY    # SSH private key for VPS access
CONTABO_VPS_HOST          # VPS hostname/IP
CONTABO_VPS_USERNAME      # VPS username (default: root)
CONTABO_SSH_PORT          # SSH port (default: 22)
```

### Notifications (Optional)
```
SLACK_WEBHOOK_URL         # Slack webhook for deployment notifications
```

## 📋 Setup Instructions

### 1. Configure Secrets
1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the required secrets listed above

### 2. SSH Key Setup
Generate and configure SSH access:

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f trae_deploy_key -C "github-actions"

# Add public key to VPS
ssh-copy-id -i trae_deploy_key.pub root@YOUR_VPS_IP

# Add private key to GitHub secrets
cat trae_deploy_key | pbcopy  # Copy to clipboard, then paste as CONTABO_SSH_PRIVATE_KEY
```

### 3. Test the Pipeline

#### Manual Test
```bash
# Trigger validation workflow
gh workflow run validate.yml

# Check status
gh run list --workflow=validate.yml
```

#### Automatic Test
Push any change to trigger the full pipeline:
```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

## 🔍 Monitoring

### GitHub Actions Tab
- View all workflow runs at: `https://github.com/YOUR_USERNAME/ai-trading-sentinel/actions`

### Real-time Logs
```bash
# View live logs
gh run watch --exit-status

# View specific workflow logs
gh run view --log --workflow=main.yml
```

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### 1. SSH Connection Failures
```bash
# Test SSH connection locally
ssh -i ~/.ssh/trae_deploy_key root@YOUR_VPS_IP

# Check VPS firewall
ufw status
systemctl status sshd
```

#### 2. Missing Dependencies
```bash
# Update requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

#### 3. Permission Errors
```bash
# Ensure VPS has correct permissions
ssh root@YOUR_VPS_IP "chmod +x /opt/trae/*.py"
```

## 🚨 Emergency Procedures

### Force Deploy (Skip Tests)
```bash
gh workflow run main.yml --ref main -f skip_tests=true
```

### Manual Rollback
```bash
# SSH to VPS and restore backup
ssh root@YOUR_VPS_IP
ls -la /opt/trae-backup-*
mv /opt/trae-backup-[TIMESTAMP] /opt/trae
systemctl restart trae
```

## 📊 Performance Metrics

The pipeline includes built-in monitoring:
- Build duration tracking
- Test coverage reports
- Security scan results
- Deployment success rates

## 🔐 Security Features

- **Dependency scanning** with safety
- **Code security** with bandit
- **Secrets scanning** enabled
- **SSH key-based** authentication only
- **No hardcoded credentials**

## 📞 Support

For issues with the CI/CD pipeline:
1. Check the [Actions tab](https://github.com/YOUR_USERNAME/ai-trading-sentinel/actions) for error logs
2. Review this README for common solutions
3. Open an issue in the repository with the workflow run URL

## 🔄 Updates

The workflows are designed to be self-updating. When you push changes to workflow files, they'll automatically take effect on the next run.