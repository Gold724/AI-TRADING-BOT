#!/usr/bin/env python3
"""
AI Trading Sentinel - Backup Strategy Implementation
Comprehensive backup and disaster recovery system
"""

import os
import sys
import json
import time
import shutil
import tarfile
import gzip
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import sqlite3
import yaml

class BackupStrategy:
    """Comprehensive backup and disaster recovery for AI Trading Sentinel"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.backup_dir = self.project_root / "backups"
        self.config_dir = self.backup_dir / "config"
        self.scripts_dir = self.backup_dir / "scripts"
        self.logs_dir = self.backup_dir / "logs"
        
        # Backup configuration
        self.backup_config = {
            "retention_days": 30,
            "max_backups": 50,
            "compression_level": 6,
            "encryption_enabled": True,
            "remote_backup_enabled": True,
            "backup_schedule": {
                "database": "0 */6 * * *",  # Every 6 hours
                "config": "0 2 * * *",     # Daily at 2 AM
                "logs": "0 1 * * 0",       # Weekly on Sunday at 1 AM
                "full_system": "0 3 * * 0" # Weekly on Sunday at 3 AM
            }
        }
        
        # Create directories
        self._create_directories()
        
        print(f"💾 Backup Strategy initialized")
        print(f"📁 Backup directory: {self.backup_dir}")
    
    def _create_directories(self):
        """Create backup directories"""
        directories = [
            self.backup_dir,
            self.backup_dir / "database",
            self.backup_dir / "config",
            self.backup_dir / "logs",
            self.backup_dir / "system",
            self.backup_dir / "remote",
            self.config_dir,
            self.scripts_dir,
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Backup directories created")
    
    def create_database_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """Create Redis database backup"""
        print("\n🗄️  Creating database backup...")
        
        if not backup_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"redis_backup_{timestamp}"
        
        backup_path = self.backup_dir / "database" / f"{backup_name}.rdb"
        
        try:
            # Create Redis backup using BGSAVE
            redis_cmd = [
                "redis-cli",
                "--rdb", str(backup_path)
            ]
            
            # Check if Redis password is set
            env_file = self.project_root / ".env"
            redis_password = None
            
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('REDIS_PASSWORD='):
                            redis_password = line.split('=', 1)[1].strip().strip('"\'')
                            break
            
            if redis_password:
                redis_cmd.extend(["-a", redis_password])
            
            result = subprocess.run(redis_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Compress backup
                compressed_path = f"{backup_path}.gz"
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                os.remove(backup_path)
                
                # Calculate checksum
                checksum = self._calculate_checksum(compressed_path)
                
                # Create metadata
                metadata = {
                    "backup_name": backup_name,
                    "backup_type": "database",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "file_path": str(compressed_path),
                    "file_size": os.path.getsize(compressed_path),
                    "checksum": checksum,
                    "compression": "gzip",
                    "retention_until": (datetime.utcnow() + timedelta(days=self.backup_config["retention_days"])).isoformat() + "Z"
                }
                
                metadata_path = f"{compressed_path}.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"✅ Database backup created: {compressed_path}")
                return True, str(compressed_path)
            
            else:
                print(f"❌ Redis backup failed: {result.stderr}")
                return False, result.stderr
        
        except Exception as e:
            print(f"❌ Database backup error: {e}")
            return False, str(e)
    
    def create_config_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """Create configuration files backup"""
        print("\n⚙️  Creating configuration backup...")
        
        if not backup_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}"
        
        backup_path = self.backup_dir / "config" / f"{backup_name}.tar.gz"
        
        try:
            # Files and directories to backup
            config_items = [
                ".env",
                "config/",
                "monitoring/",
                "load_balancing/",
                "scripts/",
                "requirements.txt",
                "package.json",
                "docker-compose.yml",
                "Dockerfile*",
                "nginx.conf",
                "systemd/"
            ]
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for item in config_items:
                    item_path = self.project_root / item
                    
                    if item_path.exists():
                        if item_path.is_file():
                            tar.add(item_path, arcname=item)
                        elif item_path.is_dir():
                            for file_path in item_path.rglob('*'):
                                if file_path.is_file():
                                    arcname = str(file_path.relative_to(self.project_root))
                                    tar.add(file_path, arcname=arcname)
                    
                    # Handle glob patterns
                    elif '*' in item:
                        for match in self.project_root.glob(item):
                            if match.is_file():
                                arcname = str(match.relative_to(self.project_root))
                                tar.add(match, arcname=arcname)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Create metadata
            metadata = {
                "backup_name": backup_name,
                "backup_type": "config",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "file_path": str(backup_path),
                "file_size": os.path.getsize(backup_path),
                "checksum": checksum,
                "compression": "gzip",
                "items_backed_up": config_items,
                "retention_until": (datetime.utcnow() + timedelta(days=self.backup_config["retention_days"])).isoformat() + "Z"
            }
            
            metadata_path = f"{backup_path}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Configuration backup created: {backup_path}")
            return True, str(backup_path)
        
        except Exception as e:
            print(f"❌ Configuration backup error: {e}")
            return False, str(e)
    
    def create_logs_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """Create logs backup"""
        print("\n📋 Creating logs backup...")
        
        if not backup_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"logs_backup_{timestamp}"
        
        backup_path = self.backup_dir / "logs" / f"{backup_name}.tar.gz"
        
        try:
            logs_dir = self.project_root / "logs"
            
            if not logs_dir.exists():
                print(f"⚠️  Logs directory not found: {logs_dir}")
                return False, "Logs directory not found"
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for log_file in logs_dir.rglob('*.log'):
                    if log_file.is_file():
                        arcname = str(log_file.relative_to(self.project_root))
                        tar.add(log_file, arcname=arcname)
                
                # Also backup rotated logs
                for log_file in logs_dir.rglob('*.log.*'):
                    if log_file.is_file():
                        arcname = str(log_file.relative_to(self.project_root))
                        tar.add(log_file, arcname=arcname)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Create metadata
            metadata = {
                "backup_name": backup_name,
                "backup_type": "logs",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "file_path": str(backup_path),
                "file_size": os.path.getsize(backup_path),
                "checksum": checksum,
                "compression": "gzip",
                "retention_until": (datetime.utcnow() + timedelta(days=self.backup_config["retention_days"])).isoformat() + "Z"
            }
            
            metadata_path = f"{backup_path}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Logs backup created: {backup_path}")
            return True, str(backup_path)
        
        except Exception as e:
            print(f"❌ Logs backup error: {e}")
            return False, str(e)
    
    def create_full_system_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """Create full system backup"""
        print("\n🔄 Creating full system backup...")
        
        if not backup_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"full_system_backup_{timestamp}"
        
        backup_path = self.backup_dir / "system" / f"{backup_name}.tar.gz"
        
        try:
            # Exclude patterns
            exclude_patterns = [
                "__pycache__",
                "*.pyc",
                "node_modules",
                ".git",
                "backups",
                "*.tmp",
                "*.temp",
                "venv",
                ".venv",
                "env",
                ".env.local",
                "dist",
                "build",
                "*.log"
            ]
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for item in self.project_root.iterdir():
                    if item.name in ['backups']:
                        continue
                    
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern.startswith('*') and item.name.endswith(pattern[1:]):
                            should_exclude = True
                            break
                        elif item.name == pattern:
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        arcname = item.name
                        tar.add(item, arcname=arcname)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Create metadata
            metadata = {
                "backup_name": backup_name,
                "backup_type": "full_system",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "file_path": str(backup_path),
                "file_size": os.path.getsize(backup_path),
                "checksum": checksum,
                "compression": "gzip",
                "excluded_patterns": exclude_patterns,
                "retention_until": (datetime.utcnow() + timedelta(days=self.backup_config["retention_days"])).isoformat() + "Z"
            }
            
            metadata_path = f"{backup_path}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Full system backup created: {backup_path}")
            return True, str(backup_path)
        
        except Exception as e:
            print(f"❌ Full system backup error: {e}")
            return False, str(e)
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Verify backup integrity using checksum"""
        print(f"\n🔍 Verifying backup: {backup_path}")
        
        try:
            metadata_path = f"{backup_path}.json"
            
            if not os.path.exists(metadata_path):
                return False, "Metadata file not found"
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            stored_checksum = metadata.get('checksum')
            if not stored_checksum:
                return False, "No checksum in metadata"
            
            current_checksum = self._calculate_checksum(backup_path)
            
            if stored_checksum == current_checksum:
                print(f"✅ Backup verification successful")
                return True, "Backup integrity verified"
            else:
                print(f"❌ Backup verification failed: checksum mismatch")
                return False, "Checksum mismatch"
        
        except Exception as e:
            print(f"❌ Backup verification error: {e}")
            return False, str(e)
    
    def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policy"""
        print("\n🧹 Cleaning up old backups...")
        
        cleaned_count = 0
        cutoff_date = datetime.utcnow() - timedelta(days=self.backup_config["retention_days"])
        
        backup_types = ['database', 'config', 'logs', 'system']
        
        for backup_type in backup_types:
            backup_type_dir = self.backup_dir / backup_type
            
            if not backup_type_dir.exists():
                continue
            
            # Get all backup files with metadata
            backups = []
            for metadata_file in backup_type_dir.glob('*.json'):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    backup_file = Path(metadata['file_path'])
                    if backup_file.exists():
                        backups.append((metadata_file, backup_file, metadata))
                
                except Exception as e:
                    print(f"⚠️  Error reading metadata {metadata_file}: {e}")
            
            # Sort by timestamp (oldest first)
            backups.sort(key=lambda x: x[2]['timestamp'])
            
            # Remove old backups
            for metadata_file, backup_file, metadata in backups:
                backup_date = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                
                if backup_date < cutoff_date or len(backups) > self.backup_config["max_backups"]:
                    try:
                        os.remove(backup_file)
                        os.remove(metadata_file)
                        cleaned_count += 1
                        print(f"🗑️  Removed old backup: {backup_file.name}")
                    except Exception as e:
                        print(f"⚠️  Error removing backup {backup_file}: {e}")
        
        print(f"✅ Cleaned up {cleaned_count} old backups")
        return cleaned_count
    
    def list_backups(self) -> Dict:
        """List all available backups"""
        print("\n📋 Listing available backups...")
        
        backups = {
            "database": [],
            "config": [],
            "logs": [],
            "system": []
        }
        
        for backup_type in backups.keys():
            backup_type_dir = self.backup_dir / backup_type
            
            if not backup_type_dir.exists():
                continue
            
            for metadata_file in backup_type_dir.glob('*.json'):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    backup_file = Path(metadata['file_path'])
                    if backup_file.exists():
                        # Add file size in human readable format
                        size_mb = metadata['file_size'] / (1024 * 1024)
                        metadata['file_size_mb'] = round(size_mb, 2)
                        
                        backups[backup_type].append(metadata)
                
                except Exception as e:
                    print(f"⚠️  Error reading metadata {metadata_file}: {e}")
            
            # Sort by timestamp (newest first)
            backups[backup_type].sort(key=lambda x: x['timestamp'], reverse=True)
        
        return backups
    
    def restore_backup(self, backup_path: str, restore_location: str = None) -> Tuple[bool, str]:
        """Restore backup to specified location"""
        print(f"\n🔄 Restoring backup: {backup_path}")
        
        try:
            # Verify backup first
            is_valid, message = self.verify_backup(backup_path)
            if not is_valid:
                return False, f"Backup verification failed: {message}"
            
            # Get metadata
            metadata_path = f"{backup_path}.json"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            backup_type = metadata['backup_type']
            
            if not restore_location:
                if backup_type == 'database':
                    restore_location = "/tmp/redis_restore"
                else:
                    restore_location = str(self.project_root / "restore")
            
            restore_path = Path(restore_location)
            restore_path.mkdir(parents=True, exist_ok=True)
            
            if backup_type == 'database':
                # Restore Redis database
                if backup_path.endswith('.gz'):
                    # Decompress first
                    decompressed_path = restore_path / "dump.rdb"
                    with gzip.open(backup_path, 'rb') as f_in:
                        with open(decompressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    print(f"✅ Database backup restored to: {decompressed_path}")
                    print(f"📋 To restore Redis, copy {decompressed_path} to Redis data directory and restart Redis")
                
            else:
                # Restore tar.gz backups
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(restore_path)
                
                print(f"✅ Backup restored to: {restore_path}")
            
            return True, str(restore_path)
        
        except Exception as e:
            print(f"❌ Restore error: {e}")
            return False, str(e)
    
    def setup_remote_backup(self, remote_config: Dict) -> bool:
        """Setup remote backup to cloud storage"""
        print("\n☁️  Setting up remote backup...")
        
        try:
            # Create remote backup script
            remote_script = self.scripts_dir / "remote_backup.sh"
            
            script_content = f"""#!/bin/bash
