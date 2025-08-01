#!/usr/bin/env python3
"""
Contabo VPS Deployment Script for AI Trading Sentinel

This script automates the deployment of the AI Trading Sentinel to a Contabo VPS.
It handles SSH connection, file transfer, and remote command execution.

Usage:
    python deploy_to_contabo.py --ip <vps_ip> --password <vps_password> [--port <ssh_port>] [--env-file <path>] [--chrome-profile <path>]

Options:
    --ip              VPS IP address
    --password        VPS root password
    --port            SSH port (default: 22)
    --env-file        Path to .env file to upload (default: .env.example)
    --chrome-profile  Path to Chrome profile directory to upload (optional)
"""

import argparse
import os
import paramiko
import sys
import time
from pathlib import Path

# ANSI color codes for terminal output
COLORS = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m'
}

def print_colored(text, color):
    """Print colored text to terminal"""
    if os.name == 'nt':  # Windows doesn't support ANSI colors in cmd
        print(text)
    else:
        print(f"{COLORS[color]}{text}{COLORS['ENDC']}")

def print_step(step_num, total_steps, description):
    """Print a formatted step indicator"""
    print_colored(f"\n[{step_num}/{total_steps}] {description}", 'BLUE')
    print("-" * 50)

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy AI Trading Sentinel to Contabo VPS')
    parser.add_argument('--ip', required=True, help='VPS IP address')
    parser.add_argument('--password', required=True, help='VPS root password')
    parser.add_argument('--port', default=22, type=int, help='SSH port (default: 22)')
    parser.add_argument('--env-file', default='.env.example', help='Path to .env file to upload')
    parser.add_argument('--chrome-profile', help='Path to Chrome profile directory to upload (optional)')
    return parser.parse_args()

