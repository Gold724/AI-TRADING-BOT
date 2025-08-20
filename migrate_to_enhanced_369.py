#!/usr/bin/env python3
"""
Tesla 369 Enhanced Strategy Migration Script
==========================================

Automated migration script to transition from existing Tesla 369 strategy
to the enhanced version with advanced features.

Usage:
    python migrate_to_enhanced_369.py --mode=gradual
    python migrate_to_enhanced_369.py --mode=full
    python migrate_to_enhanced_369.py --mode=backup
    python migrate_to_enhanced_369.py --mode=validate

Author: TRAE-SentinelOps
Version: 1.0.0
"""

import os
import sys
import shutil
import json
import argparse
from datetime import datetime
from pathlib import Path

class Tesla369Migration:
    """
    Automated migration system for Tesla 369 Enhanced Strategy
    """
    
    def __init__(self, mode="gradual"):
        self.mode = mode
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_log = []
        
        # Define file mappings
        self.file_mappings = {
            'bulenox_gold_scalping_strategy.py': 'legacy_strategy.py',
            'test_369_gold_scalping_enhanced.py': 'legacy_test.py',
            'strategy_config.py': 'legacy_config.py',
            'fibonacci_multi_tp_strategy.py': 'legacy_fibonacci.py'
        }
        
        # Enhanced files
        self.enhanced_files = [
            'tesla_369_enhanced_strategy.py',
            'tesla_369_integration.py',
            'tesla_369_config.py',
            'trade_plan_generator.py',
            'liquidity_detector.py',
            'lunar_calendar.py',
            'session_manager.py',
            'news_guard.py'
        ]
    
    def log(self, message, level="INFO"):
        """Log migration activities"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def create_backup(self):
        """Create backup of existing files"""
        os.makedirs(self.backup_dir, exist_ok=True)
        self.log(f"Creating backup in: {self.backup_dir}")
        
        for original_file in self.file_mappings.keys():
            if os.path.exists(original_file):
                backup_path = os.path.join(self.backup_dir, original_file)
                shutil.copy2(original_file, backup_path)
                self.log(f"Backed up: {original_file}")
    
    def validate_existing_setup(self):
        """Validate existing Tesla 369 setup"""
        self.log("Validating existing Tesla 369 setup...")
        
        validation_results = {
            'files_exist': {},
            'config_valid': False,
            'fibonacci_sequence': None,
            'daily_target': None,
            'ready_for_migration': False
        }
        
        # Check for existing files
        for file_name in self.file_mappings.keys():
            exists = os.path.exists(file_name)
            validation_results['files_exist'][file_name] = exists
            self.log(f"File check: {file_name} - {'EXISTS' if exists else 'MISSING'}")
        
        # Extract configuration from existing files
        try:
            # Try to read Fibonacci sequence from strategy_config.py
            if os.path.exists('strategy_config.py'):
                with open('strategy_config.py', 'r') as f:
                    content = f.read()
                    
                # Extract FIB_SEQUENCE
                if 'FIB_SEQUENCE' in content:
                    import re
                    fib_match = re.search(r'FIB_SEQUENCE\s*=\s*\[(.*?)\]', content)
                    if fib_match:
                        fib_str = fib_match.group(1)
                        validation_results['fibonacci_sequence'] = [int(x.strip()) for x in fib_str.split(',')]
                
                # Extract daily target
                if 'DAILY_PROFIT_TARGET' in content:
                    target_match = re.search(r'DAILY_PROFIT_TARGET\s*=\s*(\d+\.?\d*)', content)
                    if target_match:
                        validation_results['daily_target'] = float(target_match.group(1))
            
            validation_results['config_valid'] = True
            
        except Exception as e:
            self.log(f"Error reading configuration: {str(e)}", "ERROR")
            validation_results['config_valid'] = False
        
        # Determine readiness
        required_files = ['bulenox_gold_scalping_strategy.py', 'strategy_config.py']
        has_required = all(validation_results['files_exist'].get(f, False) for f in required_files)
        has_fibonacci = validation_results['fibonacci_sequence'] is not None
        has_target = validation_results['daily_target'] is not None
        
        validation_results['ready_for_migration'] = has_required and has_fibonacci and has_target
        
        return validation_results
    
    def generate_migration_config(self):
        """Generate migration configuration based on existing setup"""
        validation = self.validate_existing_setup()
        
        if not validation['ready_for_migration']:
            self.log("Cannot generate migration config - validation failed", "ERROR")
            return None
        
        config = {
            'migration_version': '1.0.0',
            'migration_date': datetime.now().isoformat(),
            'original_config': {
                'fibonacci_sequence': validation['fibonacci_sequence'],
                'daily_profit_target': validation['daily_target']
            },
            'enhanced_config': {
                'fibonacci_sequence': validation['fibonacci_sequence'],
                'daily_profit_target': validation['daily_target'],
                'enable_liquidity_detection': True,
                'enable_trend_analysis': True,
                'enable_news_guard': True,
                'enable_lunar_timing': True,
                'enable_session_validation': True,
                'enable_advanced_risk': True
            },
            'migration_mode': self.mode,
            'backup_created': self.backup_dir
        }
        
        # Save migration config
        with open('migration_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        self.log("Migration configuration generated")
        return config
    
    def gradual_migration(self):
        """Perform gradual migration with feature flags"""
        self.log("Starting gradual migration...")
        
        # Create integration wrapper
        integration_code = '''
#!/usr/bin/env python3
"""
Tesla 369 Gradual Migration Wrapper
==================================