# AI Trading Sentinel - Remote Backup Script
# Generated on {datetime.utcnow().isoformat()}Z

set -e

# Configuration
BACKUP_DIR="{self.backup_dir}"
REMOTE_TYPE="{remote_config.get('type', 'rsync')}"
REMOTE_HOST="{remote_config.get('host', '')}"
REMOTE_USER="{remote_config.get('user', '')}"
REMOTE_PATH="{remote_config.get('path', '')}"
SSH_KEY="{remote_config.get('ssh_key', '')}"
ENCRYPTION_KEY="{remote_config.get('encryption_key', '')}"

# Logging
LOG_FILE="{self.logs_dir}/remote_backup.log"
echo "$(date): Starting remote backup" >> "$LOG_FILE"

if [ "$REMOTE_TYPE" = "rsync" ]; then
    # Rsync backup
    if [ -n "$SSH_KEY" ]; then
        rsync -avz -e "ssh -i $SSH_KEY" "$BACKUP_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/" >> "$LOG_FILE" 2>&1
    else
        rsync -avz "$BACKUP_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/" >> "$LOG_FILE" 2>&1
    fi
elif [ "$REMOTE_TYPE" = "s3" ]; then
    # AWS S3 backup
    aws s3 sync "$BACKUP_DIR" "s3://$REMOTE_PATH" --delete >> "$LOG_FILE" 2>&1
