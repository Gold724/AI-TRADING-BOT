#!/usr/bin/env python3
"""
Configuration Manager for TradeBot Sentinel Pro Advanced

Handles loading, validation, and management of configuration files
for all automation modules with environment variable support.

Author: TradeBot Sentinel Team
Version: 2.0.0
License: MIT
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TradingConfig:
    """Trading configuration settings"""
    dry_run: bool = True
    max_trades_per_day: int = 10
    max_position_size: float = 1000.0
    stop_loss_percentage: float = 2.0
    take_profit_percentage: float = 5.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 30
    symbols: list = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTCUSDT", "ETHUSDT"]


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    dashboard_enabled: bool = True
    dashboard_port: int = 8080
    dashboard_host: str = "localhost"
    update_interval: int = 5
    metrics_retention_days: int = 30
    screenshot_on_error: bool = True
    log_level: str = "INFO"


@dataclass
class AlertConfig:
    """Alert system configuration settings"""
    enabled: bool = True
    email_enabled: bool = False
    telegram_enabled: bool = False
    slack_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    slack_webhook_url: str = ""
    alert_cooldown_minutes: int = 5


@dataclass
class BacktestConfig:
    """Backtesting configuration settings"""
    enabled: bool = True
    data_source: str = "historical"
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    initial_balance: float = 10000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    max_drawdown: float = 0.2


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    enabled: bool = True
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "tradebot"
    username: str = ""
    password: str = ""
    connection_pool_size: int = 5
    connection_timeout: int = 30
    sqlite_path: str = "data/tradebot.db"


class ConfigManager:
    """
    Centralized configuration management for TradeBot Sentinel Pro Advanced.
    Handles loading, validation, and environment variable integration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        self.config_path = Path(config_path) if config_path else Path("config/main_config.json")
        self.project_root = Path(__file__).parent.parent
        self.logger = logging.getLogger("ConfigManager")
        
        # Configuration objects
        self.trading = TradingConfig()
        self.monitoring = MonitoringConfig()
        self.alerts = AlertConfig()
        self.backtesting = BacktestConfig()
        self.database = DatabaseConfig()
        
        # Load configurations
        self._load_configurations()
        self._apply_environment_overrides()
        
        self.logger.info(f"Configuration loaded from {self.config_path}")
    
    def _load_configurations(self):
        """Load configurations from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load each configuration section
                if 'trading' in config_data:
                    self.trading = TradingConfig(**config_data['trading'])
                
                if 'monitoring' in config_data:
                    self.monitoring = MonitoringConfig(**config_data['monitoring'])
                
                if 'alerts' in config_data:
                    self.alerts = AlertConfig(**config_data['alerts'])
                
                if 'backtesting' in config_data:
                    self.backtesting = BacktestConfig(**config_data['backtesting'])
                
                if 'database' in config_data:
                    self.database = DatabaseConfig(**config_data['database'])
                
                self.logger.info("Configuration loaded successfully")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.logger.info("Using default configuration")
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides"""
        try:
            # Trading overrides
            if os.getenv('DRY_RUN_MODE'):
                self.trading.dry_run = os.getenv('DRY_RUN_MODE', 'true').lower() == 'true'
            
            if os.getenv('MAX_TRADES_PER_DAY'):
                self.trading.max_trades_per_day = int(os.getenv('MAX_TRADES_PER_DAY'))
            
            if os.getenv('MAX_POSITION_SIZE'):
                self.trading.max_position_size = float(os.getenv('MAX_POSITION_SIZE'))
            
            # Monitoring overrides
            if os.getenv('DASHBOARD_PORT'):
                self.monitoring.dashboard_port = int(os.getenv('DASHBOARD_PORT'))
            
            if os.getenv('LOG_LEVEL'):
                self.monitoring.log_level = os.getenv('LOG_LEVEL')
            
            # Alert overrides
            if os.getenv('TELEGRAM_BOT_TOKEN'):
                self.alerts.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                self.alerts.telegram_enabled = True
            
            if os.getenv('TELEGRAM_CHAT_ID'):
                self.alerts.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if os.getenv('SLACK_WEBHOOK_URL'):
                self.alerts.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
                self.alerts.slack_enabled = True
            
            # Database overrides
            if os.getenv('DATABASE_URL'):
                self._parse_database_url(os.getenv('DATABASE_URL'))
            
            if os.getenv('DATABASE_TYPE'):
                self.database.type = os.getenv('DATABASE_TYPE')
            
            self.logger.info("Environment overrides applied")
            
        except Exception as e:
            self.logger.error(f"Failed to apply environment overrides: {e}")
    
    def _parse_database_url(self, database_url: str):
        """Parse database URL and update configuration"""
        try:
            # Parse URL format: postgresql://user:pass@host:port/dbname
            if '://' in database_url:
                protocol, rest = database_url.split('://', 1)
                self.database.type = protocol
                
                if '@' in rest:
                    auth, host_db = rest.split('@', 1)
                    if ':' in auth:
                        self.database.username, self.database.password = auth.split(':', 1)
                    else:
                        self.database.username = auth
                    
                    if '/' in host_db:
                        host_port, self.database.database = host_db.split('/', 1)
                        if ':' in host_port:
                            self.database.host, port_str = host_port.split(':', 1)
                            self.database.port = int(port_str)
                        else:
                            self.database.host = host_port
                
        except Exception as e:
            self.logger.error(f"Failed to parse database URL: {e}")
    
    def _create_default_config(self):
        """Create default configuration file"""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                "trading": asdict(self.trading),
                "monitoring": asdict(self.monitoring),
                "alerts": asdict(self.alerts),
                "backtesting": asdict(self.backtesting),
                "database": asdict(self.database),
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "2.0.0"
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Default configuration created: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
    
    def get_config(self, section: str) -> Optional[Any]:
        """Get configuration section"""
        sections = {
            'trading': self.trading,
            'monitoring': self.monitoring,
            'alerts': self.alerts,
            'backtesting': self.backtesting,
            'database': self.database
        }
        return sections.get(section)
    
    def update_config(self, section: str, updates: Dict[str, Any]):
        """Update configuration section"""
        try:
            config_obj = self.get_config(section)
            if config_obj:
                for key, value in updates.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
                        self.logger.info(f"Updated {section}.{key} = {value}")
                    else:
                        self.logger.warning(f"Unknown config key: {section}.{key}")
            else:
                self.logger.error(f"Unknown config section: {section}")
                
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                "trading": asdict(self.trading),
                "monitoring": asdict(self.monitoring),
                "alerts": asdict(self.alerts),
                "backtesting": asdict(self.backtesting),
                "database": asdict(self.database),
                "metadata": {
                    "updated": datetime.now().isoformat(),
                    "version": "2.0.0"
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration settings"""
        validation_results = {
            'trading': True,
            'monitoring': True,
            'alerts': True,
            'backtesting': True,
            'database': True
        }
        
        try:
            # Validate trading config
            if self.trading.max_trades_per_day <= 0:
                validation_results['trading'] = False
                self.logger.error("Invalid trading config: max_trades_per_day must be > 0")
            
            if self.trading.max_position_size <= 0:
                validation_results['trading'] = False
                self.logger.error("Invalid trading config: max_position_size must be > 0")
            
            # Validate monitoring config
            if not (1024 <= self.monitoring.dashboard_port <= 65535):
                validation_results['monitoring'] = False
                self.logger.error("Invalid monitoring config: dashboard_port must be 1024-65535")
            
            # Validate alert config
            if self.alerts.telegram_enabled and not self.alerts.telegram_bot_token:
                validation_results['alerts'] = False
                self.logger.error("Invalid alert config: telegram_bot_token required when enabled")
            
            # Validate backtesting config
            if self.backtesting.initial_balance <= 0:
                validation_results['backtesting'] = False
                self.logger.error("Invalid backtesting config: initial_balance must be > 0")
            
            # Validate database config
            if self.database.enabled and self.database.type not in ['sqlite', 'postgresql', 'mysql']:
                validation_results['database'] = False
                self.logger.error("Invalid database config: unsupported database type")
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return {k: False for k in validation_results}
        
        return validation_results
    
    def get_database_connection_string(self) -> str:
        """Get database connection string"""
        if self.database.type == 'sqlite':
            return f"sqlite:///{self.database.sqlite_path}"
        elif self.database.type == 'postgresql':
            return f"postgresql://{self.database.username}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.database}"
        elif self.database.type == 'mysql':
            return f"mysql://{self.database.username}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.database}"
        else:
            return ""
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"ConfigManager(path={self.config_path}, sections=[trading, monitoring, alerts, backtesting, database])"