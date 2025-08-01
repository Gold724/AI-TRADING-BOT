import os
import logging
import subprocess
import requests
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('github_integration')

# Load environment variables
load_dotenv()

# GitHub configuration from environment variables
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_PAT = os.getenv('GITHUB_PAT')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# Status file for heartbeat integration
HEARTBEAT_STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'heartbeat_status.json')

def update_heartbeat_status(status, details=None):
    """
    Update the heartbeat status file with GitHub integration status
    """
    import json
    import datetime
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(HEARTBEAT_STATUS_FILE), exist_ok=True)
    
    # Read existing status if available
    if os.path.exists(HEARTBEAT_STATUS_FILE):
        try:
            with open(HEARTBEAT_STATUS_FILE, 'r') as f:
                status_data = json.load(f)
        except json.JSONDecodeError:
            status_data = {}
    else:
        status_data = {}
    
    # Update GitHub integration status
    status_data['github_integration'] = {
        'status': status,
        'timestamp': datetime.datetime.now().isoformat(),
        'details': details or {}
    }
    
    # Write updated status
    with open(HEARTBEAT_STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)

def validate_github_config():
    """
    Validate that all required GitHub configuration is present
    """
    if not GITHUB_USERNAME:
        logger.error("GITHUB_USERNAME not set in .env file")
        return False
    
    if not GITHUB_PAT:
        logger.error("GITHUB_PAT not set in .env file")
        return False
    
    if not GITHUB_REPO:
        logger.error("GITHUB_REPO not set in .env file")
        return False
    
    return True

def get_authenticated_repo_url():
    """
    Construct an authenticated GitHub repository URL using the PAT
    """
    if not validate_github_config():
        return None
    
    # Format: https://{username}:{pat}@github.com/{username}/{repo}.git
    return f"https://{GITHUB_USERNAME}:{GITHUB_PAT}@github.com/{GITHUB_USERNAME}/{GITHUB_REPO}.git"

def check_for_updates():
    """
    Check if there are any updates available in the GitHub repository
    Returns: (bool, str) - (updates_available, details)
    """
    try:
        # Ensure we're in a git repository
        repo_root = Path(__file__).parent.parent
        
        # Fetch the latest changes
        subprocess.run(['git', 'fetch'], cwd=repo_root, check=True, capture_output=True)
        
        # Get the current commit hash
        local_commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], 
            cwd=repo_root, 
            check=True, 
            capture_output=True, 
            text=True
        ).stdout.strip()
        
        # Get the remote commit hash
        remote_commit = subprocess.run(
            ['git', 'rev-parse', '@{u}'], 
            cwd=repo_root, 
            check=True, 
            capture_output=True, 
            text=True
        ).stdout.strip()
        
        # Compare the commits
        if local_commit != remote_commit:
            # Get the changes
            changes = subprocess.run(
                ['git', 'log', '--oneline', '--graph', '--decorate', '--pretty=format:%h %s (%cr) <%an>', 'HEAD..@{u}'],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            return True, changes
        
        return False, "Repository is up to date"
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.stderr}")
        update_heartbeat_status("error", {"error": f"Git command failed: {e.stderr}"})
        return False, f"Error: {e.stderr}"
    
    except Exception as e:
        logger.error(f"Failed to check for updates: {str(e)}")
        update_heartbeat_status("error", {"error": str(e)})
        return False, f"Error: {str(e)}"