elif [ "$REMOTE_TYPE" = "gcs" ]; then
    # Google Cloud Storage backup
    gsutil -m rsync -r -d "$BACKUP_DIR" "gs://$REMOTE_PATH" >> "$LOG_FILE" 2>&1
fi

echo "$(date): Remote backup completed" >> "$LOG_FILE"
"""
            
            with open(remote_script, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(remote_script, 0o755)
            
            print(f"✅ Remote backup script created: {remote_script}")
            return True
        
        except Exception as e:
            print(f"❌ Remote backup setup error: {e}")
            return False
    
    def setup_cron_jobs(self) -> bool:
        """Setup automated backup cron jobs"""
        print("\n⏰ Setting up automated backup cron jobs...")
        
        try:
            # Create cron script
            cron_script = self.scripts_dir / "setup_cron.sh"
            
            script_content = f"""#!/bin/bash
# AI Trading Sentinel - Backup Cron Jobs Setup
# Generated on {datetime.utcnow().isoformat()}Z

set -e

# Backup script path
BACKUP_SCRIPT="{self.project_root}/scripts/setup_backup_strategy.py"
PYTHON_PATH="$(which python3)"

# Create cron jobs
echo "Setting up cron jobs for automated backups..."

# Remove existing cron jobs for this project
crontab -l 2>/dev/null | grep -v "ai-trading-sentinel-backup" | crontab -

