#!/usr/bin/env python3
"""
Simple GitHub Setup for AI Trading Sentinel
Handles Windows encoding issues properly
"""

import os
import sys
import subprocess

def run_git_command(cmd):
    """Run git command with proper encoding handling"""
    try:
        # Use git directly with proper encoding
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def main():
    print("🐙 AI Trading Sentinel - Simple GitHub Setup")
    print("=" * 50)
    
    # Check if git is installed
    success, _, _ = run_git_command("git --version")
    if not success:
        print("❌ Git is not installed. Please install Git first.")
        return False
    print("✅ Git is installed")
    
    # Check if already a git repository
    if not os.path.exists(".git"):
        print("📁 Initializing Git repository...")
        success, _, error = run_git_command("git init")
        if not success:
            print(f"❌ Failed to initialize repository: {error}")
            return False
        print("✅ Git repository initialized")
    else:
        print("✅ Already a Git repository")
    
    # Check remote origin
    success, output, _ = run_git_command("git remote get-url origin")
    if success:
        print(f"✅ Remote origin: {output}")
    else:
        print("⚠️  No remote origin set")
        print("Please set your GitHub repository URL:")
        print("git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
        return False
    
    # Add all files
    print("\n📦 Adding files...")
    success, _, error = run_git_command("git add .")
    if not success:
        print(f"❌ Failed to add files: {error}")
        return False
    print("✅ Files added")
    
    # Commit changes
    print("\n💾 Committing changes...")
    commit_msg = "Update AI Trading Sentinel with cloud deployment files"
    success, output, error = run_git_command(f'git commit -m "{commit_msg}"')
    if not success:
        if "nothing to commit" in error:
            print("✅ No changes to commit (already up to date)")
        else:
            print(f"❌ Failed to commit: {error}")
            return False
    else:
        print("✅ Changes committed")
    
    # Push to GitHub
    print("\n🚀 Pushing to GitHub...")
    success, output, error = run_git_command("git push origin main")
    if not success:
        # Try master branch if main fails
        success, output, error = run_git_command("git push origin master")
        if not success:
            print(f"❌ Failed to push: {error}")
            print("\n💡 Manual push required:")
            print("git push origin main")
            print("or")
            print("git push origin master")
            return False
    
    print("✅ Successfully pushed to GitHub!")
    
    # Get repository URL
    success, repo_url, _ = run_git_command("git remote get-url origin")
    if success:
        print(f"\n🔗 Repository URL: {repo_url}")
        print("\n🎉 GitHub setup complete!")
        print("\nNext steps:")
        print("1. Get your Contabo VPS IP address")
        print("2. Run: python deploy_no_domain.py")
        print("3. Follow the deployment guide")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)