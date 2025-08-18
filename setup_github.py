#!/usr/bin/env python3
"""
🐙 GitHub Repository Setup for AI Trading Sentinel
Helps you quickly push your code to GitHub for deployment
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_git_installed():
    """Check if Git is installed"""
    success, _, _ = run_command("git --version")
    return success

def setup_github_repo():
    """Setup GitHub repository"""
    project_root = Path.cwd()
    
    print("🐙 AI Trading Sentinel - GitHub Setup")
    print("="*50)
    
    # Check if Git is installed
    if not check_git_installed():
        print("❌ Git is not installed!")
        print("📥 Please install Git from: https://git-scm.com/download/windows")
        return False
    
    print("✅ Git is installed")
    
    # Check if already a Git repository
    if (project_root / ".git").exists():
        print("✅ Already a Git repository")
    else:
        print("📁 Initializing Git repository...")
        success, _, error = run_command("git init", cwd=project_root)
        if not success:
            print(f"❌ Failed to initialize Git: {error}")
            return False
        print("✅ Git repository initialized")
    
    # Create .gitignore if it doesn't exist
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        print("📝 Creating .gitignore...")
        gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.production
.env.staging

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
frontend/dist/
frontend/build/

# Logs
logs/
*.log

# Chrome profiles and cache
chrome_profile/
chrome_profiles/
cache/

# Credentials and secrets
credentials.json
secrets.json
accounts.csv

# Browser automation
*.png
*.html
frame_*.html

# System files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Temporary files
temp/
tmp/
*.tmp

# Process files
*.pid
'''
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("✅ .gitignore created")
    
    # Get GitHub repository URL
    print("\n🔗 GitHub Repository Setup")
    print("-" * 30)
    
    # Check if remote origin exists
    success, output, _ = run_command("git remote get-url origin", cwd=project_root)
    if success and output.strip():
        repo_url = output.strip()
        print(f"✅ Remote origin already set: {repo_url}")
    else:
        print("📝 Please enter your GitHub repository URL:")
        print("   Format: https://github.com/YOUR_USERNAME/ai-trading-sentinel.git")
        print("   (Create repository on GitHub first if you haven't)")
        
        repo_url = input("🔗 Repository URL: ").strip()
        
        if not repo_url:
            print("❌ No repository URL provided")
            return False
        
        # Add remote origin
        success, _, error = run_command(f"git remote add origin {repo_url}", cwd=project_root)
        if not success:
            print(f"❌ Failed to add remote: {error}")
            # Try to set URL if remote already exists
            success, _, _ = run_command(f"git remote set-url origin {repo_url}", cwd=project_root)
            if success:
                print("✅ Remote origin URL updated")
            else:
                return False
        else:
            print("✅ Remote origin added")
    
    # Stage all files
    print("\n📦 Preparing files for commit...")
    success, _, error = run_command("git add .", cwd=project_root)
    if not success:
        print(f"❌ Failed to stage files: {error}")
        return False
    print("✅ Files staged")
    
    # Commit changes
    commit_message = "Initial commit - AI Trading Sentinel ready for deployment"
    success, _, error = run_command(f'git commit -m "{commit_message}"', cwd=project_root)
    if not success:
        if "nothing to commit" in error:
            print("✅ No changes to commit")
        else:
            print(f"❌ Failed to commit: {error}")
            return False
    else:
        print("✅ Changes committed")
    
    # Push to GitHub
    print("\n🚀 Pushing to GitHub...")
    success, _, error = run_command("git push -u origin main", cwd=project_root)
    if not success:
        # Try master branch if main fails
        success, _, error = run_command("git push -u origin master", cwd=project_root)
        if not success:
            print(f"❌ Failed to push: {error}")
            print("💡 You may need to:")
            print("   1. Create the repository on GitHub first")
            print("   2. Set up SSH keys or use personal access token")
            print("   3. Check your internet connection")
            return False
    
    print("✅ Code pushed to GitHub successfully!")
    
    # Extract username and repo name from URL
    try:
        if "github.com/" in repo_url:
            parts = repo_url.split("github.com/")[1].replace(".git", "").split("/")
            username = parts[0]
            repo_name = parts[1]
            
            print("\n" + "="*60)
            print("🎉 GITHUB SETUP COMPLETE!")
            print("="*60)
            print(f"📂 Repository: https://github.com/{username}/{repo_name}")
            print(f"🔗 Clone URL: {repo_url}")
            print("\n📋 Next Steps:")
            print("   1. Get your Contabo VPS IP address")
            print("   2. Run deployment script on VPS")
            print("   3. Upload your .env credentials")
            print("   4. Start trading!")
            print("\n💡 Use SIMPLE_DEPLOYMENT_GUIDE.md for step-by-step instructions")
            print("="*60)
            
            return True
    except:
        pass
    
    print("\n✅ GitHub setup complete!")
    print(f"🔗 Repository URL: {repo_url}")
    return True

def main():
    """Main function"""
    try:
        success = setup_github_repo()
        if success:
            print("\n🚀 Ready for deployment!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()