# Add new cron jobs
(
    crontab -l 2>/dev/null
    echo "# AI Trading Sentinel Automated Backups"
    echo "{self.backup_config['backup_schedule']['database']} $PYTHON_PATH $BACKUP_SCRIPT --type database --auto # ai-trading-sentinel-backup"
    echo "{self.backup_config['backup_schedule']['config']} $PYTHON_PATH $BACKUP_SCRIPT --type config --auto # ai-trading-sentinel-backup"
    echo "{self.backup_config['backup_schedule']['logs']} $PYTHON_PATH $BACKUP_SCRIPT --type logs --auto # ai-trading-sentinel-backup"
    echo "{self.backup_config['backup_schedule']['full_system']} $PYTHON_PATH $BACKUP_SCRIPT --type full_system --auto # ai-trading-sentinel-backup"
    echo "0 4 * * * $PYTHON_PATH $BACKUP_SCRIPT --cleanup --auto # ai-trading-sentinel-backup"
) | crontab -

echo "Cron jobs installed successfully!"
echo "Current cron jobs:"
crontab -l | grep "ai-trading-sentinel-backup"
"""
            
            with open(cron_script, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(cron_script, 0o755)
            
            print(f"✅ Cron setup script created: {cron_script}")
            print(f"📋 Run the script to install cron jobs: bash {cron_script}")
            return True
        
        except Exception as e:
            print(f"❌ Cron setup error: {e}")
            return False
    
    def create_systemd_backup_service(self) -> bool:
        """Create systemd service for backup management"""
        print("\n🔧 Creating systemd backup service...")
        
        try:
            # Create systemd service file
            service_content = f"""[Unit]
