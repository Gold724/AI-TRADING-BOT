#!/usr/bin/env python3
"""
AI Trading Sentinel - Multi-Account Scaling Architecture
Designed for running multiple trading accounts, competitions, or brokers in parallel
with isolated environments and comprehensive resource management.
"""

import asyncio
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from uuid import uuid4

import psutil
import redis
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# =============================================================================
# CONFIGURATION AND ENUMS
# =============================================================================

class AccountStatus(Enum):
    """Account status enumeration"""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class ResourceType(Enum):
    """Resource type enumeration"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK_IO = "disk_io"
    DATABASE_CONNECTIONS = "database_connections"
    REDIS_CONNECTIONS = "redis_connections"

class IsolationLevel(Enum):
    """Isolation level for account environments"""
    SHARED = "shared"  # Shared resources, separate data
    ISOLATED = "isolated"  # Separate resources, separate data
    CONTAINERIZED = "containerized"  # Docker containers
    VIRTUALIZED = "virtualized"  # Full VM isolation

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ResourceLimits:
    """Resource limits for an account"""
    max_cpu_percent: float = 25.0  # Max CPU usage percentage
    max_memory_mb: int = 1024  # Max memory usage in MB
    max_network_mbps: float = 10.0  # Max network bandwidth in Mbps
    max_disk_iops: int = 1000  # Max disk I/O operations per second
    max_db_connections: int = 10  # Max database connections
    max_redis_connections: int = 5  # Max Redis connections
    max_orders_per_minute: int = 100  # Max trading orders per minute
    max_api_calls_per_minute: int = 1000  # Max API calls per minute

@dataclass
class AccountConfig:
    """Configuration for a trading account"""
    account_id: str
    account_name: str
    broker: str
    account_type: str  # 'live', 'demo', 'competition'
    isolation_level: IsolationLevel
    resource_limits: ResourceLimits
    trading_strategy: str
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    auto_restart: bool = True
    max_restart_attempts: int = 3
    restart_delay_seconds: int = 30
    health_check_interval: int = 60
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AccountMetrics:
    """Real-time metrics for an account"""
    account_id: str
    status: AccountStatus
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    network_usage_mbps: float = 0.0
    disk_iops: int = 0
    db_connections: int = 0
    redis_connections: int = 0
    orders_per_minute: int = 0
    api_calls_per_minute: int = 0
    uptime_seconds: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    error_count: int = 0
    restart_count: int = 0
    total_trades: int = 0
    total_pnl: float = 0.0
    last_trade_time: Optional[datetime] = None

# =============================================================================
# DATABASE MODELS
# =============================================================================

Base = declarative_base()

class TradingAccount(Base):
    """Database model for trading accounts"""
    __tablename__ = 'trading_accounts'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    broker = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)
    isolation_level = Column(String(50), nullable=False)
    resource_limits = Column(JSON, nullable=False)
    trading_strategy = Column(String(255), nullable=False)
    config_overrides = Column(JSON, default={})
    environment_variables = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    auto_restart = Column(Boolean, default=True)
    max_restart_attempts = Column(Integer, default=3)
    restart_delay_seconds = Column(Integer, default=30)
    health_check_interval = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AccountMetricsHistory(Base):
    """Database model for account metrics history"""
    __tablename__ = 'account_metrics_history'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    account_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), nullable=False)
    cpu_usage_percent = Column(Float, default=0.0)
    memory_usage_mb = Column(Float, default=0.0)
    network_usage_mbps = Column(Float, default=0.0)
    disk_iops = Column(Integer, default=0)
    db_connections = Column(Integer, default=0)
    redis_connections = Column(Integer, default=0)
    orders_per_minute = Column(Integer, default=0)
    api_calls_per_minute = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    restart_count = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)

# =============================================================================
# RESOURCE MANAGER
# =============================================================================

class ResourceManager:
    """Manages system resources across multiple trading accounts"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        self.resource_locks = {}
        self.resource_usage = {}
        self.system_limits = self._get_system_limits()
        
    def _get_system_limits(self) -> Dict[str, float]:
        """Get system resource limits"""
        return {
            'max_cpu_percent': 80.0,  # Reserve 20% for system
            'max_memory_mb': psutil.virtual_memory().total / (1024 * 1024) * 0.8,  # 80% of RAM
            'max_db_connections': 180,  # Reserve 20 connections
            'max_redis_connections': 95,  # Reserve 5 connections
        }
    
    def allocate_resources(self, account_id: str, limits: ResourceLimits) -> bool:
        """Allocate resources for an account"""
        try:
            # Check if resources are available
            current_usage = self._get_current_usage()
            
            if not self._can_allocate(current_usage, limits):
                self.logger.warning(f"Cannot allocate resources for account {account_id}: insufficient resources")
                return False
            
            # Allocate resources
            allocation = {
                'account_id': account_id,
                'limits': limits.__dict__,
                'allocated_at': datetime.utcnow().isoformat(),
            }
            
            self.redis_client.hset(
                'resource_allocations',
                account_id,
                json.dumps(allocation)
            )
            
            self.logger.info(f"Resources allocated for account {account_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error allocating resources for account {account_id}: {e}")
            return False
    
    def deallocate_resources(self, account_id: str) -> bool:
        """Deallocate resources for an account"""
        try:
            self.redis_client.hdel('resource_allocations', account_id)
            self.logger.info(f"Resources deallocated for account {account_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deallocating resources for account {account_id}: {e}")
            return False
    
    def _get_current_usage(self) -> Dict[str, float]:
        """Get current system resource usage"""
        allocations = self.redis_client.hgetall('resource_allocations')
        
        usage = {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'db_connections': 0,
            'redis_connections': 0,
        }
        
        for allocation_data in allocations.values():
            allocation = json.loads(allocation_data)
            limits = allocation['limits']
            
            usage['cpu_percent'] += limits['max_cpu_percent']
            usage['memory_mb'] += limits['max_memory_mb']
            usage['db_connections'] += limits['max_db_connections']
            usage['redis_connections'] += limits['max_redis_connections']
        
        return usage
    
    def _can_allocate(self, current_usage: Dict[str, float], limits: ResourceLimits) -> bool:
        """Check if resources can be allocated"""
        checks = [
            current_usage['cpu_percent'] + limits.max_cpu_percent <= self.system_limits['max_cpu_percent'],
            current_usage['memory_mb'] + limits.max_memory_mb <= self.system_limits['max_memory_mb'],
            current_usage['db_connections'] + limits.max_db_connections <= self.system_limits['max_db_connections'],
            current_usage['redis_connections'] + limits.max_redis_connections <= self.system_limits['max_redis_connections'],
        ]
        
        return all(checks)
    
    def get_resource_usage_report(self) -> Dict[str, Any]:
        """Generate resource usage report"""
        current_usage = self._get_current_usage()
        system_usage = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_mb': psutil.virtual_memory().used / (1024 * 1024),
            'disk_usage_percent': psutil.disk_usage('/').percent,
        }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'allocated_resources': current_usage,
            'system_limits': self.system_limits,
            'actual_system_usage': system_usage,
            'utilization_percent': {
                'cpu': (current_usage['cpu_percent'] / self.system_limits['max_cpu_percent']) * 100,
                'memory': (current_usage['memory_mb'] / self.system_limits['max_memory_mb']) * 100,
                'db_connections': (current_usage['db_connections'] / self.system_limits['max_db_connections']) * 100,
                'redis_connections': (current_usage['redis_connections'] / self.system_limits['max_redis_connections']) * 100,
            }
        }

