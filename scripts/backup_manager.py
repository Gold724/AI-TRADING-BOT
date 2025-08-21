#!/usr/bin/env python3
"""
AI Trading Sentinel - Backup Manager
Comprehensive backup management and disaster recovery system.
"""

import os
import sys
import json
import yaml
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.setup_backup_strategy import BackupManager
from monitoring.slack_alerting import SlackAlerting, Alert, AlertSeverity

class BackupOrchestrator:
    """Orchestrates all backup operations and provides unified management interface."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "backup_config.yml"
        self.config = self._load_config()
        
        # Initialize components
        self.backup_manager = BackupManager(str(self.project_root))
        self.slack_alerting = SlackAlerting() if self.config.get('monitoring', {}).get('slack', {}).get('enabled') else None
        
        # Setup logging
        self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load backup configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default backup configuration."""
        return {
            'global': {
                'enabled': True,
                'backup_directory': 'backups',
                'retention_days': 30,
                'max_backups': 50,
                'compression': True,
                'encryption': True
            },
            'schedules': {
                'database': {'enabled': True, 'cron': '0 */6 * * *'},
                'config': {'enabled': True, 'cron': '0 2 * * *'},
                'logs': {'enabled': True, 'cron': '0 4 * * *'},
                'full_system': {'enabled': True, 'cron': '0 1 * * 0'}
            },
            'monitoring': {
                'health_checks': {'enabled': True, 'interval_minutes': 60},
                'slack': {'enabled': False}
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.project_root / "logs" / "backup_manager.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, backup_type: str, force: bool = False) -> bool:
        """Create a backup of specified type."""
        if not self.config['global']['enabled'] and not force:
            self.logger.warning("Backups are disabled in configuration")
            return False
        
        schedule_config = self.config.get('schedules', {}).get(backup_type, {})
        if not schedule_config.get('enabled', True) and not force:
            self.logger.warning(f"{backup_type} backups are disabled")
            return False
        
        try:
            self.logger.info(f"Starting {backup_type} backup...")
            start_time = datetime.now()
            
            success = False
            if backup_type == 'database':
                success = self.backup_manager.create_database_backup()
            elif backup_type == 'config':
                success = self.backup_manager.create_config_backup()
            elif backup_type == 'logs':
                success = self.backup_manager.create_logs_backup()
            elif backup_type == 'full_system':
                success = self.backup_manager.create_full_system_backup()
            else:
                self.logger.error(f"Unknown backup type: {backup_type}")
                return False
            
            duration = datetime.now() - start_time
            
            if success:
                self.logger.info(f"{backup_type} backup completed successfully in {duration}")
                self._send_success_notification(backup_type, duration)
                
                # Cleanup old backups
                self.cleanup_old_backups(backup_type)
                return True
            else:
                self.logger.error(f"{backup_type} backup failed")
                self._send_failure_notification(backup_type, "Backup creation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during {backup_type} backup: {e}")
            self._send_failure_notification(backup_type, str(e))
            return False
    
    def create_all_backups(self, force: bool = False) -> Dict[str, bool]:
        """Create all enabled backup types."""
        results = {}
        backup_types = ['database', 'config', 'logs', 'full_system']
        
        for backup_type in backup_types:
            results[backup_type] = self.create_backup(backup_type, force)
        
        return results
    
    def verify_backups(self, backup_type: Optional[str] = None) -> Dict[str, bool]:
        """Verify integrity of backups."""
        results = {}
        
        try:
            backups = self.backup_manager.list_backups()
            
            for btype, backup_list in backups.items():
                if backup_type and btype != backup_type:
                    continue
                    
                type_results = []
                for backup_info in backup_list:
                    backup_path = backup_info['path']
                    is_valid = self.backup_manager.verify_backup(backup_path)
                    type_results.append(is_valid)
                    
                    if not is_valid:
                        self.logger.warning(f"Backup verification failed: {backup_path}")
                
                results[btype] = all(type_results) if type_results else True
        
        except Exception as e:
            self.logger.error(f"Error during backup verification: {e}")
            results['error'] = str(e)
        
        return results
    
    def cleanup_old_backups(self, backup_type: Optional[str] = None) -> Dict[str, int]:
        """Clean up old backups based on retention policy."""
        results = {}
        
        try:
            retention_days = self.config['global']['retention_days']
            max_backups = self.config['global']['max_backups']
            
            if backup_type:
                backup_types = [backup_type]
            else:
                backup_types = ['database', 'config', 'logs', 'full_system']
            
            for btype in backup_types:
                cleaned = self.backup_manager.cleanup_old_backups(
                    backup_type=btype,
                    retention_days=retention_days,
                    max_backups=max_backups
                )
                results[btype] = cleaned
                
                if cleaned > 0:
                    self.logger.info(f"Cleaned up {cleaned} old {btype} backups")
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            results['error'] = str(e)
        
        return results
    
    def restore_backup(self, backup_path: str, restore_location: Optional[str] = None) -> bool:
        """Restore a backup to specified location."""
        try:
            self.logger.info(f"Starting restore from {backup_path}")
            
            success = self.backup_manager.restore_backup(backup_path, restore_location)
            
            if success:
                self.logger.info(f"Restore completed successfully")
                self._send_restore_notification(backup_path, True)
                return True
            else:
                self.logger.error(f"Restore failed")
                self._send_restore_notification(backup_path, False)
                return False
                
        except Exception as e:
            self.logger.error(f"Error during restore: {e}")
            self._send_restore_notification(backup_path, False, str(e))
            return False
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get comprehensive backup status report."""
        try:
            # Get backup report from manager
            report = self.backup_manager.generate_backup_report()
            
            # Add orchestrator-specific information
            report['orchestrator'] = {
                'config_loaded': bool(self.config),
                'config_path': str(self.config_path),
                'global_enabled': self.config['global']['enabled'],
                'slack_enabled': bool(self.slack_alerting),
                'last_check': datetime.now().isoformat()
            }
            
            # Add schedule information
            report['schedules'] = self.config.get('schedules', {})
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        try:
            # Check backup directory
            backup_dir = self.project_root / self.config['global']['backup_directory']
            health['checks']['backup_directory'] = {
                'exists': backup_dir.exists(),
                'writable': os.access(backup_dir, os.W_OK) if backup_dir.exists() else False,
                'path': str(backup_dir)
            }
            
            # Check recent backups
            backups = self.backup_manager.list_backups()
            for backup_type, backup_list in backups.items():
                if backup_list:
                    latest = max(backup_list, key=lambda x: x['created'])
                    age_hours = (datetime.now() - datetime.fromisoformat(latest['created'])).total_seconds() / 3600
                    health['checks'][f'{backup_type}_backup'] = {
                        'latest_age_hours': age_hours,
                        'count': len(backup_list),
                        'latest_size_mb': latest.get('size_mb', 0)
                    }
                else:
                    health['checks'][f'{backup_type}_backup'] = {
                        'latest_age_hours': None,
                        'count': 0,
                        'latest_size_mb': 0
                    }
            
            # Check configuration
            health['checks']['configuration'] = {
                'loaded': bool(self.config),
                'enabled': self.config['global']['enabled'],
                'retention_days': self.config['global']['retention_days']
            }
            
            # Determine overall status
            issues = []
            if not health['checks']['backup_directory']['exists']:
                issues.append('Backup directory does not exist')
            if not health['checks']['backup_directory']['writable']:
                issues.append('Backup directory is not writable')
            
            for backup_type in ['database', 'config']:
                check_key = f'{backup_type}_backup'
                if check_key in health['checks']:
                    age = health['checks'][check_key]['latest_age_hours']
                    if age is None or age > 48:  # No backup or older than 48 hours
                        issues.append(f'{backup_type} backup is stale')
            
            if issues:
                health['overall_status'] = 'degraded'
                health['issues'] = issues
            
        except Exception as e:
            health['overall_status'] = 'error'
            health['error'] = str(e)
        
        return health
    
    def _send_success_notification(self, backup_type: str, duration: timedelta):
        """Send success notification via Slack."""
        if not self.slack_alerting:
            return
        
        alert = Alert(
            severity=AlertSeverity.INFO,
            title=f"Backup Completed: {backup_type.title()}",
            message=f"Successfully completed {backup_type} backup in {duration}",
            source="backup_manager",
            tags=["backup", "success", backup_type]
        )
        
        self.slack_alerting.send_alert(alert)
    
    def _send_failure_notification(self, backup_type: str, error: str):
        """Send failure notification via Slack."""
        if not self.slack_alerting:
            return
        
        alert = Alert(
            severity=AlertSeverity.ERROR,
            title=f"Backup Failed: {backup_type.title()}",
            message=f"Failed to create {backup_type} backup: {error}",
            source="backup_manager",
            tags=["backup", "failure", backup_type]
        )
        
        self.slack_alerting.send_alert(alert)
    
    def _send_restore_notification(self, backup_path: str, success: bool, error: str = None):
        """Send restore notification via Slack."""
        if not self.slack_alerting:
            return
        
        severity = AlertSeverity.INFO if success else AlertSeverity.ERROR
        title = "Backup Restored" if success else "Backup Restore Failed"
        message = f"Backup restore from {backup_path}"
        
        if not success and error:
            message += f": {error}"
        
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            source="backup_manager",
            tags=["backup", "restore", "success" if success else "failure"]
        )
        
        self.slack_alerting.send_alert(alert)

def main():
    """Main CLI interface for backup management."""
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Backup Manager")
    parser.add_argument('--config', '-c', help='Path to backup configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup command
    create_parser = subparsers.add_parser('create', help='Create backup')
    create_parser.add_argument('type', choices=['database', 'config', 'logs', 'full_system', 'all'],
                              help='Type of backup to create')
    create_parser.add_argument('--force', '-f', action='store_true',
                              help='Force backup even if disabled in config')
    
    # Verify backup command
    verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
    verify_parser.add_argument('--type', choices=['database', 'config', 'logs', 'full_system'],
                              help='Backup type to verify (default: all)')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
    cleanup_parser.add_argument('--type', choices=['database', 'config', 'logs', 'full_system'],
                               help='Backup type to clean (default: all)')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_path', help='Path to backup file')
    restore_parser.add_argument('--location', help='Restore location (default: auto-detect)')
    
    # Status command
    subparsers.add_parser('status', help='Show backup status')
    
    # Health check command
    subparsers.add_parser('health', help='Perform health check')
    
    # List backups command
    subparsers.add_parser('list', help='List available backups')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize orchestrator
    orchestrator = BackupOrchestrator(args.config)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.command == 'create':
            if args.type == 'all':
                results = orchestrator.create_all_backups(args.force)
                for backup_type, success in results.items():
                    status = "✓" if success else "✗"
                    print(f"{status} {backup_type}: {'Success' if success else 'Failed'}")
                return 0 if all(results.values()) else 1
            else:
                success = orchestrator.create_backup(args.type, args.force)
                print(f"{'✓' if success else '✗'} {args.type}: {'Success' if success else 'Failed'}")
                return 0 if success else 1
        
        elif args.command == 'verify':
            results = orchestrator.verify_backups(args.type)
            for backup_type, success in results.items():
                if backup_type == 'error':
                    print(f"✗ Error: {success}")
                else:
                    status = "✓" if success else "✗"
                    print(f"{status} {backup_type}: {'Valid' if success else 'Invalid'}")
            return 0 if all(v for k, v in results.items() if k != 'error') else 1
        
        elif args.command == 'cleanup':
            results = orchestrator.cleanup_old_backups(args.type)
            for backup_type, count in results.items():
                if backup_type == 'error':
                    print(f"✗ Error: {count}")
                else:
                    print(f"✓ {backup_type}: Cleaned {count} old backups")
            return 0
        
        elif args.command == 'restore':
            success = orchestrator.restore_backup(args.backup_path, args.location)
            print(f"{'✓' if success else '✗'} Restore: {'Success' if success else 'Failed'}")
            return 0 if success else 1
        
        elif args.command == 'status':
            status = orchestrator.get_backup_status()
            print(json.dumps(status, indent=2, default=str))
            return 0
        
        elif args.command == 'health':
            health = orchestrator.health_check()
            print(json.dumps(health, indent=2, default=str))
            return 0 if health['overall_status'] == 'healthy' else 1
        
        elif args.command == 'list':
            backups = orchestrator.backup_manager.list_backups()
            for backup_type, backup_list in backups.items():
                print(f"\n{backup_type.upper()} Backups:")
                if not backup_list:
                    print("  No backups found")
                else:
                    for backup in backup_list:
                        print(f"  {backup['created']} - {backup['path']} ({backup.get('size_mb', 0):.1f} MB)")
            return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())