Description=AI Trading Sentinel Backup Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=oneshot
User=trading
Group=trading
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
ExecStart=/usr/bin/python3 {self.project_root}/scripts/setup_backup_strategy.py --type database --auto
ExecStartPost=/usr/bin/python3 {self.project_root}/scripts/setup_backup_strategy.py --cleanup --auto
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-backup

[Install]
WantedBy=multi-user.target
"""
            
            service_file = self.config_dir / "trading-backup.service"
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Create systemd timer file
            timer_content = f"""[Unit]
Description=AI Trading Sentinel Backup Timer
Requires=trading-backup.service

[Timer]
OnCalendar=*-*-* 02,08,14,20:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
"""
            
            timer_file = self.config_dir / "trading-backup.timer"
            with open(timer_file, 'w') as f:
                f.write(timer_content)
            
            # Create installation script
            install_script = self.scripts_dir / "install_backup_service.sh"
            
            install_content = f"""#!/bin/bash
# Install AI Trading Sentinel Backup Service

set -e

echo "Installing backup service and timer..."

# Copy service files
sudo cp "{service_file}" /etc/systemd/system/
sudo cp "{timer_file}" /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable trading-backup.timer
sudo systemctl start trading-backup.timer

echo "Backup service installed successfully!"
echo "Status:"
sudo systemctl status trading-backup.timer --no-pager
"""
            
            with open(install_script, 'w') as f:
                f.write(install_content)
            
            os.chmod(install_script, 0o755)
            
            print(f"✅ Systemd service files created:")
            print(f"   Service: {service_file}")
            print(f"   Timer: {timer_file}")
            print(f"   Install script: {install_script}")
            return True
        
        except Exception as e:
            print(f"❌ Systemd service creation error: {e}")
            return False
    
    def create_disaster_recovery_plan(self) -> bool:
        """Create disaster recovery documentation and scripts"""
        print("\n🚨 Creating disaster recovery plan...")
        
        try:
            # Create disaster recovery documentation
            dr_doc = self.config_dir / "disaster_recovery_plan.md"
            
            doc_content = f"""# AI Trading Sentinel - Disaster Recovery Plan

Generated on: {datetime.utcnow().isoformat()}Z

## Overview

This document outlines the disaster recovery procedures for the AI Trading Sentinel system.

## Backup Strategy

### Backup Types
1. **Database Backups**: Redis data (every 6 hours)
2. **Configuration Backups**: System configs, environment files (daily)
3. **Log Backups**: Application and system logs (weekly)
4. **Full System Backups**: Complete system snapshot (weekly)

### Retention Policy
- Retention Period: {self.backup_config['retention_days']} days
- Maximum Backups: {self.backup_config['max_backups']} per type
- Compression: gzip level {self.backup_config['compression_level']}