This wrapper allows gradual adoption of enhanced features.
Start with all features disabled and enable them one by one.
"""

from tesla_369_integration import Tesla369Integration

# Initialize with all features disabled
migration_wrapper = Tesla369Integration(
    enable_liquidity_detection=False,
    enable_trend_analysis=False,
    enable_news_guard=False,
    enable_lunar_timing=False,
    enable_session_validation=False,
    enable_advanced_risk=False
)

# Enable features gradually:
# migration_wrapper.enable_feature('liquidity_detection')
# migration_wrapper.enable_feature('trend_analysis')
# migration_wrapper.enable_feature('news_guard')
# migration_wrapper.enable_feature('lunar_timing')
# migration_wrapper.enable_feature('session_validation')
# migration_wrapper.enable_feature('advanced_risk')

# Use this wrapper in your existing code
if __name__ == "__main__":
    migration_wrapper.run_migration_test()
'''
        
        with open('migration_wrapper.py', 'w') as f:
            f.write(integration_code)
        
        self.log("Created migration_wrapper.py for gradual adoption")
    
    def full_migration(self):
        """Perform full migration replacing existing files"""
        self.log("Starting full migration...")
        
        # Create enhanced main script
        main_script = '''
#!/usr/bin/env python3
"""
Tesla 369 Enhanced Strategy - Full Migration
==========================================

This is the enhanced version of your Tesla 369 strategy.
All features are enabled by default.

