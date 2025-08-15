# GitHub Secrets Setup for VPS Deployment

This document explains how to set up GitHub secrets for secure deployment to your VPS via CI/CD pipelines.

## Setting Up GitHub Secrets

1. Go to GitHub → Repository → Settings → Secrets → Actions → New repository secret

2. Add the following secrets:

   - `CONTABO_VPS_IP` = your server IP
   - `CONTABO_VPS_PASSWORD` = root password
   - `CONTABO_SSH_PORT` = usually 22

## Important Notes

- Ensure `.env.example` is pushed to the repository (not your actual `.env` file with secrets)
- Verify that `deploy_to_contabo.py` or shell script uses `paramiko` or `scp` for secure file transfers
- The pre-commit hook will prevent accidental commits of your `.env` file

## Triggering End-to-End Deployment

After setting up the secrets and ensuring your code is ready, you can trigger a full CI/CD pipeline with:

```bash
git add .
git commit -m "chore: trigger full CI/CD pipeline"
git push origin main
```

This will run all tests and, if successful, deploy to your VPS automatically.