def pull_updates():
    """
    Pull the latest updates from the GitHub repository
    Returns: (bool, str) - (success, details)
    """
    try:
        # Ensure we're in a git repository
        repo_root = Path(__file__).parent.parent
        
        # Pull the latest changes
        result = subprocess.run(
            ['git', 'pull'], 
            cwd=repo_root, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        update_heartbeat_status("updated", {"message": "Successfully pulled updates", "details": result.stdout})
        return True, result.stdout
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Git pull failed: {e.stderr}")
        update_heartbeat_status("error", {"error": f"Git pull failed: {e.stderr}"})
        return False, f"Error: {e.stderr}"
    
    except Exception as e:
        logger.error(f"Failed to pull updates: {str(e)}")
        update_heartbeat_status("error", {"error": str(e)})
        return False, f"Error: {str(e)}"

def clone_repository(target_dir):
    """
    Clone the GitHub repository to the specified directory
    Returns: (bool, str) - (success, details)
    """
    try:
        # Get the authenticated URL
        repo_url = get_authenticated_repo_url()
        if not repo_url:
            return False, "Failed to construct repository URL"
        
        # Create the target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Clone the repository
        result = subprocess.run(
            ['git', 'clone', repo_url, target_dir],
            check=True,
            capture_output=True,
            text=True
        )
        
        update_heartbeat_status("cloned", {"message": "Successfully cloned repository", "target_dir": target_dir})
        return True, result.stdout
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed: {e.stderr}")
        update_heartbeat_status("error", {"error": f"Git clone failed: {e.stderr}"})
        return False, f"Error: {e.stderr}"
    
    except Exception as e:
        logger.error(f"Failed to clone repository: {str(e)}")
        update_heartbeat_status("error", {"error": str(e)})
        return False, f"Error: {str(e)}"

def push_changes(commit_message):
    """
    Commit and push changes to the GitHub repository
    Returns: (bool, str) - (success, details)
    """
    try:
        # Ensure we're in a git repository
        repo_root = Path(__file__).parent.parent
        
        # Add all changes
        subprocess.run(
            ['git', 'add', '.'],
            cwd=repo_root,
            check=True,
            capture_output=True
        )
        
        # Commit changes
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        # If nothing to commit, return early
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            update_heartbeat_status("unchanged", {"message": "No changes to push"})
            return True, "No changes to push"
        
        # Push changes
        push_result = subprocess.run(
            ['git', 'push'],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True
        )
        
        update_heartbeat_status("pushed", {"message": "Successfully pushed changes", "commit_message": commit_message})
        return True, f"Commit: {commit_result.stdout}\nPush: {push_result.stdout}"
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Git push failed: {e.stderr}")
        update_heartbeat_status("error", {"error": f"Git push failed: {e.stderr}"})
        return False, f"Error: {e.stderr}"
    
    except Exception as e:
        logger.error(f"Failed to push changes: {str(e)}")
        update_heartbeat_status("error", {"error": str(e)})
        return False, f"Error: {str(e)}"

def create_github_issue(title, body, labels=None):
    """
    Create an issue in the GitHub repository
    Returns: (bool, str) - (success, details)
    """
    if not validate_github_config():
        return False, "GitHub configuration is invalid"
    
    try:
        # Prepare the API request
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/issues"
        headers = {
            "Authorization": f"token {GITHUB_PAT}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        
        # Send the request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        issue_data = response.json()
        issue_number = issue_data.get("number")
        issue_url = issue_data.get("html_url")
        
        update_heartbeat_status("issue_created", {
            "message": "Successfully created GitHub issue",
            "issue_number": issue_number,
            "issue_url": issue_url
        })
        
        return True, f"Created issue #{issue_number}: {issue_url}"
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create GitHub issue: {str(e)}")
        update_heartbeat_status("error", {"error": f"Failed to create GitHub issue: {str(e)}"})
        return False, f"Error: {str(e)}"

def sync_trading_results(results_file):
    """
    Sync trading results to the GitHub repository
    This can be used to backup trading results or share them with other instances
    Returns: (bool, str) - (success, details)
    """
    try:
        # Ensure the results file exists
        if not os.path.exists(results_file):
            return False, f"Results file not found: {results_file}"
        
        # Get the relative path from the repository root
        repo_root = Path(__file__).parent.parent
        relative_path = os.path.relpath(results_file, repo_root)
        
        # Add the file
        subprocess.run(
            ['git', 'add', relative_path],
            cwd=repo_root,
            check=True,
            capture_output=True
        )
        
        # Commit the file
        commit_message = f"Update trading results: {os.path.basename(results_file)}"
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        # If nothing to commit, return early
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            return True, "No changes to sync"
        
        # Push the changes
        push_result = subprocess.run(
            ['git', 'push'],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True
        )
        
        update_heartbeat_status("results_synced", {
            "message": "Successfully synced trading results",
            "file": relative_path
        })
        
        return True, f"Synced trading results: {relative_path}"
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Git sync failed: {e.stderr}")
        update_heartbeat_status("error", {"error": f"Git sync failed: {e.stderr}"})
        return False, f"Error: {e.stderr}"
    
    except Exception as e:
        logger.error(f"Failed to sync trading results: {str(e)}")
        update_heartbeat_status("error", {"error": str(e)})
        return False, f"Error: {str(e)}"

# Main function for testing
if __name__ == "__main__":
    print("GitHub Integration Module")
    print("=======================")
    
    if validate_github_config():
        print("✓ GitHub configuration is valid")
        
        # Check for updates
        updates_available, details = check_for_updates()
        if updates_available:
            print(f"! Updates available:\n{details}")
            
            # Ask if the user wants to pull updates
            response = input("Do you want to pull these updates? (y/n): ")
            if response.lower() == 'y':
                success, result = pull_updates()
                if success:
                    print(f"✓ Updates pulled successfully:\n{result}")
                else:
                    print(f"✗ Failed to pull updates:\n{result}")
        else:
            print(f"✓ {details}")
    else:
        print("✗ GitHub configuration is invalid. Please check your .env file.")