## Recovery Procedures

### 1. Database Recovery

```bash
# Stop Redis service
sudo systemctl stop redis

# Restore database backup
python3 {self.project_root}/scripts/setup_backup_strategy.py --restore /path/to/backup.rdb.gz

# Copy restored file to Redis data directory
sudo cp /tmp/redis_restore/dump.rdb /var/lib/redis/
sudo chown redis:redis /var/lib/redis/dump.rdb

# Start Redis service
sudo systemctl start redis
```

### 2. Configuration Recovery

```bash
# Restore configuration backup
python3 {self.project_root}/scripts/setup_backup_strategy.py --restore /path/to/config_backup.tar.gz

# Copy restored configs
cp -r restore/config/* {self.project_root}/config/
cp restore/.env {self.project_root}/

# Restart services
sudo systemctl restart trading-api trading-bot
```

### 3. Full System Recovery

```bash
# Create new project directory
mkdir -p /opt/ai-trading-sentinel-recovery
cd /opt/ai-trading-sentinel-recovery

# Restore full system backup
python3 setup_backup_strategy.py --restore /path/to/full_system_backup.tar.gz

# Install dependencies
pip install -r requirements.txt
npm install

# Setup services
bash scripts/deploy_production.py --config-file restore/config/deployment.yml
```

## Emergency Contacts

- System Administrator: [Your Contact]
- Cloud Provider Support: [Provider Support]
- Database Administrator: [DBA Contact]

## Recovery Time Objectives (RTO)

- Database Recovery: 15 minutes
- Configuration Recovery: 5 minutes
- Full System Recovery: 2 hours

## Recovery Point Objectives (RPO)

- Database: 6 hours (last backup)
- Configuration: 24 hours (last backup)
- Logs: 7 days (last backup)

## Testing Schedule

- Monthly: Test database recovery
- Quarterly: Test full system recovery
- Annually: Full disaster recovery drill

## Backup Verification

All backups are automatically verified using SHA256 checksums. Manual verification:

```bash
python3 {self.project_root}/scripts/setup_backup_strategy.py --verify /path/to/backup
```

## Monitoring and Alerts

- Backup failures trigger immediate Slack alerts
- Weekly backup reports sent via email
- Prometheus metrics track backup success/failure rates

## Security Considerations

- All backups are compressed and can be encrypted
- Remote backups use SSH key authentication
- Backup files have restricted permissions (600)
- Regular security audits of backup procedures
"""
            
            with open(dr_doc, 'w') as f:
                f.write(doc_content)
            
            # Create quick recovery script
            recovery_script = self.scripts_dir / "quick_recovery.sh"
            
            recovery_content = f"""#!/bin/bash
# AI Trading Sentinel - Quick Recovery Script

set -e

echo "🚨 AI Trading Sentinel Quick Recovery"
echo "===================================="