Usage: python enhanced_main.py
"""

import sys
import os
from tesla_369_enhanced_strategy import Tesla369EnhancedStrategy
from tesla_369_config import Tesla369EnhancedConfig

def main():
    """Main execution function for enhanced strategy"""
    
    # Load configuration
    config = Tesla369EnhancedConfig()
    
    # Initialize enhanced strategy
    strategy = Tesla369EnhancedStrategy()
    
    # Print configuration summary
    config.print_configuration_summary()
    
    # Run strategy
    try:
        strategy.run_daily_cycle()
        print("Enhanced strategy execution completed successfully")
    except Exception as e:
        print(f"Error running enhanced strategy: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open('enhanced_main.py', 'w') as f:
            f.write(main_script)
        
        self.log("Created enhanced_main.py for full migration")
    
    def validate_migration(self):
        """Validate the migration was successful"""
        self.log("Validating migration...")
        
        validation_tests = []
        
        # Test 1: Check enhanced files exist
        for file_name in self.enhanced_files:
            exists = os.path.exists(file_name)
            validation_tests.append({
                'test': f'Enhanced file exists: {file_name}',
                'passed': exists,
                'message': 'OK' if exists else 'File missing'
            })
        
        # Test 2: Check configuration
        try:
            from tesla_369_config import Tesla369EnhancedConfig
            config = Tesla369EnhancedConfig()
            config_valid = config.validate_configuration()
            validation_tests.append({
                'test': 'Configuration validation',
                'passed': all(config_valid.values()),
                'message': str(config_valid)
            })
        except Exception as e:
            validation_tests.append({
                'test': 'Configuration validation',
                'passed': False,
                'message': str(e)
            })
        
        # Test 3: Check imports
        try:
            from tesla_369_enhanced_strategy import Tesla369EnhancedStrategy
            from tesla_369_integration import Tesla369Integration
            from liquidity_detector import LiquidityDetector
            from lunar_calendar import LunarCalendar
            import_success = True
            validation_tests.append({
                'test': 'Module imports',
                'passed': True,
                'message': 'All modules imported successfully'
            })
        except Exception as e:
            validation_tests.append({
                'test': 'Module imports',
                'passed': False,
                'message': str(e)
            })
        
        # Test 4: Check Fibonacci sequence
        try:
            from tesla_369_config import Tesla369EnhancedConfig
            config = Tesla369EnhancedConfig()
            fib_sequence = config.FIBONACCI_SEQUENCE
            fib_valid = len(fib_sequence) > 0 and all(isinstance(x, (int, float)) for x in fib_sequence)
            validation_tests.append({
                'test': 'Fibonacci sequence validation',
                'passed': fib_valid,
                'message': str(fib_sequence)
            })
        except Exception as e:
            validation_tests.append({
                'test': 'Fibonacci sequence validation',
                'passed': False,
                'message': str(e)
            })
        
        # Save validation results
        validation_summary = {
            'validation_date': datetime.now().isoformat(),
            'tests': validation_tests,
            'overall_passed': all(test['passed'] for test in validation_tests),
            'total_tests': len(validation_tests),
            'passed_tests': sum(1 for test in validation_tests if test['passed'])
        }
        
        with open('migration_validation.json', 'w') as f:
            json.dump(validation_summary, f, indent=2)
        
        self.log(f"Validation completed: {validation_summary['passed_tests']}/{validation_summary['total_tests']} tests passed")
        
        return validation_summary
    
    def run_migration(self):
        """Execute the complete migration process"""
        self.log(f"Starting Tesla 369 Enhanced Strategy Migration - Mode: {self.mode}")
        
        # Step 1: Validate existing setup
        validation = self.validate_existing_setup()
        if not validation['ready_for_migration'] and self.mode != 'validate':
            self.log("Existing setup validation failed", "ERROR")
            return False
        
        # Step 2: Create backup
        if self.mode in ['gradual', 'full']:
            self.create_backup()
        
        # Step 3: Generate migration configuration
        config = self.generate_migration_config()
        if not config:
            return False
        
        # Step 4: Execute migration based on mode
        if self.mode == 'gradual':
            self.gradual_migration()
        elif self.mode == 'full':
            self.full_migration()
        elif self.mode == 'backup':
            self.log("Backup mode - only creating backups")
        elif self.mode == 'validate':
            self.log("Validation mode - checking setup only")
        
        # Step 5: Validate migration
        validation_results = self.validate_migration()
        
        # Step 6: Generate migration report
        report = {
            'migration_report': {
                'migration_date': datetime.now().isoformat(),
                'migration_mode': self.mode,
                'backup_directory': self.backup_dir,
                'validation_results': validation_results,
                'migration_log': self.migration_log
            }
        }
        
        with open('migration_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.log("=" * 50)
        self.log("Tesla 369 Enhanced Strategy Migration Summary")
        self.log("=" * 50)
        self.log(f"Mode: {self.mode}")
        self.log(f"Backup: {self.backup_dir}")
        self.log(f"Validation: {validation_results['passed_tests']}/{validation_results['total_tests']} tests passed")
        
        if validation_results['overall_passed']:
            self.log("Migration completed successfully!", "SUCCESS")
            self.log("Next steps:")
            self.log("1. Review migration_report.json")
            self.log("2. Test with paper trading mode")
            self.log("3. Enable features gradually (if using gradual mode)")
            self.log("4. Monitor performance for 24 hours")
        else:
            self.log("Migration has issues - please review validation results", "WARNING")
        
        return validation_results['overall_passed']

def main():
    """Main migration script"""
    parser = argparse.ArgumentParser(description='Tesla 369 Enhanced Strategy Migration')
    parser.add_argument('--mode', choices=['gradual', 'full', 'backup', 'validate'], 
                       default='gradual', help='Migration mode')
    parser.add_argument('--config', help='Migration configuration file')
    
    args = parser.parse_args()
    
    migration = Tesla369Migration(mode=args.mode)
    
    try:
        success = migration.run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()