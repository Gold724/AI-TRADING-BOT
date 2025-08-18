#!/usr/bin/env python3
"""
Database Manager for TradeBot Sentinel Pro Advanced

Handles database connections, operations, and schema management
for all automation modules with support for SQLite, PostgreSQL, and MySQL.

Author: TradeBot Sentinel Team
Version: 2.0.0
License: MIT
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
import threading
from dataclasses import dataclass, asdict

try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


@dataclass
class TradeRecord:
    """Trade record data structure"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    symbol: str = ""
    side: str = ""  # buy/sell
    amount: float = 0.0
    price: float = 0.0
    status: str = "pending"  # pending/executed/failed/cancelled
    request_data: str = ""  # JSON string of original request
    response_data: str = ""  # JSON string of response
    execution_time: Optional[float] = None
    error_message: str = ""
    strategy: str = ""
    profit_loss: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MonitoringRecord:
    """Monitoring metrics record"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    metric_name: str = ""
    metric_value: float = 0.0
    metric_type: str = "gauge"  # gauge/counter/histogram
    tags: str = ""  # JSON string of tags
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AlertRecord:
    """Alert record data structure"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    alert_type: str = ""
    severity: str = "info"  # info/warning/error/critical
    message: str = ""
    details: str = ""  # JSON string of additional details
    acknowledged: bool = False
    resolved: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DatabaseManager:
    """
    Centralized database management for TradeBot Sentinel Pro Advanced.
    Supports SQLite, PostgreSQL, and MySQL with connection pooling.
    """
    
    def __init__(self, config_manager=None):
        """Initialize database manager"""
        self.config_manager = config_manager
        self.logger = logging.getLogger("DatabaseManager")
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.db_type = "sqlite"
        self.connection_string = ""
        
        # Initialize database
        self._initialize_database()
        self._create_tables()
        
        self.logger.info("Database manager initialized successfully")
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            if self.config_manager:
                db_config = self.config_manager.database
                self.db_type = db_config.type
                self.connection_string = self.config_manager.get_database_connection_string()
            else:
                # Default to SQLite
                self.db_type = "sqlite"
                db_path = Path("data/tradebot.db")
                db_path.parent.mkdir(parents=True, exist_ok=True)
                self.connection_string = f"sqlite:///{db_path}"
            
            # Test connection
            if self.test_connection():
                self.logger.info(f"Database connection established: {self.db_type}")
            else:
                self.logger.error("Failed to establish database connection")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            # Fallback to SQLite
            self.db_type = "sqlite"
            db_path = Path("data/tradebot.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection_string = f"sqlite:///{db_path}"
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                if self.db_type == "sqlite":
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                elif self.db_type == "postgresql" and POSTGRESQL_AVAILABLE:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                elif self.db_type == "mysql" and MYSQL_AVAILABLE:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                else:
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool or create new one"""
        conn = None
        try:
            # Try to get connection from pool
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
            
            # Create new connection if pool is empty
            if conn is None:
                conn = self._create_connection()
            
            yield conn
            
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            # Return connection to pool
            if conn:
                try:
                    with self.pool_lock:
                        if len(self.connection_pool) < 5:  # Max pool size
                            self.connection_pool.append(conn)
                        else:
                            conn.close()
                except:
                    pass
    
    def _create_connection(self):
        """Create new database connection"""
        if self.db_type == "sqlite":
            db_path = self.connection_string.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        
        elif self.db_type == "postgresql" and POSTGRESQL_AVAILABLE:
            # Parse connection string
            url = self.connection_string.replace("postgresql://", "")
            auth, host_db = url.split("@")
            username, password = auth.split(":")
            host_port, database = host_db.split("/")
            host, port = host_port.split(":")
            
            return psycopg2.connect(
                host=host,
                port=int(port),
                database=database,
                user=username,
                password=password,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        
        elif self.db_type == "mysql" and MYSQL_AVAILABLE:
            # Parse connection string
            url = self.connection_string.replace("mysql://", "")
            auth, host_db = url.split("@")
            username, password = auth.split(":")
            host_port, database = host_db.split("/")
            host, port = host_port.split(":")
            
            return mysql.connector.connect(
                host=host,
                port=int(port),
                database=database,
                user=username,
                password=password,
                dictionary=True
            )
        
        else:
            raise Exception(f"Unsupported database type: {self.db_type}")
    
    def _create_tables(self):
        """Create database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create trades table
                if self.db_type == "sqlite":
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS trades (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            symbol TEXT NOT NULL,
                            side TEXT NOT NULL,
                            amount REAL NOT NULL,
                            price REAL NOT NULL,
                            status TEXT DEFAULT 'pending',
                            request_data TEXT,
                            response_data TEXT,
                            execution_time REAL,
                            error_message TEXT,
                            strategy TEXT,
                            profit_loss REAL
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS monitoring (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            metric_name TEXT NOT NULL,
                            metric_value REAL NOT NULL,
                            metric_type TEXT DEFAULT 'gauge',
                            tags TEXT
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS alerts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            alert_type TEXT NOT NULL,
                            severity TEXT DEFAULT 'info',
                            message TEXT NOT NULL,
                            details TEXT,
                            acknowledged BOOLEAN DEFAULT FALSE,
                            resolved BOOLEAN DEFAULT FALSE
                        )
                    """)
                
                elif self.db_type == "postgresql":
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS trades (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            symbol VARCHAR(20) NOT NULL,
                            side VARCHAR(10) NOT NULL,
                            amount DECIMAL(18,8) NOT NULL,
                            price DECIMAL(18,8) NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending',
                            request_data TEXT,
                            response_data TEXT,
                            execution_time DECIMAL(10,6),
                            error_message TEXT,
                            strategy VARCHAR(50),
                            profit_loss DECIMAL(18,8)
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS monitoring (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            metric_name VARCHAR(100) NOT NULL,
                            metric_value DECIMAL(18,8) NOT NULL,
                            metric_type VARCHAR(20) DEFAULT 'gauge',
                            tags TEXT
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS alerts (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            alert_type VARCHAR(50) NOT NULL,
                            severity VARCHAR(20) DEFAULT 'info',
                            message TEXT NOT NULL,
                            details TEXT,
                            acknowledged BOOLEAN DEFAULT FALSE,
                            resolved BOOLEAN DEFAULT FALSE
                        )
                    """)
                
                conn.commit()
                self.logger.info("Database tables created successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
    
    def insert_trade(self, trade: TradeRecord) -> Optional[int]:
        """Insert trade record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO trades (timestamp, symbol, side, amount, price, status, 
                                          request_data, response_data, execution_time, 
                                          error_message, strategy, profit_loss)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trade.timestamp, trade.symbol, trade.side, trade.amount, trade.price,
                        trade.status, trade.request_data, trade.response_data, trade.execution_time,
                        trade.error_message, trade.strategy, trade.profit_loss
                    ))
                    trade_id = cursor.lastrowid
                
                elif self.db_type == "postgresql":
                    cursor.execute("""
                        INSERT INTO trades (timestamp, symbol, side, amount, price, status, 
                                          request_data, response_data, execution_time, 
                                          error_message, strategy, profit_loss)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        trade.timestamp, trade.symbol, trade.side, trade.amount, trade.price,
                        trade.status, trade.request_data, trade.response_data, trade.execution_time,
                        trade.error_message, trade.strategy, trade.profit_loss
                    ))
                    trade_id = cursor.fetchone()['id']
                
                conn.commit()
                self.logger.info(f"Trade record inserted with ID: {trade_id}")
                return trade_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert trade record: {e}")
            return None
    
    def update_trade_status(self, trade_id: int, status: str, response_data: str = "", 
                           execution_time: float = None, error_message: str = "") -> bool:
        """Update trade status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == "sqlite":
                    cursor.execute("""
                        UPDATE trades 
                        SET status = ?, response_data = ?, execution_time = ?, error_message = ?
                        WHERE id = ?
                    """, (status, response_data, execution_time, error_message, trade_id))
                
                elif self.db_type == "postgresql":
                    cursor.execute("""
                        UPDATE trades 
                        SET status = %s, response_data = %s, execution_time = %s, error_message = %s
                        WHERE id = %s
                    """, (status, response_data, execution_time, error_message, trade_id))
                
                conn.commit()
                self.logger.info(f"Trade {trade_id} status updated to: {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update trade status: {e}")
            return False
    
    def get_trades(self, limit: int = 100, status: str = None, 
                   start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get trade records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM trades WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                if self.db_type == "postgresql":
                    query = query.replace("?", "%s")
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get trades: {e}")
            return []
    
    def insert_monitoring_record(self, record: MonitoringRecord) -> Optional[int]:
        """Insert monitoring record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO monitoring (timestamp, metric_name, metric_value, metric_type, tags)
                        VALUES (?, ?, ?, ?, ?)
                    """, (record.timestamp, record.metric_name, record.metric_value, 
                          record.metric_type, record.tags))
                    record_id = cursor.lastrowid
                
                elif self.db_type == "postgresql":
                    cursor.execute("""
                        INSERT INTO monitoring (timestamp, metric_name, metric_value, metric_type, tags)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (record.timestamp, record.metric_name, record.metric_value, 
                          record.metric_type, record.tags))
                    record_id = cursor.fetchone()['id']
                
                conn.commit()
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert monitoring record: {e}")
            return None
    
    def insert_alert(self, alert: AlertRecord) -> Optional[int]:
        """Insert alert record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == "sqlite":
                    cursor.execute("""
                        INSERT INTO alerts (timestamp, alert_type, severity, message, details, 
                                          acknowledged, resolved)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (alert.timestamp, alert.alert_type, alert.severity, alert.message,
                          alert.details, alert.acknowledged, alert.resolved))
                    alert_id = cursor.lastrowid
                
                elif self.db_type == "postgresql":
                    cursor.execute("""
                        INSERT INTO alerts (timestamp, alert_type, severity, message, details, 
                                          acknowledged, resolved)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (alert.timestamp, alert.alert_type, alert.severity, alert.message,
                          alert.details, alert.acknowledged, alert.resolved))
                    alert_id = cursor.fetchone()['id']
                
                conn.commit()
                self.logger.info(f"Alert inserted with ID: {alert_id}")
                return alert_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert alert: {e}")
            return None
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Trade statistics
                cursor.execute("SELECT COUNT(*) as total_trades FROM trades")
                stats['total_trades'] = cursor.fetchone()[0 if self.db_type == 'sqlite' else 'total_trades']
                
                cursor.execute("SELECT COUNT(*) as active_trades FROM trades WHERE status = 'pending'")
                stats['active_trades'] = cursor.fetchone()[0 if self.db_type == 'sqlite' else 'active_trades']
                
                cursor.execute("SELECT COUNT(*) as successful_trades FROM trades WHERE status = 'executed'")
                stats['successful_trades'] = cursor.fetchone()[0 if self.db_type == 'sqlite' else 'successful_trades']
                
                cursor.execute("SELECT COUNT(*) as failed_trades FROM trades WHERE status = 'failed'")
                stats['failed_trades'] = cursor.fetchone()[0 if self.db_type == 'sqlite' else 'failed_trades']
                
                # Alert statistics
                cursor.execute("SELECT COUNT(*) as total_alerts FROM alerts")
                stats['total_alerts'] = cursor.fetchone()[0 if self.db_type == 'sqlite' else 'total_alerts']
                
                cursor.execute("SELECT COUNT(*) as unresolved_alerts FROM alerts WHERE resolved = 0")
                stats['unresolved_alerts'] = cursor.fetchone()[0 if self.db_type == 'sqlite' else 'unresolved_alerts']
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 30):
        """Clean up old records"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean up old monitoring records
                if self.db_type == "sqlite":
                    cursor.execute("DELETE FROM monitoring WHERE timestamp < ?", (cutoff_date,))
                    monitoring_deleted = cursor.rowcount
                    
                    cursor.execute("DELETE FROM alerts WHERE resolved = 1 AND timestamp < ?", (cutoff_date,))
                    alerts_deleted = cursor.rowcount
                
                elif self.db_type == "postgresql":
                    cursor.execute("DELETE FROM monitoring WHERE timestamp < %s", (cutoff_date,))
                    monitoring_deleted = cursor.rowcount
                    
                    cursor.execute("DELETE FROM alerts WHERE resolved = true AND timestamp < %s", (cutoff_date,))
                    alerts_deleted = cursor.rowcount
                
                conn.commit()
                self.logger.info(f"Cleaned up {monitoring_deleted} monitoring records and {alerts_deleted} resolved alerts")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
    
    def close_connections(self):
        """Close all database connections"""
        try:
            with self.pool_lock:
                for conn in self.connection_pool:
                    try:
                        conn.close()
                    except:
                        pass
                self.connection_pool.clear()
            
            self.logger.info("Database connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close_connections()