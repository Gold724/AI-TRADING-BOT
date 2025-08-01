# CI/CD Troubleshooting Checklist

This document provides a step-by-step checklist to troubleshoot common issues with GitHub Actions CI/CD pipeline for the AI Trading Sentinel project.

## ✅ 1. Check Workflow File Exists and Is Named Correctly

Go to:
```bash
.github/workflows/ci_cd_pipeline.yml
```

- ✅ Is the file present?
- ✅ Is it named with a `.yml` or `.yaml` extension?
- ✅ Is the file committed and pushed to GitHub?

👉 To verify locally:
```bash
git log -- .github/workflows/ci_cd_pipeline.yml
```

You should see a commit log entry. If not, it was never committed.

## ✅ 2. Check Workflow Triggers

Open `ci_cd_pipeline.yml` and make sure it starts like this:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:
```

If `on:` is missing or malformed, GitHub won't register the workflow.

## ✅ 3. Confirm Push Actually Went to GitHub

Sometimes changes are made locally but not pushed.

👉 Check:
```bash
git status
git log -1
```

👉 Then push if needed:
```bash
git add .github/workflows/ci_cd_pipeline.yml
git commit -m "Add CI/CD workflow"
git push origin main
```

## ✅ 4. Verify `.github` Folder Isn't in `.gitignore`

Open your `.gitignore`. If it contains `.github/`, Git is ignoring the workflows entirely.

❌ This should not appear:
```
.github/
```

✅ Instead, you can ignore secrets only:
```bash
.github/secrets.env
```

## ✅ 5. Try an Empty Commit to Trigger It

Once the workflow is fixed, do:
```bash
git commit --allow-empty -m "Trigger CI/CD"
git push origin main
```

Then refresh GitHub Actions and it should appear within 30 seconds.

## ✅ 6. Check GitHub Repository Settings

In your GitHub repository:
1. Go to Settings > Actions > General
2. Ensure Actions permissions are set to "Allow all actions and reusable workflows"
3. Check that the workflow is not disabled

## ✅ 7. Verify GitHub Secrets for Deployment

For the deployment job to work, ensure these secrets are set:
- `CONTABO_VPS_IP`
- `CONTABO_VPS_PASSWORD`
- `CONTABO_SSH_PORT`

Go to Settings > Secrets and variables > Actions to add or verify these secrets.

## ✅ 8. Check for Syntax Errors

Use the GitHub Actions workflow validator:

1. Go to your repository on GitHub
2. Navigate to Actions tab
3. If there are syntax errors, they will be displayed at the top

Alternatively, use a YAML linter locally:
```bash
pip install yamllint
yamllint .github/workflows/ci_cd_pipeline.yml
```

## ✅ 9. Review Workflow Logs

If the workflow runs but fails:

1. Go to Actions tab in your GitHub repository
2. Click on the failed workflow run
3. Expand the job that failed
4. Review the logs for error messages

## ✅ 10. Common Issues and Solutions

### Workflow Not Appearing
- Ensure the workflow file is in the correct location: `.github/workflows/`
- Check that the file has the correct extension: `.yml` or `.yaml`
- Verify the file is properly formatted YAML

### Workflow Failing
- Check for syntax errors in the workflow file
- Ensure all required secrets are set
- Verify dependencies are correctly specified
- Check that the runner environment has all necessary tools

### Deployment Failing
- Verify SSH connection details (IP, port, password)
- Check that the VPS is accessible from GitHub Actions
- Ensure the deployment script has proper permissions
- Verify the deployment script is compatible with the VPS environment

## Need More Help?

If you're still experiencing issues after going through this checklist, consider:

1. Checking the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Reviewing the [AI Trading Sentinel deployment guide](DEPLOYMENT.md)
3. Simplifying your workflow to isolate the issue