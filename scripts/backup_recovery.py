#!/usr/bin/env python3
"""
AI Trading Sentinel - Backup and Recovery System
Automated backup and disaster recovery for production deployment

Usage:
    python backup_recovery.py backup [--type full|incremental] [--compress]
    python backup_recovery.py restore --backup-id <id> [--dry-run]
    python backup_recovery.py list [--days 30]
    python backup_recovery.py cleanup [--keep-days 30]
    python backup_recovery.py verify --backup-id <id>
"""

import os
import sys
import json
import shutil
import tarfile
import gzip
import hashlib
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse
import tempfile
import psycopg2
import redis
from urllib.parse import urlparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class BackupMetadata:
    """Backup metadata structure"""
    backup_id: str
    timestamp: datetime
    backup_type: str  # 'full' or 'incremental'
    size_bytes: int
    checksum: str
    files_count: int
    database_included: bool
    redis_included: bool
    docker_volumes_included: bool
    compression: str
    status: str  # 'completed', 'failed', 'in_progress'
    restore_tested: bool
    retention_days: int
    description: str

class BackupManager:
    """Comprehensive backup and recovery system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.backup_dir = Path(self.config["backup"]["directory"])
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load backup configuration"""
        default_config = {
            "backup": {
                "directory": "/var/backups/ai-trading-sentinel",
                "retention_days": 30,
                "compression": "gzip",
                "encryption_enabled": False,
                "remote_storage": {
                    "enabled": False,
                    "type": "s3",  # s3, ftp, rsync
                    "endpoint": "",
                    "bucket": "",
                    "access_key": "",
                    "secret_key": ""
                }
            },
            "paths": {
                "application_data": "/opt/ai-trading-sentinel",
                "logs": "/var/log/ai-trading-sentinel",
                "docker_volumes": "/var/lib/docker/volumes",
                "config_files": [
                    "/opt/ai-trading-sentinel/.env",
                    "/opt/ai-trading-sentinel/docker-compose.yml",
                    "/etc/nginx/sites-available/ai-trading-sentinel",
                    "/etc/systemd/system/ai-trading-sentinel.service"
                ]
            },
            "database": {
                "postgresql": {
                    "enabled": True,
                    "host": "localhost",
                    "port": 5432,
                    "database": "trading_sentinel",
                    "username": "postgres"
                },
                "redis": {
                    "enabled": True,
                    "host": "localhost",
                    "port": 6379,
                    "database": 0
                }
            },
            "notifications": {
                "email_enabled": False,
                "slack_enabled": False,
                "webhook_url": ""
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self._deep_update(default_config, user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_path}: {e}")
        
        return default_config
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> Dict:
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
        return base_dict
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = Path("/var/log/ai-trading-sentinel")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "backup_recovery.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _save_metadata(self, metadata: BackupMetadata):
        """Save backup metadata"""
        metadata_file = self.backup_dir / f"{metadata.backup_id}.json"
        
        # Convert datetime to string for JSON serialization
        metadata_dict = asdict(metadata)
        metadata_dict["timestamp"] = metadata.timestamp.isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
    
    def _load_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata"""
        metadata_file = self.backup_dir / f"{backup_id}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            # Convert string back to datetime
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            
            return BackupMetadata(**data)
        except Exception as e:
            self.logger.error(f"Error loading metadata for {backup_id}: {e}")
            return None
    
    def backup_database(self, backup_dir: Path) -> Tuple[bool, int]:
        """Backup PostgreSQL database"""
        if not self.config["database"]["postgresql"]["enabled"]:
            return True, 0
        
        try:
            db_config = self.config["database"]["postgresql"]
            backup_file = backup_dir / "postgresql_dump.sql"
            
            # Use pg_dump to create database backup
            cmd = [
                "pg_dump",
                "-h", db_config["host"],
                "-p", str(db_config["port"]),
                "-U", db_config["username"],
                "-d", db_config["database"],
                "-f", str(backup_file),
                "--verbose",
                "--no-password"
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "")
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Database backup failed: {result.stderr}")
                return False, 0
            
            file_size = backup_file.stat().st_size
            self.logger.info(f"Database backup completed: {file_size} bytes")
            return True, file_size
            
        except Exception as e:
            self.logger.error(f"Database backup error: {e}")
            return False, 0
    
    def backup_redis(self, backup_dir: Path) -> Tuple[bool, int]:
        """Backup Redis data"""
        if not self.config["database"]["redis"]["enabled"]:
            return True, 0
        
        try:
            redis_config = self.config["database"]["redis"]
            backup_file = backup_dir / "redis_dump.rdb"
            
            # Connect to Redis and save
            r = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["database"],
                password=os.getenv("REDIS_PASSWORD")
            )
            
            # Trigger BGSAVE
            r.bgsave()
            
            # Wait for background save to complete
            import time
            while r.lastsave() == r.lastsave():
                time.sleep(1)
            
            # Copy RDB file
            redis_data_dir = Path("/var/lib/redis")
            rdb_file = redis_data_dir / "dump.rdb"
            
            if rdb_file.exists():
                shutil.copy2(rdb_file, backup_file)
                file_size = backup_file.stat().st_size
                self.logger.info(f"Redis backup completed: {file_size} bytes")
                return True, file_size
            else:
                self.logger.warning("Redis RDB file not found")
                return True, 0
                
        except Exception as e:
            self.logger.error(f"Redis backup error: {e}")
            return False, 0
    
    def backup_files(self, backup_dir: Path, backup_type: str = "full") -> Tuple[bool, int, int]:
        """Backup application files"""
        try:
            files_backup_dir = backup_dir / "files"
            files_backup_dir.mkdir(exist_ok=True)
            
            total_size = 0
            files_count = 0
            
            # Backup application data
            app_data_path = Path(self.config["paths"]["application_data"])
            if app_data_path.exists():
                app_backup_dir = files_backup_dir / "application"
                shutil.copytree(app_data_path, app_backup_dir, dirs_exist_ok=True)
                
                # Calculate size
                for file_path in app_backup_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        files_count += 1
            
            # Backup logs (last 7 days only)
            logs_path = Path(self.config["paths"]["logs"])
            if logs_path.exists():
                logs_backup_dir = files_backup_dir / "logs"
                logs_backup_dir.mkdir(exist_ok=True)
                
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for log_file in logs_path.glob("*.log*"):
                    if log_file.is_file():
                        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if mtime > cutoff_date:
                            shutil.copy2(log_file, logs_backup_dir)
                            total_size += log_file.stat().st_size
                            files_count += 1
            
            # Backup configuration files
            config_backup_dir = files_backup_dir / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            for config_file_path in self.config["paths"]["config_files"]:
                config_file = Path(config_file_path)
                if config_file.exists():
                    dest_file = config_backup_dir / config_file.name
                    shutil.copy2(config_file, dest_file)
                    total_size += config_file.stat().st_size
                    files_count += 1
            
            # Backup Docker volumes (if enabled)
            docker_volumes_path = Path(self.config["paths"]["docker_volumes"])
            if docker_volumes_path.exists():
                volumes_backup_dir = files_backup_dir / "docker_volumes"
                
                # Only backup AI Trading Sentinel volumes
                for volume_dir in docker_volumes_path.glob("ai-trading-sentinel_*"):
                    if volume_dir.is_dir():
                        dest_dir = volumes_backup_dir / volume_dir.name
                        shutil.copytree(volume_dir, dest_dir, dirs_exist_ok=True)
                        
                        for file_path in dest_dir.rglob("*"):
                            if file_path.is_file():
                                total_size += file_path.stat().st_size
                                files_count += 1
            
            self.logger.info(f"Files backup completed: {files_count} files, {total_size} bytes")
            return True, total_size, files_count
            
        except Exception as e:
            self.logger.error(f"Files backup error: {e}")
            return False, 0, 0
    
    def create_backup_archive(self, backup_dir: Path, backup_id: str) -> Tuple[bool, Path, int]:
        """Create compressed backup archive"""
        try:
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_dir, arcname=backup_id)
            
            archive_size = archive_path.stat().st_size
            
            # Clean up temporary backup directory
            shutil.rmtree(backup_dir)
            
            self.logger.info(f"Backup archive created: {archive_path} ({archive_size} bytes)")
            return True, archive_path, archive_size
            
        except Exception as e:
            self.logger.error(f"Archive creation error: {e}")
            return False, Path(), 0
    
    def create_backup(self, backup_type: str = "full", compress: bool = True) -> Optional[BackupMetadata]:
        """Create a new backup"""
        backup_id = self._generate_backup_id()
        self.logger.info(f"Starting {backup_type} backup: {backup_id}")
        
        # Create temporary backup directory
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_temp_dir = Path(temp_dir) / backup_id
            backup_temp_dir.mkdir()
            
            total_size = 0
            files_count = 0
            
            # Initialize metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.now(),
                backup_type=backup_type,
                size_bytes=0,
                checksum="",
                files_count=0,
                database_included=False,
                redis_included=False,
                docker_volumes_included=False,
                compression="gzip" if compress else "none",
                status="in_progress",
                restore_tested=False,
                retention_days=self.config["backup"]["retention_days"],
                description=f"{backup_type.title()} backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            try:
                # Backup database
                db_success, db_size = self.backup_database(backup_temp_dir)
                if db_success:
                    metadata.database_included = True
                    total_size += db_size
                
                # Backup Redis
                redis_success, redis_size = self.backup_redis(backup_temp_dir)
                if redis_success:
                    metadata.redis_included = True
                    total_size += redis_size
                
                # Backup files
                files_success, files_size, file_count = self.backup_files(backup_temp_dir, backup_type)
                if files_success:
                    metadata.docker_volumes_included = True
                    total_size += files_size
                    files_count += file_count
                
                # Create archive
                if compress:
                    archive_success, archive_path, archive_size = self.create_backup_archive(
                        backup_temp_dir, backup_id
                    )
                    if archive_success:
                        total_size = archive_size
                        metadata.checksum = self._calculate_checksum(archive_path)
                else:
                    # Move directory to final location
                    final_backup_dir = self.backup_dir / backup_id
                    shutil.move(backup_temp_dir, final_backup_dir)
                
                # Update metadata
                metadata.size_bytes = total_size
                metadata.files_count = files_count
                metadata.status = "completed"
                
                # Save metadata
                self._save_metadata(metadata)
                
                # Send notification
                self._send_backup_notification(metadata, success=True)
                
                self.logger.info(f"Backup completed successfully: {backup_id}")
                return metadata
                
            except Exception as e:
                metadata.status = "failed"
                metadata.description += f" - Error: {str(e)}"
                self._save_metadata(metadata)
                self._send_backup_notification(metadata, success=False, error=str(e))
                self.logger.error(f"Backup failed: {e}")
                return metadata
    
    def list_backups(self, days: int = 30) -> List[BackupMetadata]:
        """List available backups"""
        backups = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for metadata_file in self.backup_dir.glob("*.json"):
            backup_id = metadata_file.stem
            metadata = self._load_metadata(backup_id)
            
            if metadata and metadata.timestamp > cutoff_date:
                backups.append(metadata)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups
    
    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity"""
        metadata = self._load_metadata(backup_id)
        if not metadata:
            self.logger.error(f"Backup metadata not found: {backup_id}")
            return False
        
        # Check if backup file exists
        if metadata.compression != "none":
            backup_file = self.backup_dir / f"{backup_id}.tar.gz"
        else:
            backup_file = self.backup_dir / backup_id
        
        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Verify checksum (for compressed backups)
        if metadata.compression != "none" and metadata.checksum:
            current_checksum = self._calculate_checksum(backup_file)
            if current_checksum != metadata.checksum:
                self.logger.error(f"Checksum mismatch for backup {backup_id}")
                return False
        
        self.logger.info(f"Backup verification successful: {backup_id}")
        return True
    
    def restore_backup(self, backup_id: str, dry_run: bool = False) -> bool:
        """Restore from backup"""
        metadata = self._load_metadata(backup_id)
        if not metadata:
            self.logger.error(f"Backup not found: {backup_id}")
            return False
        
        if not self.verify_backup(backup_id):
            self.logger.error(f"Backup verification failed: {backup_id}")
            return False
        
        self.logger.info(f"Starting restore from backup: {backup_id} (dry_run={dry_run})")
        
        try:
            # Extract backup
            if metadata.compression != "none":
                backup_file = self.backup_dir / f"{backup_id}.tar.gz"
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    with tarfile.open(backup_file, "r:gz") as tar:
                        tar.extractall(temp_dir)
                    
                    restore_dir = Path(temp_dir) / backup_id
                    return self._perform_restore(restore_dir, metadata, dry_run)
            else:
                restore_dir = self.backup_dir / backup_id
                return self._perform_restore(restore_dir, metadata, dry_run)
                
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def _perform_restore(self, restore_dir: Path, metadata: BackupMetadata, dry_run: bool) -> bool:
        """Perform the actual restore operation"""
        try:
            if dry_run:
                self.logger.info("DRY RUN - No actual changes will be made")
            
            # Stop services before restore
            if not dry_run:
                self.logger.info("Stopping services...")
                subprocess.run(["systemctl", "stop", "ai-trading-sentinel"], check=False)
                subprocess.run(["docker-compose", "down"], check=False, cwd="/opt/ai-trading-sentinel")
            
            # Restore database
            if metadata.database_included:
                db_file = restore_dir / "postgresql_dump.sql"
                if db_file.exists():
                    self.logger.info(f"Restoring database from {db_file}")
                    if not dry_run:
                        self._restore_database(db_file)
            
            # Restore Redis
            if metadata.redis_included:
                redis_file = restore_dir / "redis_dump.rdb"
                if redis_file.exists():
                    self.logger.info(f"Restoring Redis from {redis_file}")
                    if not dry_run:
                        self._restore_redis(redis_file)
            
            # Restore files
            files_dir = restore_dir / "files"
            if files_dir.exists():
                self.logger.info(f"Restoring files from {files_dir}")
                if not dry_run:
                    self._restore_files(files_dir)
            
            # Restart services
            if not dry_run:
                self.logger.info("Starting services...")
                subprocess.run(["docker-compose", "up", "-d"], check=True, cwd="/opt/ai-trading-sentinel")
                subprocess.run(["systemctl", "start", "ai-trading-sentinel"], check=False)
            
            self.logger.info(f"Restore completed successfully: {metadata.backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore operation failed: {e}")
            return False
    
    def _restore_database(self, db_file: Path):
        """Restore PostgreSQL database"""
        db_config = self.config["database"]["postgresql"]
        
        cmd = [
            "psql",
            "-h", db_config["host"],
            "-p", str(db_config["port"]),
            "-U", db_config["username"],
            "-d", db_config["database"],
            "-f", str(db_file)
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Database restore failed: {result.stderr}")
    
    def _restore_redis(self, redis_file: Path):
        """Restore Redis data"""
        redis_data_dir = Path("/var/lib/redis")
        dest_file = redis_data_dir / "dump.rdb"
        
        # Stop Redis service
        subprocess.run(["systemctl", "stop", "redis"], check=False)
        
        # Copy RDB file
        shutil.copy2(redis_file, dest_file)
        
        # Start Redis service
        subprocess.run(["systemctl", "start", "redis"], check=True)
    
    def _restore_files(self, files_dir: Path):
        """Restore application files"""
        # Restore application data
        app_backup_dir = files_dir / "application"
        if app_backup_dir.exists():
            app_data_path = Path(self.config["paths"]["application_data"])
            if app_data_path.exists():
                shutil.rmtree(app_data_path)
            shutil.copytree(app_backup_dir, app_data_path)
        
        # Restore configuration files
        config_backup_dir = files_dir / "config"
        if config_backup_dir.exists():
            for config_file in config_backup_dir.iterdir():
                # Find original location
                for original_path in self.config["paths"]["config_files"]:
                    if Path(original_path).name == config_file.name:
                        shutil.copy2(config_file, original_path)
                        break
        
        # Restore Docker volumes
        volumes_backup_dir = files_dir / "docker_volumes"
        if volumes_backup_dir.exists():
            docker_volumes_path = Path(self.config["paths"]["docker_volumes"])
            for volume_backup in volumes_backup_dir.iterdir():
                dest_volume = docker_volumes_path / volume_backup.name
                if dest_volume.exists():
                    shutil.rmtree(dest_volume)
                shutil.copytree(volume_backup, dest_volume)
    
    def cleanup_old_backups(self, keep_days: int = None) -> int:
        """Clean up old backups"""
        if keep_days is None:
            keep_days = self.config["backup"]["retention_days"]
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        removed_count = 0
        
        for metadata_file in self.backup_dir.glob("*.json"):
            backup_id = metadata_file.stem
            metadata = self._load_metadata(backup_id)
            
            if metadata and metadata.timestamp < cutoff_date:
                # Remove backup files
                backup_file = self.backup_dir / f"{backup_id}.tar.gz"
                backup_dir = self.backup_dir / backup_id
                
                if backup_file.exists():
                    backup_file.unlink()
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                
                # Remove metadata
                metadata_file.unlink()
                
                removed_count += 1
                self.logger.info(f"Removed old backup: {backup_id}")
        
        self.logger.info(f"Cleanup completed: {removed_count} backups removed")
        return removed_count
    
    def _send_backup_notification(self, metadata: BackupMetadata, success: bool, error: str = None):
        """Send backup notification"""
        if not self.config["notifications"]["email_enabled"] and not self.config["notifications"]["slack_enabled"]:
            return
        
        status = "✅ Success" if success else "❌ Failed"
        message = f"AI Trading Sentinel Backup {status}\n\n"
        message += f"Backup ID: {metadata.backup_id}\n"
        message += f"Type: {metadata.backup_type}\n"
        message += f"Timestamp: {metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"Size: {metadata.size_bytes / (1024*1024):.2f} MB\n"
        message += f"Files: {metadata.files_count}\n"
        
        if error:
            message += f"\nError: {error}"
        
        # Send notifications (implementation depends on configured services)
        self.logger.info(f"Backup notification: {status}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Backup & Recovery")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument("--type", choices=["full", "incremental"], default="full")
    backup_parser.add_argument("--compress", action="store_true", default=True)
    backup_parser.add_argument("--config", help="Configuration file path")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--backup-id", required=True, help="Backup ID to restore")
    restore_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    restore_parser.add_argument("--config", help="Configuration file path")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List backups")
    list_parser.add_argument("--days", type=int, default=30, help="Show backups from last N days")
    list_parser.add_argument("--config", help="Configuration file path")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument("--keep-days", type=int, default=30, help="Keep backups for N days")
    cleanup_parser.add_argument("--config", help="Configuration file path")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup")
    verify_parser.add_argument("--backup-id", required=True, help="Backup ID to verify")
    verify_parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize backup manager
    backup_manager = BackupManager(args.config)
    
    try:
        if args.command == "backup":
            metadata = backup_manager.create_backup(args.type, args.compress)
            if metadata and metadata.status == "completed":
                print(f"✅ Backup created successfully: {metadata.backup_id}")
                print(f"   Size: {metadata.size_bytes / (1024*1024):.2f} MB")
                print(f"   Files: {metadata.files_count}")
            else:
                print("❌ Backup failed")
                sys.exit(1)
        
        elif args.command == "restore":
            success = backup_manager.restore_backup(args.backup_id, args.dry_run)
            if success:
                print(f"✅ Restore completed: {args.backup_id}")
            else:
                print(f"❌ Restore failed: {args.backup_id}")
                sys.exit(1)
        
        elif args.command == "list":
            backups = backup_manager.list_backups(args.days)
            if backups:
                print(f"Available backups (last {args.days} days):\n")
                for backup in backups:
                    status_icon = "✅" if backup.status == "completed" else "❌"
                    size_mb = backup.size_bytes / (1024*1024)
                    print(f"{status_icon} {backup.backup_id}")
                    print(f"   Date: {backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   Type: {backup.backup_type}")
                    print(f"   Size: {size_mb:.2f} MB")
                    print(f"   Files: {backup.files_count}")
                    print(f"   Status: {backup.status}")
                    print()
            else:
                print("No backups found")
        
        elif args.command == "cleanup":
            removed = backup_manager.cleanup_old_backups(args.keep_days)
            print(f"✅ Cleanup completed: {removed} backups removed")
        
        elif args.command == "verify":
            success = backup_manager.verify_backup(args.backup_id)
            if success:
                print(f"✅ Backup verification successful: {args.backup_id}")
            else:
                print(f"❌ Backup verification failed: {args.backup_id}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()