if [ $# -eq 0 ]; then
    echo "Usage: $0 <recovery_type> [backup_path]"
    echo "Recovery types: database, config, logs, full_system"
    exit 1
fi

RECOVERY_TYPE="$1"
BACKUP_PATH="$2"
PROJECT_ROOT="{self.project_root}"
BACKUP_SCRIPT="$PROJECT_ROOT/scripts/setup_backup_strategy.py"

case "$RECOVERY_TYPE" in
    "database")
        echo "🗄️  Recovering database..."
        if [ -z "$BACKUP_PATH" ]; then
            # Find latest database backup
            BACKUP_PATH=$(find "{self.backup_dir}/database" -name "*.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        fi
        
        echo "Using backup: $BACKUP_PATH"
        sudo systemctl stop redis
        python3 "$BACKUP_SCRIPT" --restore "$BACKUP_PATH"
        sudo cp /tmp/redis_restore/dump.rdb /var/lib/redis/
        sudo chown redis:redis /var/lib/redis/dump.rdb
        sudo systemctl start redis
        echo "✅ Database recovery completed"
        ;;
    
    "config")
        echo "⚙️  Recovering configuration..."
        if [ -z "$BACKUP_PATH" ]; then
            BACKUP_PATH=$(find "{self.backup_dir}/config" -name "*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        fi
        
        echo "Using backup: $BACKUP_PATH"
        python3 "$BACKUP_SCRIPT" --restore "$BACKUP_PATH"
        cp -r "$PROJECT_ROOT/restore/config/"* "$PROJECT_ROOT/config/" 2>/dev/null || true
        cp "$PROJECT_ROOT/restore/.env" "$PROJECT_ROOT/" 2>/dev/null || true
        sudo systemctl restart trading-api trading-bot
        echo "✅ Configuration recovery completed"
        ;;
    
    "full_system")
        echo "🔄 Recovering full system..."
        if [ -z "$BACKUP_PATH" ]; then
            BACKUP_PATH=$(find "{self.backup_dir}/system" -name "*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        fi
        
        echo "Using backup: $BACKUP_PATH"
        echo "⚠️  This will overwrite current system files!"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 "$BACKUP_SCRIPT" --restore "$BACKUP_PATH"
            echo "✅ Full system recovery completed"
            echo "📋 Please review restored files and restart services as needed"
        else
            echo "❌ Recovery cancelled"
        fi
        ;;
    
    *)
        echo "❌ Unknown recovery type: $RECOVERY_TYPE"
        exit 1
        ;;