# =============================================================================
# ACCOUNT MANAGER
# =============================================================================

class AccountManager:
    """Manages individual trading account instances"""
    
    def __init__(self, account_config: AccountConfig, db_session: Session, redis_client: redis.Redis):
        self.config = account_config
        self.db_session = db_session
        self.redis_client = redis_client
        self.logger = logging.getLogger(f"account.{account_config.account_id}")
        self.process = None
        self.thread = None
        self.metrics = AccountMetrics(account_id=account_config.account_id, status=AccountStatus.INACTIVE)
        self.start_time = None
        self.restart_attempts = 0
        self.last_health_check = datetime.utcnow()
        self._stop_event = threading.Event()
        
    def start(self) -> bool:
        """Start the trading account"""
        try:
            if self.metrics.status in [AccountStatus.ACTIVE, AccountStatus.STARTING]:
                self.logger.warning(f"Account {self.config.account_id} is already running")
                return False
            
            self.logger.info(f"Starting account {self.config.account_id}")
            self.metrics.status = AccountStatus.STARTING
            self._update_metrics()
            
            # Create isolated environment
            if not self._setup_environment():
                self.metrics.status = AccountStatus.ERROR
                self._update_metrics()
                return False
            
            # Start trading process
            if not self._start_trading_process():
                self.metrics.status = AccountStatus.ERROR
                self._update_metrics()
                return False
            
            # Start monitoring thread
            self.thread = threading.Thread(target=self._monitor_account, daemon=True)
            self.thread.start()
            
            self.metrics.status = AccountStatus.ACTIVE
            self.start_time = datetime.utcnow()
            self.restart_attempts = 0
            self._update_metrics()
            
            self.logger.info(f"Account {self.config.account_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting account {self.config.account_id}: {e}")
            self.metrics.status = AccountStatus.ERROR
            self._update_metrics()
            return False
    
    def stop(self) -> bool:
        """Stop the trading account"""
        try:
            if self.metrics.status == AccountStatus.INACTIVE:
                self.logger.warning(f"Account {self.config.account_id} is already stopped")
                return True
            
            self.logger.info(f"Stopping account {self.config.account_id}")
            self.metrics.status = AccountStatus.STOPPING
            self._update_metrics()
            
            # Signal stop
            self._stop_event.set()
            
            # Stop trading process
            if self.process and self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=30)
                
                if self.process.is_alive():
                    self.process.kill()
                    self.process.join()
            
            # Wait for monitoring thread
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=10)
            
            # Cleanup environment
            self._cleanup_environment()
            
            self.metrics.status = AccountStatus.INACTIVE
            self._update_metrics()
            
            self.logger.info(f"Account {self.config.account_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping account {self.config.account_id}: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause the trading account"""
        try:
            if self.metrics.status != AccountStatus.ACTIVE:
                return False
            
            self.logger.info(f"Pausing account {self.config.account_id}")
            
            # Send pause signal to trading process
            if self.process:
                # Implementation depends on trading bot's pause mechanism
                pass
            
            self.metrics.status = AccountStatus.PAUSED
            self._update_metrics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing account {self.config.account_id}: {e}")
            return False
    
    def resume(self) -> bool:
        """Resume the trading account"""
        try:
            if self.metrics.status != AccountStatus.PAUSED:
                return False
            
            self.logger.info(f"Resuming account {self.config.account_id}")
            
            # Send resume signal to trading process
            if self.process:
                # Implementation depends on trading bot's resume mechanism
                pass
            
            self.metrics.status = AccountStatus.ACTIVE
            self._update_metrics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming account {self.config.account_id}: {e}")
            return False
    
    def _setup_environment(self) -> bool:
        """Setup isolated environment for the account"""
        try:
            # Create account-specific directories
            account_dir = Path(f"/var/lib/trading-sentinel/accounts/{self.config.account_id}")
            account_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (account_dir / "logs").mkdir(exist_ok=True)
            (account_dir / "data").mkdir(exist_ok=True)
            (account_dir / "config").mkdir(exist_ok=True)
            (account_dir / "cache").mkdir(exist_ok=True)
            
            # Create account-specific configuration
            config_file = account_dir / "config" / "trading.json"
            account_config = {
                'account_id': self.config.account_id,
                'broker': self.config.broker,
                'strategy': self.config.trading_strategy,
                'isolation_level': self.config.isolation_level.value,
                'resource_limits': self.config.resource_limits.__dict__,
                **self.config.config_overrides
            }
            
            with open(config_file, 'w') as f:
                json.dump(account_config, f, indent=2)
            
            # Setup environment variables
            env_file = account_dir / "config" / ".env"
            with open(env_file, 'w') as f:
                f.write(f"ACCOUNT_ID={self.config.account_id}\n")
                f.write(f"ACCOUNT_DIR={account_dir}\n")
                f.write(f"LOG_LEVEL=INFO\n")
                
                for key, value in self.config.environment_variables.items():
                    f.write(f"{key}={value}\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up environment: {e}")
            return False
    
    def _start_trading_process(self) -> bool:
        """Start the trading process"""
        try:
            # This would start the actual trading bot process
            # Implementation depends on your trading bot architecture
            
            # For now, simulate with a dummy process
            import multiprocessing
            
            def trading_worker(account_id, config_path):
                """Dummy trading worker process"""
                import time
                import random
                
                while True:
                    # Simulate trading activity
                    time.sleep(random.uniform(1, 5))
                    
                    # Update metrics in Redis
                    # This would be replaced with actual trading logic
                    pass
            
            account_dir = Path(f"/var/lib/trading-sentinel/accounts/{self.config.account_id}")
            config_path = account_dir / "config" / "trading.json"
            
            self.process = multiprocessing.Process(
                target=trading_worker,
                args=(self.config.account_id, str(config_path))
            )
            self.process.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting trading process: {e}")
            return False
    
    def _monitor_account(self):
        """Monitor account health and performance"""
        while not self._stop_event.is_set():
            try:
                # Update metrics
                self._collect_metrics()
                self._update_metrics()
                
                # Health check
                if not self._health_check():
                    self.logger.warning(f"Health check failed for account {self.config.account_id}")
                    
                    if self.config.auto_restart and self.restart_attempts < self.config.max_restart_attempts:
                        self.logger.info(f"Attempting to restart account {self.config.account_id}")
                        self._restart_account()
                
                # Sleep until next check
                self._stop_event.wait(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring thread: {e}")
                self._stop_event.wait(10)
    
    def _collect_metrics(self):
        """Collect current metrics for the account"""
        try:
            # Update uptime
            if self.start_time:
                self.metrics.uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())
            
            # Collect process metrics
            if self.process and self.process.is_alive():
                try:
                    process = psutil.Process(self.process.pid)
                    self.metrics.cpu_usage_percent = process.cpu_percent()
                    self.metrics.memory_usage_mb = process.memory_info().rss / (1024 * 1024)
                except psutil.NoSuchProcess:
                    pass
            
            # Update heartbeat
            self.metrics.last_heartbeat = datetime.utcnow()
            
            # Collect trading-specific metrics from Redis
            metrics_key = f"account_metrics:{self.config.account_id}"
            cached_metrics = self.redis_client.hgetall(metrics_key)
            
            if cached_metrics:
                self.metrics.orders_per_minute = int(cached_metrics.get(b'orders_per_minute', 0))
                self.metrics.api_calls_per_minute = int(cached_metrics.get(b'api_calls_per_minute', 0))
                self.metrics.total_trades = int(cached_metrics.get(b'total_trades', 0))
                self.metrics.total_pnl = float(cached_metrics.get(b'total_pnl', 0.0))
                
                last_trade_str = cached_metrics.get(b'last_trade_time')
                if last_trade_str:
                    self.metrics.last_trade_time = datetime.fromisoformat(last_trade_str.decode())
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
    
    def _update_metrics(self):
        """Update metrics in database and cache"""
        try:
            # Update Redis cache
            metrics_key = f"account_metrics:{self.config.account_id}"
            self.redis_client.hmset(metrics_key, {
                'status': self.metrics.status.value,
                'cpu_usage_percent': self.metrics.cpu_usage_percent,
                'memory_usage_mb': self.metrics.memory_usage_mb,
                'uptime_seconds': self.metrics.uptime_seconds,
                'last_heartbeat': self.metrics.last_heartbeat.isoformat(),
                'error_count': self.metrics.error_count,
                'restart_count': self.metrics.restart_count,
                'total_trades': self.metrics.total_trades,
                'total_pnl': self.metrics.total_pnl,
            })
            
            # Set expiration
            self.redis_client.expire(metrics_key, 300)  # 5 minutes
            
            # Store in database (every 5 minutes)
            if datetime.utcnow().minute % 5 == 0:
                metrics_record = AccountMetricsHistory(
                    account_id=self.config.account_id,
                    status=self.metrics.status.value,
                    cpu_usage_percent=self.metrics.cpu_usage_percent,
                    memory_usage_mb=self.metrics.memory_usage_mb,
                    network_usage_mbps=self.metrics.network_usage_mbps,
                    disk_iops=self.metrics.disk_iops,
                    db_connections=self.metrics.db_connections,
                    redis_connections=self.metrics.redis_connections,
                    orders_per_minute=self.metrics.orders_per_minute,
                    api_calls_per_minute=self.metrics.api_calls_per_minute,
                    uptime_seconds=self.metrics.uptime_seconds,
                    error_count=self.metrics.error_count,
                    restart_count=self.metrics.restart_count,
                    total_trades=self.metrics.total_trades,
                    total_pnl=self.metrics.total_pnl,
                )
                
                self.db_session.add(metrics_record)
                self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _health_check(self) -> bool:
        """Perform health check on the account"""
        try:
            # Check if process is alive
            if not self.process or not self.process.is_alive():
                return False
            
            # Check heartbeat
            time_since_heartbeat = datetime.utcnow() - self.metrics.last_heartbeat
            if time_since_heartbeat > timedelta(minutes=5):
                return False
            
            # Check resource usage
            if self.metrics.cpu_usage_percent > self.config.resource_limits.max_cpu_percent * 1.2:
                self.logger.warning(f"CPU usage exceeded limit: {self.metrics.cpu_usage_percent}%")
            
            if self.metrics.memory_usage_mb > self.config.resource_limits.max_memory_mb * 1.2:
                self.logger.warning(f"Memory usage exceeded limit: {self.metrics.memory_usage_mb}MB")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return False
    
    def _restart_account(self):
        """Restart the account after failure"""
        try:
            self.restart_attempts += 1
            self.metrics.restart_count += 1
            
            self.logger.info(f"Restarting account {self.config.account_id} (attempt {self.restart_attempts})")
            
            # Stop current process
            if self.process and self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=30)
                
                if self.process.is_alive():
                    self.process.kill()
                    self.process.join()
            
            # Wait before restart
            time.sleep(self.config.restart_delay_seconds)
            
            # Start new process
            if self._start_trading_process():
                self.metrics.status = AccountStatus.ACTIVE
                self.logger.info(f"Account {self.config.account_id} restarted successfully")
            else:
                self.metrics.status = AccountStatus.ERROR
                self.logger.error(f"Failed to restart account {self.config.account_id}")
            
        except Exception as e:
            self.logger.error(f"Error restarting account: {e}")
            self.metrics.status = AccountStatus.ERROR
    
    def _cleanup_environment(self):
        """Cleanup account environment"""
        try:
            # Cleanup temporary files, connections, etc.
            # Implementation depends on specific requirements
            pass
        except Exception as e:
            self.logger.error(f"Error cleaning up environment: {e}")