def create_ssh_client(ip, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {username}@{ip}:{port}...")
    
    # Try to connect with retry logic
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            client.connect(ip, port=port, username=username, password=password)
            print_colored(f"✅ Connected to {ip}", 'GREEN')
            return client
        except Exception as e:
            if attempt < max_retries:
                print_colored(f"⚠️ Connection attempt {attempt} failed: {e}", 'YELLOW')
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print_colored(f"❌ Failed to connect to {ip} after {max_retries} attempts: {e}", 'RED')
                sys.exit(1)

def execute_command(client, command, display=True):
    if display:
        print(f"🔄 Executing: {command}")
    
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    if display:
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output:
            print(output)
        
        if error:
            print_colored(f"⚠️ Error:\n{error}", 'YELLOW')
    
    return exit_status

def upload_file(client, local_path, remote_path):
    try:
        sftp = client.open_sftp()
        print(f"Uploading {local_path} to {remote_path}...")
        sftp.put(local_path, remote_path)
        sftp.close()
        print_colored(f"✅ Uploaded {local_path}", 'GREEN')
        return True
    except Exception as e:
        print_colored(f"❌ Failed to upload {local_path}: {e}", 'RED')
        return False

def upload_directory(client, local_dir, remote_dir):
    """Upload a directory recursively to the remote server"""
    try:
        sftp = client.open_sftp()
        local_path = Path(local_dir)
        
        # Create remote directory if it doesn't exist
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass  # Directory might already exist
        
        # Upload all files and subdirectories
        for item in local_path.glob('**/*'):
            if item.is_file():
                relative_path = item.relative_to(local_path)
                remote_file_path = f"{remote_dir}/{relative_path}".replace('\\', '/')
                
                # Create parent directories if they don't exist
                remote_parent = str(Path(remote_file_path).parent).replace('\\', '/')
                try:
                    sftp.stat(remote_parent)
                except IOError:
                    # Create all parent directories
                    current_dir = Path(remote_dir)
                    for part in Path(relative_path).parent.parts:
                        current_dir = current_dir / part
                        try:
                            sftp.mkdir(str(current_dir).replace('\\', '/'))
                        except IOError:
                            pass  # Directory might already exist
                
                print(f"Uploading {item} to {remote_file_path}...")
                sftp.put(str(item), remote_file_path)
        
        sftp.close()
        print_colored(f"✅ Uploaded directory {local_dir}", 'GREEN')
        return True
    except Exception as e:
        print_colored(f"❌ Failed to upload directory {local_dir}: {e}", 'RED')
        return False

def setup_vps(client):
    print_step(1, 5, "Setting up VPS environment")
    
    # Upload setup script
    script_path = Path(__file__).parent / 'sentinel_vps_setup.sh'
    if not script_path.exists():
        print_colored("❌ sentinel_vps_setup.sh not found in the current directory", 'RED')
        return False
    
    if not upload_file(client, str(script_path), '/root/sentinel_vps_setup.sh'):
        return False
    
    # Make script executable and run it
    execute_command(client, 'chmod +x /root/sentinel_vps_setup.sh')
    exit_status = execute_command(client, '/root/sentinel_vps_setup.sh')
    
    if exit_status != 0:
        print_colored("❌ VPS setup failed", 'RED')
        return False
    
    print_colored("✅ VPS environment setup completed", 'GREEN')
    return True

def upload_project_files(client, env_file, chrome_profile=None):
    print_step(2, 5, "Uploading project files")
    
    # Create project directory
    execute_command(client, 'mkdir -p /root/ai-trading-sentinel')
    
    # Upload project files
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if not upload_directory(client, project_dir, '/root/ai-trading-sentinel'):
        return False
    
    # Upload .env file
    if os.path.exists(env_file):
        if not upload_file(client, env_file, '/root/ai-trading-sentinel/.env'):
            return False
    else:
        print_colored(f"⚠️ {env_file} not found, using default .env.example", 'YELLOW')
        # Create a basic .env file on the remote server
        execute_command(client, 'cd /root/ai-trading-sentinel && cp .env.example .env')
    
    # Upload Chrome profile if provided
    if chrome_profile:
        print("Uploading Chrome profile (this may take a while)...")
        chrome_profile_dir = '/root/.config/google-chrome/Default'
        execute_command(client, f'mkdir -p {chrome_profile_dir}')
        if not upload_directory(client, chrome_profile, chrome_profile_dir):
            print_colored("⚠️ Failed to upload Chrome profile. Continuing without it.", 'YELLOW')
    
    print_colored("✅ Project files uploaded successfully", 'GREEN')
    return True

def install_dependencies(client):
    print_step(3, 5, "Installing Python dependencies")
    
    # Install Python dependencies
    exit_status = execute_command(client, 'cd /root/ai-trading-sentinel && pip3 install -r requirements.txt')
    
    if exit_status != 0:
        print_colored("❌ Failed to install Python dependencies", 'RED')
        return False
    
    print_colored("✅ Python dependencies installed successfully", 'GREEN')
    return True

def configure_environment(client):
    print_step(4, 5, "Configuring environment")
    
    # Create logs directory
    execute_command(client, 'mkdir -p /root/ai-trading-sentinel/logs')
    
    # Set permissions
    execute_command(client, 'chmod +x /root/ai-trading-sentinel/*.py')
    
    print_colored("✅ Environment configured successfully", 'GREEN')
    return True

def start_trading_sentinel(client):
    print_step(5, 5, "Starting AI Trading Sentinel")
    
    # Install tmux if not already installed
    execute_command(client, 'apt-get install -y tmux')
    
    # Kill existing tmux session if it exists
    execute_command(client, 'tmux kill-session -t trading_sentinel 2>/dev/null || true', display=False)
    
    # Start a new tmux session
    execute_command(client, 'tmux new-session -d -s trading_sentinel "cd /root/ai-trading-sentinel && python3 heartbeat.py"')
    
    # Check if the session is running
    exit_status = execute_command(client, 'tmux has-session -t trading_sentinel', display=False)
    
    if exit_status != 0:
        print_colored("❌ Failed to start trading sentinel", 'RED')
        return False
    
    print_colored("✅ AI Trading Sentinel started successfully in tmux session 'trading_sentinel'", 'GREEN')
    return True

def main():
    args = parse_args()
    
    print_colored("\n====================================", 'HEADER')
    print_colored("AI Trading Sentinel - Contabo VPS Deployment", 'HEADER')
    print_colored("====================================", 'HEADER')
    print()
    
    # Connect to VPS
    client = create_ssh_client(args.ip, args.port, 'root', args.password)
    
    # Deploy the trading sentinel
    if setup_vps(client) and \
       upload_project_files(client, args.env_file, args.chrome_profile) and \
       install_dependencies(client) and \
       configure_environment(client) and \
       start_trading_sentinel(client):
        print_colored("\n====================================", 'HEADER')
        print_colored("Deployment Completed Successfully!", 'HEADER')
        print_colored("====================================", 'HEADER')
        print(f"\nYour AI Trading Sentinel is now running on {args.ip}")
        print("\nTo monitor the application:")
        print(f"1. SSH into your VPS: ssh root@{args.ip}")
        print("2. Attach to the tmux session: tmux attach -t trading_sentinel")
        print("3. To detach from the session: Press Ctrl+B, then D")
    else:
        print_colored("\n====================================", 'HEADER')
        print_colored("Deployment Failed", 'RED')
        print_colored("====================================", 'HEADER')
        print("Please check the error messages above and try again.")
    
    # Close SSH connection
    client.close()

if __name__ == "__main__":
    main()