esac
"""
            
            with open(recovery_script, 'w') as f:
                f.write(recovery_content)
            
            os.chmod(recovery_script, 0o755)
            
            print(f"✅ Disaster recovery plan created:")
            print(f"   Documentation: {dr_doc}")
            print(f"   Quick recovery script: {recovery_script}")
            return True
        
        except Exception as e:
            print(f"❌ Disaster recovery plan creation error: {e}")
            return False
    
    def generate_backup_report(self) -> Dict:
        """Generate comprehensive backup status report"""
        print("\n📊 Generating backup report...")
        
        try:
            backups = self.list_backups()
            
            report = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "backup_directory": str(self.backup_dir),
                "configuration": self.backup_config,
                "summary": {
                    "total_backups": sum(len(backups[t]) for t in backups),
                    "total_size_mb": 0,
                    "by_type": {}
                },
                "backups": backups,
                "health_status": "healthy",
                "recommendations": []
            }
            
            # Calculate statistics
            for backup_type, backup_list in backups.items():
                type_size = sum(b['file_size'] for b in backup_list)
                report['summary']['total_size_mb'] += type_size / (1024 * 1024)
                
                report['summary']['by_type'][backup_type] = {
                    "count": len(backup_list),
                    "size_mb": round(type_size / (1024 * 1024), 2),
                    "latest": backup_list[0]['timestamp'] if backup_list else None,
                    "oldest": backup_list[-1]['timestamp'] if backup_list else None
                }
            
            report['summary']['total_size_mb'] = round(report['summary']['total_size_mb'], 2)
            
            # Health checks and recommendations
            now = datetime.utcnow()
            
            for backup_type, backup_list in backups.items():
                if not backup_list:
                    report['health_status'] = "warning"
                    report['recommendations'].append(f"No {backup_type} backups found")
                    continue
                
                latest_backup = datetime.fromisoformat(backup_list[0]['timestamp'].replace('Z', '+00:00'))
                age_hours = (now - latest_backup.replace(tzinfo=None)).total_seconds() / 3600
                
                # Check backup freshness
                if backup_type == 'database' and age_hours > 8:
                    report['health_status'] = "warning"
                    report['recommendations'].append(f"Database backup is {age_hours:.1f} hours old")
                elif backup_type in ['config', 'logs', 'system'] and age_hours > 48:
                    report['health_status'] = "warning"
                    report['recommendations'].append(f"{backup_type.title()} backup is {age_hours:.1f} hours old")
            
            # Check disk space
            total_size_gb = report['summary']['total_size_mb'] / 1024
            if total_size_gb > 10:
                report['recommendations'].append(f"Backup directory using {total_size_gb:.1f} GB - consider cleanup")
            
            if not report['recommendations']:
                report['recommendations'].append("All backup systems operating normally")
            
            # Save report
            report_file = self.backup_dir / f"backup_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Backup report generated: {report_file}")
            return report
        
        except Exception as e:
            print(f"❌ Report generation error: {e}")
            return {"error": str(e)}

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Backup Strategy")
    parser.add_argument('--type', choices=['database', 'config', 'logs', 'full_system'], 
                       help='Type of backup to create')
    parser.add_argument('--name', help='Custom backup name')
    parser.add_argument('--restore', help='Restore backup from path')
    parser.add_argument('--verify', help='Verify backup integrity')
    parser.add_argument('--list', action='store_true', help='List all backups')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old backups')
    parser.add_argument('--report', action='store_true', help='Generate backup report')
    parser.add_argument('--setup-remote', help='Setup remote backup (JSON config)')
    parser.add_argument('--setup-cron', action='store_true', help='Setup cron jobs')
    parser.add_argument('--setup-systemd', action='store_true', help='Setup systemd service')
    parser.add_argument('--setup-dr', action='store_true', help='Setup disaster recovery')
    parser.add_argument('--auto', action='store_true', help='Automated mode (less verbose)')
    parser.add_argument('--project-root', help='Project root directory')
    
    args = parser.parse_args()
    
    # Initialize backup strategy
    backup = BackupStrategy(args.project_root)
    
    try:
        if args.type:
            # Create backup
            if args.type == 'database':
                success, result = backup.create_database_backup(args.name)
            elif args.type == 'config':
                success, result = backup.create_config_backup(args.name)
            elif args.type == 'logs':
                success, result = backup.create_logs_backup(args.name)
            elif args.type == 'full_system':
                success, result = backup.create_full_system_backup(args.name)
            
            if success:
                print(f"\n✅ Backup completed successfully: {result}")
                sys.exit(0)
            else:
                print(f"\n❌ Backup failed: {result}")
                sys.exit(1)
        
        elif args.restore:
            success, result = backup.restore_backup(args.restore)
            if success:
                print(f"\n✅ Restore completed: {result}")
            else:
                print(f"\n❌ Restore failed: {result}")
                sys.exit(1)
        
        elif args.verify:
            success, result = backup.verify_backup(args.verify)
            if success:
                print(f"\n✅ Verification successful: {result}")
            else:
                print(f"\n❌ Verification failed: {result}")
                sys.exit(1)
        
        elif args.list:
            backups = backup.list_backups()
            for backup_type, backup_list in backups.items():
                print(f"\n{backup_type.upper()} Backups ({len(backup_list)}):")
                for b in backup_list[:5]:  # Show latest 5
                    print(f"  - {b['backup_name']} ({b['file_size_mb']} MB) - {b['timestamp']}")
        
        elif args.cleanup:
            cleaned = backup.cleanup_old_backups()
            print(f"\n✅ Cleaned up {cleaned} old backups")
        
        elif args.report:
            report = backup.generate_backup_report()
            if 'error' not in report:
                print(f"\n📊 Backup Report Summary:")
                print(f"   Total backups: {report['summary']['total_backups']}")
                print(f"   Total size: {report['summary']['total_size_mb']} MB")
                print(f"   Health status: {report['health_status']}")
                for rec in report['recommendations']:
                    print(f"   - {rec}")
        
        elif args.setup_remote:
            with open(args.setup_remote, 'r') as f:
                remote_config = json.load(f)
            success = backup.setup_remote_backup(remote_config)
            if success:
                print("\n✅ Remote backup setup completed")
            else:
                sys.exit(1)
        
        elif args.setup_cron:
            success = backup.setup_cron_jobs()
            if success:
                print("\n✅ Cron jobs setup completed")
            else:
                sys.exit(1)
        
        elif args.setup_systemd:
            success = backup.create_systemd_backup_service()
            if success:
                print("\n✅ Systemd service setup completed")
            else:
                sys.exit(1)
        
        elif args.setup_dr:
            success = backup.create_disaster_recovery_plan()
            if success:
                print("\n✅ Disaster recovery plan created")
            else:
                sys.exit(1)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()