#!/usr/bin/env python3
"""
Logger Setup for TradeBot Sentinel Pro Advanced

Provides comprehensive logging configuration with file rotation,
structured logging, and multiple output formats for all system components.

Author: TradeBot Sentinel Team
Version: 2.0.0
License: MIT
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = "INFO"
    format_type: str = "detailed"  # simple, detailed, json
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_directory: str = "logs"
    

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_'):
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Create colored level name
        colored_level = f"{level_color}{record.levelname}{reset_color}"
        
        # Replace level name in record
        original_levelname = record.levelname
        record.levelname = colored_level
        
        # Format the record
        formatted = super().format(record)
        
        # Restore original level name
        record.levelname = original_levelname
        
        return formatted


class TradeLogFilter(logging.Filter):
    """Filter for trade-related logs"""
    
    def filter(self, record):
        """Filter trade-related log records"""
        trade_keywords = ['trade', 'order', 'execution', 'buy', 'sell', 'position']
        message = record.getMessage().lower()
        return any(keyword in message for keyword in trade_keywords)


class ErrorLogFilter(logging.Filter):
    """Filter for error logs"""
    
    def filter(self, record):
        """Filter error log records"""
        return record.levelno >= logging.ERROR


def setup_logger(name: str, log_file: Optional[str] = None, 
                 level: str = "INFO", config: Optional[LogConfig] = None) -> logging.Logger:
    """
    Setup comprehensive logger with file rotation and structured logging.
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Logging level
        config: Logging configuration
    
    Returns:
        Configured logger instance
    """
    # Use provided config or create default
    if config is None:
        config = LogConfig(level=level)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create log directory
    log_dir = Path(config.log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup formatters
    formatters = {
        'simple': logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ),
        'detailed': logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        ),
        'json': JSONFormatter()
    }
    
    formatter = formatters.get(config.format_type, formatters['detailed'])
    
    # Console handler
    if config.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Use colored formatter for console if not JSON
        if config.format_type != 'json' and os.getenv('TERM') != 'dumb':
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        else:
            console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    # File handler
    if config.file_enabled:
        if log_file is None:
            log_file = log_dir / f"{name.lower().replace(' ', '_')}.log"
        else:
            log_file = Path(log_file)
        
        # Ensure log file directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Separate error log file
        error_log_file = log_file.parent / f"{log_file.stem}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(ErrorLogFilter())
        logger.addHandler(error_handler)
        
        # Trade-specific log file
        trade_log_file = log_file.parent / f"{log_file.stem}_trades.log"
        trade_handler = logging.handlers.RotatingFileHandler(
            trade_log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        trade_handler.setFormatter(formatter)
        trade_handler.addFilter(TradeLogFilter())
        logger.addHandler(trade_handler)
    
    # Add system info to first log
    logger.info(f"Logger '{name}' initialized - Level: {config.level}, Format: {config.format_type}")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Platform: {sys.platform}")
    logger.debug(f"Working directory: {os.getcwd()}")
    
    return logger


def setup_system_loggers(base_config: Optional[LogConfig] = None) -> Dict[str, logging.Logger]:
    """
    Setup all system loggers with consistent configuration.
    
    Args:
        base_config: Base logging configuration
    
    Returns:
        Dictionary of configured loggers
    """
    if base_config is None:
        base_config = LogConfig()
    
    loggers = {}
    
    # System component loggers
    logger_configs = {
        'TradeBot': 'tradebot_main.log',
        'TradeExecutor': 'trade_executor.log',
        'MonitoringDashboard': 'monitoring.log',
        'AlertSystem': 'alerts.log',
        'BacktestingEngine': 'backtesting.log',
        'ContinuousImprovement': 'improvement.log',
        'ConfigManager': 'config.log',
        'DatabaseManager': 'database.log',
        'HealthMonitor': 'health.log'
    }
    
    for logger_name, log_file in logger_configs.items():
        loggers[logger_name] = setup_logger(
            name=logger_name,
            log_file=Path(base_config.log_directory) / log_file,
            level=base_config.level,
            config=base_config
        )
    
    return loggers


def configure_third_party_loggers(level: str = "WARNING"):
    """
    Configure third-party library loggers to reduce noise.
    
    Args:
        level: Logging level for third-party loggers
    """
    third_party_loggers = [
        'urllib3',
        'requests',
        'selenium',
        'asyncio',
        'websockets',
        'aiohttp',
        'psycopg2',
        'mysql.connector'
    ]
    
    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))


def get_log_stats(log_directory: str = "logs") -> Dict[str, Any]:
    """
    Get logging statistics.
    
    Args:
        log_directory: Log directory path
    
    Returns:
        Dictionary of log statistics
    """
    log_dir = Path(log_directory)
    
    if not log_dir.exists():
        return {"error": "Log directory not found"}
    
    stats = {
        "total_log_files": 0,
        "total_size_mb": 0.0,
        "log_files": [],
        "oldest_log": None,
        "newest_log": None
    }
    
    try:
        log_files = list(log_dir.glob("*.log*"))
        stats["total_log_files"] = len(log_files)
        
        if log_files:
            total_size = sum(f.stat().st_size for f in log_files)
            stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # Get file info
            for log_file in log_files:
                file_stat = log_file.stat()
                stats["log_files"].append({
                    "name": log_file.name,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
            
            # Find oldest and newest
            oldest = min(log_files, key=lambda f: f.stat().st_mtime)
            newest = max(log_files, key=lambda f: f.stat().st_mtime)
            
            stats["oldest_log"] = {
                "name": oldest.name,
                "modified": datetime.fromtimestamp(oldest.stat().st_mtime).isoformat()
            }
            
            stats["newest_log"] = {
                "name": newest.name,
                "modified": datetime.fromtimestamp(newest.stat().st_mtime).isoformat()
            }
    
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def cleanup_old_logs(log_directory: str = "logs", days: int = 30):
    """
    Clean up old log files.
    
    Args:
        log_directory: Log directory path
        days: Number of days to keep logs
    """
    log_dir = Path(log_directory)
    
    if not log_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    deleted_count = 0
    deleted_size = 0
    
    try:
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                file_size = log_file.stat().st_size
                log_file.unlink()
                deleted_count += 1
                deleted_size += file_size
        
        if deleted_count > 0:
            logger = logging.getLogger("LogCleanup")
            logger.info(f"Cleaned up {deleted_count} old log files ({deleted_size / (1024*1024):.2f} MB)")
    
    except Exception as e:
        logger = logging.getLogger("LogCleanup")
        logger.error(f"Error cleaning up logs: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test logger setup
    test_config = LogConfig(
        level="DEBUG",
        format_type="detailed",
        log_directory="test_logs"
    )
    
    logger = setup_logger("TestLogger", config=test_config)
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test trade-related logging
    logger.info("Trade executed: BUY BTCUSDT 0.1 @ 45000")
    logger.error("Trade execution failed: Connection timeout")
    
    # Test JSON logging
    json_config = LogConfig(
        level="INFO",
        format_type="json",
        log_directory="test_logs"
    )
    
    json_logger = setup_logger("JSONTestLogger", config=json_config)
    json_logger.info("JSON formatted log message", extra={"trade_id": 12345, "symbol": "BTCUSDT"})
    
    # Get log stats
    stats = get_log_stats("test_logs")
    print(f"Log statistics: {json.dumps(stats, indent=2)}")
    
    print("Logger testing completed. Check test_logs directory for output.")