# =============================================================================
# MULTI-ACCOUNT ORCHESTRATOR
# =============================================================================

class MultiAccountOrchestrator:
    """Orchestrates multiple trading accounts with resource management"""
    
    def __init__(self, db_url: str, redis_url: str):
        self.logger = logging.getLogger(__name__)
        
        # Database setup
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Redis setup
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        
        # Components
        self.resource_manager = ResourceManager(self.redis_client)
        self.account_managers: Dict[str, AccountManager] = {}
        self.executor = ThreadPoolExecutor(max_workers=50)
        
        # Control
        self._running = False
        self._monitor_thread = None
        
    def start(self):
        """Start the multi-account orchestrator"""
        try:
            self.logger.info("Starting Multi-Account Orchestrator")
            self._running = True
            
            # Load account configurations
            self._load_account_configurations()
            
            # Start monitoring thread
            self._monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
            self._monitor_thread.start()
            
            self.logger.info("Multi-Account Orchestrator started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting orchestrator: {e}")
            raise
    
    def stop(self):
        """Stop the multi-account orchestrator"""
        try:
            self.logger.info("Stopping Multi-Account Orchestrator")
            self._running = False
            
            # Stop all accounts
            for account_id in list(self.account_managers.keys()):
                self.stop_account(account_id)
            
            # Wait for monitor thread
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=30)
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            self.logger.info("Multi-Account Orchestrator stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping orchestrator: {e}")
    
    def add_account(self, config: AccountConfig) -> bool:
        """Add a new trading account"""
        try:
            with self.SessionLocal() as session:
                # Check if account already exists
                existing = session.query(TradingAccount).filter_by(id=config.account_id).first()
                if existing:
                    self.logger.warning(f"Account {config.account_id} already exists")
                    return False
                
                # Create database record
                db_account = TradingAccount(
                    id=config.account_id,
                    name=config.account_name,
                    broker=config.broker,
                    account_type=config.account_type,
                    isolation_level=config.isolation_level.value,
                    resource_limits=config.resource_limits.__dict__,
                    trading_strategy=config.trading_strategy,
                    config_overrides=config.config_overrides,
                    environment_variables=config.environment_variables,
                    enabled=config.enabled,
                    auto_restart=config.auto_restart,
                    max_restart_attempts=config.max_restart_attempts,
                    restart_delay_seconds=config.restart_delay_seconds,
                    health_check_interval=config.health_check_interval,
                )
                
                session.add(db_account)
                session.commit()
                
                self.logger.info(f"Account {config.account_id} added successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding account {config.account_id}: {e}")
            return False
    
    def remove_account(self, account_id: str) -> bool:
        """Remove a trading account"""
        try:
            # Stop account if running
            if account_id in self.account_managers:
                self.stop_account(account_id)
            
            with self.SessionLocal() as session:
                # Remove from database
                account = session.query(TradingAccount).filter_by(id=account_id).first()
                if account:
                    session.delete(account)
                    session.commit()
                
                self.logger.info(f"Account {account_id} removed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing account {account_id}: {e}")
            return False
    
    def start_account(self, account_id: str) -> bool:
        """Start a specific trading account"""
        try:
            if account_id in self.account_managers:
                return self.account_managers[account_id].start()
            
            # Load account configuration
            config = self._load_account_config(account_id)
            if not config:
                return False
            
            # Allocate resources
            if not self.resource_manager.allocate_resources(account_id, config.resource_limits):
                self.logger.error(f"Cannot allocate resources for account {account_id}")
                return False
            
            # Create account manager
            with self.SessionLocal() as session:
                account_manager = AccountManager(config, session, self.redis_client)
                
                if account_manager.start():
                    self.account_managers[account_id] = account_manager
                    return True
                else:
                    self.resource_manager.deallocate_resources(account_id)
                    return False
            
        except Exception as e:
            self.logger.error(f"Error starting account {account_id}: {e}")
            return False
    
    def stop_account(self, account_id: str) -> bool:
        """Stop a specific trading account"""
        try:
            if account_id not in self.account_managers:
                self.logger.warning(f"Account {account_id} is not running")
                return True
            
            account_manager = self.account_managers[account_id]
            
            if account_manager.stop():
                del self.account_managers[account_id]
                self.resource_manager.deallocate_resources(account_id)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error stopping account {account_id}: {e}")
            return False
    
    def pause_account(self, account_id: str) -> bool:
        """Pause a specific trading account"""
        if account_id in self.account_managers:
            return self.account_managers[account_id].pause()
        return False
    
    def resume_account(self, account_id: str) -> bool:
        """Resume a specific trading account"""
        if account_id in self.account_managers:
            return self.account_managers[account_id].resume()
        return False
    
    def get_account_status(self, account_id: str) -> Optional[AccountMetrics]:
        """Get status of a specific account"""
        if account_id in self.account_managers:
            return self.account_managers[account_id].metrics
        return None
    
    def get_all_accounts_status(self) -> Dict[str, AccountMetrics]:
        """Get status of all accounts"""
        return {account_id: manager.metrics for account_id, manager in self.account_managers.items()}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_accounts': len(self.account_managers),
            'active_accounts': len([m for m in self.account_managers.values() if m.metrics.status == AccountStatus.ACTIVE]),
            'resource_usage': self.resource_manager.get_resource_usage_report(),
            'accounts': {account_id: {
                'status': manager.metrics.status.value,
                'uptime_seconds': manager.metrics.uptime_seconds,
                'cpu_usage_percent': manager.metrics.cpu_usage_percent,
                'memory_usage_mb': manager.metrics.memory_usage_mb,
                'total_trades': manager.metrics.total_trades,
                'total_pnl': manager.metrics.total_pnl,
            } for account_id, manager in self.account_managers.items()}
        }
    
    def _load_account_configurations(self):
        """Load all account configurations from database"""
        try:
            with self.SessionLocal() as session:
                accounts = session.query(TradingAccount).filter_by(enabled=True).all()
                
                for account in accounts:
                    config = AccountConfig(
                        account_id=account.id,
                        account_name=account.name,
                        broker=account.broker,
                        account_type=account.account_type,
                        isolation_level=IsolationLevel(account.isolation_level),
                        resource_limits=ResourceLimits(**account.resource_limits),
                        trading_strategy=account.trading_strategy,
                        config_overrides=account.config_overrides,
                        environment_variables=account.environment_variables,
                        enabled=account.enabled,
                        auto_restart=account.auto_restart,
                        max_restart_attempts=account.max_restart_attempts,
                        restart_delay_seconds=account.restart_delay_seconds,
                        health_check_interval=account.health_check_interval,
                    )
                    
                    # Auto-start enabled accounts
                    if config.enabled:
                        self.executor.submit(self.start_account, config.account_id)
                
        except Exception as e:
            self.logger.error(f"Error loading account configurations: {e}")
    
    def _load_account_config(self, account_id: str) -> Optional[AccountConfig]:
        """Load specific account configuration"""
        try:
            with self.SessionLocal() as session:
                account = session.query(TradingAccount).filter_by(id=account_id).first()
                
                if not account:
                    return None
                
                return AccountConfig(
                    account_id=account.id,
                    account_name=account.name,
                    broker=account.broker,
                    account_type=account.account_type,
                    isolation_level=IsolationLevel(account.isolation_level),
                    resource_limits=ResourceLimits(**account.resource_limits),
                    trading_strategy=account.trading_strategy,
                    config_overrides=account.config_overrides,
                    environment_variables=account.environment_variables,
                    enabled=account.enabled,
                    auto_restart=account.auto_restart,
                    max_restart_attempts=account.max_restart_attempts,
                    restart_delay_seconds=account.restart_delay_seconds,
                    health_check_interval=account.health_check_interval,
                )
                
        except Exception as e:
            self.logger.error(f"Error loading account config {account_id}: {e}")
            return None
    
    def _monitor_system(self):
        """Monitor overall system health and performance"""
        while self._running:
            try:
                # Generate system status report
                status = self.get_system_status()
                
                # Store system metrics
                self.redis_client.set(
                    'system_status',
                    json.dumps(status),
                    ex=300  # 5 minutes expiration
                )
                
                # Check for resource constraints
                resource_report = self.resource_manager.get_resource_usage_report()
                utilization = resource_report['utilization_percent']
                
                # Alert on high resource usage
                for resource, usage in utilization.items():
                    if usage > 90:
                        self.logger.warning(f"High {resource} utilization: {usage:.1f}%")
                
                # Sleep until next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
                time.sleep(10)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function for testing the multi-account architecture"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    db_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:password@localhost:5432/trading_sentinel')
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Create orchestrator
    orchestrator = MultiAccountOrchestrator(db_url, redis_url)
    
    try:
        # Start orchestrator
        orchestrator.start()
        
        # Example: Add test accounts
        test_accounts = [
            AccountConfig(
                account_id="test_account_1",
                account_name="Test Account 1",
                broker="test_broker",
                account_type="demo",
                isolation_level=IsolationLevel.ISOLATED,
                resource_limits=ResourceLimits(
                    max_cpu_percent=10.0,
                    max_memory_mb=512,
                    max_db_connections=5,
                    max_redis_connections=2
                ),
                trading_strategy="scalping"
            ),
            AccountConfig(
                account_id="test_account_2",
                account_name="Test Account 2",
                broker="test_broker",
                account_type="live",
                isolation_level=IsolationLevel.ISOLATED,
                resource_limits=ResourceLimits(
                    max_cpu_percent=15.0,
                    max_memory_mb=1024,
                    max_db_connections=8,
                    max_redis_connections=3
                ),
                trading_strategy="swing"
            )
        ]
        
        # Add and start test accounts
        for config in test_accounts:
            orchestrator.add_account(config)
            orchestrator.start_account(config.account_id)
        
        # Monitor for a while
        print("Multi-Account Orchestrator running. Press Ctrl+C to stop.")
        
        while True:
            status = orchestrator.get_system_status()
            print(f"\nSystem Status: {status['active_accounts']}/{status['total_accounts']} accounts active")
            
            for account_id, account_status in status['accounts'].items():
                print(f"  {account_id}: {account_status['status']} - {account_status['uptime_seconds']}s uptime")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main()