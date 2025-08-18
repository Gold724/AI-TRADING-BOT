#!/usr/bin/env python3
"""
TradeBot Sentinel Pro Advanced - Setup and Installation Script

This script automates the complete setup process for the advanced trading automation system.
It handles dependency installation, configuration setup, database initialization, and system validation.

Usage:
    python setup_advanced.py [options]

Options:
    --full          Full installation with all optional dependencies
    --minimal       Minimal installation with core dependencies only
    --dev           Development installation with testing and debugging tools
    --docker        Docker-based installation setup
    --validate      Validate existing installation
    --reset         Reset configuration to defaults
    --help          Show this help message

Author: TradeBot Sentinel Pro Team
Version: 2.0.0
License: MIT
"""

import os
import sys
import json
import subprocess
import shutil
import platform
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'setup_advanced_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class TradeBotAdvancedSetup:
    """Advanced setup and installation manager for TradeBot Sentinel Pro."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.system_info = self._get_system_info()
        self.python_version = sys.version_info
        self.installation_log = []
        
        # Directory structure
        self.directories = {
            'automation': self.project_root / 'automation',
            'automation_config': self.project_root / 'automation' / 'config',
            'automation_templates': self.project_root / 'automation' / 'templates',
            'data': self.project_root / 'data',
            'logs': self.project_root / 'logs',
            'reports': self.project_root / 'reports',
            'monitoring': self.project_root / 'monitoring',
            'backups': self.project_root / 'backups',
            'screenshots': self.project_root / 'screenshots',
            'tests': self.project_root / 'tests',
            'docs': self.project_root / 'docs'
        }
        
        # Configuration files
        self.config_files = {
            'trade_executor': 'automation/config/trade_executor.json',
            'monitoring_dashboard': 'automation/config/monitoring_dashboard.json',
            'alert_system': 'automation/config/alert_system.json',
            'backtesting_engine': 'automation/config/backtesting_engine.json',
            'continuous_improvement': 'automation/config/continuous_improvement.json'
        }
        
        # Dependency groups
        self.dependency_groups = {
            'core': [
                'playwright>=1.40.0',
                'requests>=2.31.0',
                'flask>=2.3.0',
                'flask-socketio>=5.3.0',
                'pandas>=2.1.0',
                'numpy>=1.24.0',
                'python-dotenv>=1.0.0',
                'Pillow>=10.0.0',
                'curlconverter>=0.0.1',
                'beautifulsoup4>=4.12.0',
                'colorama>=0.4.6',
                'rich>=13.6.0',
                'psutil>=5.9.0'
            ],
            'database': [
                'sqlalchemy>=2.0.0',
                'psycopg2-binary>=2.9.0'
            ],
            'financial': [
                'yfinance>=0.2.0',
                'ta>=0.10.0',
                'alpha-vantage>=2.3.0',
                'quandl>=3.7.0'
            ],
            'visualization': [
                'matplotlib>=3.7.0',
                'seaborn>=0.12.0',
                'plotly>=5.17.0'
            ],
            'notifications': [
                'email-validator>=2.1.0',
                'twilio>=8.10.0',
                'telegram-bot-api>=7.0.0',
                'discord.py>=2.3.0'
            ],
            'testing': [
                'pytest>=7.4.0',
                'pytest-asyncio>=0.21.0',
                'pytest-cov>=4.1.0',
                'pytest-mock>=3.11.0'
            ],
            'development': [
                'black>=23.9.0',
                'flake8>=6.1.0',
                'isort>=5.12.0',
                'mypy>=1.6.0',
                'ipython>=8.16.0',
                'jupyter>=1.0.0'
            ],
            'machine_learning': [
                'scikit-learn>=1.3.0',
                'tensorflow>=2.13.0',
                'torch>=2.1.0',
                'xgboost>=1.7.0',
                'lightgbm>=4.1.0'
            ],
            'cloud': [
                'boto3>=1.29.0',
                'google-cloud-storage>=2.10.0',
                'azure-storage-blob>=12.19.0'
            ],
            'monitoring': [
                'prometheus-client>=0.18.0',
                'elasticsearch>=8.10.0',
                'sentry-sdk>=1.38.0'
            ]
        }
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation()
        }
    
    def _log_step(self, message: str, success: bool = True):
        """Log installation step."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'success': success
        }
        self.installation_log.append(log_entry)
        
        if success:
            logger.info(f"✅ {message}")
        else:
            logger.error(f"❌ {message}")
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        logger.info("🔍 Checking system prerequisites...")
        
        # Check Python version
        if self.python_version < (3, 8):
            self._log_step(f"Python 3.8+ required, found {self.python_version}", False)
            return False
        self._log_step(f"Python version {self.python_version} ✓")
        
        # Check pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         check=True, capture_output=True)
            self._log_step("pip available ✓")
        except subprocess.CalledProcessError:
            self._log_step("pip not available", False)
            return False
        
        # Check git (optional)
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            self._log_step("git available ✓")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._log_step("git not available (optional)", True)
        
        # Check available disk space
        disk_usage = shutil.disk_usage(self.project_root)
        free_gb = disk_usage.free / (1024**3)
        if free_gb < 5:
            self._log_step(f"Insufficient disk space: {free_gb:.1f}GB available, 5GB required", False)
            return False
        self._log_step(f"Disk space: {free_gb:.1f}GB available ✓")
        
        return True
    
    def create_directory_structure(self) -> bool:
        """Create project directory structure."""
        logger.info("📁 Creating directory structure...")
        
        try:
            for name, path in self.directories.items():
                path.mkdir(parents=True, exist_ok=True)
                self._log_step(f"Created directory: {name} ({path})")
            
            # Create subdirectories
            subdirs = [
                self.directories['automation'] / 'modules',
                self.directories['automation'] / 'strategies',
                self.directories['automation'] / 'utils',
                self.directories['data'] / 'trades',
                self.directories['data'] / 'backtest',
                self.directories['data'] / 'market_data',
                self.directories['logs'] / 'trades',
                self.directories['logs'] / 'system',
                self.directories['logs'] / 'errors',
                self.directories['reports'] / 'daily',
                self.directories['reports'] / 'weekly',
                self.directories['reports'] / 'monthly',
                self.directories['monitoring'] / 'metrics',
                self.directories['monitoring'] / 'alerts'
            ]
            
            for subdir in subdirs:
                subdir.mkdir(parents=True, exist_ok=True)
                self._log_step(f"Created subdirectory: {subdir}")
            
            return True
            
        except Exception as e:
            self._log_step(f"Failed to create directory structure: {e}", False)
            return False
    
    def install_dependencies(self, groups: List[str] = None, upgrade: bool = False) -> bool:
        """Install Python dependencies."""
        if groups is None:
            groups = ['core', 'database', 'financial', 'visualization']
        
        logger.info(f"📦 Installing dependencies for groups: {', '.join(groups)}...")
        
        # Collect all packages
        packages = []
        for group in groups:
            if group in self.dependency_groups:
                packages.extend(self.dependency_groups[group])
            else:
                logger.warning(f"Unknown dependency group: {group}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_packages = []
        for pkg in packages:
            pkg_name = pkg.split('>=')[0].split('==')[0]
            if pkg_name not in seen:
                seen.add(pkg_name)
                unique_packages.append(pkg)
        
        try:
            # Upgrade pip first
            logger.info("Upgrading pip...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ], check=True)
            self._log_step("pip upgraded")
            
            # Install packages in batches to avoid memory issues
            batch_size = 10
            for i in range(0, len(unique_packages), batch_size):
                batch = unique_packages[i:i + batch_size]
                cmd = [sys.executable, '-m', 'pip', 'install']
                if upgrade:
                    cmd.append('--upgrade')
                cmd.extend(batch)
                
                logger.info(f"Installing batch {i//batch_size + 1}: {', '.join(batch)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self._log_step(f"Installed batch {i//batch_size + 1}")
                else:
                    self._log_step(f"Failed to install batch {i//batch_size + 1}: {result.stderr}", False)
                    logger.error(f"Error output: {result.stderr}")
                    return False
            
            # Install Playwright browsers
            logger.info("Installing Playwright browsers...")
            subprocess.run([
                sys.executable, '-m', 'playwright', 'install', 'chromium'
            ], check=True)
            self._log_step("Playwright browsers installed")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self._log_step(f"Failed to install dependencies: {e}", False)
            return False
        except Exception as e:
            self._log_step(f"Unexpected error during installation: {e}", False)
            return False
    
    def setup_configuration(self, reset: bool = False) -> bool:
        """Setup configuration files."""
        logger.info("⚙️ Setting up configuration files...")
        
        try:
            for config_name, config_path in self.config_files.items():
                full_path = self.project_root / config_path
                
                if full_path.exists() and not reset:
                    self._log_step(f"Configuration exists: {config_name}")
                    continue
                
                # Create default configuration based on type
                config_data = self._get_default_config(config_name)
                
                # Ensure parent directory exists
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write configuration
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                self._log_step(f"Created configuration: {config_name}")
            
            return True
            
        except Exception as e:
            self._log_step(f"Failed to setup configuration: {e}", False)
            return False
    
    def _get_default_config(self, config_name: str) -> Dict:
        """Get default configuration for a given config type."""
        configs = {
            'trade_executor': {
                "enabled": True,
                "execution": {
                    "max_concurrent_trades": 5,
                    "retry_attempts": 3,
                    "timeout_seconds": 30,
                    "dry_run": True
                },
                "risk_management": {
                    "max_position_size_percent": 2.0,
                    "stop_loss_percent": 1.0,
                    "take_profit_percent": 2.0,
                    "max_daily_loss_percent": 5.0
                },
                "strategies": {
                    "FVG Midpoint": {
                        "enabled": True,
                        "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
                        "parameters": {
                            "min_gap_size": 10,
                            "max_gap_age_hours": 24,
                            "confidence_threshold": 0.7
                        }
                    }
                },
                "database": {
                    "path": "data/trades.db",
                    "backup_interval_hours": 24
                },
                "logging": {
                    "level": "INFO",
                    "file": "logs/trade_executor.log",
                    "max_size_mb": 100,
                    "backup_count": 5
                }
            },
            'monitoring_dashboard': {
                "enabled": True,
                "dashboard": {
                    "mode": "web",
                    "host": "localhost",
                    "port": 5000,
                    "auto_open_browser": True
                },
                "refresh_intervals": {
                    "web_seconds": 5,
                    "cli_seconds": 2
                },
                "metrics": {
                    "update_interval_seconds": 10,
                    "history_retention_days": 30
                },
                "charts": {
                    "equity_curve": True,
                    "trade_distribution": True,
                    "performance_metrics": True
                },
                "database": {
                    "path": "data/monitoring.db"
                }
            },
            'alert_system': {
                "enabled": True,
                "channels": {
                    "email": {
                        "enabled": False,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "username": "",
                        "password": "",
                        "recipients": []
                    },
                    "telegram": {
                        "enabled": False,
                        "bot_token": "",
                        "chat_id": ""
                    },
                    "file": {
                        "enabled": True,
                        "path": "logs/alerts.log"
                    }
                },
                "rate_limiting": {
                    "max_alerts_per_minute": 10,
                    "cooldown_seconds": 60
                },
                "database": {
                    "path": "data/alerts.db"
                }
            },
            'backtesting_engine': {
                "enabled": True,
                "backtesting": {
                    "default_capital": 10000,
                    "commission_percent": 0.1,
                    "slippage_percent": 0.05
                },
                "data_sources": {
                    "yahoo_finance": {
                        "enabled": True,
                        "api_key": ""
                    },
                    "csv": {
                        "enabled": True,
                        "data_directory": "data/market_data"
                    }
                },
                "strategies": {
                    "FVG Midpoint": {
                        "enabled": True,
                        "parameters": {
                            "min_gap_size": [5, 10, 15, 20],
                            "max_gap_age_hours": [12, 24, 48]
                        }
                    }
                },
                "output": {
                    "results_directory": "reports/backtest",
                    "save_trades": True,
                    "save_equity_curve": True
                },
                "database": {
                    "path": "data/backtest.db"
                }
            },
            'continuous_improvement': {
                "enabled": True,
                "monitoring": {
                    "check_interval_seconds": 30,
                    "ui_change_threshold": 0.7
                },
                "selectors": {
                    "login_username": [
                        "input[name='username']",
                        "input[type='email']",
                        "#username",
                        ".username-input"
                    ],
                    "login_password": [
                        "input[name='password']",
                        "input[type='password']",
                        "#password",
                        ".password-input"
                    ]
                },
                "snapshots": {
                    "enabled": True,
                    "directory": "screenshots/sessions",
                    "retention_days": 7
                },
                "database": {
                    "path": "data/improvement.db"
                }
            }
        }
        
        return configs.get(config_name, {})
    
    def initialize_database(self) -> bool:
        """Initialize database tables."""
        logger.info("🗄️ Initializing databases...")
        
        try:
            # Create database initialization script
            init_script = self.project_root / 'init_databases.py'
            
            init_code = '''
import sqlite3
import os
from pathlib import Path

def init_database(db_path: str, tables: dict):
    """Initialize SQLite database with tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for table_name, schema in tables.items():
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(schema)
    
    conn.commit()
    conn.close()
    print(f"Initialized database: {db_path}")

# Database schemas
databases = {
    "data/trades.db": {
        "trades": """
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                strategy TEXT,
                profit_loss REAL DEFAULT 0,
                commission REAL DEFAULT 0,
                notes TEXT
            )
        """,
        "positions": """
            CREATE TABLE positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL,
                unrealized_pnl REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
    },
    "data/monitoring.db": {
        "metrics": """
            CREATE TABLE metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT
            )
        """,
        "system_status": """
            CREATE TABLE system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            )
        """
    },
    "data/alerts.db": {
        "alerts": """
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                channel TEXT,
                sent BOOLEAN DEFAULT FALSE,
                metadata TEXT
            )
        """
    },
    "data/backtest.db": {
        "backtest_runs": """
            CREATE TABLE backtest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                parameters TEXT
            )
        """,
        "backtest_trades": """
            CREATE TABLE backtest_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                profit_loss REAL DEFAULT 0,
                FOREIGN KEY (run_id) REFERENCES backtest_runs (id)
            )
        """
    },
    "data/improvement.db": {
        "ui_changes": """
            CREATE TABLE ui_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                page_url TEXT NOT NULL,
                element_selector TEXT NOT NULL,
                change_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                confidence REAL DEFAULT 0,
                auto_fixed BOOLEAN DEFAULT FALSE
            )
        """,
        "sessions": """
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT NOT NULL,
                duration_seconds INTEGER,
                trades_captured INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                screenshot_path TEXT,
                metadata TEXT
            )
        """
    }
}

# Initialize all databases
for db_path, tables in databases.items():
    init_database(db_path, tables)

print("All databases initialized successfully!")
'''
            
            with open(init_script, 'w', encoding='utf-8') as f:
                f.write(init_code)
            
            # Run database initialization
            subprocess.run([sys.executable, str(init_script)], check=True)
            
            # Clean up initialization script
            init_script.unlink()
            
            self._log_step("Databases initialized")
            return True
            
        except Exception as e:
            self._log_step(f"Failed to initialize databases: {e}", False)
            return False
    
    def create_environment_file(self) -> bool:
        """Create .env file template."""
        logger.info("🔐 Creating environment file template...")
        
        try:
            env_file = self.project_root / '.env.template'
            env_content = '''
# TradeBot Sentinel Pro Advanced - Environment Configuration
# Copy this file to .env and fill in your actual values

# Trading Platform Credentials
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here

# Database Configuration
DATABASE_URL=sqlite:///data/trades.db
DATABASE_BACKUP_ENABLED=true

# Web Dashboard
DASHBOARD_HOST=localhost
DASHBOARD_PORT=5000
DASHBOARD_SECRET_KEY=your_secret_key_here

# Email Notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECIPIENTS=trader1@example.com,trader2@example.com

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Discord Notifications
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
QUANDL_API_KEY=your_quandl_key_here
YAHOO_FINANCE_API_KEY=your_yahoo_finance_key_here

# Cloud Storage (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your_s3_bucket_here

# Monitoring and Logging
LOG_LEVEL=INFO
LOG_FILE_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
METRICS_RETENTION_DAYS=30

# Security
ENCRYPTION_KEY=your_encryption_key_here
JWT_SECRET_KEY=your_jwt_secret_here
SESSION_TIMEOUT_MINUTES=60

# Performance
MAX_CONCURRENT_TRADES=5
REQUEST_TIMEOUT_SECONDS=30
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5

# Risk Management
MAX_POSITION_SIZE_PERCENT=2.0
STOP_LOSS_PERCENT=1.0
TAKE_PROFIT_PERCENT=2.0
MAX_DAILY_LOSS_PERCENT=5.0

# Development and Testing
DEBUG_MODE=false
DRY_RUN_MODE=true
TEST_MODE=false
SCREENSHOT_ON_ERROR=true

# Browser Configuration
HEADLESS_MODE=true
BROWSER_TIMEOUT_SECONDS=30
PAGE_LOAD_TIMEOUT_SECONDS=30
USER_AGENT_ROTATION=true

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=30
BACKUP_DIRECTORY=backups

# External Services
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=false
GRAFANA_PORT=3000
ELASTICSEARCH_URL=http://localhost:9200

# Timezone and Locale
TIMEZONE=UTC
LOCALE=en_US.UTF-8
DATE_FORMAT=%Y-%m-%d
TIME_FORMAT=%H:%M:%S

# Feature Flags
FEATURE_BACKTESTING=true
FEATURE_LIVE_TRADING=false
FEATURE_PAPER_TRADING=true
FEATURE_SOCIAL_TRADING=false
FEATURE_AI_SIGNALS=false

# Advanced Configuration
CUSTOM_STRATEGIES_PATH=automation/strategies
CUSTOM_INDICATORS_PATH=automation/indicators
CUSTOM_TEMPLATES_PATH=automation/templates
CUSTOM_PLUGINS_PATH=automation/plugins
'''
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content.strip())
            
            self._log_step("Environment file template created")
            
            # Check if .env already exists
            actual_env = self.project_root / '.env'
            if not actual_env.exists():
                logger.info("📝 Please copy .env.template to .env and configure your settings")
            
            return True
            
        except Exception as e:
            self._log_step(f"Failed to create environment file: {e}", False)
            return False
    
    def validate_installation(self) -> Tuple[bool, List[str]]:
        """Validate the installation."""
        logger.info("🔍 Validating installation...")
        
        issues = []
        
        # Check directories
        for name, path in self.directories.items():
            if not path.exists():
                issues.append(f"Missing directory: {name} ({path})")
        
        # Check configuration files
        for name, path in self.config_files.items():
            full_path = self.project_root / path
            if not full_path.exists():
                issues.append(f"Missing configuration: {name} ({path})")
            else:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    issues.append(f"Invalid JSON in configuration: {name}")
        
        # Check core dependencies
        core_packages = ['playwright', 'requests', 'flask', 'pandas', 'numpy']
        for package in core_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(f"Missing core package: {package}")
        
        # Check database files
        db_files = ['data/trades.db', 'data/monitoring.db', 'data/alerts.db']
        for db_file in db_files:
            db_path = self.project_root / db_file
            if not db_path.exists():
                issues.append(f"Missing database: {db_file}")
        
        # Check environment file
        env_template = self.project_root / '.env.template'
        if not env_template.exists():
            issues.append("Missing .env.template file")
        
        success = len(issues) == 0
        
        if success:
            self._log_step("Installation validation passed")
        else:
            self._log_step(f"Installation validation failed: {len(issues)} issues found", False)
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        return success, issues
    
    def generate_installation_report(self) -> str:
        """Generate installation report."""
        report_path = self.project_root / f'installation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            'project_root': str(self.project_root),
            'installation_log': self.installation_log,
            'directories_created': list(self.directories.keys()),
            'config_files_created': list(self.config_files.keys())
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Installation report saved: {report_path}")
        return str(report_path)
    
    def run_full_setup(self, groups: List[str] = None, reset: bool = False) -> bool:
        """Run complete setup process."""
        logger.info("🚀 Starting TradeBot Sentinel Pro Advanced setup...")
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Directory Structure", self.create_directory_structure),
            ("Dependencies", lambda: self.install_dependencies(groups)),
            ("Configuration", lambda: self.setup_configuration(reset)),
            ("Database", self.initialize_database),
            ("Environment", self.create_environment_file)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*50}")
            logger.info(f"Step: {step_name}")
            logger.info(f"{'='*50}")
            
            try:
                if not step_func():
                    logger.error(f"❌ Setup failed at step: {step_name}")
                    return False
            except Exception as e:
                logger.error(f"❌ Unexpected error in step {step_name}: {e}")
                return False
        
        # Validate installation
        logger.info(f"\n{'='*50}")
        logger.info("Validation")
        logger.info(f"{'='*50}")
        
        success, issues = self.validate_installation()
        
        # Generate report
        report_path = self.generate_installation_report()
        
        if success:
            logger.info("\n🎉 Setup completed successfully!")
            logger.info("\n📋 Next steps:")
            logger.info("1. Copy .env.template to .env and configure your settings")
            logger.info("2. Run: python tradebot_sentinel_pro_advanced.py --help")
            logger.info("3. Start with: python tradebot_sentinel_pro_advanced.py --mode capture")
            logger.info(f"4. Check installation report: {report_path}")
            return True
        else:
            logger.error("\n❌ Setup completed with issues. Please check the log and fix the problems.")
            return False

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="TradeBot Sentinel Pro Advanced Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_advanced.py --full              # Full installation
  python setup_advanced.py --minimal           # Minimal installation
  python setup_advanced.py --dev               # Development installation
  python setup_advanced.py --validate          # Validate existing installation
  python setup_advanced.py --reset             # Reset configuration
        """
    )
    
    parser.add_argument('--full', action='store_true',
                       help='Full installation with all dependencies')
    parser.add_argument('--minimal', action='store_true',
                       help='Minimal installation with core dependencies only')
    parser.add_argument('--dev', action='store_true',
                       help='Development installation with testing tools')
    parser.add_argument('--docker', action='store_true',
                       help='Docker-based installation setup')
    parser.add_argument('--validate', action='store_true',
                       help='Validate existing installation')
    parser.add_argument('--reset', action='store_true',
                       help='Reset configuration to defaults')
    parser.add_argument('--groups', nargs='+',
                       help='Specific dependency groups to install')
    parser.add_argument('--upgrade', action='store_true',
                       help='Upgrade existing packages')
    
    args = parser.parse_args()
    
    setup = TradeBotAdvancedSetup()
    
    # Handle validation only
    if args.validate:
        success, issues = setup.validate_installation()
        if success:
            print("✅ Installation is valid")
            sys.exit(0)
        else:
            print("❌ Installation has issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
    
    # Determine dependency groups
    groups = None
    if args.minimal:
        groups = ['core']
    elif args.dev:
        groups = ['core', 'database', 'financial', 'visualization', 'testing', 'development']
    elif args.full:
        groups = list(setup.dependency_groups.keys())
    elif args.groups:
        groups = args.groups
    else:
        # Default installation
        groups = ['core', 'database', 'financial', 'visualization', 'notifications']
    
    # Run setup
    success = setup.run_full_setup(groups=groups, reset=args.reset)
    
    if success:
        print("\n🎉 Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Check the logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()